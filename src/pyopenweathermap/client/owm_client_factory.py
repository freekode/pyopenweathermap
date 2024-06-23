import logging

from .free_client import OWMFreeClient
from .onecall_client import OWMOneCallClient


def create_owm_client(api_key, api_type, units="metric", lang='en'):
    logger = logging.getLogger(__name__)
    
    logger.info('Initializing OWMClient with api type: ' + str(api_type))
    if api_type == 'v3.0' or api_type == 'v2.5':
        return OWMOneCallClient(api_key, api_type, units, lang)
    if api_type == 'current' or api_type == 'forecast':
        return OWMFreeClient(api_key, api_type, units, lang)
    else:
        raise Exception('Unsupported API type ' + str(api_type))
