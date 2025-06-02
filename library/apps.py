from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "library"
    
    def ready(self):
        """Connect signals when the app is ready."""
        import library.signals  # noqa
        import library.ai_signals  # Import AI image generation signals
