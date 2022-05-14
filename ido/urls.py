from django.urls import path

from .views import (IDOCreateView, IDOUpdateView, IDODeleteView,
                    IDORetrieveView, IDOListView, ParticipateIDOView,
                    AddUserQueue, ChargeTokensManuallyView,
                    ChargeRefundAllocationView)


urlpatterns = [
    path('create/', IDOCreateView.as_view(), name='create_ido'),
    path('update/<int:pk>/', IDOUpdateView.as_view(), name='update_ido'),
    path('delete/<int:pk>/', IDODeleteView.as_view(), name='delete_ido'),
    path('<int:pk>/', IDORetrieveView.as_view(), name='retrieve_ido'),

    path('attach_to_queue/', AddUserQueue.as_view(), name='attach_to_queue'),
    path('participate/', ParticipateIDOView.as_view(), name='participate_ido'),

    path('charge_manually/', ChargeTokensManuallyView.as_view(), name='charge_manually'),
    path('charge_refund_allocation/', ChargeRefundAllocationView.as_view(), name='charge_refund_allocation'),

    path('', IDOListView.as_view(), name='list_ido'),
]
