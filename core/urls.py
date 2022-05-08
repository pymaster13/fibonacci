from django.urls import path

from .views import (AddMetamaskWalletView, RetrieveMetamaskWalletView)


urlpatterns = [
    path('set_metamask/', AddMetamaskWalletView.as_view(), name='set_metamask'),
    path('retrieve_metamask/', RetrieveMetamaskWalletView.as_view(), name='retrieve_metamask'),
]
