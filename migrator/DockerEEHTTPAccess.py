from HTTPAccess import HTTPAccess
import logging
import urllib
'''
    Simple API for accessing Docker EE resources
'''
class DockerEEHTTPAccess(HTTPAccess):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=False):
        super(DockerEEHTTPAccess, self).__init__(url, username, password, ignore_cert, exlog)
        self.log = logging.getLogger(__name__)
        self.page_size = 100

    '''
        Iterate over the results via headers 'next page'
        @ return the aggregrated results
    '''
    def get_with_header_pagination(self, path, attribute, page_handler):
        result = []
        start = True
        while start:
            page_results, start = self.get_page_with_header(path, attribute, start)
            page_handler(result, page_results)
        return result

    '''
        Perform a request and look at the header
        @ return The page results, the next start ID (or None if no more results)
    '''
    def get_page_with_header(self, path, attribute, start):
        page_path = path + '?pageSize=' + str(self.page_size)
        if start and start is not True:
            page_path = page_path + '&pageStart=' + urllib.quote(start.encode('utf8'))
        # Allow raw array results
        results, raw_results = self.get_code_and_msg_wrapper(page_path)
        start = raw_results.info().getheader('x-next-page-start')
        if attribute:
            page_results = results[attribute]
        else:
            page_results = results
        return page_results, start


    def get_with_pagination(self, path, attribute, order, page_handler, pageSizeQueryParam='limit', pageStartQueryParam='start'):
        result = []
        page_results = True
        while page_results and (not isinstance(page_results, list) or len(page_results) >= self.page_size - 1):
            start = None
            if (page_results and isinstance(page_results, list)):
                start = self.get_attribute(page_results[-1], order)
            page_results = self.get_page(path, attribute, order, start, pageSizeQueryParam, pageStartQueryParam)
            page_handler(result, page_results)
        return result

    def get_page(self, path, attribute, order, start, pageSizeQueryParam, pageStartQueryParam):
        page_path = path + '?' + pageSizeQueryParam + '=' + str(self.page_size)
        if (order):
            page_path = page_path + '&order=' + order
        if (start):
            page_path = page_path + '&' + pageStartQueryParam + '=' + urllib.quote(start.encode('utf8'))
        if (attribute):
            page_results = self.get_call_wrapper(page_path)[attribute]
        else:
            page_results = self.get_call_wrapper(page_path)
        if (start and page_results):
            page_results.pop(0)
        return page_results

    def get_attribute(self, object, attribute):
        parts = attribute.split('.')
        result = object
        for part in parts:
            result = result[part]
        return result
