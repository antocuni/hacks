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
        return headers, self.filter(resp.text.encode('utf-8'))

    def filter(self, content):
        raise NotImplementedError

class Gazzetta(AbstractFeed):

    URL = 'https://www.gazzetta.it/rss/home.xml'

    def filter(self, content):
        rss = etree.fromstring(content)
        for item in rss.xpath("//item"):
            link = item.find('link')
            if link is None:
                continue
            if link.text.startswith('http'):
                item.getparent().remove(item)
        return etree.tostring(rss, pretty_print=True, xml_declaration=True,
                              encoding='UTF-8')


# WSGI-compatible entry point
def application(environ, start_response):
    uri = util.request_uri(environ)
    path = urlparse.urlsplit(uri).path
    if path.startswith('/gazzetta'):
        feed = Gazzetta()
    else:
        start_response('404 Not Found', [])
        return ['Not found: %s' % path]
    #
    headers, content = feed.fetch_and_filter()
    start_response('200 OK', headers)
    return [content]


# only useful for debugging/development
def main():
    feed = Gazzetta()
    headers, content = feed.fetch_and_filter()
    for key, value in headers:
        print '%s: %s' % (key, value)
    print
    print content

if __name__ == '__main__':
    main()
