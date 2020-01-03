from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class HBPOAuth2Account(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get("links", {}).get("html", {}).get("href")

    def get_avatar_url(self):
        return self.account.extra_data.get("links", {}).get("avatar", {}).get("href")

    def to_str(self):
        dflt = super().to_str()
        return self.account.extra_data.get("display_name", dflt)


class HBPOAuth2Provider(OAuth2Provider):
    id = "hbp_oauth2"
    name = "Human Brain Project"
    account_class = HBPOAuth2Account

    def extract_uid(self, data):
        return data["sub"]

    def extract_common_fields(self, data):
        return dict(email=data.get("email"), username=data.get("preferred_username"), name=data.get("name"))


provider_classes = [HBPOAuth2Provider]
