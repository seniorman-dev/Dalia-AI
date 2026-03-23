import asyncio
from datetime import datetime



class ActionExecutor:
    """
    Executes individual actions from the execution plan.
    Each method corresponds to an action type from the intent parser.

    Currently simulates execution with realistic delays.
    Real Google Calendar and Gmail API calls slot in here
    when integrations are live.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id

    async def execute_step(self, action: str, parameters: dict) -> dict:
        """
        Routes an action to the correct executor method.
        """
        executors = {
            'create_calendar_event': self.create_calendar_event,
            'send_email': self.send_email,
            'create_task': self.create_task,
            'send_slack_message': self.send_slack_message,
            'read_emails': self.read_emails,
            'update_calendar_event': self.update_calendar_event,
            'delete_calendar_event': self.delete_calendar_event,
        }

        executor_fn = executors.get(action)
        if not executor_fn:
            raise Exception(f"Unknown action: {action}")

        return await executor_fn(parameters)

    async def create_calendar_event(self, params: dict) -> dict:
        """
        Creates a Google Calendar event.
        Simulated for now - real API call slots in here.
        """
        # Simulate API call delay
        await asyncio.sleep(1.5)

        title = params.get('title', 'Untitled Meeting')
        date = params.get('date', 'tomorrow')
        time = params.get('time', '09:00')
        attendees = params.get('attendees', [])

        return {
            'event_id': 'cal_evt_mock_001',
            'title': title,
            'date': date,
            'time': time,
            'attendees': attendees,
            'meet_link': 'https://meet.google.com/mock-link-xyz',
            'status': 'created'
        }

    async def send_email(self, params: dict) -> dict:
        """
        Sends an email via Gmail API.
        Simulated for now.
        """
        await asyncio.sleep(1.2)

        recipient = params.get('to', '')
        subject = params.get('subject', '')

        return {
            'message_id': 'gmail_msg_mock_001',
            'to': recipient,
            'subject': subject,
            'status': 'sent',
            'sent_at': datetime.utcnow().isoformat()
        }

    async def create_task(self, params: dict) -> dict:
        await asyncio.sleep(0.8)
        return {
            'task_id': 'task_mock_001',
            'title': params.get('title', ''),
            'status': 'created'
        }

    async def send_slack_message(self, params: dict) -> dict:
        await asyncio.sleep(0.9)
        return {
            'message_id': 'slack_msg_mock_001',
            'channel': params.get('channel', ''),
            'status': 'sent'
        }

    async def read_emails(self, params: dict) -> dict:
        await asyncio.sleep(1.0)
        return {
            'emails_fetched': 5,
            'status': 'completed'
        }

    async def update_calendar_event(self, params: dict) -> dict:
        await asyncio.sleep(1.0)
        return {
            'event_id': params.get('event_id', ''),
            'status': 'updated'
        }

    async def delete_calendar_event(self, params: dict) -> dict:
        await asyncio.sleep(0.8)
        return {
            'event_id': params.get('event_id', ''),
            'status': 'deleted'
        }