from rest_framework import serializers
from .models import Integration, IntegrationPermission






class IntegrationPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationPermission
        fields = [
            'id',
            'permission',
            'label',
            'is_granted'
        ]


class IntegrationSerializer(serializers.ModelSerializer):
    permissions = IntegrationPermissionSerializer(
        many=True,
        read_only=True
    )

    tool_label = serializers.SerializerMethodField()

    class Meta:
        model = Integration
        fields = [
            'id',
            'tool',
            'tool_label',
            'status',
            'scopes',
            'permissions',
            'connected_at',
            'last_used_at'
        ]

        read_only_fields = [
            'access_token',
            'refresh_token',
            'token_expires_at'
        ]

    def get_tool_label(self, obj):
        labels = {
            'gmail': 'Gmail',
            'google_calendar': 'Google Calendar',
            'slack': 'Slack',
            'notion': 'Notion'
        }
        return labels.get(obj.tool, obj.tool)


class UpdatePermissionSerializer(serializers.Serializer):
    """
    Flutter frontend sends this when user toggles
    a permission in the App Manager
    """
    permission = serializers.CharField()
    is_granted = serializers.BooleanField()


class ConnectIntegrationSerializer(serializers.Serializer):
    """
    Flutter frontend sends OAuth tokens (ideally) after
    completing the OAuth flow
    """
    tool = serializers.ChoiceField(choices=[
        'gmail',
        'google_calendar',
        'slack',
        'notion'
    ])
    access_token = serializers.CharField()
    refresh_token = serializers.CharField(required=False)
    scopes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )