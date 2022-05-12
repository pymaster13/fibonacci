from django.urls import path
from knox.views import LogoutView

from .views import (GetTgCodeView, RegisterUserView, LoginUserView,
                    ConfirmTgAccountView, ResetPasswordView,
                    CheckResetTokenView, ChangeUserPasswordView,
                    GenerateGoogleQRView, VerifyGoogleCodeView,
                    RetrievePermissionsView, RetrieveUserInfoView,
                    RetrieveUserPartnersView)


urlpatterns = [
    # Telegram
    path('get_tg_code/', GetTgCodeView.as_view(), name='get_tg_code'),
    path('confirm_tg_account/', ConfirmTgAccountView.as_view(), name='confirm_tg_account'),

    # Auth processes
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Google Authenticator
    path('generate_qr/', GenerateGoogleQRView.as_view(), name='generate_qr'),
    path('verify_google_code/', VerifyGoogleCodeView.as_view(), name='verify_google_code'),

    # User permissions
    path('retrieve_permissions/', RetrievePermissionsView.as_view(), name='retrieve_permissions'),
    path('retrieve_partners/', RetrieveUserPartnersView.as_view(), name='retrieve_partners'),
    path('info/', RetrieveUserInfoView.as_view(), name='info'),

    # Reset user password
    path('reset_password_confirm/', CheckResetTokenView.as_view(), name='reset_password_confirm'),
    path('reset_password/', ResetPasswordView.as_view(), name='reset_password'),
    path('change_password/', ChangeUserPasswordView.as_view(), name='change_password'),
]
