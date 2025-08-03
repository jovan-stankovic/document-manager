from django.apps import AppConfig


class FileVersionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "propylon_document_manager.file_versions"
    verbose_name = "File Versions"

    def ready(self):
        import allauth.account.signals
