import requests

from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter, OAuth2CallbackView, OAuth2LoginView

from .provider import HBPOAuth2Provider


_URL_PREFIX = "https://services.humanbrainproject.eu/oidc/"


class HBPOAuth2Adapter(OAuth2Adapter):
    provider_id = HBPOAuth2Provider.id
    access_token_url = _URL_PREFIX + "token"
    authorize_url = _URL_PREFIX + "authorize"
    profile_url = _URL_PREFIX + "userinfo"

    def complete_login(self, request, app, token, **kwargs):
        resp = requests.get(self.profile_url, params={"access_token": token.token})
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth_login = OAuth2LoginView.adapter_view(HBPOAuth2Adapter)
oauth_callback = OAuth2CallbackView.adapter_view(HBPOAuth2Adapter)
