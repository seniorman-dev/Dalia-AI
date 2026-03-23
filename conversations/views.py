from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.responses import DaliaResponse
from .models import Conversation, Message, ExecutionSession
from .serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    CreateConversationSerializer,
    UpdateConversationSerializer,
    MessageSerializer,
    ExecutionSessionSerializer
)


class ConversationListView(APIView):
    """
    GET  /api/conversations/        --> list all user's conversations
    POST /api/conversations/        --> create a new conversation
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        conversations = Conversation.objects.filter(
            user=request.user
        ).order_by('-updated_at')

        serializer = ConversationSerializer(
            conversations,
            many=True
        )
        return DaliaResponse.success(
            data={
                'conversations': serializer.data,
                'total': conversations.count()
            }
        )

    def post(self, request: Request):
        serializer = CreateConversationSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return DaliaResponse.error(
                message="Could not create conversation",
                errors=serializer.errors
            )
        conversation = serializer.save()
        return DaliaResponse.success(
            data=ConversationSerializer(conversation).data,
            message="Conversation created",
            status=201
        )


class ConversationDetailView(APIView):
    """
    GET    /api/conversations/<id>/  -- get full conversation with messages
    PATCH  /api/conversations/<id>/  -- update title or archive
    DELETE /api/conversations/<id>/  -- delete conversation
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, request: Request, conversation_id: str):
        return get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user
        )

    def get(self, request: Request, conversation_id: str):
        conversation = self.get_object(request, conversation_id)
        serializer = ConversationDetailSerializer(conversation)
        return DaliaResponse.success(
            data=serializer.data
        )

    def patch(self, request: Request, conversation_id: str):
        conversation = self.get_object(request, conversation_id)
        serializer = UpdateConversationSerializer(
            conversation,
            data=request.data,
            partial=True
        )
        if not serializer.is_valid():
            return DaliaResponse.error(
                message="Update failed",
                errors=serializer.errors
            )
        serializer.save()
        return DaliaResponse.success(
            data=ConversationDetailSerializer(conversation).data,
            message="Conversation updated"
        )

    def delete(self, request: Request, conversation_id: str):
        conversation = self.get_object(request, conversation_id)
        conversation.delete()
        return DaliaResponse.success(
            message="Conversation deleted",
            status=204
        )


class MessageListView(APIView):
    """
    GET /api/conversations/<id>/messages/
    -- paginated message history for a conversation
    Flutter calls this on chat screen open
    to load history before the socket connects
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, conversation_id: str):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user
        )

        # Simple pagination
        # Flutter client sends ?page=1&limit=30
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 30))
        offset = (page - 1) * limit

        messages = conversation.messages.order_by(
            '-created_at'
        )[offset:offset + limit]

        # Reverse so Flutter gets oldest first
        messages = list(reversed(messages))

        serializer = MessageSerializer(messages, many=True)

        return DaliaResponse.success(
            data={
                'messages': serializer.data,
                'page': page,
                'limit': limit,
                'conversation_id': str(conversation.id)
            }
        )


class ExecutionSessionDetailView(APIView):
    """
    GET /api/conversations/sessions/<session_id>/
    -- Full execution session with all steps
    Flutter uses this to reload a past
    execution timeline from history
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, session_id: str):
        session = get_object_or_404(
            ExecutionSession,
            id=session_id,
            conversation__user=request.user
        )
        serializer = ExecutionSessionSerializer(session)
        return DaliaResponse.success(
            data=serializer.data
        )


class ClearConversationView(APIView):
    """
    DELETE /api/conversations/<id>/clear/
    -- Deletes all messages in a conversation
    but keeps the conversation itself
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, conversation_id: str):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user
        )
        deleted_count, _ = Message.objects.filter(
            conversation=conversation
        ).delete()
        Conversation.objects.filter(id=conversation_id).delete()

        return DaliaResponse.success(
            data={
                "messages_deleted": deleted_count
            },
            message="Conversation cleared",
            status=204
        )