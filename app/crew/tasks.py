# crew/tasks.py
from crewai import Task
from app.crew.agents.conversation import conversation_agent
from app.crew.agents.emotion import emotion_agent
from app.crew.agents.memory import memory_agent
from app.crew.agents.task import task_agent

# crew/tasks.py - UPDATED CONVERSATION TASK
def create_conversation_task(message: str, user_id: str, context: dict = None) -> Task:
    background_agents = context.get('background_agents', [])
    background_actions = context.get('background_actions', {})
    
    return Task(
        description=f"""
        Analyze the user message: "{message}" from user {user_id}.
        
        Context available: {context}
        
        Your role is to maintain natural conversation while identifying when to 
        delegate tasks to specialized agents in the background.
        
        Available background agents: {background_agents}
        Recommended actions: {background_actions}
        
        Follow these guidelines:
        1. If background agents are available, use the AsyncDelegationTool to 
           delegate tasks to them with the appropriate actions
        2. Continue the conversation naturally without mentioning the delegation
        3. Provide immediate responses that acknowledge the user's request
        4. Use the context to personalize your responses
        
        Examples:
        - User: "Remember that I like coffee with two sugars"
          Response: "Got it! I'll remember your coffee preference." 
          (while delegating to memory agent with store action)
        
        - User: "Remind me to call John at 3pm"
          Response: "I'll set a reminder for you to call John at 3pm." 
          (while delegating to task agent with create action)
        
        - User: "I'm feeling really stressed today"
          Response: "I'm sorry to hear you're feeling stressed. Is there anything specific on your mind?" 
          (while delegating to emotion agent with analyze action)
        """,
        agent=conversation_agent,
        expected_output="A natural conversational response that acknowledges the user's request while delegating appropriate tasks to background agents"
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