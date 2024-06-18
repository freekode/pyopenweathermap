import logging

from .freemium_client import OWMFreemiumClient
from .onecall_client import OWMOneCallClient


class OWMClientFactory:
    logger = logging.getLogger(__name__)

    def get_client(self, api_key, api_type, units="metric", lang='en'):
        self.logger.info('Initializing OWMClient with api type: ' + str(api_type))
        if api_type == 'v3.0' or api_type == 'v2.5':
            return OWMOneCallClient(api_key, api_type, units, lang)
        if api_type == 'current' or api_type == 'forecast':
            return OWMFreemiumClient(api_key, api_type, units, lang)
        else:
            raise Exception('Unsupported API type ' + str(api_type))

        pass
