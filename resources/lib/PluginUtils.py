import urllib2
import htmllib
import time
import re

from xbmcswift2 import Plugin
plugin = Plugin()

def get_string(key):
    string = plugin.get_string(key)
    string = string.replace("&amp;", "&")
    return string

# Static Method that tries to execute the request two times, with 3 second delay
def do_request(url):

    req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
    response = None

    try:
        response = urllib2.urlopen(req)
    except:
        time.sleep(3)
        try:
            response = urllib2.urlopen(req)
        except:
            return None

    return response

# Method that will unescape the HTML
def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

# Method that will parse common youtube URL formats
def parse_youtube_url(url):
    youtube_id = 'EMPTY'
    youtube_Time = ''
    matches = re.findall("(\?|\&)([^=]+)\=([^&]+)", url)
    if (matches is not None):
        for match in matches:
            if (match is not None):
                if (match[1] == "v"):
                    youtube_id = match[2]
                if (match[1] == "t"):
                    youtube_Time = match[2]

    return {'videoId' : youtube_id,
             'time' : youtube_Time}

def write_file(contents):
    # Open a file
    fo = open("foo.txt", "wb")
    fo.write(contents);

    # Close file
    fo.close()

