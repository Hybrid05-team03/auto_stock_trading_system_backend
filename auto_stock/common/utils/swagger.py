from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


## Swagger 스키마 정의 
schema_view = get_schema_view(
    openapi.Info(
        title="Auto-Stock Trading Project",
        default_version='v1',
        description="Hybrid05 Team03 API 문서입니다.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="trre1827151@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)