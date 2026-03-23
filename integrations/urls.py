from django.urls import path
from .views import (
    IntegrationListView,
    ConnectIntegrationView,
    DisconnectIntegrationView,
    IntegrationDetailView,
    UpdatePermissionView
)

urlpatterns = [
    # List all tools
    path(
        '',
        IntegrationListView.as_view(),
        name='integration-list'
    ),

    # Connect a tool after OAuth
    path(
        'connect/',
        ConnectIntegrationView.as_view(),
        name='integration-connect'
    ),

    # Single tool detail
    path(
        '<str:tool>/',
        IntegrationDetailView.as_view(),
        name='integration-detail'
    ),

    # Disconnect a tool
    path(
        '<str:tool>/disconnect/',
        DisconnectIntegrationView.as_view(),
        name='integration-disconnect'
    ),

    # Update a permission
    path(
        '<str:tool>/permissions/',
        UpdatePermissionView.as_view(),
        name='integration-permissions'
    ),
]