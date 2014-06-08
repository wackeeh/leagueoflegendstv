from collections import namedtuple
import json
import datetime
from operator import attrgetter
import re

from bs4 import BeautifulSoup
from resources.lib import PluginUtils


def get_poll_results(url):
    
    pollResult = namedtuple('pollResult', 'team1 team2 votes')
    pollResults = []
    
    # Do the request
    response = PluginUtils.do_request(url + "/r", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36")
    if (response is None):
        return None
    
    soup = BeautifulSoup(response)
    for node in soup.find_all('div', id='pollBody'):
        for options in node.find_all('div', class_='pollOption'):
            gameName = options.find('div', class_='pollOptionName').text.replace(" vs ", ",")
            teams = gameName.split(',')
            
            result = options.find(text = re.compile('\d{1,4} votes'))
            votes = 0
            if (result is not None):
                try:
                    votes = int(result.replace(" votes", ""))
                except:
                    votes = 0
                
            pollResults.append(pollResult(teams[0], teams[1], votes))
            
    return pollResults