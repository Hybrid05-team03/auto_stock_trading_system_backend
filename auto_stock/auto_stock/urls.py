from django.contrib import admin
from django.urls import path, include, re_path
from common.utils.swagger import schema_view

urlpatterns = [
    # (관리자) admin
    path('admin/', admin.site.urls),

    # (개발용) 한투 API 테스트
    path('api/data/', include('data.urls')),

    # (개발용) 서비스 API 문서 - Swagger
    re_path(r'swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # (개발용) metrics 엔드포인트
    path('', include('django_prometheus.urls')),

    ## (서비스용) trading app
    path('api/trading/', include('trading.urls')),
]