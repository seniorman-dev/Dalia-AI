
# Register your models here.
from django.contrib import admin
from .models import Integration, IntegrationPermission



admin.site.register(Integration)
admin.site.register(IntegrationPermission)