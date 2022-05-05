from django.urls import path
from knox.views import LogoutView

from .views import (GetTgCodeView, RegisterUserView, LoginUserView,
                    ConfirmTgAccountView)


urlpatterns = [
    path('get_tg_code/', GetTgCodeView.as_view(), name='get_tg_code'),
    path('confirm_tg_account/', ConfirmTgAccountView.as_view(), name='confirm_tg_account'),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
