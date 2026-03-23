
# Create your models here.
from django.db import models
from django.conf import settings
import uuid





class Conversation(models.Model):
    """
    A conversation session between the user and Dalia.
    One user can have many conversations with Dalia.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        default='New Conversation'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.email} — {self.title}"


class Message(models.Model):
    """
    A single message within a conversation.
    Role is either 'user' (sent by user) or 'dalia' (sent by AI).
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('dalia', 'Dalia'),
        ('system', 'System'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"


class ExecutionSession(models.Model):
    """
    Tracks a single execution run triggered by a user instruction.
    One message can trigger one execution session.
    Multiple steps are tracked under one session.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='execution_sessions'
    )
    user_message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='execution_sessions'
    )
    raw_instruction = models.TextField()  # The original user instruction
    parsed_plan = models.JSONField(null=True, blank=True)  # AI parsed steps
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'execution_sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.id} — {self.status}"


class ExecutionStep(models.Model):
    """
    A single action within an execution session.
    e.g. 'Create calendar event', 'Send email to Japhet'
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    session = models.ForeignKey(
        ExecutionSession,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    step_number = models.PositiveIntegerField()
    action = models.CharField(max_length=100)  # e.g. 'create_calendar_event'
    description = models.CharField(max_length=255)  # Human readable
    parameters = models.JSONField(null=True, blank=True)  # Step input data
    result = models.JSONField(null=True, blank=True)  # Step output data
    error_message = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'execution_steps'
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number}: {self.action} — {self.status}"