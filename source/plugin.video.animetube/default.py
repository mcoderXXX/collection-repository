#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import urllib,re,os,urlparse
import xbmcplugin,xbmcgui
import xbmcaddon,xbmc
import simple_requests as requests
import xbmcvfs

addon = xbmcaddon.Addon(id='plugin.video.animetube')
home = addon.getAddonInfo('path').decode('utf-8')
image = xbmc.translatePath(os.path.join(home, 'icon.png'))
datapath = xbmc.translatePath('special://profile/addon_data/plugin.video.animetube/')
favs = os.path.join(datapath,'favs.txt')

if not os.path.isdir(datapath):
    os.mkdir(datapath)

pluginhandle = int(sys.argv[1])

def kategorien():
    addDir('Neu','http://www.anime-tube.tv','neu','','')
    addDir('Serien','http://www.anime-tube.tv/animeliste-1-all.html','abc','','')
    addDir('Filme','http://www.anime-tube.tv/animeliste-2-all.html','liste','','')
    addDir('Ovas','http://www.anime-tube.tv/animeliste-3-all.html','liste','','')
    addDir('Specials','http://www.anime-tube.tv/animeliste-4-all.html','liste','','')
    addDir('AMV','http://www.anime-tube.tv/animeliste-5-all.html','liste','','')
    addDir('Suche','http://www.anime-tube.tv/suche.html','suche','','')
    addDir('Meine Anime','','meine','','')
    xbmcplugin.endOfDirectory(pluginhandle)

def meine():
    if os.path.exists(favs):
        fh = open(favs, 'r')
        content = fh.read()
        match = re.findall('{"name":"(.*?)","url":"(.*?)","cover":"(.*?)","plot":"(.*?)"}', content, re.DOTALL)
        for name,url,cover,plot in match:
            cm = []
            u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(name)+"&mode="+urllib.quote_plus('rem')+"&iconimage="+urllib.quote_plus(cover)+"&plot="+urllib.quote_plus(plot)
            cm.append( ('Von Meine Anime entfernen', "XBMC.RunPlugin(%s)" % u) )
            u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(name)+"&mode="+urllib.quote_plus('add_to_library')+"&type="+'meine'
            cm.append( ('Zur Bibliothek hinzufuegen', "XBMC.RunPlugin(%s)" % u) )
            addDir(name,url,'folgen',cover,plot,cm=cm)
        fh.close()
        xbmcplugin.endOfDirectory(pluginhandle)

def add():
    name = args['name'][0]
    url = args['url'][0]
    cover = args['iconimage'][0]
    plot = args['plot'][0]
    amventry = '{"name":"'+name+'","url":"'+url+'","cover":"'+cover+'","plot":"'+plot+'"}'
    if os.path.exists(favs):
        fh = open(favs, 'r')
        content = fh.read()
        fh.close()
        if content.find(amventry) == -1:
            fh = open(favs, 'a')
            fh.write(amventry+"\n")
            fh.close()
    else:
        fh = open(favs, 'a')
        fh.write(amventry+"\n")
        fh.close()
    xbmc.executebuiltin('Notification(Info: Anime hinzugefuegt!,)')

def rem():
    name = args['name'][0]
    url = args['url'][0]
    cover = args['iconimage'][0]
    plot = args['plot'][0]
    amventry = '{"name":"'+name+'","url":"'+url+'","cover":"'+cover+'","plot":"'+plot+'"}'
    fh = open(favs, 'r')
    content = fh.read()
    fh.close()
    entry = content[content.find(amventry):]
    fh = open(favs, 'w')
    fh.write(content.replace(amventry+"\n", ""))
    fh.close()
    xbmc.executebuiltin('Notification(Info: Anime entfernt!,)')

def neu():
    url = args['url'][0]
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
    content = requests.get(url, headers=headers).text
    match = re.findall('<a href=".(/video.+?)".*?<img src=".(/cover.+?)".*?<div class="alt">(.+?)<', content, re.DOTALL)
    for url,cover,name in match:
        url = 'http://www.anime-tube.tv' + url
        cover = 'http://www.anime-tube.tv' + cover
        addLink(name,url,'play',cover,'')
    xbmcplugin.endOfDirectory(pluginhandle)

def add_to_library():
    try:
        url = args['url'][0]
        type = args['type'][0]
        anime = args['name'][0].strip()
        add_to_library_2(url,anime,type)
        import time
        time.sleep(5)
        xbmc.executebuiltin('UpdateLibrary(video)')
    except:
        if os.path.exists(favs):
            fh = open(favs, 'r')
            content = fh.read()
            if content:
                match = re.findall('"name":"(.*?)","url":"(.*?)"', content, re.DOTALL)
                for name, url in match:
                    url = url
                    anime = name.strip()
                    type = 'meine'
                    add_to_library_2(url,anime,type)
                import time
                time.sleep(5)
                xbmc.executebuiltin('UpdateLibrary(video)')
            else:
              xbmc.executebuiltin('Notification(Info: Kein Anime zum aktualisieren vorhanden!,)')
        else:
            xbmc.executebuiltin('Notification(Info: Kein Anime zum aktualisieren vorhanden!,)')

def add_to_library_2(url,anime,type):
    if type == 'movie':
        ordner = addon.getSetting('filme_ordner')
    else:
        ordner = addon.getSetting('serien_ordner')
    if ordner:
        content = requests.get(url).text
        match = re.findall("(/anime-.*?-.*?.html)'>", content)
        for url in match:
            url = 'http://www.anime-tube.tv' + url
            content = requests.get(url).text
            match = re.findall('<div class="title"><a href=".(.*?)" title=".*?">(.*?)</a>', content)
            for url, name in match:
                url = 'http://www.anime-tube.tv' + url
                strmname = 's01.e' + name + '.strm'.strip()
                strmentry = 'plugin://plugin.video.animetube/?url=' + urllib.quote_plus(url) + '&mode=play' + '&name=' + urllib.quote_plus(name)
                strm = os.path.join(ordner, anime, strmname)
                strm = xbmc.makeLegalFilename(strm)
                if not xbmcvfs.exists(os.path.dirname(strm)):
                    try:
                        try: xbmcvfs.mkdirs(os.path.dirname(strm))
                        except: os.path.mkdir(os.path.dirname(strm))
                    except:
                        xbmc.executebuiltin('Notification(Info: Konnte keinen Ordner erstellen!,)')
                old_strmentry=''
                try:
                    f = xbmcvfs.File(strm, 'r')
                    old_strmentry = f.read()
                    f.close()
                except:  pass
                if strmentry != old_strmentry:
                    try:
                        file_desc = xbmcvfs.File(strm, 'w')
                        file_desc.write(strmentry)
                        file_desc.close()
                    except:
                        xbmc.executebuiltin('Notification(Info: Konnte keine Datei erstellen!,)')
    else:
        addon.openSettings()

def update():
    try:
        add_to_library()
    except:
        xbmc.executebuiltin('Notification(Info: Kein Anime Update moeglich!,)')

def abc():
    url = args['url'][0]
    content = requests.get(url).text
    match = re.findall('<a href=".(/animeliste.*?html)" class="cat-title">(.*?)</a>', content)
    for url,name in match:
        if 'all' in url:
            pass
        else:
            url = 'http://www.anime-tube.tv' + url
            addDir(name,url,'liste','','')
    xbmcplugin.endOfDirectory(pluginhandle)
               
def liste():
    url = args['url'][0]
    oldurl = url
    if 'animeliste-2' in url:
        type='movie'
    else:
        type='serie'
    content = requests.get(oldurl).text
    match = re.findall('/><div><center>.*?</center></div><br></div></div>', content)
    seiten = re.findall('<a href=".*?">(.*?)</a>', match[0])
    if seiten:
        seiten = seiten[-1]
    else:
        seiten = 1
    seite = 1
    seiten = int(seiten)
    while seite <= seiten:
        if not seite == 1:
            url = oldurl.replace('.html','') + '-' + str(seite) + '.html'
            content = requests.get(url).text
        seite += 1
        match = re.findall('preview".*?src="(.*?)".*?></a>.*?"title"><a href=".(/anime.*?html)" title="(.*?)">.*?Jahr</b>: (.*?)</span>.*?</div>.*?<div class="element">.*?<div class="meta_r" style=".*?">(.*?)</div>', content, re.DOTALL)
        for cover,url,name,year,plot in match:
            url = 'http://www.anime-tube.tv' + url
            content = requests.get(url).text
            try:
                plot = re.findall('<li><b>Beschreibung</b>: (.*?)</li>', content, re.DOTALL)[0]
            except:
                plot = 'Keine Beschreibung vorhanden'
            #plot = plot.replace("&hellip;","...")
            year = year.replace("<i>Unbekannt</i>","...")
            libname = name
            name = name + ' ' + '(' + year + ')'
            cm = []
            u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(libname)+"&mode="+urllib.quote_plus('add')+"&iconimage="+urllib.quote_plus(cover)+"&plot="+urllib.quote_plus(plot)
            cm.append( ('Zu Meine Anime hinzufuegen', "XBMC.RunPlugin(%s)" % u) )
            u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(libname)+"&mode="+urllib.quote_plus('add_to_library')+"&type="+str(type)
            cm.append( ('Zur Bibliothek hinzufuegen', "XBMC.RunPlugin(%s)" % u) )
            if oldurl == 'http://www.anime-tube.tv/animeliste-5-all.html':
                addLink(name,url,'play',cover,plot)
            else:
                 addDir(name,url,'folgen',cover,plot,cm=cm)
    xbmcplugin.endOfDirectory(pluginhandle)

def folgen():
    url = args['url'][0]
    content = requests.get(url).text
    match = re.findall("(/anime-.*?-.*?.html)'>", content)
    for url in match:
        url = 'http://www.anime-tube.tv' + url
        content = requests.get(url).text
        match = re.findall('<div class="title"><a href=".(.*?)" title=".*?">(.*?)</a>', content)
        for url,name in match:
            url = 'http://www.anime-tube.tv' + url
            addLink(name,url,'play','','')
    xbmcplugin.endOfDirectory(pluginhandle)

def play():
    u = args['url'][0]
    name = args['name'][0]
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
    content = requests.get(u).text
    match = re.findall('ani-stream.*?<iframe.*?src\s*=\s*(?:\'|")(.*?)(?:\'|")', content, re.DOTALL + re.IGNORECASE)
    if match:
        url = match[0]
        if not url.startswith('http'):
            if url.startswith('//'):
                url = 'http:%s' % url
            else:
                url = 'http://%s' % url
        if 'skystream' in url:
            headers.update({'Referer':u, 'Host':'player.skystream.tv'})
            content = requests.get(url, headers=headers).text.replace('\\','')
            match = re.findall('"redirect_url":"(.*?)"', content)
            if match:
                url = match[0]
        content = requests.get(url).text
        stream = re.findall("file\s*:\s*(?:'|\")(.+?)(?:\'|\")", content)
        if stream:
            try:
                r = requests.head(stream[0], headers=headers)
                if r.headers.get('location'):
                    stream = [r.headers.get('location')]
            except:
                pass
            stream = '%s|User-Agent=iPhone' % stream[0]
            listitem = xbmcgui.ListItem(path = stream)
            listitem.setInfo( type="video", infoLabels={ "title": name } )
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        else:
            xbmc.executebuiltin('Notification(Info: Kein Stream gefunden,)')

def suche():
    url = args['url'][0]
    kb = xbmc.Keyboard('', 'Suche Anime-Tube.TV', False)
    kb.doModal()
    search = kb.getText()
    data = {'suchtext': search, 'submit': 'Go'}
    content = requests.post(url, data=data).text
    match = re.findall('preview".*?src="(.*?)".*?></a>.*?"title"><a href=".(/anime.*?html)" title="(.*?)">.*?Jahr</b>: (.*?)</span>.*?</div>.*?<div class="element">.*?<div class="meta_r" style=".*?">(.*?)</div>', content, re.DOTALL)
    for cover,url,name,year,plot in match:
        url = 'http://www.anime-tube.tv' + url
        plot = plot.replace("&hellip;","...")
        year = year.replace("<i>Unbekannt</i>","...")
        addDir(name + ' ' + '(' + year + ')',url,'folgen',cover,plot)
    xbmcplugin.endOfDirectory(pluginhandle)

def addLink(name,url,mode,iconimage,plot):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+str(name)
    item=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    item.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot } )
    item.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(pluginhandle,url=u,listitem=item)

def addDir(name,url,mode,iconimage,plot,cm=False):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
    item=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    item.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot } )
    if cm:
        u2=sys.argv[0]+"?mode="+urllib.quote_plus('update')
        cm.append( ('Bibliothek aktualisieren', "XBMC.RunPlugin(%s)" % u2) )
        item.addContextMenuItems( cm )
    else:
        cm=[]
        u2=sys.argv[0]+"?mode="+urllib.quote_plus('update')
        cm.append( ('Bibliothek aktualisieren', "XBMC.RunPlugin(%s)" % u2) )
        item.addContextMenuItems( cm )
    xbmcplugin.addDirectoryItem(pluginhandle,url=u,listitem=item,isFolder=True)

args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)
print 'Arguments: '+str(args)

if mode==None:
    kategorien()
else:
    exec '%s()' % mode[0]