from HTTPAccess import HTTPAccess
import urlparse
import logging


class DockerTokenAccess(HTTPAccess):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=False):
        super(DockerTokenAccess, self).__init__(url=url, ignore_cert=ignore_cert, exlog=exlog) # Don't want basic auth
        self.log = logging.getLogger(__name__)
        self.username = username
        self.password = password
        self.token = None


    '''
        Populate this access object with a generic token that will be used for the next call
    '''
    def populate_generic_token(self):
        self.get_raw_call_wrapper('/v2/')

    '''
        Returns true if there is a token
    '''
    def has_token(self):
        return self.token

    '''
        Perform a GET request to the specified url (path) with the specified headers.
        Will try to get a token tries amount of times if the response sends the www-authenticate header.
        Interprets the result into a more python friendly form.
        @param url - The url path to perform the request on
        @param headers - The headers to add to the call
        @param tries - The number of tries to try to reauth
    '''
    def get_code_and_msg_wrapper(self, url, headers=None, tries=1):
        if not headers:
            headers = {}
        response = self.get_raw_call_wrapper(url, headers, tries)
        if response:
            return self.process_response(response), response
        return False


    '''
        Perform a GET request to the specified url (path) with the specified headers.
        Will try to get a token tries amount of times if the response sends the www-authenticate header.
        Provides the raw response
        @param url = The url path to perform the request on
        @param headers - The headers to add to the call
        @param tries - The number of tries to try to reauth
    '''
    def get_raw_call_wrapper(self, url, headers=None, tries=1):
        if not headers:
            headers = {}
        try:
            headers = dict(headers.items() + self.__get_token_header().items())
            response, stat = self.do_unprocessed_request(method='GET', path=url, headers=headers)
            # If no token was provided or token is no longer valid, try to get a new token (limited number of tries)
            if tries > 0 and response and 'www-authenticate'in response.headers:
                self.token = self.__get_token(response.headers['www-authenticate'])
                return self.get_raw_call_wrapper(url=url, headers=headers, tries=tries - 1)
            return response
        except Exception as ex:
            self.log.error("While performing GET request for '%s':  %s" % (url, ex.message))
            return False

    def __get_token_url(self, auth_header):
        components = dict(x.split('=') for x in auth_header.split(','))
        components = {k.lower(): v for k, v in components.items()}
        url = components.pop('bearer realm', None)
        if not url:
            self.log.error("www-authenticate header did not provide a valid URL for a token.")
            return None
        url = url.replace('"', '')
        if len(components) > 0:
            url = url + '?'
            for key, value in components.iteritems():
                url = url + str(key) + '=' + str(value).replace('"', '') + "&"
            url = url[:-1]
        return url

    def __get_token(self, auth_header):
        url = self.__get_token_url(auth_header)
        if url:
            scheme, netloc, path, query, frag = urlparse.urlsplit(url)
            # If the user provided credentials, use them to get the token
            access = HTTPAccess(url=scheme + "://" + netloc, username=self.username, password=self.password,
                                ignore_cert=self.ignore_cert)
            token_response = access.dorequest('GET', path + '?' + query)
            if token_response and token_response['token']:
                return token_response['token']
        return None

    def __get_token_header(self):
        if self.token:
            return {'Authorization': 'Bearer ' + self.token}
        return {}
