from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from propylon_document_manager.file_versions.api.views import FileShareViewSet, FileVersionViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"file_versions", FileVersionViewSet, basename="file-versions")
router.register(r"file_shares", FileShareViewSet, basename="file-shares")


app_name = "api"
urlpatterns = router.urls
