# crew/orchestrator.py
from crewai import Crew, Process
from app.crew.agents.conversation import conversation_agent
from app.crew.agents.emotion import emotion_agent
from app.crew.agents.memory import memory_agent
from app.crew.agents.task import task_agent
from app.crew.tasks import (
    create_conversation_task, 
    create_emotion_task, 
    create_memory_task, 
    create_task_management_task
)
from app.services.memory_service import MemoryService
# from app.services.task_service import TaskService
import asyncio
from typing import Dict, Any
import re
import logging
import traceback

logger = logging.getLogger(__name__)

class CrewOrchestrator:
    def __init__(self):
        self.agents = [conversation_agent, emotion_agent, memory_agent, task_agent]
        self.memory_service = MemoryService()
        # self.task_service = TaskService()
        self.conversation_context = {}
    
    def _analyze_intent(self, message: str, user_id: str) -> dict:
        """Enhanced intent analysis with better fallback handling"""
        message_lower = message.lower().strip()
        
        # Check for simple greetings
        if message_lower in ["hi", "hello", "hey", "hi there", "hello there"]:
            return {"type": "greeting", "needs_processing": False}
        
        # Memory patterns
        memory_patterns = {
            "memory_store": r"(remember|save|store|don't forget|note that|keep in mind|make a note)",
            "memory_search": r"(recall|what did i say|what do you remember|find|search memory|my info|my details|tell me about)",
            "personal_info": r"(my name is|call me|nickname is|i am|i'm called|my (email|phone|address) is)"
        }

        # Task patterns
        task_patterns = {
            "task_create": r"(remind|reminder|task|schedule|todo|set a|create|add|need to|should|must|have to)",
            "task_get": r"(my tasks|my reminders|what tasks|show tasks|list tasks|pending tasks|what do i have to do)"
        }
        
        # Question patterns
        question_patterns = r"(what|when|where|why|how|who|which|can you|could you|would you|do you)"
        
        # Emotional content
        emotion_words = ["sad", "happy", "angry", "excited", "worried", "stressed", 
                        "frustrated", "annoyed", "delighted", "upset", "anxious", "depressed",
                        "joy", "anger", "fear", "surprise", "love", "hate"]
        
        intents = {
            "type": "complex",
            "needs_processing": True,
            "memory_store": any(re.search(pattern, message_lower) for pattern in [memory_patterns["memory_store"]]),
            "memory_search": any(re.search(pattern, message_lower) for pattern in [memory_patterns["memory_search"]]),
            "personal_info": any(re.search(pattern, message_lower) for pattern in [memory_patterns["personal_info"]]),
            "task_create": any(re.search(pattern, message_lower) for pattern in [task_patterns["task_create"]]),
            "task_get": any(re.search(pattern, message_lower) for pattern in [task_patterns["task_get"]]),
            "emotional": any(word in message_lower for word in emotion_words),
            "is_question": bool(re.search(question_patterns, message_lower)),
            "has_entities": len(message.split()) > 3  # Longer messages likely need processing
        }
        
        # Default to conversation if it's a question or longer message
        if intents["is_question"] or intents["has_entities"]:
            intents["needs_conversation"] = True
        
        return intents
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context from memory for personalized responses"""
        try:
            # Get recent conversation history
            recent_memories = await self.memory_service.search_memories(
                user_id, "conversation", limit=5
            )
            
            # Get user preferences and personal info
            user_info = await self.memory_service.search_memories(
                user_id, "personal_info", limit=10
            )
            
            # Get pending tasks (commented out for now)
            # pending_tasks = await self.task_service.get_tasks(user_id, completed=False)
            pending_tasks = []
            
            return {
                "recent_conversation": recent_memories,
                "user_info": user_info,
                "pending_tasks": pending_tasks
            }
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {}
    
    async def _handle_simple_message(self, message: str, user_id: str) -> str:
        """Handle simple messages without full crew processing"""
        try:
            user_context = await self._get_user_context(user_id)
            
            # Personalized greeting based on context
            if user_context.get('user_info'):
                user_name = next((mem['content'].get('name') for mem in user_context['user_info'] 
                                if mem['content'].get('name')), "there")
                return f"Hello {user_name}! How can I help you today?"
            
            return "Hello! How can I assist you today?"
        except Exception as e:
            return "Hello! How can I help you today?"
    
    async def process_message(self, message: str, user_id: str) -> str:
        """Process message through CrewAI with better fallback handling"""
        try:
            # Analyze intent
            intents = self._analyze_intent(message, user_id)
            logger.info(f"Analyzed intents: {intents}")
            
            # Handle simple greetings without crew processing
            if intents.get("type") == "greeting":
                response = await self._handle_simple_message(message, user_id)
                return response
            
            # Store conversation in memory
            try:
                await self.memory_service.store_memory(
                    user_id, 
                    "conversation", 
                    {"message": message, "type": "user_input"},
                    meta_data={"timestamp": "now", "sentiment": "neutral"}
                )
            except Exception as e:
                logger.error(f"Error storing memory: {e}")
            
            # Get user context
            user_context = await self._get_user_context(user_id)
            
            tasks = []
            
            # Add tasks based on specific intents
            if intents["emotional"]:
                tasks.append(create_emotion_task(message))
            
            if intents["memory_store"] or intents["personal_info"]:
                tasks.append(create_memory_task(message, user_id, "store"))
            
            if intents["memory_search"]:
                tasks.append(create_memory_task(message, user_id, "search"))
            
            if intents["task_create"]:
                tasks.append(create_task_management_task(message, user_id, "create"))
            
            if intents["task_get"]:
                tasks.append(create_task_management_task(message, user_id, "get"))
            
            # Always add conversation task for better handling of unstructured messages
            # FIX: Pass context parameter correctly
            tasks.append(create_conversation_task(message, user_id, user_context))
            
            # Use crew for processing if we have specific tasks OR if it's a complex message
            if len(tasks) > 1 or (intents["is_question"] and len(message.split()) > 5):
                crew = Crew(
                    agents=self.agents,
                    tasks=tasks,
                    process=Process.sequential,
                    verbose=True,
                    max_rpm=5,
                    memory=True
                )
                
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(crew.kickoff),
                        timeout=120
                    )
                    
                    final_response = str(result.raw) if hasattr(result, 'raw') else str(result)
                    
                except asyncio.TimeoutError:
                    final_response = "I apologize, but the request took too long to process. Please try again with a simpler question."
                    logger.warning("Crew processing timeout")
                except Exception as crew_error:
                    logger.error(f"Crew processing error: {crew_error}")
                    final_response = await self._handle_with_conversation_agent(message, user_id, user_context)
            else:
                # Use conversation agent directly for simpler messages
                final_response = await self._handle_with_conversation_agent(message, user_id, user_context)
            
            # Store assistant response
            try:
                await self.memory_service.store_memory(
                    user_id, 
                    "conversation", 
                    {"message": final_response, "type": "assistant_response"},
                    meta_data={"timestamp": "now"}
                )
            except Exception as e:
                logger.error(f"Error storing response memory: {e}")
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return "I apologize, but I encountered an unexpected error. Please try again with a different message."
        

    async def _handle_with_conversation_agent(self, message: str, user_id: str, context: dict) -> str:
        """Handle message using just the conversation agent"""
        try:
            # Create a minimal crew with just conversation agent
            # FIX: Pass context parameter correctly
            conversation_task = create_conversation_task(message, user_id, context)
            
            mini_crew = Crew(
                agents=[conversation_agent],
                tasks=[conversation_task],
                process=Process.sequential,
                verbose=False,
                memory=True
            )
            
            result = await asyncio.wait_for(
                asyncio.to_thread(mini_crew.kickoff),
                timeout=30
            )
            
            return str(result.raw) if hasattr(result, 'raw') else str(result)
            
        except Exception as e:
            logger.error(f"Error in conversation agent: {e}")
            # Fallback to simple response
            return self._generate_fallback_response(message)
    def _generate_fallback_response(self, message: str) -> str:
        """Generate intelligent fallback responses"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["what", "when", "where", "why", "how", "who"]):
            return "That's an interesting question. I'd be happy to help you with that. Could you provide a bit more context?"
        
        if any(word in message_lower for word in ["can you", "could you", "would you"]):
            return "I'd be glad to help with that. Please tell me more about what you need."
        
        if len(message.split()) > 8:  # Longer messages
            return "Thank you for sharing that with me. I understand what you're saying. How can I best assist you with this?"
        
        # Default engaging response
        return "I appreciate your message. How can I help you with that today?"


    


# Global orchestrator instance
orchestrator = CrewOrchestrator()

async def run_crew(message: str, user_id: str) -> str:
    """Main entry point for CrewAI processing"""
    return await orchestrator.process_message(message, user_id)


