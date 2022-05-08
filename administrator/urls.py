from django.urls import path

from .views import (LoginAdminUserView, GrantPermissionsView,
                    Reset2FAView, AllowUserInviteView, AddVIPUserView,
                    DeleteVIPUserView)


urlpatterns = [
    path('login_admin_2fa/', LoginAdminUserView.as_view(), name='login_admin_2fa'),
    path('reset_2fa/', Reset2FAView.as_view(), name='reset_2fa'),
    path('grant_permissions/', GrantPermissionsView.as_view(), name='grant_permissions'),
    path('allow_invite/', AllowUserInviteView.as_view(), name='allow_invite'),
    path('vip_user/', AddVIPUserView.as_view(), name='vip_user'),
    path('delete_vip_user/', DeleteVIPUserView.as_view(), name='delete_vip_user'),

]
