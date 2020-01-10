from django.apps import AppConfig


class HBPOAuth2AppConfig(AppConfig):
    name = "cloud_ilastik.hbp_oauth2"

    def ready(self):
        from . import checks  # noqa

        return super().ready()
