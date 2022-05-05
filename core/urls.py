from django.urls import path

from .views import (AddMetamaskWalletView)


urlpatterns = [
    path('add_metamask_wallet/', AddMetamaskWalletView.as_view(), name='add_metamask_wallet'),
]
