from collections import namedtuple
import json
import datetime
from operator import attrgetter

from resources.lib.BeautifulSoup import BeautifulSoup
from resources.lib import PluginUtils

# CONSTANTS
LOLEVENTURL = PluginUtils.unescape(PluginUtils.get_string(30105))
LOLMATCHESURL = PluginUtils.unescape(PluginUtils.get_string(30106))
ACTIVE_STRING = PluginUtils.get_string(30050)
FINISHED_STRING = PluginUtils.get_string(30051)
FEATURED_STRING = PluginUtils.get_string(30052)
FINISHEDFEATURED_STRING = PluginUtils.get_string(30053)

PAGE_SIZE = 10
#NOTSTREAMED_STRING = "**Not Streamed**"

def load_events(sortByStatus, after):
    # The reddit api does things like this:
    # /r/bla.json?limit=pagesize&after=postId
    # Let's build a URL

    urlAppend = '?limit=' + str(PAGE_SIZE)

    if (after is not 'none'):
        urlAppend += '&after=' + after
    
    response = PluginUtils.do_request(LOLEVENTURL + urlAppend)
    if (response is None):
        return None

    events = []

    # Now lets parse results
    decoded_data = json.load(response)
    root = decoded_data['data']
    # after link = 
    afterPost = root['after']

    LoLEvent = namedtuple('LoLEvent', 'title status eventId createdOn imageUrl')

    # For Each Item in Children
    for post in root['children']:
        html = post['data']['selftext_html']
        if (html is not None):
            soup = BeautifulSoup(PluginUtils.unescape(html))

            imgUrl = ''
            isEvent = False
            link = soup.find('a', href='#EVENT_TITLE')
            if (link is not None):
                isEvent = True

            link = soup.find('a', href='#EVENT_PICTURE')
            if (link is not None):
                imgUrl = link.title

        status = 99
        # Using numbers for status so we can easily sort by this
        # link_flair_css_class: "ongoing"
        # link_flair_css_class: "finished"
        # link_flair_css_class: "twitchongoing"
        # link_flair_css_class: "featured"
        # link_flair_css_class: "finishedfeatured"
        # link_flair_css_class: null
        flair_css = post['data']['link_flair_css_class']
        if (flair_css is not None):
            if (flair_css.lower()== FEATURED_STRING):
                status = 0
            if (flair_css.lower()== ACTIVE_STRING):
                status = 1
            if (flair_css.lower()== FINISHED_STRING):
                status = 2
            if (flair_css.lower()== FINISHEDFEATURED_STRING):
                status = 2

        # Some don't have link_flair_css_class but are events
        if (status == 99 and isEvent):
            status = 98


        childEvent = LoLEvent(title = post['data']['title'],
                              status = status,
                              eventId = post['data']['id'],
                              createdOn = datetime.datetime.fromtimestamp(int(post['data']['created'])),
                              imageUrl = imgUrl)

        events.append(childEvent)


    if (sortByStatus):
        # sort
        return afterPost, sorted(events, key=attrgetter('status'))
    else:
        return afterPost, events

def load_event_content(eventId):

    LoLEventDay = namedtuple('LoLEventDay', 'dayId day matches recommended imageUrl')
    LoLEventMatch = namedtuple('LoLEventMatch', 'gameId team1 team2 videoLinks')

    url = LOLMATCHESURL % eventId

    response = PluginUtils.do_request(url)
    if (response is None):
        return None
    # Now lets parse results
    decoded_data = json.load(response)

    selfText = decoded_data[0]['data']['children'][0]['data']['selftext_html']

    eventTitle = ''
    days = []

    soup = BeautifulSoup(PluginUtils.unescape(selfText))

    # Get all the recommended matches, we add those to the events
    # We do it like this Game H1_C1_C4
    recommended = ''
    #a href="/spoiler"
    spoilers = soup.findAll("a", href="/spoiler")
    if (spoilers is not None):
        for spoiler in spoilers:
            # add them to the list
            games = spoiler.text.replace(',', '_')
            recommended += games + "_"

    imgUrl = ''
    link = soup.find('a', href='#EVENT_PICTURE')
    if (link is not None):
        imgUrl = link.title

    # find all tables
    tables = soup.findAll("table")
    for idx, table in enumerate(tables):
        if (table is not None):

            titleLink = table.find("a", href="http://www.table_title.com")
            if (titleLink is not None):
                eventTitle = titleLink['title']

            YouTubeColumns = []
            Team1Index = -1
            Team2Index = -1

            # Investigate the right columns for youtube links
            rows = table.find("thead").findAll("tr")
            for row in rows :
                cols = row.findAll("th")
                for i, col in enumerate(cols):
                 if (col.text.lower() == "youtube"):
                     YouTubeColumns.append(i)
                 if (col.text.lower() == "team 1"):
                     Team1Index = i
                 if (col.text.lower() == "team 2"):
                     Team2Index = i

            #
            matches=[]

            rows = table.find("tbody").findAll("tr")
            for row in rows :
                videos = []
                cols = row.findAll("td")
                if (cols is not None):
                    for yv in YouTubeColumns:
                        if (cols[yv] is not None):
                            if (cols[yv].a is not None):

                                youTubeData = PluginUtils.parse_youtube_url(cols[yv].a['href'])
                                videos.append({'text' : cols[yv].a.text,
                                               'videoId' : youTubeData['videoId'],
                                               'time' : youTubeData['time'] })

                matches.append(LoLEventMatch(cols[0].text, cols[Team1Index].text, cols[Team2Index].text, videos))

            days.append(LoLEventDay(dayId = idx,
                                day=eventTitle,
                                matches = matches,
                                recommended = recommended,
                                imageUrl = imgUrl))
    return days

