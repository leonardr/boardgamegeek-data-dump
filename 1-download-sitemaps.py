from bs4 import BeautifulSoup
from httplib2 import Http
import os

http = Http()

if len(sys.argv) > 1:
    DATE_DIR = sys.argv[1]
else:
    DATE_DIR = datetime.strftime(datetime.datetime.now(), "%Y%m")

DUMP_DIR = os.path.join("BoardGameGeek.xml", DATE_DIR)

SITEMAP_DIRECTORY = os.path.join(DUMP_DIR, "maps")
if not os.path.exists(SITEMAP_DIRECTORY):
    os.makedirs(SITEMAP_DIRECTORY)

def req(*args, **kwargs):
    try:
        response, body = http.request(*args, **kwargs)
    except Exception, e:
        print "Could not request %r %r: %s" % (args, kwargs, e)
        return None, None
    return response, body

response, body = req('http://boardgamegeek.com/sitemapindex')
import time

soup = BeautifulSoup(body, "lxml")
for loc in soup.find_all("loc"):
    url = loc.string.strip()
    filename = url[url.rindex("sitemap_")+len("sitemap_"):]
    path = os.path.join(SITEMAP_DIRECTORY, filename)
    if os.path.exists(path):
        continue
    print "%s -> %s" % (url, path)
    response, body = req(url)
    open(path, "w").write(body)
    time.sleep(1)
