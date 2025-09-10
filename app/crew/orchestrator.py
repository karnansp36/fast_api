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
import asyncio


class CrewOrchestrator:
    def __init__(self):
        self.agents = [conversation_agent, emotion_agent, memory_agent, task_agent]
    
    def _analyze_intent(self, message: str) -> dict:
        """Simple intent analysis"""
        message_lower = message.lower()
        
        intents = {
            "memory_store": any(word in message_lower for word in ["remember", "save", "store", "don't forget"]),
            "memory_search": any(word in message_lower for word in ["recall", "what do you remember", "find", "search memory"]),
            "task_create": any(word in message_lower for word in ["remind", "reminder", "task", "schedule", "todo"]),
            "task_get": any(word in message_lower for word in ["my tasks", "my reminders", "what tasks", "show tasks"]),
            "emotional": any(word in message_lower for word in ["sad", "happy", "angry", "excited", "worried", "stressed"])
        }
        
        return intents
    
    async def process_message(self, message: str, user_id: str) -> str:
        """Process message through CrewAI"""
        try:
            intents = self._analyze_intent(message)
            tasks = []
            
            # Always add emotion analysis
            if intents["emotional"] or any(intents.values()):
                tasks.append(create_emotion_task(message))
            
            # Add specific tasks based on intent
            if intents["memory_store"]:
                tasks.append(create_memory_task(message, user_id, "store"))
            elif intents["memory_search"]:
                tasks.append(create_memory_task(message, user_id, "search"))
            
            if intents["task_create"]:
                tasks.append(create_task_management_task(message, user_id, "create"))
            elif intents["task_get"]:
                tasks.append(create_task_management_task(message, user_id, "get"))
            
            # Always add conversation task as the main coordinator
            tasks.append(create_conversation_task(message, user_id))
            
            # Create and run crew
            crew = Crew(
                agents=self.agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
                max_rpm=10,  # Add rate limiting
                memory=True  # Enable crew memory
            )
            
            # Run the crew with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(crew.kickoff),
                    timeout=30.0  # 30 second timeout
                )
                
                # Extract the final response
                if hasattr(result, 'raw'):
                    return str(result.raw)
                else:
                    return str(result)
                    
            except asyncio.TimeoutError:
                return "I apologize, but the request took too long to process. Please try again."
                
        except Exception as e:
            return f"I apologize, but I encountered an error processing your message: {str(e)}"

# Global orchestrator instance
orchestrator = CrewOrchestrator()

async def run_crew(message: str, user_id: str) -> str:
    """Main entry point for CrewAI processing"""
    return await orchestrator.process_message(message, user_id)