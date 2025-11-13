from django.contrib import admin
from django.urls import path, include
from common.swagger import schema_view

urlpatterns = [
    # (관리자) admin
    path('admin/', admin.site.urls),

    # (개발용) 한투 API 테스트
    path('api/kis-test/', include('kis_test.urls')),

    # (개발용) 서비스 API 문서 - Swagger
    path(r'swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(r'swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # (서비스용) common app
    path('api/', include('common.urls')),

    ## (서비스용) trading app
    path('api/trading/', include('trading.urls')),
    path('api/market/', include('indices.urls')),
]