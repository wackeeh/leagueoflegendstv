from resources.lib.BeautifulSoup import BeautifulSoup   
from resources.lib import PluginUtils

TEAMS_NA = {
    'C9' : 'Cloud 9 HyperX',
    'CLG' : 'Counter Logic Gaming',
    'CRS' : 'Curse',
    'EG' : 'Evil Geniuses',
    'CST' : 'Team Coast',
    'DIG' : 'Team Dignitas',
    'TSM' : 'Team SoloMid',
    'XDG' : 'XDG'
}

TEAMS_EU = { 'ROC' : 'ROCCAT',
    'GMB' : 'Gambit Gaming',
    'FNC' : 'Fnatic',
    'SK' : 'SK Gaming',
    'ALL' : 'Alliance',
    'MIL' : 'Millenium',
    'CW' : 'Copenhagen Wolves',
    'SHC' : 'Supa Hot Crew' }



def get_lcs_standings(teamName):
    # This method loads the latest standings from the Gamepedia server
    url=''
    if (teamName in TEAMS_EU):
        url = PluginUtils.unescape(PluginUtils.get_string(30104))
    if (teamName in TEAMS_NA):
        url = PluginUtils.unescape(PluginUtils.get_string(30103))

    if (url != ''):
        response = PluginUtils.do_request(url)
        if (response is not None):

            # Lets process the html
            # decoded_data = json.load(response)
            soup = BeautifulSoup(response)

            tables = soup.findAll('table')

            if (tables is not None):
                for table in tables:
                    # We have the table, now lets try and get the right row
                    rows = table.find('tbody').findAll('tr')

                    if (rows is not None):
                        for idx, row in enumerate(rows):
                            columns = row.findAll('td')
                            if (columns is not None):
                                if (columns[2] is not None):
                                    if (teamName in TEAMS_EU):
                                        if (columns[2].find('a').text.lower() == TEAMS_EU[teamName].lower()):
                                            return {'standing' : idx+1,
                                                    'record' : columns[3].find('span').text + "W-" + columns[4].find('span').text +"L" }
                                    if (teamName in TEAMS_NA):
                                        if (columns[2].find('a').text.lower() == TEAMS_NA[teamName].lower()):
                                            return {'standing' : idx+1,
                                                    'record' : columns[3].find('span').text + "W-" + columns[4].find('span').text +"L"}
    return None