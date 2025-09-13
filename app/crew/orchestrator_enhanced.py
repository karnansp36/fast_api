from crewai import Crew, Process
from app.crew.agents.router import get_router
from app.services.memory_service import MemoryService
from typing import Dict, Any, List
import asyncio
import logging
import time
from app.crew.llm_config import default_llm

logger = logging.getLogger(__name__)

class EnhancedOrchestrator:
    def __init__(self):
        self.memory_service = MemoryService()
        self.router = get_router()
        self.agent_instances = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all available agents"""
        agents = {}
        
        try:
            from app.crew.agents.conversation import conversation_agent
            # Import tool here to avoid circular imports
            from app.tools.async_delegation_tool import AsyncDelegationTool
            # Add tool to conversation agent
            if hasattr(conversation_agent, 'tools'):
                conversation_agent.tools.append(AsyncDelegationTool())
            else:
                conversation_agent.tools = [AsyncDelegationTool()]
            agents["conversation_agent"] = conversation_agent
        except Exception as e:
            logger.error(f"Failed to load conversation agent: {e}")
            
        try:
            from app.crew.agents.emotion import emotion_agent
            agents["emotion_agent"] = emotion_agent
        except Exception as e:
            logger.error(f"Failed to load emotion agent: {e}")
            
        try:
            from app.crew.agents.memory import memory_agent
            agents["memory_agent"] = memory_agent
        except Exception as e:
            logger.error(f"Failed to load memory agent: {e}")
            
        try:
            from app.crew.agents.task import task_agent
            agents["task_agent"] = task_agent
        except Exception as e:
            logger.error(f"Failed to load task agent: {e}")
            
        return agents
    
    async def process_message(self, message: str, user_id: str) -> str:
        """Enhanced message processing with conversation agent as primary interface"""
        # Get user context
        context = await self._get_user_context(user_id)
        
        # Use router to determine which agents should handle this in background
        selected_agent_names = await self.router.select_best_agent(message, context)
        
        # Filter out conversation agent (we'll handle that separately)
        background_agents = [name for name in selected_agent_names 
                           if name in self.agent_instances and name != "conversation_agent"]
        
        # Add background agents info to context for conversation agent to use
        context['background_agents'] = background_agents
        context['background_actions'] = self._determine_agent_actions(message, background_agents)
        
        # Execute only with conversation agent (which will handle background delegation)
        result = await self._execute_single_agent("conversation_agent", message, user_id, context)
        
        # Update performance metrics
        success = len(result.strip()) > 10
        self.router.update_agent_performance("conversation_agent", success)
        
        return result
    
    def _determine_agent_actions(self, message: str, agent_names: List[str]) -> Dict[str, str]:
        """Determine what actions background agents should take"""
        actions = {}
        message_lower = message.lower()
        
        for agent_name in agent_names:
            if agent_name == "memory_agent":
                if any(word in message_lower for word in ["remember", "store", "save"]):
                    actions[agent_name] = "store"
                else:
                    actions[agent_name] = "search"
            elif agent_name == "task_agent":
                if any(word in message_lower for word in ["create", "add", "new", "set"]):
                    actions[agent_name] = "create"
                else:
                    actions[agent_name] = "get"
            elif agent_name == "emotion_agent":
                actions[agent_name] = "analyze"
                
        return actions
    
    async def _execute_single_agent(self, agent_name: str, message: str, user_id: str, context: Dict[str, Any]) -> str:
        """Execute with a single agent"""
        agent = self.agent_instances[agent_name]
        
        # Create appropriate task based on agent type
        task = self._create_task_for_agent(agent_name, message, user_id, context)
        
        # Execute the task
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = await asyncio.to_thread(crew.kickoff)
        return str(result)
    
    def _create_task_for_agent(self, agent_name: str, message: str, user_id: str, context: Dict[str, Any]):
        """Create appropriate task based on agent type"""
        from app.crew.tasks import create_conversation_task
        
        if agent_name == "conversation_agent":
            return create_conversation_task(message, user_id, context)
        # Other agents are handled through async delegation
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context from memory service"""
        context = {
            "recent_conversation": [],
            "user_info": [],
            "pending_tasks": [],
            "timestamp": time.time()
        }
        
        try:
            context["recent_conversation"] = await self.memory_service.search_memories(
                user_id, "conversation", limit=5
            )
        except Exception as e:
            logger.warning(f"Could not fetch recent conversations: {e}")
        
        try:
            context["user_info"] = await self.memory_service.search_memories(
                user_id, "personal_info", limit=10
            )
        except Exception as e:
            logger.warning(f"Could not fetch user info: {e}")
            
        return context

# Global enhanced orchestrator instance
_enhanced_orchestrator_instance = None

def get_enhanced_orchestrator() -> EnhancedOrchestrator:
    """Get singleton enhanced orchestrator instance"""
    global _enhanced_orchestrator_instance
    if _enhanced_orchestrator_instance is None:
        _enhanced_orchestrator_instance = EnhancedOrchestrator()
    return _enhanced_orchestrator_instance

async def run_enhanced_crew(message: str, user_id: str) -> str:
    """Main entry point for enhanced CrewAI processing"""
    orchestrator = get_enhanced_orchestrator()
    return await orchestrator.process_message(message, user_id)