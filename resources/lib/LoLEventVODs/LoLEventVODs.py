import json
import datetime
import re

from collections import namedtuple
from operator import attrgetter
from bs4 import BeautifulSoup
from resources.lib import PluginUtils
from resources.lib.LoLEventVODs import StrawPoll


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
            
            link = soup.find('a', href="#EVENT_DESCRIPTION")
            if (link is not None):
                isEvent = True
                    
            link = soup.find('a', href='#EVENT_PICTURE')
            if (link is not None):
                if (link.has_attr('title')):
                    imgUrl = link['title']

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

def load_event_content(eventId, includeStrawpoll):
    
    LoLEventDay = namedtuple('LoLEventDay', 'dayId day previewShow matches imageUrl')
    LoLEventMatch = namedtuple('LoLEventMatch', 'gameId team1 team2 videoLinks strawPollScore')

    url = LOLMATCHESURL % eventId

    response = PluginUtils.do_request(url)
    if (response is None):
        return None
        
    
    # Now lets parse results
    decoded_data = json.load(response)

    selfText = decoded_data[0]['data']['children'][0]['data']['selftext_html']

    days = []

    data = PluginUtils.unescape(selfText).replace("<sup>", "").replace("</sup>", "")

    soup = BeautifulSoup(data)

    imgUrl = ''
    link = soup.find('a', href='#EVENT_PICTURE')
    if (link is not None):
        imgUrl = link['title']
    
    # This method loops through all the h2 / h4 tags that have week and day in there
    # So, now that we have the day, we can add it
    for node in soup.find_all(name=re.compile("h\d{1}")):
        dayTitle = node.text
        
        # Create a tag based on the title
        idx = dayTitle
        table = node.find_next_sibling('table')
        
        strawpoll = ''
        ulTag = table.find_next_sibling('ul')
        if (ulTag is not None):
            sp = ulTag.find('strong', text=re.compile("recommended games:", re.IGNORECASE))
            if (sp is not None):
                links = sp.parent.find('a')
                if (links is not None):
                    if (links.text.lower() == "strawpoll"):
                        strawpoll = links['href']  

        pollResults = None
        if (strawpoll != '') and (includeStrawpoll):
            pollResults = StrawPoll.get_poll_results(strawpoll)
            
        matches=[]
        
        matchesList = {}
        # Parse table
        # So first, get all the links
        links = table.find_all('a', href=re.compile("www.youtube.com/watch"))
        for link in links:
            row = link.parent.parent
            #print link.text
            if (row is not None):
                id = row.find_next('td').text.strip()
                tdVs = row.find('td', text=re.compile('vs', re.IGNORECASE))
                team1 = tdVs.find_previous('td')
                team2 = tdVs.find_next('td')
                video = {"text" : link.text, "link": link['href'] }
                
                if (id not in matchesList):
                    #matchesList.append(match)
                    matchesList[id] = {}
                    matchesList[id]["team1"] = team1.text.strip()
                    matchesList[id]["team2"] = team2.text.strip()
                    matchesList[id]["videos"] = []
                    matchesList[id]["videos"].append(video)
                else:
                    matchesList[id]["videos"].append(video)
                
        for match in matchesList:
            videos = []
            
            for video in matchesList[match]['videos']:
                youTubeData = PluginUtils.parse_youtube_url(video['link'])
                videos.append({'text' : video['text'],
                        'videoId' : youTubeData['videoId'],
                        'time' : youTubeData['time'] })

            votes = 0
            if (pollResults is not None):
                for result in pollResults:
                    print result
                    if (result.team1 == matchesList[match]['team1']) or (result.team1 == matchesList[match]['team2']):
                        votes = result.votes
                
            matches.append(LoLEventMatch(match, matchesList[match]['team1'], matchesList[match]['team2'], videos, votes))    
                

        previewShow = None
        ulTag = node.find_next('ul')
        if (ulTag is not None):
            preview = ulTag.find('strong', text=re.compile("LCS Preview Show", re.IGNORECASE))
            if (preview is not None):
                for links in preview.parent.find_all('a'):
                    if (links.text.lower() == "youtube"):
                    #youTubeData = PluginUtils.parse_youtube_url(node.nextSibling['href'])
                        youTubeData = PluginUtils.parse_youtube_url(links['href'])
                        previewShow = {'text' : 'Preview Show',
                                    'videoId' : youTubeData['videoId'],
                                    'time' : youTubeData['time'] }

        if (len(matches) > 0):
            days.append(LoLEventDay(dayId = idx,
                day=dayTitle,
                previewShow = previewShow,
                matches = matches,
                imageUrl = imgUrl))
    
    return days