import os

class OpenstackEnvironment:
    def __init__(
        self,
        *,
        OS_IDENTITY_PROVIDER_URL: str = '',
        OS_AUTH_URL: str = '',
        OS_IDENTITY_PROVIDER: str = '',
        OS_PROJECT_ID: str = '',
        OS_IDENTITY_API_VERSION: str = '',
        OS_AUTH_TYPE: str = "",
        OS_INTERFACE: str = "",
        OS_PROTOCOL: str = "",
        OS_AUTH_TOKEN: str = '',
        OS_STORAGE_URL: str = ''
    ):
        self.OS_IDENTITY_PROVIDER_URL = OS_IDENTITY_PROVIDER_URL or os.environ["OS_IDENTITY_PROVIDER_URL"]
        self.OS_AUTH_URL = OS_AUTH_URL or os.environ["OS_AUTH_URL"]
        self.OS_IDENTITY_PROVIDER = OS_IDENTITY_PROVIDER or os.environ["OS_IDENTITY_PROVIDER"]
        self.OS_PROJECT_ID = OS_PROJECT_ID or os.environ["OS_PROJECT_ID"]
        self.OS_IDENTITY_API_VERSION = OS_IDENTITY_API_VERSION or os.environ["OS_IDENTITY_API_VERSION"]
        self.OS_AUTH_TYPE = OS_AUTH_TYPE or os.environ["OS_AUTH_TYPE"]
        self.OS_INTERFACE = OS_INTERFACE or os.environ["OS_INTERFACE"]
        self.OS_PROTOCOL = OS_PROTOCOL or os.environ["OS_PROTOCOL"]
        self.OS_AUTH_TOKEN = OS_AUTH_TOKEN or os.environ["OS_AUTH_TOKEN"]
        self.OS_STORAGE_URL = OS_STORAGE_URL or os.environ["OS_STORAGE_URL"]

class CscsOpenstackEnvironment(OpenstackEnvironment):
    def __init__(self, OS_USERNAME: str = "", OS_PASSWORD: str = ""):
        OS_USERNAME = OS_USERNAME or os.environ["OS_USERNAME"]
        OS_PASSWORD = OS_PASSWORD or os.environ["OS_PASSWORD"]
        OS_PROJECT_ID = "2dc0b65279674a42833a064ce3677297"
        # from https://user.cscs.ch/storage/object_storage/usage_examples/tokens/
        from keystoneauth1.identity import v3
        from keystoneauth1 import session
        from keystoneauth1.extras._saml2 import V3Saml2Password
        from keystoneclient.v3 import client

        saml_auth = V3Saml2Password(auth_url='https://pollux.cscs.ch:13000/v3',
                               identity_provider='cscskc',
                               protocol='mapped',
                               identity_provider_url='https://auth.cscs.ch/auth/realms/cscs/protocol/saml/',
                               username=OS_USERNAME,
                               password=OS_PASSWORD)
        unscoped_sess = session.Session(auth=saml_auth)
        kc_token = unscoped_sess.get_token()
        #With the project id you can now request to the Keystone service a scoped token for project :
        auth = v3.Token(auth_url=saml_auth.auth_url,
                        token=kc_token,
                        project_id=OS_PROJECT_ID)
        scoped_sess = session.Session(auth=auth)
        super().__init__(
            OS_AUTH_TOKEN=scoped_sess.get_token(),
            OS_STORAGE_URL=f"https://object.cscs.ch/v1/AUTH_{OS_PROJECT_ID}",
            OS_IDENTITY_PROVIDER_URL=saml_auth.identity_provider_url,
            OS_AUTH_URL=saml_auth.auth_url,
            OS_PROTOCOL=saml_auth.protocol,
            OS_IDENTITY_API_VERSION="3",
            OS_AUTH_TYPE="token",
            OS_IDENTITY_PROVIDER=saml_auth.identity_provider,
            OS_INTERFACE="public",
            OS_PROJECT_ID=OS_PROJECT_ID
        )
