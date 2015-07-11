from httplib2 import Http
import os
import re
import time

if len(sys.argv) > 1:
    DATE_DIR = sys.argv[1]
else:
    DATE_DIR = datetime.strftime(datetime.datetime.now(), "%Y%m")

DUMP_DIR = os.path.join("BoardGameGeek.xml", DATE_DIR)

SITEMAP_DIRECTORY = os.path.join(DUMP_DIR, "maps")
GAME_OUTPUT_DIRECTORY = os.path.join(DUMP_DIR, "boardgame_batches")
GEEKLIST_OUTPUT_DIRECTORY = os.path.join(DUMP_DIR, "geeklist")
GAME_NUMBER = re.compile("/boardgame/([0-9]+)/")
GEEKLIST_NUMBER = re.compile("/geeklist/([0-9]*)/")

for d in GAME_OUTPUT_DIRECTORY, GEEKLIST_OUTPUT_DIRECTORY:
    if not os.path.exists(d):
        os.makedirs(d)

BATCH_SIZE = 20

BOARDGAME_URL = "http://boardgamegeek.com/xmlapi/boardgame/%s?comments=1&stats=1"
GEEKLIST_URL = "http://boardgamegeek.com/xmlapi/geeklist/%s?comments=1"

http = Http()

def req(*args, **kwargs):
    try:
        response, body = http.request(*args, **kwargs)
    except Exception, e:
        print "Could not request %r %r: %s" % (args, kwargs, e)
        return None, None
    return response, body

def download_geeklist(number):
    filename = os.path.join(GEEKLIST_OUTPUT_DIRECTORY, "geeklist-%s.xml" % number)
    if os.path.exists(filename):
        print "Skipping %s" % filename
        return False
    url = GEEKLIST_URL % number
    if number in ("36742", "35076", "34435", "30058", "29485", "16221", "8785", "4368", "49088"):
        # For whatever reason these are known to be bad.
        return False
    print "Downloading geeklist %s" % number
    response, body = req(
        url, "GET", headers = {
            "Accept-Encoding": "gzip,deflate",
            "User-Agent" : "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:5.0) Gecko/20100101 Firefox/5.0)" })
    if body is not None:
        open(filename, "w").write(body)
    return True

def download_boardgame_batch(numbers):
    url = BOARDGAME_URL % ",".join(numbers)
    if len(numbers) == 1:
        filename = "boardgame-" + numbers[0] + ".xml"
    else:
        filename = "boardgame-" + numbers[0] + "-" + numbers[-1] + ".xml"
    path = os.path.join(GAME_OUTPUT_DIRECTORY, filename)
    if os.path.exists(path):
        print "Skipping %s, already present." % path
        return False
    print filename, url
    response, body = req(url, "GET", headers={
            "Accept-Encoding": "gzip,deflate",
            "User-Agent": "Mozilla/5.0 (X11; U; Linux i586; de; rv:5.0) Gecko/20100101 Firefox/5.0" })
    if body is not None:
        open(path, "w").write(body)
    return True

def crawl_boardgame_file(filename):
    """Download the listing for every board game in a single site map file."""
    print "Processing %s" % filename
    numbers = []
    for line in open(filename):
        match = GAME_NUMBER.search(line)
        if match is not None:
            (number,) = match.groups()
            numbers.append(number)
            if len(numbers) >= BATCH_SIZE:
                try:
                    made_request = download_boardgame_batch(numbers)
                except Exception, e:
                    made_request = download_boardgame_batch(numbers)
                if made_request:
                    time.sleep(1)
                numbers = []
    # Do one last batch.
    if len(numbers) > 0:
        download_boardgame_batch(numbers)

def crawl_geeklist_file(filename):
    numbers = []
    for line in open(filename):
        match = GEEKLIST_NUMBER.search(line)
        if match is not None:
            number = match.groups()[0]
            made_request = download_geeklist(number)
            if made_request:
                time.sleep(0.5)

def crawl_boardgames():
    """Download the listing for every board game in the site map."""
    for filename in os.listdir(SITEMAP_DIRECTORY):
        if '_boardgame_' in filename:
            crawl_boardgame_file(os.path.join(SITEMAP_DIRECTORY, filename))

def crawl_geeklists():
    for filename in os.listdir(SITEMAP_DIRECTORY):
        if 'geeklist' in filename:
            crawl_geeklist_file(os.path.join(SITEMAP_DIRECTORY, filename))

crawl_boardgames()
crawl_geeklists()
