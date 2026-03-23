import asyncio
import json
import uuid
from datetime import datetime, timezone
from django.utils import timezone as django_timezone
import asyncio

from .intent_parser import IntentParser
from .executors import ActionExecutor




class AgentOrchestrator:
    """
    Orchestrates the full execution lifecycle.

    Flow:
    instruction -> parse intent -> build plan
    -> execute steps (parallel where possible)
    -> stream each update back to Flutter
    -> save everything to DB
    -> send final summary
    """

    def __init__(self, sio, sid, user_id, conversation_id):
        self.sio = sio          # Socket.IO server instance
        self.sid = sid          # Flutter client session ID
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.parser = IntentParser()
        self.executor = ActionExecutor(user_id=user_id)


    async def stream_step_started(self, step_id, step_number, action, description):
        await self.sio.emit('step_started', {
            'step_id': step_id,
            'step_number': step_number,
            'action': action,
            'description': description,
            "result": description,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, to=self.sid)

    async def stream_step_completed(self, step_id, description, result=None):
        await self.sio.emit('step_completed', {
            'step_id': step_id,
            'description': description,
            'result': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, to=self.sid)

    async def stream_step_failed(self, step_id, description, error):
        await self.sio.emit('step_failed', {
            'step_id': step_id,
            'description': description,
            'result': error,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, to=self.sid)

    async def stream_execution_complete(self, summary, status):
        await self.sio.emit('execution_complete', {
            'status': status,  # 'completed' | 'partial' | 'failed'
            'result': summary,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, to=self.sid)

    async def execute(self, instruction: str):
        from conversations.models import (
            Conversation, Message,
            ExecutionSession, ExecutionStep
        )
        from asgiref.sync import sync_to_async

        # ── 1. Save user message to DB ──
        conversation = await sync_to_async(
            self._get_or_create_conversation
        )(self.conversation_id)

        user_message = await sync_to_async(Message.objects.create)(
            conversation=conversation,
            role='user',
            content=instruction
        )

        session = await sync_to_async(ExecutionSession.objects.create)(
            conversation=conversation,
            user_message=user_message,
            raw_instruction=instruction,
            status='running'
        )

        session_id = str(session.id)

        await self.sio.emit('parsing_intent', {
            'message': 'Understanding your request...',
            'session_id': session_id
        }, to=self.sid)

        try:
            execution_plan = await self.parser.parse(instruction)
        except Exception as e:
            await self.stream_execution_complete(
                summary=f"Failed to understand instruction: {str(e)}",
                status='failed'
            )
            await sync_to_async(self._update_session_status)(
                session, 'failed'
            )
            return

        # Save the parsed plan to the session
        await sync_to_async(self._save_plan)(session, execution_plan)

        await self.sio.emit('plan_ready', {
            'session_id': session_id,
            'total_steps': len(execution_plan),
            'steps': execution_plan
        }, to=self.sid)

        await asyncio.sleep(0.5)

        completed = 0
        failed = 0
        step_records = []

        for step_data in execution_plan:
            step_id = str(uuid.uuid4())
            step_number = step_data.get('step', 1)
            action = step_data.get('action', '')
            description = step_data.get('description', '')
            parameters = step_data.get('parameters', {})

            # Save step to DB
            step_record = await sync_to_async(ExecutionStep.objects.create)(
                session=session,
                step_number=step_number,
                action=action,
                description=description,
                parameters=parameters,
                status='running',
                started_at=django_timezone.now()
            )
            step_records.append(step_record)

            # Stream: step is starting
            await self.stream_step_started(
                step_id=str(step_record.id),
                step_number=step_number,
                action=action,
                description=description
            )

            await asyncio.sleep(0.8)

            try:
                result = await self.executor.execute_step(
                    action=action,
                    parameters=parameters
                )

                # Update step in DB
                await sync_to_async(self._complete_step)(
                    step_record, result
                )

                # Stream "Step completed"
                await self.stream_step_completed(
                    step_id=str(step_record.id),
                    description=f"{description} — Done",
                    result=result
                )
                completed += 1

            except Exception as e:
                error_msg = str(e)

                await sync_to_async(self._fail_step)(
                    step_record, error_msg
                )

                await self.stream_step_failed(
                    step_id=str(step_record.id),
                    description=description,
                    error=error_msg
                )
                failed += 1

            await asyncio.sleep(0.5)

        if failed == 0:
            final_status = 'completed'
            summary = f"All {completed} actions completed successfully."
        elif completed == 0:
            final_status = 'failed'
            summary = f"All {failed} actions failed."
        else:
            final_status = 'partial'
            summary = (
                f"{completed} action(s) succeeded, "
                f"{failed} action(s) failed. "
                f"You can retry the failed steps."
            )

        await sync_to_async(Message.objects.create)(
            conversation=conversation,
            role='dalia',
            content=summary
        )

        await sync_to_async(self._update_session_status)(
            session, final_status
        )

        await self.stream_execution_complete(
            summary=summary,
            status=final_status
        )


    async def retry_step(self, session_id: str, step_id: str):
        """
        Re-executes a single failed step.
        """
        from conversations.models import ExecutionStep
        from asgiref.sync import sync_to_async
        from django.utils import timezone as django_timezone

        try:
            step = await sync_to_async(ExecutionStep.objects.get)(
                id=step_id,
                session__id=session_id
            )
        except ExecutionStep.DoesNotExist:
            await self.sio.emit('error', {
                'message': 'Step not found'
            }, to=self.sid)
            return

        # Update step status to running
        await sync_to_async(self._update_step_status)(
            step, 'running'
        )

        await self.stream_step_started(
            step_id=str(step.id),
            step_number=step.step_number,
            action=step.action,
            description=f"Retrying: {step.description}"
        )

        await asyncio.sleep(0.8)

        try:
            result = await self.executor.execute_step(
                action=step.action,
                parameters=step.parameters or {}
            )
            await sync_to_async(self._complete_step)(step, result)
            await self.stream_step_completed(
                step_id=str(step.id),
                description=f"{step.description} — Done",
                result=result
            )
        except Exception as e:
            await sync_to_async(self._fail_step)(step, str(e))
            await self.stream_step_failed(
                step_id=str(step.id),
                description=step.description,
                error=str(e)
            )


    def _get_or_create_conversation(self, conversation_id):
        from conversations.models import Conversation
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(id=self.user_id)

        if conversation_id:
            try:
                return Conversation.objects.get(
                    id=conversation_id,
                    user=user
                )
            except Conversation.DoesNotExist:
                pass

        return Conversation.objects.create(
            user=user,
            title='New Conversation'
        )

    def _save_plan(self, session, plan):
        session.parsed_plan = plan
        session.save(update_fields=['parsed_plan'])

    def _update_session_status(self, session, status):
        from django.utils import timezone as django_timezone
        session.status = status
        session.completed_at = django_timezone.now()
        session.save(update_fields=['status', 'completed_at'])

    def _complete_step(self, step, result):
        from django.utils import timezone as django_timezone
        step.status = 'completed'
        step.result = result
        step.completed_at = django_timezone.now()
        step.save(update_fields=['status', 'result', 'completed_at'])

    def _fail_step(self, step, error_message):
        from django.utils import timezone as django_timezone
        step.status = 'failed'
        step.error_message = error_message
        step.completed_at = django_timezone.now()
        step.save(update_fields=['status', 'error_message', 'completed_at'])

    def _update_step_status(self, step, status):
        from django.utils import timezone as django_timezone
        step.status = status
        step.started_at = django_timezone.now()
        step.save(update_fields=['status', 'started_at'])