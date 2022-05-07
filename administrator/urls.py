from django.urls import path

from .views import (LoginAdminUserView, GrantPermissionsView,
                    Reset2FAView, AllowUserInviteView)


urlpatterns = [

    path('login_admin_2fa/', LoginAdminUserView.as_view(), name='login_admin_2fa'),
    path('reset_2fa/', Reset2FAView.as_view(), name='reset_2fa'),

    # User permissions
    path('grant_permissions/', GrantPermissionsView.as_view(), name='grant_permissions'),
    path('allow_invite/', AllowUserInviteView.as_view(), name='allow_invite'),
]
