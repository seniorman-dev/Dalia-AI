
# Create your models here.
from django.db import models
from django.conf import settings
import uuid


class Integration(models.Model):
    """
    A connected third-party tool for a specific user.
    e.g. Gmail, Google Calendar, Slack, Notion
    """
    TOOL_CHOICES = [
        ('gmail', 'Gmail'),
        ('google_calendar', 'Google Calendar'),
        ('slack', 'Slack'),
        ('notion', 'Notion'),
    ]

    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('expired', 'Expired'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='integrations'
    )
    tool = models.CharField(max_length=50, choices=TOOL_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='disconnected'
    )
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    scopes = models.JSONField(default=list)  # Granted permission scopes
    connected_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'integrations'
        # One user can only have one connection per tool
        unique_together = ['user', 'tool']

    def __str__(self):
        return f"{self.user.email} — {self.tool} ({self.status})"


class IntegrationPermission(models.Model):
    """
    Granular permission control per integration.
    The user decides exactly what Dalia can do within each tool.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    permission = models.CharField(max_length=100)  # e.g. 'send_email'
    label = models.CharField(max_length=255)
    is_granted = models.BooleanField(default=False)

    class Meta:
        db_table = 'integration_permissions'

    def __str__(self):
        status = 'granted' if self.is_granted else 'denied'
        return f"{self.integration.tool} — {self.permission} ({status})"