from django.urls import path

from .views import (AddMetamaskWalletView, RetrieveMetamaskWalletView,
                    FillUserReserveView, TakeOffUserReserveView,
                    RetrieveAdminWalletView)


urlpatterns = [
    path('set_metamask/', AddMetamaskWalletView.as_view(), name='set_metamask'),
    path('retrieve_metamask/', RetrieveMetamaskWalletView.as_view(), name='retrieve_metamask'),
    path('retrieve_admin_wallet/', RetrieveAdminWalletView.as_view(), name='retrieve_admin_wallet'),

    path('fill_user_reserve/', FillUserReserveView.as_view(), name='fill_user_reserve'),
    path('takeoff_user_reserve/', TakeOffUserReserveView.as_view(), name='takeoff_user_reserve'),

]
