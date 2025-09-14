# crew/tasks.py
from crewai import Task
from app.crew.agents.conversation import conversation_agent
from app.crew.agents.emotion import emotion_agent
from app.crew.agents.memory import memory_agent
from app.crew.agents.task import task_agent
from typing import Dict, Any

# crew/tasks.py - UPDATED CONVERSATION TASK
def create_conversation_task(message: str, user_id: str, context: Dict[str, Any]) -> Task:
    """Create a conversation task that handles both chat and delegation"""
    
    background_agents = context.get('background_agents', [])
    background_actions = context.get('background_actions', {})
    
    if background_agents:
        # Task with delegation capability
        return Task(
            description=f"""Continue the conversation with the user while handling background tasks.
            
            User Message: {message}
            
            User Context:
            - Recent conversation: {context.get('recent_conversation', [])}
            - User information: {context.get('user_info', [])}
            - Pending tasks: {context.get('pending_tasks', [])}
            
            Background tasks needed:
            {', '.join([f'{agent}: {action}' for agent, action in background_actions.items()])}
            
            Instructions:
            1. First, provide a natural conversational response to the user
            2. Then, use the AsyncDelegationTool to handle the background tasks
            3. Never mention that you're delegating tasks - keep the conversation natural
            4. If it's a task creation, confirm it was done naturally
            5. Reference previous conversations when relevant
            """,
            agent=conversation_agent,
            expected_output="A natural conversational response that addresses the user's message and handles any background tasks seamlessly"
        )
    else:
        # Pure conversation task
        return Task(
            description=f"""Have a natural conversation with the user, referencing previous context when appropriate.
            
            User Message: {message}
            
            User Context:
            - Recent conversation: {context.get('recent_conversation', [])}
            - User information: {context.get('user_info', [])}
            - Pending tasks: {context.get('pending_tasks', [])}
            
            Instructions:
            1. Respond naturally to the user's message
            2. Reference previous conversations or user information when relevant
            3. Maintain a friendly, helpful tone
            4. If the user asks about tasks or reminders, respond conversationally
            5. Only use delegation if explicitly asked to create/store something
            """,
            agent=conversation_agent,
            expected_output="A natural, contextual conversational response"
        )
    


def create_emotion_task(message: str) -> Task:
    return Task(
        description=f"""
        Analyze the emotional tone of this message: "{message}"
        
        Identify:
        1. Primary emotion (happy, sad, angry, anxious, excited, neutral)
        2. Emotional intensity (low, medium, high)
        3. Any emotional context that might affect the response
        
        Provide insights that will help other agents respond appropriately.
        Keep your response concise and focused on emotional analysis only.
        """,
        agent=emotion_agent,
        expected_output="Emotional analysis with detected emotion, intensity, and response recommendations"
    )

def create_memory_task(message: str, user_id: str, action: str) -> Task:
    if action == "store":
        return Task(
            description=f"""
            Store important information from this message: "{message}" for user {user_id}.
            
            Extract and store:
            1. Key facts or information the user wants remembered
            2. Personal preferences mentioned
            3. Important details for future reference
            
            Use the store_memory tool to save this information.
            Make sure to extract the actual content to store, not just the instruction.
            """,
            agent=memory_agent,
            expected_output="Confirmation that memory has been stored with details of what was saved"
        )
    else:  # search
        return Task(
            description=f"""
            Search for relevant memories for user {user_id} based on query: "{message}"
            
            Find and retrieve:
            1. Related memories that match the query
            2. Contextually relevant information
            3. Personal details that might be helpful
            
            Use the search_memory tool to find relevant information.
            """,
            agent=memory_agent,
            expected_output="Relevant memories found based on the search query"
        )

def create_task_management_task(message: str, user_id: str, action: str) -> Task:
    if action == "create":
        return Task(
            description=f"""
            Create a reminder or task based on this request: "{message}" for user {user_id}.
            
            Extract:
            1. What task/reminder to create (be specific)
            2. When it should be scheduled (must be in ISO format like "2023-12-25 14:30" or "now")
            3. Any additional details
            
            If no time is specified, use "now".
            Use the create_reminder tool to set up the task.
            Make sure to pass string values, not dictionaries, to the tool.
            """,
            agent=task_agent,
            expected_output="Confirmation that the reminder/task has been created with details"
        )
    else:  # get
        return Task(
            description=f"""
            Retrieve all current tasks and reminders for user {user_id}.
            
            Use the get_reminders tool to fetch the user's tasks and present them 
            in an organized, helpful format.
            """,
            agent=task_agent,
            expected_output="List of current tasks and reminders for the user"
        )