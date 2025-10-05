# app/test.py
import asyncio
from app.core.db import AsyncSessionLocal
from app.core.models import ConversationHistory

async def main():
    async with AsyncSessionLocal() as session:
        # Insert a test row
        new_entry = ConversationHistory(
            user_id="test-user",
            message="Hello!",
            response="Hi there 👋",
            emotion="neutral"
        )
        session.add(new_entry)
        await session.commit()

        # Query back
        result = await session.execute(
            ConversationHistory.__table__.select().order_by(ConversationHistory.id.desc()).limit(1)
        )
        row = result.fetchone()
        print("✅ Inserted & fetched row:", row)

if __name__ == "__main__":
    asyncio.run(main())
