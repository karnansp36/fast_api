import asyncio
import json
from app.crew.llm_config import get_llm


class IntentExtractorAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.3)

    async def extract_intent(self, message: str) -> dict:
        prompt = f"""
Analyze the following user message and extract the intent and any relevant entities.
Return a JSON with fields: intent (reminder, memory, query, conversation), entities (dict), and original_message.
Message: '''{message}'''
"""
        # Call Gemini LLM (sync) safely inside a thread for async compatibility
        response = await asyncio.to_thread(
            lambda: self.llm.call(prompt)
        )

        try:
            result = json.loads(response)
        except Exception:
            result = {
                "intent": "conversation",
                "entities": {},
                "original_message": message,
            }
        return result


intent_extractor_agent = IntentExtractorAgent()
