from HTTPAccess import HTTPAccess
import logging
import re
'''
    Simple API for accessing Docker EE resources
'''
class DockerEEHTTPAccess(HTTPAccess):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=False):
        super(DockerEEHTTPAccess, self).__init__(url, username, password, ignore_cert, exlog)
        self.log = logging.getLogger(__name__)
        self.page_size = 100

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
            page_path = u''.join((page_path + '&' + pageStartQueryParam + '=', start)).encode('utf-8')
            page_path = urlEncodeNonAscii(page_path)
        page_results = self.get_call_wrapper(page_path)[attribute]
        if (start and page_results):
            page_results.pop(0)
        return page_results

    def get_attribute(self, object, attribute):
        parts = attribute.split('.')
        result = object
        for part in parts:
            result = result[part]
        return result

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)