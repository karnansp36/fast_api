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
from typing import Dict, Any, List, Optional
import re
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class CrewOrchestrator:
    def __init__(self):
        self.agents = [conversation_agent, emotion_agent, memory_agent, task_agent]
        self.memory_service = MemoryService()
        # self.task_service = TaskService()
        self.conversation_context = {}
        self.fallback_responses = [
            "I appreciate your message. How can I help you with that?",
            "Thank you for sharing. How can I assist you today?",
            "I understand. What would you like me to help you with?",
            "That's interesting. How can I be of service?",
            "I'm here to help. What do you need assistance with?"
        ]
    
    def _analyze_intent(self, message: str, user_id: str) -> Dict[str, Any]:
        """Comprehensive intent analysis with pattern matching"""
        message_lower = message.lower().strip()
        
        # Greeting patterns
        greeting_patterns = [
            r"^(hi|hello|hey|greetings|howdy|good\s(morning|afternoon|evening))",
            r"^(what's up|sup|yo|hi there|hello there)",
            r"^(how are you|how's it going|how do you do)"
        ]
        
        # Memory patterns
        memory_patterns = {
            "memory_store": [
                r"(remember|save|store|don't forget|note that|keep in mind|make a note)",
                r"(my name is|call me|nickname is|i am|i'm called|my (email|phone|address) is)",
                r"(i live in|my address is|contact me at)"
            ],
            "memory_search": [
                r"(recall|what did i say|what do you remember|find|search memory|my info|my details)",
                r"(tell me about|do you remember|have i told you|my previous messages)"
            ]
        }

        # Task patterns
        task_patterns = {
            "task_create": [
                r"(remind|reminder|task|schedule|todo|set a|create|add|need to|should|must|have to)",
                r"(set alarm|create event|add to calendar|plan|organize)"
            ],
            "task_get": [
                r"(my tasks|my reminders|what tasks|show tasks|list tasks|pending tasks)",
                r"(what do i have to do|upcoming tasks|my schedule|my todos)"
            ]
        }
        
        # Emotional patterns
        emotion_words = [
            "sad", "happy", "angry", "excited", "worried", "stressed", 
            "frustrated", "annoyed", "delighted", "upset", "anxious", "depressed",
            "joy", "anger", "fear", "surprise", "love", "hate", "nervous", "calm"
        ]
        
        # Question patterns
        question_words = ["what", "when", "where", "why", "how", "who", "which", "can", "could", "would"]
        
        # Analyze patterns
        intents = {
            "type": "complex",
            "needs_processing": True,
            "is_greeting": any(re.search(pattern, message_lower) for pattern in greeting_patterns),
            "memory_store": any(re.search(pattern, message_lower) for pattern in memory_patterns["memory_store"]),
            "memory_search": any(re.search(pattern, message_lower) for pattern in memory_patterns["memory_search"]),
            "task_create": any(re.search(pattern, message_lower) for pattern in task_patterns["task_create"]),
            "task_get": any(re.search(pattern, message_lower) for pattern in task_patterns["task_get"]),
            "emotional": any(word in message_lower for word in emotion_words),
            "is_question": any(word in message_lower for word in question_words),
            "message_length": len(message.split()),
            "has_entities": len(message.split()) > 2
        }
        
        # Determine primary intent type
        if intents["is_greeting"]:
            intents["type"] = "greeting"
            intents["needs_processing"] = False
        elif intents["memory_store"] or intents["memory_search"]:
            intents["type"] = "memory"
        elif intents["task_create"] or intents["task_get"]:
            intents["type"] = "task"
        elif intents["emotional"]:
            intents["type"] = "emotional"
        elif intents["is_question"]:
            intents["type"] = "question"
        
        return intents
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Safely get user context with comprehensive error handling"""
        context = {
            "recent_conversation": [],
            "user_info": [],
            "pending_tasks": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get recent conversation history
            try:
                context["recent_conversation"] = await self.memory_service.search_memories(
                    user_id, "conversation", limit=5
                )
            except Exception as e:
                logger.warning(f"Could not fetch recent conversations: {e}")
            
            # Get user preferences and personal info
            try:
                context["user_info"] = await self.memory_service.search_memories(
                    user_id, "personal_info", limit=10
                )
            except Exception as e:
                logger.warning(f"Could not fetch user info: {e}")
            
            # Get pending tasks (commented out for now)
            # try:
            #     context["pending_tasks"] = await self.task_service.get_tasks(user_id, completed=False)
            # except Exception as e:
            #     logger.warning(f"Could not fetch tasks: {e}")
                
        except Exception as e:
            logger.error(f"Error in _get_user_context: {e}")
        
        return context
    
    async def _store_conversation_memory(self, user_id: str, message: str, message_type: str) -> bool:
        """Safely store conversation memory"""
        try:
            await self.memory_service.store_memory(
                user_id, 
                "conversation", 
                {
                    "message": message, 
                    "type": message_type,
                    "timestamp": datetime.now().isoformat()
                },
                meta_data={
                    "timestamp": datetime.now().isoformat(),
                    "sentiment": "neutral",
                    "processed": False
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error storing {message_type} memory: {e}")
            return False
    
    async def _handle_simple_greeting(self, message: str, user_id: str) -> str:
        """Handle greeting messages with personalized response"""
        try:
            # Try to get user context for personalization
            user_context = await self._get_user_context(user_id)
            
            # Extract user name if available
            user_name = "there"
            if user_context.get('user_info'):
                for mem in user_context['user_info']:
                    if mem.get('content', {}).get('name'):
                        user_name = mem['content']['name']
                        break
            
            # Generate appropriate greeting response
            message_lower = message.lower()
            
            if "how are you" in message_lower:
                return f"I'm doing well, thank you for asking {user_name}! How can I help you today?"
            elif "good morning" in message_lower:
                return f"Good morning {user_name}! How can I assist you today?"
            elif "good afternoon" in message_lower:
                return f"Good afternoon {user_name}! What can I help you with?"
            elif "good evening" in message_lower:
                return f"Good evening {user_name}! How can I be of service?"
            else:
                return f"Hello {user_name}! How can I help you today?"
                
        except Exception as e:
            logger.error(f"Error in greeting handler: {e}")
            return "Hello! How can I assist you today?"
    
    def _select_tasks_based_on_intent(self, message: str, user_id: str, intents: Dict[str, Any], context: Dict[str, Any]) -> List:
        """Select appropriate tasks based on analyzed intents"""
        tasks = []
        
        # Always add conversation task as base
        tasks.append(create_conversation_task(message, user_id, context))
        
        # Add specialized tasks based on intent
        if intents["emotional"]:
            tasks.append(create_emotion_task(message))
        
        if intents["memory_store"]:
            tasks.append(create_memory_task(message, user_id, "store"))
        
        if intents["memory_search"]:
            tasks.append(create_memory_task(message, user_id, "search"))
        
        if intents["task_create"]:
            tasks.append(create_task_management_task(message, user_id, "create"))
        
        if intents["task_get"]:
            tasks.append(create_task_management_task(message, user_id, "get"))
        
        return tasks
    
    async def _execute_crew_processing(self, tasks: List, timeout: int = 90) -> Optional[str]:
        """Execute crew processing with robust error handling"""
        if not tasks:
            return None
            
        try:
            crew = Crew(
                agents=self.agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
                max_rpm=5,
                memory=False   
            )
            
            result = await asyncio.wait_for(
                asyncio.to_thread(crew.kickoff),
                timeout=timeout
            )
            
            return str(result.raw) if hasattr(result, 'raw') else str(result)
            
        except asyncio.TimeoutError:
            logger.warning("Crew processing timeout")
            return "I apologize, but the request took too long to process. Please try again with a simpler question."
        except Exception as crew_error:
            logger.error(f"Crew processing error: {crew_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def _handle_with_conversation_agent_only(self, message: str, user_id: str, context: Dict[str, Any]) -> str:
        """Handle message using just the conversation agent"""
        try:
            conversation_task = create_conversation_task(message, user_id, context)
            
            mini_crew = Crew(
                agents=[conversation_agent],
                tasks=[conversation_task],
                process=Process.sequential,
                verbose=False,
                memory=False   
            )
            
            result = await asyncio.wait_for(
                asyncio.to_thread(mini_crew.kickoff),
                timeout=30
            )
            
            return str(result.raw) if hasattr(result, 'raw') else str(result)
            
        except Exception as e:
            logger.error(f"Error in conversation-only agent: {e}")
            return self._generate_fallback_response(message)
    
    def _generate_fallback_response(self, message: str) -> str:
        """Generate intelligent fallback responses based on message content"""
        message_lower = message.lower()
        
        # Question patterns
        if any(word in message_lower for word in ["what", "when", "where", "why", "how", "who"]):
            return "That's an interesting question. I'd be happy to help you with that. Could you provide a bit more context?"
        
        # Request patterns
        if any(word in message_lower for word in ["can you", "could you", "would you", "please"]):
            return "I'd be glad to help with that. Please tell me more about what you need."
        
        # Emotional content
        emotion_words = ["sad", "happy", "angry", "worried", "excited", "frustrated"]
        if any(word in message_lower for word in emotion_words):
            return "I understand this might be important to you. Let me help you work through this."
        
        # Long messages
        if len(message.split()) > 8:
            return "Thank you for sharing that with me. I understand what you're saying. How can I best assist you with this?"
        
        # Default engaging response
        return self.fallback_responses[len(message) % len(self.fallback_responses)]
    
    async def process_message(self, message: str, user_id: str) -> str:
        """Main message processing pipeline with comprehensive error handling"""
        if not message or not message.strip():
            return "I didn't receive your message. Could you please try again?"
        
        try:
            # Step 1: Analyze intent
            intents = self._analyze_intent(message, user_id)
            logger.info(f"Message: '{message}' | Intents: {intents}")
            
            # Step 2: Handle simple greetings without full processing
            if intents["type"] == "greeting":
                response = await self._handle_simple_greeting(message, user_id)
                # Still try to store the greeting for context
                await self._store_conversation_memory(user_id, message, "user_input")
                await self._store_conversation_memory(user_id, response, "assistant_response")
                return response
            
            # Step 3: Get user context
            user_context = await self._get_user_context(user_id)
            
            # Step 4: Store user input (with error tolerance)
            await self._store_conversation_memory(user_id, message, "user_input")
            
            # Step 5: Select appropriate tasks
            tasks = self._select_tasks_based_on_intent(message, user_id, intents, user_context)
            
            # Step 6: Process with appropriate strategy
            final_response = None
            
            # Use full crew for complex messages or multiple intents
            if len(tasks) > 1 or (intents["is_question"] and intents["message_length"] > 5):
                final_response = await self._execute_crew_processing(tasks)
            
            # Fallback to conversation agent if crew failed or for simple messages
            if not final_response:
                final_response = await self._handle_with_conversation_agent_only(message, user_id, user_context)
            
            # Final fallback if everything else fails
            if not final_response:
                final_response = self._generate_fallback_response(message)
            
            # Step 7: Store assistant response
            await self._store_conversation_memory(user_id, final_response, "assistant_response")
            
            return final_response
            
        except Exception as e:
            logger.error(f"Critical error in process_message: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return "I apologize, but I encountered an unexpected error while processing your message. Please try again with a different message or rephrase your request."


# Global orchestrator instance with lazy initialization
_orchestrator_instance = None

def get_orchestrator() -> CrewOrchestrator:
    """Get singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = CrewOrchestrator()
    return _orchestrator_instance

async def run_crew(message: str, user_id: str) -> str:
    """Main entry point for CrewAI processing"""
    orchestrator = get_orchestrator()
    return await orchestrator.process_message(message, user_id)