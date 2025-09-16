# crew/orchestrator.py
from crewai import Crew, Process, Task
from app.services.memory_service import memory_service
from app.services.emotion_service import emotion_service
from typing import Dict, Any
import asyncio
import logging
import time

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
    
    async def process_message(self, message: str, user_id: str) -> str:
        """Process message with personal manager agent"""
        if not self.agent:
            return "I'm experiencing technical difficulties. Please try again later."
        
        # Get user context
        context = await self._get_user_context(user_id)
        
        # Detect emotion
        emotion_data = emotion_service.detect_emotion(message)
        emotion = emotion_data.get("emotion", "neutral")
        
        # Create task for the personal manager
        task = self._create_personal_manager_task(message, context, emotion)
        
        try:
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )
            
            # Execute the crew
            result = await asyncio.to_thread(crew.kickoff)
            response = str(result)
            
            # Store conversation in history
            await memory_service.store_conversation(user_id, message, response, emotion)
            
            return response
            
        except Exception as e:
            logger.error(f"Personal manager failed: {e}")
            # Fallback response
            return "I apologize, but I'm having trouble processing your request right now. Could you please try again?"
    
    def _create_personal_manager_task(self, message: str, context: Dict[str, Any], emotion: str) -> Task:
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

DETECTED EMOTION: {emotion}

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
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context"""
        return await memory_service.get_user_context(user_id)

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