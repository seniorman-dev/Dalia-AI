import json
import asyncio
from openai import AsyncOpenAI
from django.conf import settings


class IntentParser:
    """
    Sends the user's raw instruction to GPT-4o (replacement = llama-3.3-70b-versatile).
    Gets back a structured JSON execution plan.
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            #api_key=settings.OPENAI_API_KEY
            api_key=settings.GROQ_LLAMA_API_KEY,   # free at console.groq.com
            base_url="https://api.groq.com/openai/v1"
        )

    SYSTEM_PROMPT = """
You are Dalia's intent parser. Your only job is to take a 
natural language instruction and break it into a precise, 
ordered list of executable steps.

You must respond with ONLY a valid JSON array. 
No explanation. No preamble. No markdown. Just the JSON array.

Each step must have exactly these fields:
- step: integer (the step number, starting from 1)
- action: string (snake_case action identifier)
- description: string (clear human-readable description for UI display)
- parameters: object (all data needed to execute this action)
- depends_on: array of integers (step numbers this step must wait for, empty if none)

Available actions:
- create_calendar_event
- send_email
- create_task
- send_slack_message
- read_emails
- update_calendar_event
- delete_calendar_event

For create_calendar_event parameters use:
{
  "title": string,
  "date": string (YYYY-MM-DD),
  "time": string (HH:MM 24hr),
  "attendees": array of strings (names),
  "meeting_type": "virtual" | "physical",
  "duration_minutes": integer
}

For send_email parameters use:
{
  "to": string (recipient name or email),
  "subject": string,
  "body": string,
  "tone": "formal" | "casual"
}

Example input:
"Book a 3pm meeting with John tomorrow and email Sarah that it's confirmed"

Example output:
[
  {
    "step": 1,
    "action": "create_calendar_event",
    "description": "Creating meeting with John for tomorrow at 3:00 PM",
    "parameters": {
      "title": "Meeting with John",
      "date": "tomorrow",
      "time": "15:00",
      "attendees": ["John"],
      "meeting_type": "virtual",
      "duration_minutes": 60
    },
    "depends_on": []
  },
  {
    "step": 2,
    "action": "send_email",
    "description": "Emailing Sarah to confirm the meeting",
    "parameters": {
      "to": "Sarah",
      "subject": "Meeting Confirmed",
      "body": "Hi Sarah, just letting you know the meeting with John has been booked for tomorrow at 3pm.",
      "tone": "casual"
    },
    "depends_on": [1]
  }
]
"""

    async def parse(self, instruction: str) -> list:
        """
        Sends instruction to OpenAI.
        Returns a list of execution steps.
        """
        try:
            response = await self.client.chat.completions.create(
                #model="gpt-4o",
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": instruction
                    }
                ],
                temperature=0.1,
                max_tokens=1500
            )

            raw = response.choices[0].message.content.strip()

            # Clean up in case model adds markdown
            raw = raw.replace('```json', '').replace('```', '').strip()

            plan = json.loads(raw)

            if not isinstance(plan, list):
                raise ValueError("Parser did not return a list")

            return plan

        except json.JSONDecodeError as e:
            raise Exception(f"Intent parser returned invalid JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Intent parsing failed: {str(e)}")