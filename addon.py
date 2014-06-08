from resources.lib.LoLEventVODs import LoLEventVODs
from resources.lib.LoLEventVODs import LCSStandings
from resources.lib.LoLLearningCenter import LearningCenter
from resources.lib import PluginUtils
from xbmcswift2 import Plugin

plugin = Plugin()

# Main Menu
@plugin.route('/')
def index():
    # Main Menu
    items = []
    
    item  = { 'label': PluginUtils.get_string(30001), 'path': plugin.url_for('show_featured_events'), 'thumbnail' : 'http://c.thumbs.redditmedia.com/QzaSL6tRjZuybp0J.png' }
    items.append(item)
    item  = { 'label': PluginUtils.get_string(30002), 'path': plugin.url_for('show_learning_center') }
    items.append(item)
    item  = { 'label': PluginUtils.get_string(30003), 'path':plugin.url_for('open_settings')  }
    items.append(item)

    return items

# Settings
@plugin.route("/settings/")
def open_settings():
    plugin.open_settings()

# Show all the events that are officially featured on /r/loleventvods
@plugin.route('/loleventvods/featured')
#@plugin.cached(TTL=10)
def show_featured_events():
    
    items = show_events()
    show_items = []
    if (items is not None):
        for item in items:
            if (item['label'].lower().find('featured') > -1):
                show_items.append(item)

    item  = { 'label': PluginUtils.get_string(30004), 'path': plugin.url_for('show_events', after='none') }
    show_items.append(item)
    
    return show_items
    
@plugin.route('/loleventvods/<after>')
@plugin.cached(TTL=10)
def show_events(after='none'):
    # False uses the reddit sorting

    afterPost, events = LoLEventVODs.load_events(True, after)
    items = []

    for lolevent in events:
        date = lolevent.createdOn.strftime('%d/%m/%y')
        
        status = PluginUtils.get_string(30005)
        if (lolevent.status < 99):
            if (lolevent.status == 1):
                status = PluginUtils.get_string(30006)
            if (lolevent.status == 0):
                status = PluginUtils.get_string(30007)
       
            print date
            item  = { 'label': lolevent.title + " (" + status + ")", 'label2': date, 'path': plugin.url_for('show_event', eventId=lolevent.eventId),
                      'thumbnail' : lolevent.imageUrl}
            items.append(item)
            
    if (afterPost is not None):
        item  = { 'label': PluginUtils.get_string(30010), 'path': plugin.url_for('show_events', after=afterPost) }
        items.append(item)        

    return items

@plugin.route('/loleventvods/event/<eventId>')
@plugin.cached(TTL=10)
def show_event(eventId):
    items = []
    
    includeStrawpoll = plugin.get_setting('highlight_recommended_games', bool)

    days = LoLEventVODs.load_event_content(eventId, includeStrawpoll)
    
    for day in days:
        #dayId day previewVideo matches imageUrl
        item  = { 'label': day.day.replace('&amp;', '&'), 'path': plugin.url_for('show_matches', eventId=eventId, dayId = day.dayId), 'replace_context_menu': True }
        items.append(item)

    return items

@plugin.route('/loleventvods/event/<eventId>/matches/<dayId>')
@plugin.cached(TTL=10)
def show_matches(eventId, dayId):
    items = []

    includeStrawpoll = plugin.get_setting('highlight_recommended_games', bool)

    days = LoLEventVODs.load_event_content(eventId, includeStrawpoll)

    day = None
    # Get the right thing
    for d in days:
        if (d.dayId == dayId):
            day = d
 
    if (day is not None):
        
        if (day.previewShow is not None):
            # We can iterate the video links
            if (day.previewShow['text'] is not None and day.previewShow['videoId'] is not None):
                if (day.previewShow['videoId'] != 'EMPTY'):
                    youtube_url = PluginUtils.get_string(30100) % day.previewShow['videoId']
                else:
                    youtube_url = ""

                item  = { 'label': day.previewShow['text'].replace('&amp;', '&'),
                          'path': youtube_url,
                          'thumbnail' : PluginUtils.get_string(30101) % day.previewShow['videoId'],
                          'is_playable': True }
                items.append(item)
        
        
        for match in day.matches:
            recommended = ''#match.strawPollScore
            # Add spoiler data?

            titleFormat = PluginUtils.get_string(30008)

            title = titleFormat.format(match.gameId, match.team1, match.team2, recommended, "", "")
            item  = { 'label': title,
                      'path': plugin.url_for('show_videos', eventId=eventId, dayId = dayId, gameId = match.gameId),
                      'thumbnail' : day.imageUrl, 'replace_context_menu': True
            }

            items.append(item)

    return items


@plugin.route('/loleventvods/event/<eventId>/matches/<dayId>/videos/<gameId>')
@plugin.cached(TTL=10)
def show_videos(eventId, dayId, gameId):
    items = []
    includeStrawpoll = plugin.get_setting('highlight_recommended_games', bool)

    days = LoLEventVODs.load_event_content(eventId, includeStrawpoll)
    
    day = None
    # Get the right thing
    for d in days:
        if (d.dayId == dayId):
            day = d
 
    if (day is not None):
        for match in day.matches:
            if (match.gameId == gameId):
                for video in match.videoLinks:
                    if (video is not None):
                        # We can iterate the video links
                        if (video['text'] is not None and video['videoId'] is not None):
                            if (video['videoId'] is not None and video['videoId'] != 'EMPTY'):
                                youtube_url = PluginUtils.get_string(30100) % video['videoId']
                            else:
                                youtube_url = ""

                            label = video['text'].replace('&amp;', '&')
                            if (video['time'] is not ''):
                                label = label + " @" + video['time']
                            item  = { 'label': label,
                                      'path': youtube_url,
                                      'thumbnail' : PluginUtils.get_string(30101) % video['videoId'],
                                      'is_playable': True }
                            items.append(item)

    return items

# LEARNING CENTER
@plugin.route('/learning')
def show_learning_center():
    items = []
    # TODO: Localized strings
    item  = { 'label': PluginUtils.get_string(30009), 'path': plugin.url_for('show_leaguecraft101') }
    items.append(item)

    return items

@plugin.route('/learning/leaguecraft101')
def show_leaguecraft101():
    items = []

    for video in LearningCenter.leaguecraft_videos():

        youtube_url = PluginUtils.get_string(30100) % video['videoId']

        item  = { 'label': video['text'],
                  'path': youtube_url,
                  'thumbnail' :PluginUtils.get_string(30101) % video['videoId'],
                  'is_playable': True, 'replace_context_menu': True}
        items.append(item)

    return items


# Run the plugin
if __name__ == '__main__':
    plugin.run()
