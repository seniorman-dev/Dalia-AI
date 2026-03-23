from django.urls import path
from .views import (
    ConversationListView,
    ConversationDetailView,
    MessageListView,
    ExecutionSessionDetailView,
    ClearConversationView
)

urlpatterns = [
    # Conversation CRUD
    path(
        '',
        ConversationListView.as_view(),
        name='conversation-list'
    ),
    path(
        '<uuid:conversation_id>/',
        ConversationDetailView.as_view(),
        name='conversation-detail'
    ),

    # Messages
    path(
        '<uuid:conversation_id>/messages/',
        MessageListView.as_view(),
        name='message-list'
    ),
    path(
        '<uuid:conversation_id>/clear/',
        ClearConversationView.as_view(),
        name='conversation-clear'
    ),

    # Execution sessions
    path(
        'sessions/<uuid:session_id>/',
        ExecutionSessionDetailView.as_view(),
        name='execution-session-detail'
    ),
]