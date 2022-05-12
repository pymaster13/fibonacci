from django.urls import path

from .views import (LoginAdminUserView, GrantPermissionsView,
                    Reset2FAView, AllowUserInviteView, AddVIPUserView,
                    DeleteVIPUserView, SetUserPermanentPlaceView,
                    GetUserIDOView, RetrieveUsersInformationView)


urlpatterns = [
    path('login_admin_2fa/', LoginAdminUserView.as_view(), name='login_admin_2fa'),
    path('reset_2fa/', Reset2FAView.as_view(), name='reset_2fa'),
    path('grant_permissions/', GrantPermissionsView.as_view(), name='grant_permissions'),
    path('allow_invite/', AllowUserInviteView.as_view(), name='allow_invite'),
    path('vip_user/', AddVIPUserView.as_view(), name='vip_user'),
    path('delete_vip_user/', DeleteVIPUserView.as_view(), name='delete_vip_user'),
    path('set_user_queue/', SetUserPermanentPlaceView.as_view(), name='set_user_queue'),
    path('get_user_ido_allocation/', GetUserIDOView.as_view(), name='get_user_ido_allocation'),
    path('retrieve_users_info/', RetrieveUsersInformationView.as_view(), name='retrieve_users_info'),
]
