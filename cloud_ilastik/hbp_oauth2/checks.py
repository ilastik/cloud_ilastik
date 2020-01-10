from allauth.socialaccount import models
from django.core.checks import register, Warning, Tags
from django.db.utils import OperationalError

from . import provider


@register(Tags.database)
def check_hbp_client_is_registered(app_configs=None, **kwargs):
    try:
        social_apps = models.SocialApp.objects.filter(provider=provider.HBPOAuth2Provider.id).count()
    except OperationalError:
        social_apps = 0

    if social_apps:
        return []

    return [
        Warning(
            "The HBP client should be registered to allow HBP OIDC authorization/registration",
            hint=("Run manage.py register_hbp_client <client_id> <client_secret>"),
            id="hbp_oauth2.W001",
        )
    ]
