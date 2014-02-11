# -*- coding: utf-8 -*-

'''
   XBMC ESO video add-on.
   Copyright (C) 2013 José Antonio Montes (jamontes)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
   
   This is the first trial of the ESO video add-on for XBMC.
   This add-on gets the videos from ESO web site and shows them properly ordered.
   You can choose the preferred subtitled language for the videos, if it is available.
   This plugin depends on the lutil library functions.
'''

import lutil

pluginhandle = int(sys.argv[1])
plugin_id = 'plugin.video.eso'

settings = lutil.get_plugin_settings(plugin_id)
lutil.set_debug_mode(settings.getSetting("debug"))
translation = settings.getLocalizedString
root_dir = settings.getAddonInfo('path')
lutil.set_fanart_file(root_dir)

# Gets the quality for videos from settings
try:
    quality = settings.getSetting("quality")
except:
    settings.openSettings()
    quality = settings.getSetting("quality")

root_url = 'http://www.eso.org'

# Entry point
def run():
    lutil.log("eso.run")
    
    # Get params
    params = lutil.get_plugin_parms()
    
    if params.get("action") is None:
        create_index(params)
    else:
        action = params.get("action")
        exec action+"(params)"
    

# Main menu
def create_index(params):
    lutil.log("eso.create_index "+repr(params))

    action = 'main_list'

    # All Videos entry
    url = 'http://www.eso.org/public/videos/list/1/'
    title = translation(30107)
    genre = 'All the Videos'
    lutil.log('eso.create_index action=["%s"] title=["All the Videos"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    buffer_web = lutil.carga_web(url)
    pattern_genre='<a href="(/public/videos/archive/category/[^"]+)">([^<]+)</a>'

    # Category list
    for genre_url, genre_title in lutil.find_multiple(buffer_web, pattern_genre):
        url = '%s%s' % (root_url, genre_url)
        title = genre_title.replace('&quot;', '"').replace('&#039;', '´').replace('&amp;', '&')  # Cleanup the title.
        lutil.log('eso.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
        lutil.addDir(action=action, title=title, url=url, genre=title)

    # Search
    action = 'search'
    url   = ''
    title = translation(30104)
    genre = 'Search'
    lutil.log('eso.create_index action=["%s"] title=["Search"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=False)


# Main list menu
def main_list(params):
    lutil.log("eso.main_list "+repr(params))

    # Loads the web page from ESO with the video list.
    page_url = params.get("url")
    reset_cache = params.get("reset_cache")
    genre = params.get("genre")

    buffer_web = lutil.carga_web(page_url)
    
    # Extract video items from the html content
    pattern_nextpage    = '<a href="[^"]*?">([^<]*?)</a></span><span class="paginator_next">&nbsp;<a href="([^"]*?)">'
    pattern_prevpage    = '<span class="paginator_previous"><a href="([^"]*?)">'
    pattern_pagenum     = '/([0-9]+)/'
    pattern_videos      = '<td class="imagerow[^>]+><a href="([^"]+)"><img src="([^"]+)" width="[^"]+" alt="([^"]+)" /></a></td>'

    lutil.set_content_list(pluginhandle, 'tvshows')
    lutil.set_plugin_category(pluginhandle, genre)

    # We must setup the previous page entry from the second page onwards.
    prev_page_url = lutil.find_first(buffer_web, pattern_prevpage)
    if prev_page_url:
        prev_page = lutil.find_first(prev_page_url, pattern_pagenum)
        lutil.log('eso.main_list Value of prev_page: %s prev_page_url: "%s%s"' % (prev_page, root_url, prev_page_url))
        prev_page_url = "%s%s" % (root_url, prev_page_url.replace('&amp;', '&').replace('&quot;', '"'))
        reset_cache = "yes"
        lutil.addDir(action="main_list", title="<< %s (%s)" % (translation(30106), prev_page), url=prev_page_url, reset_cache=reset_cache, genre=genre)

    # This is to force ".." option to go back to main index instead of previous page list.
    updateListing = reset_cache == "yes"

    for video_link, thumbnail_link, title in lutil.find_multiple(buffer_web, pattern_videos):
        video_info     = {}
        url            = '%s%s' % (root_url, video_link)
        thumbnail      = '%s%s' % (root_url, thumbnail_link)
        title          = title.strip().replace('&quot;', '"').replace('&#39;', '´').replace('&amp;', '&')  # Cleanup the title.
        video_info['Genre']   = genre
        video_info['Plot']    = title
        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, url=url, thumbnail=thumbnail, video_info=video_info)
 
    # Here we get the next page URL to add it at the end of the current video list page.
    for last_page, next_page_url in lutil.find_multiple(buffer_web, pattern_nextpage):
        next_page = lutil.find_first(next_page_url, pattern_pagenum)
        lutil.log('eso.main_list Value of next_page: %s last_page: %s next_page_url: "%s%s"' % (next_page, last_page, root_url, next_page_url))
        next_page_url = "%s%s" % (root_url, next_page_url.replace('&amp;', '&').replace('&quot;', '"'))
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (translation(30010), next_page, last_page), url=next_page_url, reset_cache=reset_cache, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


# This function performs a search through all the videos catalogue.
def search(params):
    search_string = lutil.get_keyboard_text(translation(30105))
    if search_string:
        params['url'] = 'http://www.eso.org/public/videos/?search=%s' % lutil.get_url_encoded(search_string)
        lutil.log("eso.search Value of search url: %s" % params['url'])
        return main_list(params)

    return lutil.close_dir(pluginhandle)


# This funtion search into the URL link to get the video link from the different sources.
def play_video(params):
    lutil.log("eso.play "+repr(params))

    buffer_link = lutil.carga_web(params.get("url"))
    pattern_video_failover = '<span class="archive_dl_text"><a href="([^"]*?)"'
    pattern_video = 'var %s = fix_protocol\("([^"]*?)"\)' % ('mobilefile', 'hdfile')[int(quality)]
    video_url = lutil.find_first(buffer_link, pattern_video)
    if video_url:
        try:
            lutil.log("eso.play: We have found this video: '%s' and let's going to play it!" % video_url)
            return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
        except:
            lutil.log('eso.play ERROR: we cannot reproduce this video URL: "%s"' % video_url)
            return lutil.showWarning(translation(30012))
    else:
        video_url = lutil.find_first(buffer_link, pattern_video_failover)
        if video_url:
            try:
                video_url = "%s%s" % (root_url, video_url)
                lutil.log("eso.play: We have found this video as failover option: '%s' and let's going to play it!" % video_url)
                return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
            except:
                lutil.log('eso.play ERROR: we cannot reproduce this video URL as failover: "%s"' % video_url)
                return lutil.showWarning(translation(30012))


    lutil.log('eso.play ERROR: we cannot play the video from this source yet: "%s"' % params.get("url"))
    return lutil.showWarning(translation(30011))

run()
