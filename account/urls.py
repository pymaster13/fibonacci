from django.urls import path
from knox.views import LogoutView

from .views import (GetTgCodeView, RegisterUserView, LoginUserView,
                    ConfirmTgAccountView, ResetPasswordView,
                    CheckResetTokenView, ChangeUserPasswordView,
                    GenerateGoogleQRView, VerifyGoogleCodeView,
                    LoginAdminUserView, GrantPermissionsView)


urlpatterns = [
    # Telegram
    path('get_tg_code/', GetTgCodeView.as_view(), name='get_tg_code'),
    path('confirm_tg_account/', ConfirmTgAccountView.as_view(), name='confirm_tg_account'),

    # Auth processes
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('login_admin_2fa/', LoginAdminUserView.as_view(), name='login_admin_2fa'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Google Authenticator
    path('generate_qr/', GenerateGoogleQRView.as_view(), name='generate_qr'),
    path('verify_google_code/', VerifyGoogleCodeView.as_view(), name='verify_google_code'),

    path('grant_permissions/', GrantPermissionsView.as_view(), name='grant_permissions'),

    # Reset user password
    path('reset_password_confirm/', CheckResetTokenView.as_view(), name='reset_password_confirm'),
    path('reset_password/', ResetPasswordView.as_view(), name='reset_password'),
    path('change_password/', ChangeUserPasswordView.as_view(), name='change_password'),
]
