from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.responses import DaliaResponse
from .models import Integration, IntegrationPermission
from .serializers import (
    IntegrationSerializer,
    UpdatePermissionSerializer,
    ConnectIntegrationSerializer
)


DEFAULT_PERMISSIONS = {
    'gmail': [
        {'permission': 'read_emails', 'label': 'Read emails'},
        {'permission': 'send_emails', 'label': 'Send emails'},
        {'permission': 'delete_emails', 'label': 'Delete emails'},
    ],
    'google_calendar': [
        {'permission': 'read_events', 'label': 'Read calendar events'},
        {'permission': 'create_events', 'label': 'Create calendar events'},
        {'permission': 'update_events', 'label': 'Update calendar events'},
        {'permission': 'delete_events', 'label': 'Delete calendar events'},
    ],
    'slack': [
        {'permission': 'read_messages', 'label': 'Read messages'},
        {'permission': 'send_messages', 'label': 'Send messages'},
    ],
    'notion': [
        {'permission': 'read_pages', 'label': 'Read pages'},
        {'permission': 'create_pages', 'label': 'Create pages'},
        {'permission': 'update_pages', 'label': 'Update pages'},
    ]
}


class IntegrationListView(APIView):
    """
    GET /api/integrations/
    Returns all tools — connected and disconnected
    Flutter uses this to build the App Manager screen
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        # Get all tools defined in the system
        all_tools = ['gmail', 'google_calendar', 'slack', 'notion']

        # Get user's existing integrations
        user_integrations = Integration.objects.filter(
            user=request.user
        ).prefetch_related('permissions')

        # Map by tool name for quick lookup
        integration_map = {
            i.tool: i for i in user_integrations
        }

        result = []
        for tool in all_tools:
            if tool in integration_map:
                # User has this integration
                result.append(
                    IntegrationSerializer(
                        integration_map[tool]
                    ).data
                )
            else:
                # Tool not connected yet
                # Return a disconnected placeholder
                result.append({
                    'id': None,
                    'tool': tool,
                    'tool_label': tool.replace('_', ' ').title(),
                    'status': 'disconnected',
                    'scopes': [],
                    'permissions': [],
                    'connected_at': None,
                    'last_used_at': None
                })

        return DaliaResponse.success(
            data={
                'integrations': result,
                'connected_count': len([
                    i for i in result
                    if i['status'] == 'connected'
                ])
            }
        )


class ConnectIntegrationView(APIView):
    """
    POST /api/integrations/connect/
    Flutter calls this after OAuth flow completes
    Saves tokens and creates default permissions
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = ConnectIntegrationSerializer(
            data=request.data
        )
        if not serializer.is_valid():
            return DaliaResponse.error(
                message="Connection failed",
                errors=serializer.errors
            )

        data = serializer.validated_data
        tool = data['tool']

        # Create or update integration
        integration, created = Integration.objects.update_or_create(
            user=request.user,
            tool=tool,
            defaults={
                'status': 'connected',
                'access_token': data['access_token'],
                'refresh_token': data.get('refresh_token', ''),
                'scopes': data.get('scopes', []),
                'connected_at': timezone.now(),
            }
        )

        # Create default permissions if new integration
        if created:
            defaults = DEFAULT_PERMISSIONS.get(tool, [])
            for perm in defaults:
                IntegrationPermission.objects.create(
                    integration=integration,
                    permission=perm['permission'],
                    label=perm['label'],
                    # Grant read permissions by default
                    # Write permissions require explicit user grant
                    is_granted='read' in perm['permission']
                )

        return DaliaResponse.success(
            data=IntegrationSerializer(integration).data,
            message=f"{tool.replace('_', ' ').title()} connected successfully",
            status=201 if created else 200
        )


class DisconnectIntegrationView(APIView):
    """
    DELETE /api/integrations/<tool>/disconnect/
    Removes the integration and all its permissions
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, tool: str):
        integration = get_object_or_404(
            Integration,
            user=request.user,
            tool=tool
        )
        integration.delete()
        return DaliaResponse.success(
            message=f"{tool.replace('_', ' ').title()} disconnected",
            status=204
        )


class IntegrationDetailView(APIView):
    """
    GET /api/integrations/<tool>/
    Full detail for a single integration
    including all permissions
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, tool: str):
        integration = get_object_or_404(
            Integration,
            user=request.user,
            tool=tool
        )
        return DaliaResponse.success(
            data=IntegrationSerializer(integration).data
        )


class UpdatePermissionView(APIView):
    """
    PATCH /api/integrations/<tool>/permissions/
    Flutter calls this when user toggles
    a permission switch in App Manager
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, tool: str):
        integration = get_object_or_404(
            Integration,
            user=request.user,
            tool=tool
        )

        serializer = UpdatePermissionSerializer(
            data=request.data
        )
        if not serializer.is_valid():
            return DaliaResponse.error(
                message="Invalid permission data",
                errors=serializer.errors
            )

        permission_name: str = serializer.validated_data['permission']
        is_granted: bool = serializer.validated_data['is_granted']

        # Find and update the permission
        permission = get_object_or_404(
            IntegrationPermission,
            integration=integration,
            permission=permission_name
        )
        permission.is_granted = is_granted
        permission.save(update_fields=['is_granted'])

        return DaliaResponse.success(
            data={
                'permission': permission_name,
                'is_granted': is_granted,
                'tool': tool
            },
            message="Permission updated"
        )