from wsgiref import util
import urlparse
from lxml import etree
import requests

class AbstractFeed(object):

    URL = None

    def fetch_and_filter(self):
        resp = requests.get(self.URL)
        resp.raise_for_status()
        headers = []
        for header in ('Content-Type', 'Date', 'Expires', 'Cache-Control'):
            headers.append((header, resp.headers[header]))
        return headers, self.filter(resp.content)

    def filter(self, content):
        raise NotImplementedError


class FilterHosts(AbstractFeed):
    ALLOWED_HOSTS = frozenset()

    def filter(self, content):
        rss = etree.fromstring(content)
        for item in rss.xpath("//item"):
            link = item.find('link')
            if link is None:
                continue
            parts = urlparse.urlsplit(link.text)
            if parts.netloc not in self.ALLOWED_HOSTS:
                item.getparent().remove(item)
        return etree.tostring(rss, pretty_print=True, xml_declaration=True,
                              encoding='UTF-8')



class Gazzetta(FilterHosts):
    URL = 'https://www.gazzetta.it/rss/home.xml'
     # '' means "allow only links which do NOT specify an external site"
    ALLOWED_HOSTS = frozenset(['', 'gazzetta.it', 'www.gazzetta.it'])


class Corriere(FilterHosts):
    URL = 'https://www.corriere.it/rss/homepage.xml'
    ALLOWED_HOSTS = frozenset(['', 'corriere.it', 'www.corriere.it'])


# WSGI-compatible entry point
def application(environ, start_response):
    uri = util.request_uri(environ)
    path = urlparse.urlsplit(uri).path
    if path.startswith('/gazzetta'):
        feed = Gazzetta()
    elif path.startswith('/corriere'):
        feed = Corriere()
    else:
        start_response('404 Not Found', [])
        return ['Not found: %s' % path]
    #
    headers, content = feed.fetch_and_filter()
    start_response('200 OK', headers)
    return [content]


# only useful for debugging/development
def main():
    #feed = Gazzetta()
    feed = Corriere()
    headers, content = feed.fetch_and_filter()
    for key, value in headers:
        print '%s: %s' % (key, value)
    print
    print content

if __name__ == '__main__':
    main()
