from django.urls import path

from .views import (IDOCreateView, IDOUpdateView, IDODeleteView,
                    IDORetrieveView, IDOListView)


urlpatterns = [
    path('create/', IDOCreateView.as_view(), name='create_ido'),
    path('update/<int:pk>/', IDOUpdateView.as_view(), name='update_ido'),
    path('delete/<int:pk>/', IDODeleteView.as_view(), name='delete_ido'),
    path('<int:pk>/', IDORetrieveView.as_view(), name='retrieve_ido'),
    path('', IDOListView.as_view(), name='list_ido'),
]
