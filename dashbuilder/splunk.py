import urllib2
import urllib
import urlparse
import base64
import ssl
import xml.etree.ElementTree as ETtree


def auth_header(username, password):
    base64auth = base64.encodestring('{}:{}'.format(username, password)).replace('\n', '')
    header = ("Authorization", "Basic {}".format(base64auth))
    return header


def no_ssl_check():
    return ssl._create_unverified_context()


class Verbs(object):
    Post = 'POST'
    Delete = 'DELETE'
    Get = 'GET'


class ServerInfo(object):
    def __init__(self, addr="localhost", port=8089):
        self.addr = addr
        self.port = port

    def api(self):
        return "{}:{}".format(self.addr, self.port)


class AuthenticationInfo(object):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password


class Context(object):
    def __init__(self, server, auth):
        self.server = server
        self.auth = auth


class Client(object):
    def __init__(self, server=ServerInfo(), auth=AuthenticationInfo()):
        self.context = Context(server, auth)

    def dashboards(self):
        return DashboardClient(self.context)


class DashboardClient(object):
    def __init__(self, context):
        self.context = context

    def _resource(self, username, app, dashboard=None):
        resource = urlparse.urljoin(
            self.context.server.api(),
            "servicesNS/{}/{}/data/ui/views/".format(username, app))

        if dashboard is not None:
            resource = urlparse.urljoin(resource, dashboard)

        return resource

    def _request(self, app, dashboard=None, data=None, verb=None):
        context = self.context
        resource = self._resource(context.auth.username, app, dashboard)

        if data is None:
            req = urllib2.Request(resource)
        else:
            req = urllib2.Request(resource, data=data)

        if verb is not None:
            req.get_method = lambda: verb

        req.add_header(*auth_header(context.auth.username, context.auth.password))
        return req

    def get(self, app, dashboard):
        req = self._request(app, dashboard, verb=Verbs.Get)
        response = urllib2.urlopen(req, timeout=60, context=no_ssl_check())
        raw_data = response.read()

        print raw_data

        ns = {'s': 'http://dev.splunk.com/ns/rest'}
        root = ETtree.XML(raw_data)
        dashboard_data = root.find(".//s:key[@name='eai:data']", ns).text.strip()

        return dashboard_data

    def exists(self, app, dashboard):
        try:
            req = self._request(app, dashboard, verb=Verbs.Get)
            urllib2.urlopen(req, timeout=60, context=no_ssl_check())
            return True
        except urllib2.HTTPError as e:
            if e.code == 404:
                return False
            raise

    def create(self, app, dashboard, data):
        req = self._request(app,
                            verb=Verbs.Post,
                            data=urllib.urlencode({
                                'name': dashboard,
                                'eai:data': data
                            }))
        response = urllib2.urlopen(req, timeout=60, context=no_ssl_check())
        print response.read()

    def update(self, app, dashboard, data):
        req = self._request(app,
                            dashboard,
                            verb=Verbs.Post,
                            data=urllib.urlencode({
                                'eai:data': data
                            }))
        response = urllib2.urlopen(req, timeout=60, context=no_ssl_check())
        print response.read()

    def delete(self, app, dashboard):
        req = self._request(app, dashboard, verb='DELETE')
        response = urllib2.urlopen(req, timeout=60, context=no_ssl_check())
        print response.read()
