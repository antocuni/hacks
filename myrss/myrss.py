from wsgiref import util
import urlparse
from lxml import etree
import requests

GAZZETTA_RSS = 'https://www.gazzetta.it/rss/home.xml'

def application(environ, start_response):
    uri = util.request_uri(environ)
    path = urlparse.urlsplit(uri).path
    if path.startswith('/gazzetta'):
        return gazzetta(start_response)
    start_response('404 Not Found', [])
    return ['Not found: %s' % path]

def gazzetta(start_response):
    resp = requests.get(GAZZETTA_RSS)
    resp.raise_for_status()
    headers = []
    for header in ('Content-Type', 'Date', 'Expires', 'Cache-Control'):
        headers.append((header, resp.headers[header]))
    start_response('200 OK', headers)
    return [filter_gazzetta_rss(resp.text.encode('utf-8'))]

def filter_gazzetta_rss(content):
    rss = etree.fromstring(content)
    for item in rss.xpath("//item"):
        link = item.find('link')
        if link is None:
            continue
        if link.text.startswith('http'):
            item.getparent().remove(item)
    return etree.tostring(rss, pretty_print=True, xml_declaration=True,
                          encoding='UTF-8')


def main():
    resp = requests.get(GAZZETTA_RSS)
    print filter_gazzetta_rss(resp.text.encode('utf-8'))

if __name__ == '__main__':
    main()
