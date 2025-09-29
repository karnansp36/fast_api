# crew/orchestrator.py
from crewai import Crew, Process, Task
from app.services.memory_service import memory_service
from app.crew.agents.intent_extractor import intent_extractor_agent
from typing import Dict, Any
import asyncio
import logging
import time
from app.core.db import  AsyncSessionLocal  # Import AsyncSessionLocal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
logger = logging.getLogger(__name__)

class PersonalManagerOrchestrator:
    def __init__(self):
        self.agent = self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the personal manager agent"""
        try:
            from app.crew.agents.personal_manager import personal_manager_agent
            return personal_manager_agent
        except Exception as e:
            logger.error(f"Failed to load personal manager agent: {e}")
            return None
    
  # In orchestrator.py, update the process_message method:

    
    # In orchestrator.py, update the _get_user_context method and its usage:

    async def process_message(self, message: str, user_id: str) -> str:
        """Process message with intent extraction and CrewAI agent delegation."""
        if not self.agent:
            return "I'm experiencing technical difficulties. Please try again later."

        # Use a single session for the entire request
        async with AsyncSessionLocal() as session:
            try:
                # 1. Extract intent and entities asynchronously
                intent_result = await intent_extractor_agent.extract_intent(message)
                intent = intent_result.get("intent", "conversation")
                entities = intent_result.get("entities", {})
                # 2. Route based on intent
                if intent == "memory":
                    # Store memory
                    content = entities if entities else {"text": message}
                    result = await memory_service.store_memory(session, user_id, "general", content)
                    return f"I'll remember that for you. ({result})"
                elif intent == "reminder" or intent == "task":
                    from app.services.reminders import create_reminder
                    task_text = entities.get("task") or entities.get("text") or message
                    time_str = entities.get("time")
                    result = await create_reminder(task=task_text, time=time_str, user_id=user_id, db=session)
                    if "error" in result:
                        return f"Sorry, I couldn't set the reminder: {result['error']}"
                    return f"I've added that to your tasks! (Task: {result['task']})"
                elif intent == "query":
                    # Query memories or conversation history (future: retrieval agent)
                    query_text = entities.get("query") or message
                    # Try memories first
                    memories = await memory_service.search_memories(session, user_id, query=query_text, limit=3)
                    if memories:
                        return f"Here's what I found: " + ", ".join([m['text'] for m in memories])
                    # Fallback: conversation history
                    history = await memory_service.get_conversation_history(session, user_id, 10)
                    matches = [h for h in history if query_text.lower() in h['message'].lower() or query_text.lower() in h['response'].lower()]
                    if matches:
                        return f"From our past conversations: " + ", ".join([m['response'] for m in matches])
                    return "I couldn't find that information in your records."
                # 3. Default: normal conversation
                context = await self._get_user_context(session, user_id)
                task = self._create_personal_manager_task(message, context)
                crew = Crew(
                    agents=[self.agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False
                )
                result = await asyncio.to_thread(crew.kickoff)
                response = str(result)
                storage_success = await memory_service.store_conversation(session, user_id, message, response)
                if storage_success:
                    logger.info(f"✅ Conversation stored successfully for user {user_id}")
                else:
                    logger.warning(f"⚠️ Failed to store conversation for user {user_id}")
                return response
            except Exception as e:
                logger.error(f"Personal manager failed: {e}")
                await session.rollback()
                error_response = "I apologize, but I'm having trouble processing your request right now. Could you please try again?"
                try:
                    await memory_service.store_conversation(session, user_id, message, error_response, "error")
                except:
                    pass
                return error_response

    async def _get_user_context(self, session: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context using provided session - UPDATED SIGNATURE"""
        try:
            # Update all internal calls to use the passed session
            # You'll need to update memory_service methods to accept session parameter
            
            # Get recent conversation history
            conversation_history = await memory_service.get_conversation_history(session, user_id, 5)
            
            # Get recent memories
            recent_memories = await memory_service.search_memories(session, user_id, limit=5)
            
            # Get user preferences
            preferences = await memory_service.search_memories(session, user_id, "preference", limit=5)
            
            # Get pending tasks
            pending_tasks = await memory_service.get_user_tasks(session, user_id, status="pending")
            
            return {
                "conversation_history": conversation_history,
                "recent_memories": recent_memories,
                "preferences": preferences,
                "pending_tasks": pending_tasks,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {}




    def _create_personal_manager_task(self, message: str, context: Dict[str, Any]) -> Task:
        """Create task for personal manager with full context"""
        
        # Format conversation history
        history_text = ""
        if context.get("conversation_history"):
            for exchange in context["conversation_history"]:
                history_text += f"User: {exchange['message']}\nAssistant: {exchange['response']}\n\n"
        
        # Format recent memories
        memories_text = ""
        if context.get("recent_memories"):
            for memory in context["recent_memories"]:
                memories_text += f"- {memory['text'][:100]}...\n"
        
        # Format preferences
        preferences_text = ""
        if context.get("preferences"):
            for pref in context["preferences"]:
                preferences_text += f"- {pref['text'][:100]}...\n"
        
        return Task(
            description=f"""Have a natural, empathetic conversation with the user while handling any background tasks seamlessly.

USER MESSAGE: {message}


USER CONTEXT:
- Conversation History:
{history_text if history_text else '  No recent conversation history'}

- Recent Memories:
{memories_text if memories_text else '  No recent memories'}

- User Preferences:
{preferences_text if preferences_text else '  No stored preferences'}

INSTRUCTIONS:
1. Respond naturally and empathetically to the user's message
2. Adjust your tone based on the detected emotion
3. Use tools as needed to handle tasks, reminders, or memory operations
4. Never mention technical details or delegation - just confirm actions naturally
5. Reference previous conversations and user context when relevant
6. Maintain a consistent, warm personality throughout
7. If using tools, integrate the results seamlessly into the conversation

EXAMPLE RESPONSES:
- For task creation: "Sure, I've added that to your tasks!"
- For memory storage: "I'll remember that for you."
- For emotional content: "I understand how you're feeling. [empathetic response]"

Keep your response conversational and focused on the user's needs.""",
            agent=self.agent,
            expected_output="A natural, empathetic response that addresses the user's message and handles any background tasks seamlessly"
        )
    
    
# Global orchestrator instance
_orchestrator_instance = None

def get_orchestrator() -> PersonalManagerOrchestrator:
    """Get singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = PersonalManagerOrchestrator()
    return _orchestrator_instance

async def run_personal_manager(message: str, user_id: str) -> str:
    """Main entry point for personal manager processing"""
    orchestrator = get_orchestrator()
    return await orchestrator.process_message(message, user_id)