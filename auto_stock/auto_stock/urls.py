from django.contrib import admin
from django.urls import path, include
from common.swagger import schema_view

urlpatterns = [
    # admin
    path('admin/', admin.site.urls),

    # Swagger UI
    path(r'swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(r'swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # common app
    path('api/', include('common.urls')),
    path('api/market/', include('indices.urls')),
]