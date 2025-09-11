# crew/tasks.py
from crewai import Task
from app.crew.agents.conversation import conversation_agent
from app.crew.agents.emotion import emotion_agent
from app.crew.agents.memory import memory_agent
from app.crew.agents.task import task_agent

def create_conversation_task(message: str, user_id: str) -> Task:
    return Task(
        description=f"""
        Analyze the user message: "{message}" from user {user_id}.
        
        IMPORTANT: You are the main coordinator. Use the Ask question to coworker tool to 
        get information from other agents, but provide the final response yourself.
        
        Determine the intent and coordinate with other agents as needed:
        1. If the user wants to remember something, ask the memory agent
        2. If the user wants to create a reminder/task, ask the task agent  
        3. If the user seems emotional, get context from emotion agent
        4. Provide a natural, helpful response based on the user's needs
        
        Always maintain conversation context and be helpful and friendly.
        DO NOT use the "Delegate work to coworker" tool - use "Ask question to coworker" instead.
        """,
        agent=conversation_agent,
        expected_output="A natural conversational response that addresses the user's needs"
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
            2. When it should be scheduled (if specified, otherwise use "now")
            3. Any additional details
            
            If the message doesn't specify details, ask the user for clarification.
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