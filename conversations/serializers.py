from rest_framework import serializers
from .models import Conversation, Message, ExecutionSession, ExecutionStep






class ExecutionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionStep
        fields = [
            'id',
            'step_number',
            'action',
            'description',
            'parameters',
            'result',
            'error_message',
            'status',
            'started_at',
            'completed_at'
        ]


class ExecutionSessionSerializer(serializers.ModelSerializer):
    steps = ExecutionStepSerializer(many=True, read_only=True)

    class Meta:
        model = ExecutionSession
        fields = [
            'id',
            'raw_instruction',
            'parsed_plan',
            'status',
            'steps',
            'started_at',
            'completed_at'
        ]


class MessageSerializer(serializers.ModelSerializer):
    # Attach execution session if this message
    # triggered one ----- Flutter uses this to
    # render the execution timeline in chat
    execution_sessions = ExecutionSessionSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Message
        fields = [
            'id',
            'role',
            'content',
            'execution_sessions',
            'created_at'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    # keeps the list response lean and fast
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'is_active',
            'message_count',
            'last_message',
            'created_at',
            'updated_at'
        ]

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if last:
            return {
                'content': last.content[:100],
                'role': last.role,
                'created_at': last.created_at
            }
        return None


class ConversationDetailSerializer(serializers.ModelSerializer):
    # Used in detail view -- full messages loaded
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'is_active',
            'messages',
            'created_at',
            'updated_at'
        ]


class CreateConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['title']

    def create(self, validated_data):
        # User is injected from the view
        user = self.context['request'].user
        return Conversation.objects.create(
            user=user,
            **validated_data
        )


class UpdateConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['title', 'is_active']