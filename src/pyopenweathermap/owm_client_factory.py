import logging


class OWMClientFactory:
    def __init__(self, api_type, api_key, units="metric", lang='en'):
        self.logger.info('Initializing OWMClient with api type: ' + str(api_type))
        if api_version == 'v3.0':
            self.main_url = API_V30_URL
        elif api_version == 'v2.5':
            self.main_url = API_V25_URL
        else:
            raise Exception('Unsupported API version ' + str(api_version))
        
        pass
