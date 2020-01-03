from allauth.socialaccount.providers.oauth.urls import default_urlpatterns

from .provider import HBPOAuth2Provider


urlpatterns = default_urlpatterns(HBPOAuth2Provider)
