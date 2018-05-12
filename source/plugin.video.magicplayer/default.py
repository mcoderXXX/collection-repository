#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
#import httplib      //required only for getRedirectLocation if use
import urllib
import urllib2
import urlparse
import urlresolver
import liveresolver

addon_id            = 'plugin.video.magicplayer'
addon               = xbmcaddon.Addon(addon_id)
addon_name          = addon.getAddonInfo('name')
ADDONFANART         = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id , 'fanart.jpg'))
ADDONICON           = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id, 'icon.png'))
dialog              = xbmcgui.Dialog()
dialogP             = xbmcgui.DialogProgress()
DATA_FOLDER         = xbmc.translatePath(os.path.join('special://home/userdata/addon_data/' + addon_id))
HISTORYPLAY_LST     = xbmc.translatePath(os.path.join(DATA_FOLDER, 'historyplay.lst'))
HISTORYCHANNELIST_LST = xbmc.translatePath(os.path.join(DATA_FOLDER, 'historychannellist.lst'))
PLUGIN_F4M          = xbmc.translatePath(os.path.join('special://home/addons/plugin.video.f4mTester'))
HOME                = xbmc.translatePath(os.path.join('special://home'))
TITLE               = "[COLOR blue]%s[/COLOR]" % (addon_name)


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

# Create DATA-Folder if necessary
if not os.path.exists(DATA_FOLDER):
  os.mkdir(DATA_FOLDER);


### Common Functions

def build_url(query):
    return base_url+'?'+urllib.urlencode(query)

def getFileExt(pathfile):
    return os.path.splitext(pathfile)[1]

# Get the local ressource directory
def getLocalResDir():
    return addon.getSetting('localResDir')

def getDirList(path, filterext=()):
    dirlist = {'dirs': [], 'files': []}

    dirlist['dirs'], dirlist['files'] = xbmcvfs.listdir(path)

    # sort list
    dirlist['dirs'] = sorted(dirlist['dirs'])
    dirlist['files'] = sorted(dirlist['files'])

    # create flat list
    flatdirlist = [] 
    for i in dirlist['dirs']:
        flatdirlist.append({'name': i, 'type': 'd'})

    for i in dirlist['files']:
        flatdirlist.append({'name': i, 'type': 'f'})

    return flatdirlist

def showDir(showpath):
    fileExtFilter = (".m3u", ".m3u8", ".ts", ".mp3", ".mp4", ".avi", ".mkv", ".mpeg", ".mpeg2")
    resdir = getLocalResDir()

    dirlist = getDirList(showpath, fileExtFilter);

    #@DEBUG:
    xbmc.log('showDir(%s, %d)' % (showpath, addon_handle), xbmc.LOGDEBUG)

    #prepare list
    for f in dirlist:
        #@todo: iconImage anpassen
        if f['type'] == 'f':
            #file
            li = xbmcgui.ListItem(f['name'], iconImage='DefaultVideo.png')
            ext = getFileExt(f['name']) 

            if ext.lower() in (".m3u8", ".m3u"):
                url = build_url({'mode': 'filelist', 'file': showpath + '/' + f['name']})
            else:
                url = build_url({'mode': 'play', 'url': showpath + '/' + f['name']})

            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        else:
            #dir
            li = xbmcgui.ListItem(f['name'], iconImage='DefaultFolder.png')
            url = build_url({'mode': 'folder', 'resdir': showpath + '/' + f['name']})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)


    #@todo: funktioniert das man setContent nach ListItem setzt? - Alternative: 'files'
    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.endOfDirectory(addon_handle)
        

def getM3U8List(pathfile):

    #@todo: improve the parser
    def parseParams(text):
        result = {}

        status = 0
        name = ''
        value = ''
        skip = False
        for c in text:
            if status == 0:
                if c == '=':
                    status = 1
                    continue
                else:
                    if c != ' ':
                        name += c

            if status == 1:
                if c == ' ': continue
                if c == '"':
                    status = 2
                    continue

            if status == 2:
                if c == '"':
                    status = 0
                    result[name] = value
                    name = ''
                    value = ''
                    continue
                else:
                    value += c

        return result

    
    prefixEntry = "#EXTINF:"

    entryList = []
    expectUrl = False
    paramReg = re.compile('^([-0-9]*) *(.*)')

    f = xbmcvfs.File(pathfile)
    rfile = f.read()

    rfile.replace('\r', '')
    rfile = rfile.split('\n') 

    for l in rfile:
        xbmc.log('read m3u: line: %s' % (l), xbmc.LOGDEBUG)
        xbmc.log('status: %s' % (str(l)), xbmc.LOGDEBUG)

        if not l:
            continue

        elif l[:len(prefixEntry)] == prefixEntry:
            head = l[len(prefixEntry):].split(',', 2)
            m = paramReg.match(head[0].rstrip())
            time = m.group(1)
            params = parseParams(m.group(2))
            if len(head) > 1:
                title = head[1].rstrip()
            else:
                title = ""

            expectUrl = True

        else:
            if l[0] == "#":
                continue

            if expectUrl == True:
                url = l.rstrip()
                entryList.append({'time': time, 'params': params, 'title': title, 'url': url})
                expectUrl = False

    f.close()

    return entryList        
            

def showM3U8List(pathfile):
    xbmc.log('showM3U8List(%s)' % (pathfile), xbmc.LOGDEBUG)

    playList = getM3U8List(pathfile)
    
    name = os.path.basename(pathfile)

    # Add to history
    addHistory(HISTORYCHANNELIST_LST, pathfile, name)

    for e in playList:
        url = build_url({'mode': 'play', 'url': e['url'], 'name': e['title']})
        iconimg = e['params'].get('tvg-logo', 'DefaultVideo.png')
        li = xbmcgui.ListItem(e['title'])
        li.setArt({'icon': iconimg, 'thumb': iconimg})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
    
    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.endOfDirectory(addon_handle)


#@todo: erstelle ein history-Datei (wo wird die gespeichert?); Konfiguration Wert festlegen wieviele Einträge gespeichert werden sollen!; ggf. Kontextmenü implementieren um die Reihenfolge, sowie einzelne Löschungen zu ermöglichen
def showHistoryPlay():
    hlst = getHistory(HISTORYPLAY_LST)

    for l in hlst:
        ext = getFileExt(l['url'])
        if len(l['name']): 
            name = l['name']
        else:
            name = os.path.basename(l['url'])

        url = build_url({'mode': 'play', 'name': l['name'], 'url': l['url']})
        
        li = xbmcgui.ListItem(name + ' - [' + l['url'] + ']', iconImage='DefaultVideo.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

    xbmcplugin.setContent(addon_handle, 'files')
    xbmcplugin.endOfDirectory(addon_handle)


def showHistoryChannelList():
    hlst = getHistory(HISTORYCHANNELIST_LST)

    for l in hlst:
        ext = getFileExt(l['url'])
        if len(l['name']): 
            name = l['name']
        else:
            name = 'Unknown'

        urlpath = os.path.dirname(l['url'])

        url = build_url({'mode': 'filelist', 'name': name, 'file': l['url']})
        
        li = xbmcgui.ListItem(name + ' - [' + urlpath + '/]', iconImage='DefaultVideo.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.setContent(addon_handle, 'files')
    xbmcplugin.endOfDirectory(addon_handle)

# @brief Fügt einen Eintrag zur History hinzu
# @param url    erwartet einen relativen Pfad zur base_url
def addHistory(historyfile, url, name=None):
    historyMaxEntry = 20
    countEntry = 0
    newEntry = name.replace(':', '_') + ': ' + url

    #read list
    hlst = []
    if os.path.isfile(historyfile):
        with open(historyfile, 'rt') as f:
            for l in f:
                entry = l.rstrip()
                if entry != newEntry:
                    hlst.append(entry)
                    countEntry += 1

    hlst.append(newEntry)

    with open(historyfile, 'wt') as f:
        for e in hlst[-historyMaxEntry:]: 
            f.write(e + "\n")


def getHistory(historyfile):
    hlst = []
    if os.path.isfile(historyfile):
        with open(historyfile, 'rt') as f:
            for l in f:
                hlst.append(l.rstrip())

            hlst.reverse()
    
    result = []
    for e in hlst:
        (name, url) = e.split(': ', 2)
        result += [{'name': name, 'url': url}]

    return result;

def clearHistory():
    f = open(HISTORYPLAY_LST, 'wt')
    f.close()
    f = open(HISTORYCHANNELIST_LST, 'wt')
    f.close()

#@todo: Konfiguration erweitern, wo ein Remote-Pfad hinterlegt wird, mit welchem das Directory synchronisiert werden kann - ggf. über eine Tar-Datei nachdenken
def updateDirectory(url):
    req = urllib2.Request(url)
    try:
        xbmc.log('Open URL: %s' % (url), xbmc.LOGDEBUG)
        response = urllib2.urlopen(req, None, 30)
        content = response.read()
        xbmc.log("Response content:\n" + content, xbmc.LOGDEBUG)

    except HTTPError as e:
        msg = "The server response a HTTP-Error!\n"
        msg += "Error-Code: " + e.code
        dialog.notifcation(TITLE, msg, xbmcgui.NOTIFICATION_ERROR)
        xbmc.log("Error-Msg: %s" % (msg), xbmc.LOGDEBUG)
    except URLError as e:
        msg = "Failed reach the server!"
        msg += "Reason: " + e.reason
        dialog.notification(TITLE, msg, xbmcgui.NOTIFICATION_ERROR)
        xbmc.log("Error-Msg: %s" % (msg), xbmc.LOGDEBUG)
    else:
        msg = "Code: %s; OK - update successfully!" % response.getcode()
        dialog.notification(TITLE, msg, xbmcgui.NOTIFICATION_INFO)
        xbmc.log("Info-Msg: %s" % (msg), xbmc.LOGDEBUG)

    quit()


def useLocalFile():
    url = dialog.browse(1, TITLE, 'files', '', False, False, HOME)
    ext = getFileExt(url)

    if ext.lower() in ('.m3u', '.m3u8'):
        showM3U8List(url)
    else:
        basename = os.path.basename(url)
        if not len(basename):
            basename = 'Unknown'

        Player(basename, url, None)

def useRemoteFile():
    url = ''

    kbd = xbmc.Keyboard(url, 'Enter URL to play')
    kbd.doModal()
    if kbd.isConfirmed():
        url = kbd.getText().strip()

        if not re.match(r"(http|https|rmtp|plugin)", url):
            dialog.ok(TITLE, "Unsupported URL request!")
            quit()

        ext = getFileExt(url)

        if ext.lower() in ('.m3u', 'm3u8'):
            showM3U8List(url)
        else:
            Player('URL', url, None)

    else:
        quit()


#@todo: siehe .blueprint
def Player(name, url, icon=None):
    dialogP.create(TITLE, "Open URL: " + url, "Please wait ...")

    # Add to history
    addHistory(HISTORYPLAY_LST, url, name)
    #xbmc.executebuiltin("Container.Refresh")

    ext = getFileExt(url)
    (urlfile, ext) = os.path.splitext(url)

    if urlresolver.HostedMediaFile(url).valid_url(): 
        stream_url = urlresolver.HostedMediaFile(url).resolve()
        #li = xbmcgui.ListItem(path=stream_url)
        li = xbmcgui.ListItem(name)

        dialogP.close()

        xbmc.log('Play with support from urlresolver: %s - %s' % (name, url), xbmc.LOGDEBUG)
        #xbmcplugin.setResolveUrl(addon_handle, True, listitem=li)
        xbmc.Player().play(stream_url, li, False)

    elif liveresolver.isValid(url)==True: 
        stream_url = liveresolver.resolve(url)
        #li = xbmcgui.ListItem(path=stream_url)
        li = xbmcgui.ListItem(name)

        dialogP.close()

        xbmc.log('Play with support from liveresolver: %s - %s' % (name, url), xbmc.LOGDEBUG)
        #xbmcplugin.setResolveUrl(addon_handle, True, listitem=li)
        xbmc.Player().play(stream_url, li, False)
    
    elif ext.lower() in ('.ts', 'mpegts'):
        #Check for plugin f4m
        if re.match(r"plugin://plugin.video.f4mTester", url):
            if not os.path.exists(PLUGIN_F4M):
                dialog.ok('[COLOR red]F4M TESTER NOT INSTALLED![/COLOR]', "Please install F4M Tester first")
                quit()
        
        url_mod = url

        #check if http-request is a http-redirect (302), than resolve it an pass this further ...
        #url_redirect = getRedirectLocation(url_mod, maxredirect=1, timeout=30, dialog=dialogP)
        #url_mod = url_redirect['url']

        #if url_redirect['accept'] == False:
        #    dialogP.close()

        #    msg = "3. Redirection failed!"
        #    dialog.notification(TITLE, msg, xbmcgui.NOTIFICATION_ERROR)
        #    xbmc.log('4. Redirection failed: URL: %s, Statuscode: %s' % (url_mod, url_redirect['status']), xbmc.LOGERROR)
        #    quit()
            
        #xbmc.log('5. Use Redirect[Code:%s]: %s' % (url_redirect['status'], url_mod), xbmc.LOGDEBUG)

        #streamtype = 'HLSRETRY'
        streamtype = 'TSDOWNLOADER'
        
        proxyurl = 'plugin://plugin.video.f4mTester/?mode=play&streamtype='+streamtype+'&name=' + urllib2.quote(name) + '&url=' + urllib2.quote(url_mod)
        li = xbmcgui.ListItem(name)

        dialogP.close()

        xbmc.log('Play with f4m: %s - %s (mod: %s)' % (name, url, url_mod), xbmc.LOGDEBUG)
        xbmc.Player().play(proxyurl, li, False)

    else:
        li = xbmcgui.ListItem(name)
        dialogP.close()

        xbmc.log('Play normal: %s - %s' % (name, url), xbmc.LOGDEBUG)
        xbmc.Player().play(url, li, False)


#@todo: Request-Header, User-Agent hinzufügen
def getRedirectLocation(url, maxredirect=1, timeout=5, dialog=None):
    ret_url = url
    count = 0
    status = None
    accept = True
    
    xbmc.log('1. getRedirectLocation: init', xbmc.LOGDEBUG)

    if maxredirect > 0:
        accept = False
        while count < maxredirect:
            urlpart = urlparse.urlparse(ret_url)
            hostname = urlpart.hostname
            port = urlpart.port if urlpart.port != None else 80

            conn = httplib.HTTPConnection(hostname, port, timeout=timeout)
            # HEAD Anfrage führt bei manchen Servern, zu einem verfälschtem bzw. anderem Response-Code, verglichen mit GET -oder einer POST-Anfrage
            #conn.request("HEAD", urlpart.path + ( '?' if urlpart.query != '' else '' ) + urlpart.query + ( '#' if urlpart.fragment != '' else '' ) + urlpart.fragment)
            conn.request("GET", urlpart.path + ( '?' if urlpart.query != '' else '' ) + urlpart.query + ( '#' if urlpart.fragment != '' else '' ) + urlpart.fragment)
            res = conn.getresponse()
            conn.close()

            status = res.status
            redirect_location = res.getheader('location')

            xbmc.log('2. getRedirectLocation: %s, %s: %s' % (res.status, res.reason, redirect_location), xbmc.LOGDEBUG)

            if dialog != None:
                dialog.update(0, 'Redirect[%s]' % (count+1), redirect_location, ('%s' % status) + ' :' + res.reason)

            # Check for redirect
            if status in (300, 301, 302, 303, 307, 308):
                ret_url = redirect_location
                if (count+1) >= maxredirect:
                    accept = True

            elif status >= 200 and status < 300:
                accept = True
                break

            count += 1


    return {'url': ret_url, 'status': status, 'accept': accept}



def showMain():
    # prepare list

    # Redirect to UseLocalFile
    url = build_url({'mode': 'uselocalfile'})
    li = xbmcgui.ListItem("Use local file", iconImage='DefaultVideo.png')
    li.setArt({'fanart': ADDONFANART}) 
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    # Redirect to UseRemoteFile
    url = build_url({'mode': 'useremotefile'})
    li = xbmcgui.ListItem("Use remote file", iconImage='DefaultVideo.png')
    li.setArt({'fanart': ADDONFANART}) 
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    # Redirect to showDir
    url = build_url({'mode': 'folder'})
    li = xbmcgui.ListItem("Directory", iconImage='DefaultPlayList.png')
    li.setArt({'fanart': ADDONFANART}) 
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    # Redirect to showHistoryPlay
    url = build_url({'mode': 'historyplay'})
    li = xbmcgui.ListItem("History-Play", iconImage='DefaultRecentlyAddedMovies.png')
    li.setArt({'fanart': ADDONFANART}) 
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    # Redirect to showHistoryChannelList
    url = build_url({'mode': 'historychannellist'})
    li = xbmcgui.ListItem("History-Channellist", iconImage='DefaultRecentlyAddedMovies.png')
    li.setArt({'fanart': ADDONFANART}) 
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    # Redirect to clearHistory
    url = build_url({'mode': 'clearhistory'})
    li = xbmcgui.ListItem("Clear history", iconImage='DefaultVideo.png')
    li.setArt({'fanart': ADDONFANART}) 
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

    # Redirect to updateDirectory
    url = build_url({'mode': 'updatedirectory'})
    li = xbmcgui.ListItem("Update directory", iconImage='DefaultVideo.png')
    li.setArt({'fanart': ADDONFANART}) 
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

    xbmcplugin.setContent(addon_handle, 'files')
    xbmcplugin.endOfDirectory(addon_handle)



### MAIN ###
xbmc.log('addon_id: ' + addon_id, xbmc.LOGDEBUG)
xbmc.log('addon_name: ' + addon_name, xbmc.LOGDEBUG)
xbmc.log('addon_handle: ' + str(addon_handle), xbmc.LOGDEBUG)
xbmc.log("Call Magic Player: " + str(sys.argv), xbmc.LOGDEBUG)

mode = args.get('mode', None)

xbmc.log("Run mode: " + str(mode), xbmc.LOGDEBUG)

try:
    #IMPLEMENTIEREN!
    if mode is None:
        showMain()

    #TESTEN!
    elif mode[0] == 'uselocalfile':
        useLocalFile()

    elif mode[0] == 'useremotefile':
        useRemoteFile()

    elif mode[0] == 'folder':
        d = args.get('resdir', [getLocalResDir()])
        showDir(d[0])

    elif mode[0] == 'historyplay':
        showHistoryPlay()

    elif mode[0] == 'historychannellist':
        showHistoryChannelList()

    elif mode[0] == 'clearhistory':
        clearHistory()

    elif mode[0] == 'updatedirectory':
        url = addon.getSetting('updateDirectoryLink')
        updateDirectory(url)

    elif mode[0] == 'filelist':
        filelist = args.get('file', [None])
        showM3U8List(filelist[0])

    elif mode[0] == 'play':
        url = args.get('url', [None])
        name = args.get('name', ['Unknown'])

        if url:
            Player(name[0], url[0])


except IOError as e:
    dialog.ok(TITLE, "I/O error(X): %s" % e.args)
