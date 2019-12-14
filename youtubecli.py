import requests
import subprocess
import os
import json
from socketio import Client as SocketClient
from bs4 import BeautifulSoup
import getFromPath

dir_path = os.path.dirname(os.path.realpath(__file__))

player = subprocess.Popen([os.path.join(dir_path, 'player\\youtubecli-win32-x64\\youtubecli.exe')], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
playerSocket = SocketClient()
playerSocket.connect('http://localhost:8081')

scraper = requests.Session()
scraper.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

filters = {
    'video': 'EgIQAQ==',
    'channel': 'EgIQAg==',
    'playlist': 'EgIQAw=='
}
commands = ['play', 'pause', 'forward', 'rewind', 'volumeUp', 'volumeDown']

BLANK_ROW = '|' + ('-' * 3) + '|' + ('-' * 94) + '|\n'

def main():
    try:
        command = ''
        while True:
            command = input('youtube> ')

            if command == 'quit' or command == 'exit':
                playerSocket.disconnect()
                break
            else:
                commandParts = command.split(':')
                if len(commandParts) == 2 and commandParts[0] in filters.keys():
                    options = getOptions(commandParts[1], commandParts[0])
                    navigateOptions(options, commandParts[0])
                elif commandParts[0] in commands:
                    if (len(commandParts) == 2):
                        playerSocket.emit('control', json.dumps({'command': commandParts[0], 'param': commandParts[1]}))
                    else:
                        playerSocket.emit('control', json.dumps({'command': commandParts[0]}))
                else:
                    print('Bad input')
    except Exception as e:
        playerSocket.disconnect()
        raise e
    

def getOptions(query, filterType, continuation=""):
    raw = scraper.get('https://www.youtube.com/results', params={'search_query':  query.replace(' ', '+'), 'sp': filters[filterType]}).content
    soup = BeautifulSoup(raw, 'html.parser')
    script = [str(script) for script in soup.find_all('script') if 'window["ytInitialData"]' in str(script)][0]
    data = json.loads(script[script.index('{') : script.rindex('};\n') + 1])
    items = getFromPath.get(data, 'contents.twoColumnSearchResultsRenderer.primaryContents.sectionListRenderer.contents.[0].itemSectionRenderer.contents')
    
    if filterType == 'video':
        options = {
            'continuation': getFromPath.safeGet(data, 'contents.twoColumnSearchResultsRenderer.primaryContents.sectionListRenderer.contents.[0].itemSectionRenderer.continuations.[0].nextContinuationData.continuation'),
            'list': [{
                'title': getFromPath.safeGet(rawItem, 'videoRenderer.title.runs.[0].text', ''),
                'channel': getFromPath.safeGet(rawItem, 'videoRenderer.ownerText.runs.[0].text', ''),
                'duration': getFromPath.safeGet(rawItem, 'videoRenderer.lengthText.simpleText', ''),
                'age': getFromPath.safeGet(rawItem, 'videoRenderer.publishedTimeText.simpleText', ''),
                'views': getFromPath.safeGet(rawItem, 'videoRenderer.shortViewCountText.simpleText', ''),
                'id': getFromPath.safeGet(rawItem, 'videoRenderer.videoId', '')
            } for rawItem in items if not(getFromPath.safeGet(rawItem, 'videoRenderer.videoId') == None)]
        }
        
        return options
    elif filterType == 'channel':
        options = {
            'continuation': data['contents.twoColumnSearchResultsRenderer.primaryContents.sectionListRenderer.contents.[0].itemSectionRenderer.continuations.[0].nextContinuationData.continuation'],
            'list': [{
                'title': getFromPath.safeGet(rawItem, 'channelRenderer.title.simpleText', ''),
                'subs': getFromPath.safeGet(rawItem, 'channelRenderer.subscriberCountText.simpleText', ''),
                'id': getFromPath.safeGet(rawItem, 'channelRenderer.channelId', '')
            } for rawItem in items if not(getFromPath.safeGet(rawItem, 'channelRenderer.channelId') == None)]
        }

        return options
    else:
        options = {
            'continuation': data['contents.twoColumnSearchResultsRenderer.primaryContents.sectionListRenderer.contents.[0].itemSectionRenderer.continuations.[0].nextContinuationData.continuation'],
            'list': [{
                'title': getFromPath.safeGet(rawItem, 'playlistRenderer.title.simpleText', ''),
                'count': getFromPath.safeGet(rawItem, 'playlistRenderer.videoCount', ''),
                'id': getFromPath.safeGet(rawItem, 'playlistRenderer.playlistId', '')
            } for rawItem in items if not(getFromPath.safeGet(rawItem, 'playlistRenderer.playlistId') == None)]
        }

        return options

def navigateOptions(options, optionsType):
    index = 0

    while True:
        printThreeOptions(options, index, optionsType)

        navCommand = input('0-' + str(len(options["list"]) - 1) + ': start a video\nnext / previous / cancel: navigate\nEnter an option from above: ')

        if navCommand == 'cancel':
            break
        elif navCommand == 'next':
            if (index + 3) < len(options['list']):
                index += 3
        elif navCommand == 'previous':
            if index > 3:
                index -= 3
            else:
                index = 0
        else:
            try:
                selectedIndex = int(navCommand)
                if not(optionsType == 'channel'):
                    sendVideoOrPlaylist(options['list'][selectedIndex]['id'], optionsType)
                else:
                    pass

                break
            except:
                print('Not an index')
                break

def printThreeOptions(options, index, optionsType):
    optionsTable = BLANK_ROW

    if optionsType == 'video':
        for i, option in enumerate(options['list'][index : index + 3]):
            optionsTable += '|{:^3}|{:>94}|\n'.format(str(i + index), option['title'])
            optionsTable += '|{:^3}|{:>94}|\n'.format('', option['channel'] + ' ' + str(option['duration']) + ' ' +  option['age'] + ' ' + option['views'])
            optionsTable += BLANK_ROW
    elif optionsType == 'channel':
        optionsTable = ''
    else:
        optionsTable = ''

    print(optionsTable)
    

def sendVideoOrPlaylist(id, contentType):
    print('sending '  + id + '...')

    if contentType == 'playlist':
        playerSocket.emit('playlist', id)
    else:
        playerSocket.emit('video', id)

    print('sent')

if __name__ == "__main__":
    main()