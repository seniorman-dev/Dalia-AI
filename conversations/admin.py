
# Register your models here.
from django.contrib import admin
from .models import Conversation, Message, ExecutionSession, ExecutionStep


admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(ExecutionSession)
admin.site.register(ExecutionStep)