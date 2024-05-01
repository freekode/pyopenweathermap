from .owm_client import OWMClient

from .v25 import OWMClientV25
from .v30 import OWMClientV3


class OWMClientFactory:
    @staticmethod
    def get_client(api_key, api_version, units="metric", lang='en') -> OWMClient:
        if api_version == 'v3.0':
            return OWMClientV3(api_key, units, lang)
        elif api_version == 'v2.5':
            return OWMClientV25(api_key, units, lang)
        raise Exception("Invalid API version")
