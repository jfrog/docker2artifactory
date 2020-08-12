import urllib2
import json
import ssl
import base64
import re
import StringIO
import xml.etree.ElementTree as ET
import urlparse
import logging
import mmap
import os


class HTTPAccess(object):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=True):
        self.log = logging.getLogger(__name__)
        self.url = url.rstrip('/')

        self.username = username
        self.password = password
        self.ignore_cert = ignore_cert
        self.json = re.compile(r'^application/(?:[^;]+\+)?json(?:;.+)?$')
        self.xml = re.compile(r'^application/(?:[^;]+\+)?xml(?:;.+)?$')
        self.exlog = exlog
        # Install custom handlers for handling SSL (ignore certs) and redirects
        opener=None
        if self.ignore_cert:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            opener = urllib2.build_opener(urllib2.HTTPSHandler(context=ctx), CleanAuthenticationHeadersOnRedirectHandler)
        else:
            opener = urllib2.build_opener(CleanAuthenticationHeadersOnRedirectHandler)
        urllib2.install_opener(opener)
        # Set up the connection
        headers = {'User-Agent': 'Docker registry to Artifactory migrator'}
        if username and password:
            enc = base64.b64encode(username + ':' + password)
            headers['Authorization'] = "Basic " + enc
        url_comp = urlparse.urlparse(self.url)
        self.connection = url_comp.scheme, url_comp.netloc, url_comp.path, headers

    def get_username(self):
        return self.username

    def get_call_wrapper(self, arg):
        try:
            response = self.dorequest('GET', arg)
            return response
        except Exception as ex:
            self.log.info("Exception caught when executing get request: %s", ex)
            return False

    def head_call_wrapper(self, arg):
        try:
            r, s = self.do_unprocessed_request('HEAD', arg)
            return s == 200
        except Exception as ex:
            return False

    '''
        Perform a GET request to the specified url (path) with the specified headers.
        Interprets the result into a more python friendly form. Includes 
        @param url - The url path to perform the request on
        @param headers - The headers to add to the call
    '''
    def get_code_and_msg_wrapper(self, url, headers=None):
        if not headers:
            headers = {}
        response = self.get_raw_call_wrapper(url, headers)
        if response:
            return self.process_response(response), response
        return False


    '''
        Perform a GET request to the specified url (path) with the specified headers.
        Provides the raw response
        @param url = The url path to perform the request on
        @param headers - The headers to add to the call
    '''
    def get_raw_call_wrapper(self, url, headers=None):
        if not headers:
            headers = {}
        try:
            response, stat = self.do_unprocessed_request(method='GET', path=url, headers=headers)
            return response
        except Exception as ex:
            self.log.error("While performing GET request for '%s':  %s" % (url, ex.message))
            return False



    # Helper REST method
    def dorequest(self, method, path, body=None, headers=None):
        if not headers:
            headers = {}
        resp, stat = self.do_unprocessed_request(method, path, body, headers)
        if resp and resp.info():
            ctype = resp.info().get('Content-Type', 'application/octet-stream')
        if not isinstance(stat, (int, long)) or stat < 200 or stat >= 300:
            msg = "Unable to " + method + " " + path + ": " + str(stat) + "."
            raise Exception(msg)
        try:
            if self.json.match(ctype) != None: msg = json.load(resp)
            elif self.xml.match(ctype) != None: msg = ET.parse(resp)
            else: msg = resp.read()
        except: pass
        return msg

    # Helper REST method
    def do_unprocessed_request(self, method, path, body=None, headers=None):
        if not headers:
            headers = {}
        resp, stat, msg, ctype = None, None, None, None
        if 'Content-Type' in headers:
            pass
        elif isinstance(body, (dict, list, tuple)):
            body = json.dumps(body)
            headers['Content-Type'] = 'application/json'
        elif isinstance(body, ET.ElementTree):
            fobj = StringIO.StringIO()
            body.write(fobj)
            body = fobj.getvalue()
            fobj.close()
            headers['Content-Type'] = 'application/xml'
        scheme, host, rootpath, extraheaders = self.connection
        headers.update(extraheaders)
        url = urlparse.urlunsplit((scheme, host, rootpath + path, '', ''))
        req = MethodRequest(url, body, headers, method=method)
        self.log.info("Sending %s request to %s.", method, url)
        try:
            resp = urllib2.urlopen(req)
            stat = resp.getcode()
        except urllib2.HTTPError as ex:
            if self.exlog:
                self.log.exception("Error making request:\n%s", ex.read())
            stat = ex.code
            resp = ex
        except urllib2.URLError as ex:
            if self.exlog:
                self.log.exception("Error making request:")
            stat = ex.reason
            resp = ex
        return resp, stat

    '''
        Interprets a valid response into a more python friendly form
    '''
    def process_response(self, resp):
        msg = False
        if resp and resp.info():
            ctype = resp.info().get('Content-Type', 'application/octet-stream')
        try:
            if self.json.match(ctype) != None: msg = json.load(resp)
            elif self.xml.match(ctype) != None: msg = ET.parse(resp)
            else: msg = resp.read()
        except: pass
        return msg

    '''
        Takes a URI and extracts only the path + query (removing any method and host info)
        Expects a valid full URL (http://...) or relative URL (/v2/something...)
    '''
    def get_relative_url(self, url):
        out = urlparse.urlparse(url)
        if out:
            return out.path + '?' + out.query
        return url

    '''
        Deploys a file using a stream instead of loading into memory
        @param path - The path to deploy to
        @param file_path - The path of the file to stream
        @param headers - Any optional headers
    '''
    def deployFileByStream(self, path, file_path, headers=None):
        if not headers:
            headers = {}
        stat = None
        artifact_headers = {'Content-Type': 'application/octet-stream'}
        mmapped_file_as_string = None
        try:
            artifact_headers['Content-Length'] = str(os.stat(file_path).st_size)
            artifact_headers.update(headers)
            with open(file_path, 'rb') as f:
                self.log.info("Uploading artifact to %s.", path)
                mmapped_file_as_string = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                scheme, host, rootpath, extraheaders = self.connection
                artifact_headers.update(extraheaders)
                url = urlparse.urlunsplit((scheme, host, rootpath + path, '', ''))
                req = PutRequest(url, mmapped_file_as_string, artifact_headers)
                try:
                   stat = urllib2.urlopen(req).getcode()
                except urllib2.HTTPError as ex:
                    msg = "Error uploading artifact:\n%s"
                    self.log.exception(msg, ex.read())
                    stat = ex.code
                except urllib2.URLError as ex:
                    self.log.exception("Error uploading artifact:")
                    stat = ex.reason
        except BaseException as ex:
            self.log.exception("Error uploading artifact:")
            stat = str(ex)
        if mmapped_file_as_string:
            mmapped_file_as_string.close()
        return stat



# REST Helper methods
class MethodRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else: self._method = None
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        if self._method is not None: return self._method
        return urllib2.Request.get_method(self, *args, **kwargs)

class PutRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        return 'PUT'

class CleanAuthenticationHeadersOnRedirectHandler(urllib2.HTTPRedirectHandler):
    def __init__(self, context=None):
        self.context=context


    def redirect_request(self, req, fp, code, msg, headers, newurl):
        print "Handling redirect to %s with code %d" % (newurl, code)
        m = req.get_method()
        if (code in (301, 302, 303, 307) and m in ("GET", "HEAD")
            or code in (301, 302, 303) and m == "POST"):
            newurl = newurl.replace(' ', '%20')

            host = req.get_host()
            next_host = urlparse.urlparse(newurl).netloc
            new_host = next_host != host

            newheaders = dict((k,v) for k,v in req.headers.items()
                              if k.lower() not in ("content-length", "content-type") and (not new_host or k.lower() != "authorization")
                             )
            return urllib2.Request(newurl,
                           headers=newheaders,
                           origin_req_host=req.get_origin_req_host(),
                           unverifiable=True)
        else:
            raise urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)
