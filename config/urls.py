from django.conf.urls.static import static 
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (SpectacularAPIView,
                                   SpectacularSwaggerView)

from .settings import MEDIA_ROOT, MEDIA_URL


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/account/', include('account.urls')),
    path('api/v1/news/', include('news.urls')),
    path('api/v1/core/', include('core.urls')),
    path('api/v1/ido/', include('ido.urls')),

    #Swagger UI
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(
        template_name="swagger-ui.html", url_name="schema"),
        name="swagger-ui",
    ),
] + static(MEDIA_URL, document_root=MEDIA_ROOT)
