from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from propylon_document_manager.file_versions.api.views import (
    CustomLoginView,
    GetFileVersionByCAS,
    GetFileVersionByURL,
    LogoutView,
    UserRegistrationView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Documents manager API",
        default_version="v1",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

# API URLS
urlpatterns = [
    # API docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # API base url
    path("api/", include("propylon_document_manager.site.api_router")),
    # API url
    path("<slug:url>", GetFileVersionByURL.as_view(), name="get_document_by_url"),
    path("<str:cas_url>", GetFileVersionByCAS.as_view(), name="get_document_by_cas_url"),
    # API auth
    path("auth/register/", UserRegistrationView.as_view(), name="user_register"),
    path("auth/login/", CustomLoginView.as_view(), name="custom-login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
]

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
