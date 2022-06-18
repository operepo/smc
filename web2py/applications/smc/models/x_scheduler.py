# -*- coding: utf-8 -*-

import os
import time
import subprocess
from gluon.contrib.simplejson import loads, dumps
import sys
import shutil
import requests
import webvtt
import traceback
import pytube, pytube.exceptions
import datetime

if 1 == 2:
    # Stop pylance highlighting everything
    cache = cache
    db = db
    db_scheduler = db_scheduler
    session = session
    DAL = DAL
    current = current
    request = request
    response = response
    Canvas = Canvas
    get_app_folders = get_app_folders
    load_media_file_json = load_media_file_json
    get_media_file_path = get_media_file_path
    load_document_file_json = load_document_file_json
    find_ffmpeg = find_ffmpeg
    w2py_folder = w2py_folder
    save_media_file_json = save_media_file_json
    save_document_file_json = save_document_file_json
    get_youtube_proxies = get_youtube_proxies
    is_media_captions_present = is_media_captions_present

### Monkeypatch YT Caption class to fix caption issue: https://github.com/pytube/pytube/issues/1085
## review after 7/1/22
def fix_xml_caption_to_srt(self, xml_captions: str) -> str:
    import xml.etree.ElementTree as ElementTree
    from html import unescape
    """Convert xml caption tracks to "SubRip Subtitle (srt)".

    :param str xml_captions:
        XML formatted caption tracks.
    """
    segments = []
    root = ElementTree.fromstring(xml_captions)[0]
    i=0
    for child in list(root):
        if child.tag == 'p':
            caption = child.text
            caption = unescape(caption.replace("\n", " ").replace("  ", " "),)
            try:
                duration = float(child.attrib["d"])/1000.0
            except KeyError:
                duration = 0.0
            start = float(child.attrib["t"])/1000.0
            end = start + duration
            sequence_number = i + 1  # convert from 0-indexed to 1.
            line = "{seq}\n{start} --> {end}\n{text}\n".format(
                seq=sequence_number,
                start=self.float_to_srt_time_format(start),
                end=self.float_to_srt_time_format(end),
                text=caption,
            )
            segments.append(line)
            i += 1
    return "\n".join(segments).strip()

pytube.Caption.xml_caption_to_srt = fix_xml_caption_to_srt



PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY33 = sys.version_info[0:2] >= (3, 3)
if PY2:
    reload(sys)
    sys.setdefaultencoding('utf8')
    import urllib2
    from urllib import urlencode
    from urllib2 import URLError
    from urllib2 import quote
    from urllib2 import unquote
    from urllib2 import urlopen
    from urllib2 import Request
    from urlparse import parse_qsl
    from urllib2 import HTTPError
    from HTMLParser import HTMLParser

    def install_proxy(proxy_handler):
        """
        install global proxy.
        :param proxy_handler:
            :samp:`{"http":"http://my.proxy.com:1234", "https":"https://my.proxy.com:1234"}`
        :return:
        """
        proxy_support = urllib2.ProxyHandler(proxy_handler)
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)

    def unescape(s):
        """Strip HTML entries from a string."""
        html_parser = HTMLParser()
        return html_parser.unescape(s)

    def unicode(s):
        """Encode a string to utf-8."""
        return s.encode('utf-8')

elif PY3:
    from urllib.error import URLError
    from urllib.parse import parse_qsl
    from urllib.parse import quote
    from urllib.parse import unquote
    from urllib.parse import urlencode
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from urllib.request import Request
    from urllib.request import urlretrieve
    # NOTE - Leave off!! - will override web2py request object
    #from urllib import request

    def install_proxy(proxy_handler):
        proxy_support = urllib.request.ProxyHandler(proxy_handler)
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)

    def unicode(s):
        """No-op."""
        return s

    if PY33:
        from html.parser import HTMLParser

        def unescape(s):
            """Strip HTML entries from a string."""
            html_parser = HTMLParser()
            return html_parser.unescape(s)
    else:
        from html import unescape


# For finding number of CPUs
import multiprocessing

from pytube import YouTube
#from applications.smc.modules.pytube import YouTube

from ednet.ad import AD
from ednet import Faculty
from ednet import Student


# Task Scheduler Code
def update_media_database_from_json_files():
    # Go through the media files and find json files that aren't
    # already in the database.
    # This is useful for when we copy movie files back and forth between systems
    # Starts in the Models folder

    (w2py_folder, applications_folder, app_folder) = get_app_folders()
    target_folder = os.path.join(app_folder, "static/media")
    
    # Walk the folders/files
    print("looking in: " + target_folder)
    for root, dirs, files in os.walk(target_folder):
        for f in files:
            # Don't process flashcard data files
            if f.endswith("json") and f != "data.json":
                # f_path = os.path.join(root, f)
                # update_media_meta_data(f_path)
                file_guid, ext = os.path.splitext(f)
                load_media_file_json(file_guid)
    
    # Make sure to do this and unlock the db
    db.commit()

    return True

def update_document_database_from_json_files():
    # Go through the document files and find json files that aren't
    # already in the database.
    # This is useful for when we copy document files back and forth between systems
    # Starts in the Models folder

    (w2py_folder, applications_folder, app_folder) = get_app_folders()
    target_folder = os.path.join(app_folder, "static/documents")
    
    # Walk the folders/files
    print("looking in: " + target_folder)
    for root, dirs, files in os.walk(target_folder):
        for f in files:
            # Don't process flashcard data files
            if f.endswith("json") and f != "data.json":
                file_guid, ext = os.path.splitext(f)
                load_document_file_json(file_guid)
    
    # Make sure to do this and unlock the db
    db.commit()
    return True


def process_media_file(media_id):
    ret = ""

    # Find ffmpeg binary
    (ffmpeg, acodec) = find_ffmpeg()

    # Find number of CPUs
    cpus = int(multiprocessing.cpu_count())
    # Drop the number of threads so we don't use up all CPU power
    cpus -= 3 # W 4 cpus, use only one, always leave 3 for processing if available.
    if cpus < 1:
        cpus = 1
    
    # Grab the media file
    # media_file = None
    media_file = db(db.media_file_import_queue.id==media_id).select().first()
    if media_file is None:
        return dict(error="Invalid Media File")
    else:
        print("Processing media file: " + str(media_id) + " [" + str(time.time()) + "]")

    media_guid = media_file.media_guid

    db(db.media_file_import_queue.id == media_id).update(status='processing')
    # Make sure to do this and unlock the db
    db.commit()
    
    # Get the uploads path
    # (something like /var/www/clients/client1/web1/web/applications/smc/uploads/media_files.media_file/b6)
    tmp_path = db.media_file_import_queue.media_file.retrieve_file_properties(db.media_file_import_queue(media_file.id).media_file)['path']
    # NOTE Has stupid databases/../uploads in the path, replace databases/../ with nothing
    tmp_path = tmp_path.replace("\\", "/").replace('databases/../', '')
    # print("TmpPath: " + tmp_path)
    
    uploads_folder = os.path.join(w2py_folder, tmp_path)
    # print("Upload Path: " + uploads_folder)
    input_file = os.path.join(uploads_folder, media_file.media_file).replace("\\", "/")

    # Get the output file paths
    output_webm = get_media_file_path(media_guid, ".webm")  # target_file + ".webm"
    output_ogv = get_media_file_path(media_guid, ".ogv")  # target_file + ".ogv"
    output_mp4 = get_media_file_path(media_guid, ".mp4")  # target_file + ".mp4"
    output_mobile_mp4 = get_media_file_path(media_guid, ".mobile.mp4")  # target_file + ".mobile.mp4"
    output_meta = get_media_file_path(media_guid, ".json")  # target_file + ".json"
    output_poster = get_media_file_path(media_guid, ".poster.png")  # target_file + ".poster.png"
    output_thumb = get_media_file_path(media_guid, ".thumb.png")  # target_file + ".thumb.png"
    
    print("Output files: ")
    # print(output_webm)
    # print(output_ogv)
    print(output_mp4)
    
    webm_ret = ""
    ogv_ret = ""
    mp4_ret = ""
    poster_ret = ""
    thumb_ret = ""
    
    # Run ffmpeg to process file
    
    # Do webm - NOTE No webm support in ffmpeg right now - # TODO unknown encoder libvpx
    # cmd = ffmpeg + " -i '" + input_file + "' -vcodec libvpx -qscale 6 -acodec libvorbis
    # -ab 128k -vf scale='480:-1' '" + output_webm + "'"
    # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    # webm_ret = p.communicate()[0].decode()
    
    # Do OGV
    # cmd = ffmpeg + " -y -i '" + input_file + "' -vcodec libtheora -qscale 6
    # -acodec libvorbis -ab 192k -vf scale='640:-1' '" + output_ogv + "'"
    # cmd = ffmpeg + " -y -i '" + input_file + "' -vcodec libtheora -qscale:v 5
    # -acodec libvorbis -ab 128k '" + output_ogv + "'"
    # print("Creating OGV..."  + " [" + str(time.time()) + "]")
    print("!clear!10%")
    # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    # ogv_ret = p.communicate()[0].decode()

    # Do MP4
    # cmd = ffmpeg + " -y -i '" + input_file + "' -vcodec libx264 -preset slow -profile main
    # -crf 20 -acodec libfaac -ab 192k -vf scale='720:-1' '" + output_mp4 + "'"
    cmd = ffmpeg + " -y -i \"" + input_file + \
          "\" -vcodec libx264 -preset slow -movflags faststart -profile:v main -crf 20 -acodec " + \
          acodec + " -ab 128k -threads " + str(cpus) + " \"" + output_mp4 + "\""
    # print("Creating MP4..."  + " [" + str(time.time()) + "]")
    print("MP4: " + cmd)
    print("!clear!30%")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    mp4_ret = p.communicate()[0].decode()
    
    # Do MP4 with mobile quality
    cmd = ffmpeg + " -y -i \"" + input_file + \
          "\" -vcodec libx264 -preset slow -movflags faststart -profile main -crf 20 -acodec " +\
          acodec + " -ab 128k -vf scale='2*trunc(oh*a/2):480' -threads " + str(cpus) + " \"" +\
          output_mobile_mp4 + "\""
    # print("Creating mobile MP4..."  + " [" + str(time.time()) + "]")
    print("!clear!70%")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    mp4_ret += p.communicate()[0].decode()

    # Generate poster image
    cmd = ffmpeg + " -y -ss 5 -i \"" + input_file + "\" -vf  \"thumbnail,scale=640:-1\" -frames:v 1 \"" + output_poster + "\""
    # print("Creating poster image..." + " [" + str(time.time()) + "]")
    print("!clear!85%")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    poster_ret = p.communicate()[0].decode()
    
    # Generate thumbnail image
    cmd = ffmpeg + " -y -ss 5 -i \"" + input_file + "\" -vf  \"thumbnail,scale=128:-1\" -frames:v 1 \"" + output_thumb + "\""
    # print("Creating thumbnail image..."  + " [" + str(time.time()) + "]")
    print("!clear!95%")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    thumb_ret = p.communicate()[0].decode()

    # -vf scale="480:2*trunc(ow*a/2)"
    # ffmpeg -i [your video] [encoding options as specified above]
    # [your output video with appropriate extension - eg output.mp4, output.ogv or output.webm]
    
    # Make webm file - 480p
    # cmd = ffmpeg + " -i 'input_file.avi' -codec:v libvpx -quality good -cpu-used
    # 0 -movflags faststart -b:v 600k -maxrate 600k -bufsize 1200k -qmin 10 -qmax 42 -vf
    # scale=-1:480 -threads 4 -codec:a vorbis -b:a 128k output_file.webm"
    # -vcodec libvpx -qscale 6 -acodec libvorbis -ab 128k

    # Make ogv file
    # cmd = ""
    # -vcodec libtheora -qscale 6 -acodec libvorbis -ab 128k
    
    # Make mp4 file - 480p
    # cmd = ffmpeg + " -i inputfile.avi -codec:v libx264 -profile:v main -preset slow
    # -movflags faststart -b:v 400k -maxrate 400k -bufsize 800k -vf scale=-1:480 -threads 0
    # -codec:a libfdk_aac -b:a 128k output.mp4"  #codec:a libfdk_aac  codec:a mp3
    # -vcodec libx264 -preset slow -profile main -crf 20 -acodec libfaac -ab 128k
    
    # Update file info
    
    db.media_files.insert(title=media_file.title,
                          media_guid=media_file.media_guid.replace('-', ''),
                          description=media_file.description,
                          original_file_name=media_file.original_file_name,
                          media_type=media_file.media_type,
                          category=media_file.category,
                          tags=media_file.tags,
                          width=media_file.width,
                          height=media_file.height,
                          quality=media_file.quality,
                          youtube_url=media_file.youtube_url
                          )
    
    # media_file.update(status='done')
    db(db.media_file_import_queue.id==media_id).delete()
    
    # Dump meta data to the folder along side the video files
    # This can be used for export/import
    # meta = {'title': media_file.title, 'media_guid': media_file.media_guid.replace('-', ''),
    #         'description': media_file.description, 'original_file_name': media_file.original_file_name,
    #         'media_type': media_file.media_type, 'category': media_file.category,
    #         'tags': dumps(media_file.tags), 'width': media_file.width,
    #         'height': media_file.height, 'quality': media_file.quality}
    #
    # meta_json = dumps(meta)
    # f = os_open(output_meta, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
    # os.write(f, meta_json)
    # os.close(f)
    save_media_file_json(media_guid)
    
    print("!clear!100%")

    # Have to call commit in tasks if changes made to the db
    db.commit()
    
    return dict(mp4_ret=mp4_ret, ogv_ret=ogv_ret, webm_ret=webm_ret, poster_ret=poster_ret, thumb_ret=thumb_ret)


def log_to_video(yt_url, msg):
    # Add to the download_log on the selected video
    media_item = db(db.media_files.youtube_url==yt_url).select().first()
    if media_item:
        log = media_item.download_log
        if log is None:
            log = ""
        if len(log) > 0:
            log += "\n"
        log += f"{msg}"
        media_item.download_log = log
        media_item.update_record()
        db.commit()
    return True

def find_best_yt_stream(yt_url):
    yt = None
    res = '480p'
    stream = None
    return_code = "OK"

    if yt_url is None:
        print("ERROR: yt_url was none?")
        yt_url = ""

    # print("Looking for YT: " + yt_url)

    if session.yt_urls_error_msg is None:
        session.yt_urls_error_msg = ""

    # Change out embed for watch so the link works properly
    yt_url_tmp = yt_url.replace("/embed/", "/watch?v=")
    proxies = get_youtube_proxies()
    # Proxies comes in as a list, add None on the list so we try a None proxy too
    #proxies.insert(0, None)
    proxies.append(None)

    for proxy in proxies[0:5]:  # Only try the first 5 proxies - don't try forever
        # Try each proxy in order trying to get this video.
        proxy_item = db(db.youtube_proxy_list.proxy_url==proxy).select().first()
        if proxy_item:
            proxy_item.last_request_on = datetime.datetime.utcnow()
            proxy_item.update_record()
            db.commit()
        try:
            msg = f"Trying to get {yt_url} from proxy {proxy}"
            print(msg)
            log_to_video(yt_url, msg)
            p = None
            if not proxy is None:
                # Youtube proxy wants it in p['https']='https://123.123.321.321:35000' form
                p = {
                    'https': proxy,
                    'http': proxy,
                }

            # Try w the current proxy
            yt = YouTube(yt_url_tmp, proxies=p)

            s = None
    
            s = yt.streams.filter(file_extension='mp4', progressive=True, res=res).first()
            if s is None:
                # Try 360p
                res = '360p'
                s = yt.streams.filter(file_extension='mp4', progressive=True, res=res).first()
            if s is None:
                # Try 720p
                res = '720p'
                s = yt.streams.filter(file_extension='mp4', progressive=True, res=res).first()
            if s is None:
                # If that doesn't exist, then get the first one in the list
                s = yt.streams.filter(file_extension='mp4', progressive=True).first()
            # s.download()  # put in folder name
    
            stream = s

            # Got one - break the loop and return it.
            return_code = "OK"
            return yt, stream, res, return_code
        ## These exceptions mean we can't get it - don't keep trying other proxies
        except (
            pytube.exceptions.AgeRestrictedError,
            pytube.exceptions.LiveStreamError,
            pytube.exceptions.MembersOnly,
            pytube.exceptions.RecordingUnavailable,
            pytube.exceptions.VideoPrivate,
            pytube.exceptions.VideoRegionBlocked,
            pytube.exceptions.VideoUnavailable,
            pytube.exceptions.MaxRetriesExceeded,
        ) as ex:
            if proxy_item:
                proxy_item.last_error_on = datetime.datetime.utcnow()
                proxy_item.update_record()
                db.commit()
            msg = f"Error grabbing YT video - Video not availalble or blocked - check to see if the url is correct, that it isn't private, that it is available in your region, etc... {yt_url} -- {ex}"
            session.yt_urls_error_msg += msg
            print(msg)
            log_to_video(yt_url, msg)
            return_code = "Permanent Error"

            return yt, stream, res, return_code
            #raise Exception(msg)


        ## These exceptions mean there as a parsing/temp error - don't keep trying other proxies
        except (
            pytube.exceptions.ExtractError,
            pytube.exceptions.HTMLParseError,
            pytube.exceptions.RegexMatchError,
        ) as ex:
            if proxy_item:
                proxy_item.last_error_on = datetime.datetime.utcnow()
                proxy_item.update_record()
                db.commit()
            msg = f"Error grabbing YT video - PyTube error - Youtube might have changed something, update PyTube and try again: {yt_url} -- {ex}"
            session.yt_urls_error_msg += msg
            print(msg)
            log_to_video(yt_url, msg)
            return_code = "Permanent Error"
            return yt, stream, res, return_code
        
        
        # Other exceptions inherit from this - just catch a general exception
        #except pytube.exceptions.PytubeError as ex:
        #    pass        
                
        except HTTPError as ex:
            if ex.code == 429:  # Do we need this w max retries?
                # Youtube not happy with this IP/Proxy
                # if "Retry-After" in ex.headers:
                #     sleep_time = int(ex.headers["Retry-After"])
                if proxy_item:
                    proxy_item.last_error_on = proxy_item.last_429_error_on = datetime.datetime.utcnow()
                    proxy_item.update_record()
                    db.commit()
                msg = f"429 error on this proxy: {proxy}"
                log_to_video(yt_url, msg)
                
                # Try next proxy in list - don't return yet
        
        except Exception as ex:
            # Unknown exception?
            msg = f"Error grabbing YT video - Bad YT URL? {yt_url} -- {ex}"
            session.yt_urls_error_msg += msg
            print(msg)
            log_to_video(yt_url, msg)

            # For unknown errors - call it - quit trying.
            return_code = "Permanent Error"
            return yt, stream, res, return_code
    
    # If getting here, we didn't find a good one!
    return_code = "Temporary Error"
    return yt, stream, res, return_code

def pull_youtube_caption(yt_url, media_guid):
    # Download the specified caption file.

    if is_media_captions_present(media_guid):
        msg = "VTT file present."
        print(msg)
        log_to_video(yt_url, msg)
        time.sleep(5)
        return True
    
    # Pull the db info
    media_file = db(db.media_files.media_guid==media_guid).select().first()
    if media_file is None:
        print("ERROR - Unable to find a db record for " + str(media_guid))
        # Slight pause - let scheduler grab output
        return False

    (w2py_folder, applications_folder, app_folder) = get_app_folders()

    # Mark this as the currently downloading item.
    media_file.current_download=True
    media_file.update_record()
    db.commit()

    target_file = get_media_file_path(media_guid, "srt")
    from pytube import YouTube
    try:
        #yt = YouTube(yt_url.replace("/embed/", "/watch?v="), proxies=get_youtube_proxies())
        yt, stream, res = find_best_yt_stream(yt_url)
    except Exception as ex:
        msg = "YT Captions - Bad YT URL? " + yt_url + " -- " + str(ex)
        log_to_video(yt_url, msg)
        print(msg)
        return False

    for cap in yt.captions:
        lang = cap.code
        output_caption_file = target_file.replace(".srt", "_" + lang + ".srt")
        log_to_video(yt_url, f"Trying to save {lang} to {output_caption_file}")

        try:
            msg = f"Saving {lang} to {output_caption_file}"
            print(msg)
            log_to_video(yt_url, msg)
            #caption_url = cap.url
            #r = requests.get(caption_url)
            caption_srt = cap.generate_srt_captions()
            if len(caption_srt) > 1:
                # Save SRT file
                f = open(output_caption_file, "wb")
                f.write(caption_srt.encode('utf-8'))
                f.close()

                # Convert to webvtt format
                vtt = webvtt.from_srt(output_caption_file)
                output_caption_file = output_caption_file.replace("srt", "vtt")
                vtt.save(output_caption_file)
                msg = f"Converted to VTT - Saved {lang} to {output_caption_file}"
                print(msg)
                log_to_video(yt_url, msg)
            else:
                msg = f"Error - generate_srt_captions returned nothing - {lang}"
                print(msg)
                log_to_video(yt_url, msg)
            
        except Exception as ex:
            msg = f"Error - unable to grab caption for lang: {yt_url} / {lang}\n{ex}\n{traceback.format_exc()}"
            print(msg)
            log_to_video(yt_url, msg)
            continue

    # Mark this as the currently downloading item.
    media_file = db(db.media_files.media_guid==media_guid).select().first()
    media_file.current_download=False
    media_file.needs_caption_downloading=False
    media_file.update_record()
    db.commit()
    # Slight pause - let scheduler grab output
    time.sleep(5)
    return True
    

def pull_youtube_video(yt_url, media_guid):
    # Download the specified movie.
    had_errors = False

    # Pull the db info
    media_file = db(db.media_files.media_guid==media_guid).select().first()
    if media_file is None:
        print("ERROR - Unable to find a db record for " + str(media_guid))
        # Slight pause - let scheduler grab output
        time.sleep(5)
        return False

    # Mark this as the currently downloading item.
    media_file.current_download=True
    media_file.update_record()
    db.commit()
    
    (w2py_folder, applications_folder, app_folder) = get_app_folders()
    (ffmpeg, acodec) = find_ffmpeg()

    # Figure out output file name (use media guid)
    # static/media/01/010102alj29vsor3.webm
    file_guid = media_file.media_guid.replace('-', '')
    # print("File GUID: " + str(file_guid))
    target_folder = os.path.join(app_folder, 'static', 'media')

    file_prefix = file_guid[0:2]

    target_folder = os.path.join(target_folder, file_prefix)
    # print("Target Dir: " + target_folder)

    try:
        os.makedirs(target_folder)
    except OSError as message:
        pass

    target_file = os.path.join(target_folder, file_guid).replace("\\", "/")

    output_mp4 = target_file + ".mp4"
    output_mp4_filename = file_guid + ".mp4"  # Note - NOT -it quits adding it? - don't add mp4 as yt will do that
    output_meta = target_file + ".json"
    output_poster = target_file + ".poster.png"
    output_thumb = target_file + ".thumb.png"
    output_en_caption = target_file + "_en.xml"

    from pytube import YouTube
    try:
        yt, stream, res, return_code = find_best_yt_stream(yt_url)
        if return_code != "OK":
            print(f"Unable to get video {yt_url}.")
            log_to_video(yt_url, f"Failed to download video from {yt_url}, will stop trying.")
            media_file = db(db.media_files.media_guid==media_guid).select().first()
            media_file.needs_downloading = False
            media_file.needs_caption_downloading = False
            media_file.update_record()
            db.commit()
            time.sleep(5)
            return True
    except Exception as ex:
        print("Unknown HTTP error pulling yt video? " + str(ex))
        return False

    try:
        msg = f"Downloading {yt_url}\n\n"
        print(msg)
        log_to_video(yt_url, msg)
        
        stream.download(output_path=target_folder, filename=output_mp4_filename, max_retries=3, timeout=300)  # put in folder name

        msg = f"Downlaod Complete!"
        print(msg)
        log_to_video(yt_url, msg)
    
    except Exception as ex:
        print("Error Downloading YouTube Video!  Are you online? " + str(ex))
        # Slight pause - let scheduler grab output
        time.sleep(5)
        return False

    # print("TN File: " + output_thumb)
    make_own_thumbnail = False
    thumbnail_url = ""
    try:
        thumbnail_url = yt.thumbnail_url
    except:
        make_own_thumbnail = True

    # Download the thumbnail file if its set
    if thumbnail_url != "":
        try:
            tn = urlopen(thumbnail_url)
            with open(output_thumb, 'wb') as f:
                f.write(tn.read())
            # Copy the thumbnail to the poster
            shutil.copy(output_thumb, output_poster)
        except Exception as ex:
            print("Error trying to save thumbnail file: " + str(thumbnail_url) + " - " + str(ex))
            make_own_thumbnail = True

    if make_own_thumbnail is True:
        # Unable to pull thumbnail - make our own.
        if ffmpeg is None:
            print("FFMPEG NOT FOUND! Can't make thumbnail.")
            # note - let things keep going so at least we have the video
        else:
            # Process the video
            # Generate thumbnail image
            input_file = output_mp4
            print("Input File: " + input_file)
            cmd = ffmpeg + " -y -ss 5 -i \"" + input_file + "\" -vf  \"thumbnail,scale=128:-1\" -frames:v 1 \"" + \
                output_thumb + "\""
            # print("Creating thumbnail image..."  + " [" + str(time.time()) + "]")
            print("Generating Thumbnail...")
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                thumb_ret = p.communicate()[0].decode()
            except Exception as ex:
                print("Error generating thumbnail: " + str(output_thumb) + " - " + str(ex))

            # Generate poster image
            cmd = ffmpeg + " -y -ss 5 -i \"" + input_file + "\" -vf  \"thumbnail,scale=640:-1\" -frames:v 1 \"" + \
                output_poster + "\""
            # print("Creating poster image..." + " [" + str(time.time()) + "]")
            print("Generating Poster Image...")
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                poster_ret = p.communicate()[0].decode()
            except Exception as ex:
                print("Error generating poster: " + str(output_poster) + " - " + str(ex))

    # Update media file to show it has been downloaded
    title = yt.title
    description = yt.description

    media_file.update_record(needs_downloading=False, title=title, description=description)
    db.commit()
    # pull w updated info
    media_file = db(db.media_files.media_guid == media_guid).select().first()

    # Save JSON info
    meta = {'title': media_file.title, 'media_guid': media_file.media_guid.replace('-', ''),
            'description': media_file.description, 'original_file_name': media_file.original_file_name,
            'media_type': media_file.media_type, 'category': media_file.category,
            'tags': dumps(media_file.tags), 'width': media_file.width,
            'height': media_file.height, 'quality': media_file.quality, 'youtube_url': media_file.youtube_url}

    meta_json = dumps(meta)
    #f = os_open(output_meta, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
    #os.write(f, meta_json)
    #os.close(f)
    f = open(output_meta, "w")
    f.write(meta_json)
    f.close()

    # Mark that this is done downloading.
    media_file = db(db.media_files.media_guid==media_guid).select().first()
    media_file.current_download=False
    if had_errors == False:
        media_file.needs_downloading = False
    media_file.update_record()
    # Have to call commit in tasks if changes made to the db
    db.commit()

    # Scheduler delays now, don't need this.
    # Throw a little delay in here to help keep from getting blocked by youtube
    #time.sleep(15)
    return True


def remove_old_wamap_video_files():
    # Loop through the old table and remove the video files
    rows = db(db.wamap_questionset).select()
    db.commit()
    
    # Make sure we are in the correct current directory
    # Starts in the Models folder
    w2py_folder = os.path.abspath(__file__)
    # print("Running File: " + app_folder)
    w2py_folder = os.path.dirname(w2py_folder)
    # app folder
    w2py_folder = os.path.dirname(w2py_folder)
    app_folder = w2py_folder
    # Applications folder
    w2py_folder = os.path.dirname(w2py_folder)
    # Root folder
    w2py_folder = os.path.dirname(w2py_folder)
    # print("W2Py Folder: " + w2py_folder)
    
    # Ensure the wamap folder exists
    wamap_folder = os.path.join(app_folder, "static")
    wamap_folder = os.path.join(wamap_folder, "media")
    wamap_folder = os.path.join(wamap_folder, "wamap")
    
    if os.path.isdir(wamap_folder) is not True:
        os.mkdir(wamap_folder)
    
    removed = []
    not_removed = []
    for row in rows:
        # Remove the file if it exists
        fpath = os.path.join(wamap_folder, "wamap_" + str(row.wamap_id) + ".mp4")
        if os.path.exists(fpath) is True:
            try:
                print("removing " + fpath  + " [" + str(time.time()) + "]")
                os.remove(fpath)
                removed.append(fpath)
            except:
                print("error removing " + fpath  + " [" + str(time.time()) + "]")
                not_removed.append(fpath)
        else:
            print("skipping " + fpath  + " [" + str(time.time()) + "]")
            not_removed.append(fpath)
    print("Done." + str(time.time()))
    
    # Have to call commit in tasks if changes made to the db
    db.commit()
    # return dict(removed=removed, not_removed=not_removed)
    # Slight pause - let scheduler grab output
    time.sleep(5)
    return True


def process_wamap_video_links():
    # Make sure we are in the correct current directory
    # Starts in the Models folder
    w2py_folder = os.path.abspath(__file__)
    # print("Running File: " + app_folder)
    w2py_folder = os.path.dirname(w2py_folder)
    # app folder
    w2py_folder = os.path.dirname(w2py_folder)
    app_folder = w2py_folder
    # Applications folder
    w2py_folder = os.path.dirname(w2py_folder)
    # Root folder
    w2py_folder = os.path.dirname(w2py_folder)
    print("W2Py Folder: " + w2py_folder)
    
    # Ensure the wamap folder exists
    wamap_folder = os.path.join(app_folder, "static")
    wamap_folder = os.path.join(wamap_folder, "media")
    wamap_folder = os.path.join(wamap_folder, "wamap")
    
    if os.path.isdir(wamap_folder) is not True:
        os.mkdir(wamap_folder)
    
    process_count = 50
    last_row = 0
    
    while process_count > 0:
        process_count -= 1

        had_errors = False
        item = db(db.wamap_videos.downloaded==False).select().first()
        db.commit()
        ret = ""
        if item is None:
            ret += "Out of wamap items to process"
            print("Done processing videos.")
            return dict(ret=ret)
        
        print("-----------------------\n")
        print("Processing " + str(item.source_url) + "\n")
        last_row = item.id
        
        yt_url = item.source_url
        if ('youtube.com' in yt_url or 'youtu.be' in yt_url) and "admin.correctionsed.com" not in yt_url:
            # check if the file already exists
            vidfile = os.path.join(wamap_folder, "wamap_" + str(item.media_guid))
            # print("Checking vid file: " + vidfile + ".mp4")
            if os.path.exists(vidfile + ".mp4") is not True:
                # print("Downloading video: " + str(yt_url))
                # download the video
                try:
                    os.chdir(wamap_folder)
                    # Store the original link in a link file
                    meta = {'media_guid':item.media_guid, 'yt_url':yt_url}
                    meta_json = dumps(meta)
                    #f = os_open("wamap_" + str(item.media_guid) + ".link", os.O_TRUNC|os.O_WRONLY|os.O_CREAT)
                    #os.write(f, meta_json)
                    #os.close(f)
                    f = open("wamap_" + str(item.media_guid) + ".link", "w")
                    f.write(meta_json)
                    f.close()

                    # Download the video from the internet
                    yt = YouTube(proxies=get_youtube_proxies())
                    yt_url = yt_url.replace("!!1", "").replace("!!0", "")  # because some urls end up with the
                    # field separator still in it
                    if "/embed/" in yt_url:
                        # Embedded link doesn't return correctly, change it back
                        # to normal link
                        yt_url = yt_url.replace("/embed/", "/watch?v=")
                    yt.url = yt_url
                    yt.filename = "wamap_" + str(item.media_guid)
                    f = yt.filter('mp4')[-1]
                    f.download()                    
                except Exception as e:
                    print(" ****** Error fetching movie ****** " + str(e))
                    had_errors = True
                os.chdir(w2py_folder)
            else:
                pass
                # print("Video already downloaded " + str(vidfile))
            
            # update wamap db??
            if had_errors is not True:
                if os.path.exists(vidfile + ".mp4") is True:
                    new_url = "https://admin.correctionsed.com/media/wmplay/" + str(item.media_guid)
                    # print(" Updating (" + str(yt_url) + ") to point to (" + new_url + ")")
                    db(db.wamap_videos.id==item.id).update(new_url=new_url)
                    db.commit()
                    
                    db_wamap = DAL('mysql://smc:aaaaaaa!!@wamap.correctionsed.com/imathsdb')
                    
                    # Update all locations...
                    # DEBUG TODO -
                    # imas_inlinetext (text column)
                    sql = "UPDATE imas_inlinetext SET `text`=REPLACE(`text`, '" + yt_url + "', '" + new_url + "') WHERE `text` like '%" + yt_url + "%'"
                    # print(sql)
                    db_wamap.executesql(sql)
                    
                    # imas_assessments (intro colum  youtube embed link?)
                    sql = "UPDATE imas_assessments SET `intro`=REPLACE(`intro`, '" + yt_url + "', '" + new_url + "') WHERE `intro` like '%" + yt_url + "%'"
                    # print(sql)
                    db_wamap.executesql(sql)
                    
                    # imas_linkedtext (summary column)
                    sql = "UPDATE imas_linkedtext SET `summary`=REPLACE(`summary`, '" + yt_url + "', '" + new_url + "') WHERE `summary` like '%" + yt_url + "%'"
                    # print(sql)
                    db_wamap.executesql(sql)
                    
                    # imas_linkedtext (text column)
                    sql = "UPDATE imas_linkedtext SET `text`=REPLACE(`text`, '" + yt_url + "', '" + new_url + "') WHERE `text` like '%" + yt_url + "%'"
                    # print(sql)
                    db_wamap.executesql(sql)
                    
                    # imas_questionset (control)
                    sql = "UPDATE imas_questionset SET `control`=REPLACE(`control`, '" + yt_url + "', '" + new_url + "') WHERE `control` like '%" + yt_url + "%'"
                    #print(sql)
                    db_wamap.executesql(sql)
                    
                    # imas_questionset (qtext)
                    sql = "UPDATE imas_questionset SET `qtext`=REPLACE(`qtext`, '" + yt_url + "', '" + new_url + "') WHERE `qtext` like '%" + yt_url + "%'"
                    #print(sql)
                    db_wamap.executesql(sql)
                    
                    # imas_questionset (extref)
                    sql = "UPDATE imas_questionset SET `extref`=REPLACE(`extref`, '" + yt_url + "', '" + new_url + "') WHERE `extref` like '%" + yt_url + "%'"
                    # print(sql)
                    db_wamap.executesql(sql)
                    
                    db_wamap.commit()
                    db_wamap.close()
        else:
            print("No youtube link found (" + str(item.source_url) + ")")
        
        db(db.wamap_videos.id==item.id).update(downloaded=True)
        db.commit()
    
    return dict(ret=ret, last_row=last_row)


def create_home_directory(user_name, home_directory):
    print("Creating home directory for: " + user_name + " [" + str(time.time()) + "]")
    ret = AD.CreateHomeDirectory(user_name, home_directory)
    print("Done Creating home directory for: " + user_name + " [" + str(time.time()) + "]")
    print("Result: " + ret)
    
    # Have to call commit in tasks if changes made to the db
    db.commit()

    return ret


def download_wamap_qimages():
    ret = True
    # Make sure we are in the correct current directory
    # Starts in the Models folder
    w2py_folder = os.path.abspath(__file__)
    # print("Running File: " + app_folder)
    w2py_folder = os.path.dirname(w2py_folder)
    # app folder
    w2py_folder = os.path.dirname(w2py_folder)
    app_folder = w2py_folder
    # Applications folder
    w2py_folder = os.path.dirname(w2py_folder)
    # Root folder
    w2py_folder = os.path.dirname(w2py_folder)
    # print("W2Py Folder: " + w2py_folder)
    
    # -------- Process qimages files --------
    # Download them
    
    # Ensure the wamap folder exists
    wamap_folder = os.path.join(app_folder, "static")
    wamap_folder = os.path.join(wamap_folder, "media")
    wamap_folder = os.path.join(wamap_folder, "wamap")
    pdfs_folder = os.path.join(wamap_folder, "pdfs")
    wamap_folder = os.path.join(wamap_folder, "qimages")
    
    if os.path.isdir(wamap_folder) is not True:
        os.mkdir(wamap_folder)
    if os.path.isdir(pdfs_folder) is not True:
        os.mkdir(pdfs_folder)

    # Loop over each distinct qimages entry
    rs = db(db.wamap_qimages).select(db.wamap_qimages.source_filename, distinct=True)
    for row in rs:
        source_url = "https://www.wamap.org/assessment/qimages/" + row["source_filename"]
        s3_source_url = "https://s3.amazonaws.com/wamapdata/qimages/" + row["source_filename"]
        local_path = os.path.join(wamap_folder, row["source_filename"])
        if os.path.exists(local_path) is True:
            if '<title>404' in open(local_path).read():
                pass  # File has 404 error, try again
            else:
                continue  # Skip trying to download if the file is already there
        try:
            print("Downloading " + row["source_filename"])
            urlretrieve(source_url, local_path)
            if '<title>404' in open(local_path).read():
                # Didn't find, try dl from amazonaws
                urlretrieve(s3_source_url, local_path)
        except Exception as e:
            print("Exception trying to download " + source_url + "(" + str(e) + ")")
            ret = False
    
    # -------- Process imas_instr_files -------- 
    # Just download them
    
    # Ensure the wamap folder exists
    wamap_folder = os.path.join(app_folder, "static")
    wamap_folder = os.path.join(wamap_folder, "media")
    wamap_folder = os.path.join(wamap_folder, "wamap")
    wamap_folder = os.path.join(wamap_folder, "inst_files")
    
    if os.path.isdir(wamap_folder) is not True:
        os.mkdir(wamap_folder)
    
    db_wamap = DAL('mysql://smc:aaaaaaa!!@wamap.correctionsed.com/imathsdb')
    # Loop over each distinct instr_files entry
    rs = db_wamap.executesql("select filename from `imas_instr_files`")
    for row in rs:
        source_url = "https://www.wamap.org/course/files/" + row[0]
        alt_source_url = "https://s3.amazonaws.com/wamapdata/cfiles/" + row[0]
        local_path = os.path.join(wamap_folder, row[0])
        if os.path.exists(local_path) is True:
            if '<title>404' in open(local_path).read():
                pass  # File has 404 error, try again
            else:
                continue  # Skip trying to download if the file is already there
        try:
            print("Downloading " + row[0])
            urlretrieve(source_url, local_path)
            if '<title>404' in open(local_path).read():
                # Didn't find, try dl from amazonaws
                # print("404 getting " + source_url)
                urlretrieve(alt_source_url, local_path)
        except Exception as e:
            print("Exception trying to download " + source_url + "(" + str(e) + ")")
            ret = False

    # -------- Process imas_linkedtext -------- 
    # Download what we can and adjust the links
    # Only grab PDF files for now
    # Loop over each distinct pdf entry
    rs = db(db.wamap_pdfs).select()
    for row in rs:
        source_url = row.source_url
        local_path = os.path.join(pdfs_folder, row.media_guid + ".pdf")
        if os.path.exists(local_path) is True:
            if '<title>404' in open(local_path).read():
                pass # File has 404 error, try again
            else:
                new_url = "https://admin.correctionsed.com/static/media/wamap/pdfs/" + str(row.media_guid) + ".pdf"
                print(" Updating (" + str(source_url) + ") to point to (" + new_url + ")")
                db(db.wamap_pdfs.id==row.id).update(new_url=new_url)
                db.commit()
                continue # Skip trying to download if the file is already there
        try:
            print("Downloading " + row.source_url)
            urlretrieve(source_url, local_path)
            if '<title>404' in open(local_path).read():
                print("404 getting " + source_url)
                # Didn't find, try dl from amazonaws
                # urlretrieve(s3_source_url, local_path)
            else:
                os.chdir(pdfs_folder)
                # Store the original link in a link file
                meta = {'media_guid':row.media_guid, 'source_url':source_url}
                meta_json = dumps(meta)
                #f = os_open("wamap_" + str(row.media_guid) + ".link", os.O_TRUNC|os.O_WRONLY|os.O_CREAT)
                #os.write(f, meta_json)
                #os.close(f)
                f = open("wamap_" + str(row.media_guid) + ".link", "w")
                f.write(meta_json)
                f.close()

                new_url = "https://admin.correctionsed.com/static/media/wamap/pdfs/" + str(row.media_guid) + ".pdf"
                print(" Updating (" + str(source_url) + ") to point to (" + new_url + ")")
                db(db.wamap_pdfs.id==row.id).update(new_url=new_url)
                db.commit()
        except Exception as e:
            print("Exception trying to download " + source_url + "(" + str(e) + ")")
            ret = False
    
    # Update PDF links!!
    rs = db(db.wamap_pdfs).select()
    for row in rs:
        # Replace this url with the new one
        old_url = row.source_url
        new_url = row.new_url
        if new_url == "":
            continue # Skip empty urls
        # Pull pdfs from imas_questionset.extref
        t = "imas_questionset"
        c = "extref"
        sql = "UPDATE " + t + " SET `" + c + "`=REPLACE(`" + c + "`, '" + old_url + "', '" + new_url + "') WHERE `" + c + "` like '%" + old_url + "%'"
        print("SQL: " + sql)
        db_wamap.executesql(sql)
        
        # Pull pdfs from imas_questionset.control
        t = "imas_questionset"
        c = "control"
        sql = "UPDATE " + t + " SET `" + c + "`=REPLACE(`" + c + "`, '" + old_url + "', '" + new_url + "') WHERE `" + c + "` like '%" + old_url + "%'"
        print("SQL: " + sql)
        db_wamap.executesql(sql)
        
        # Pull pdfs from imas_questionset.qtext
        t = "imas_questionset"
        c = "qtext"
        sql = "UPDATE " + t + " SET `" + c + "`=REPLACE(`" + c + "`, '" + old_url + "', '" + new_url + "') WHERE `" + c + "` like '%" + old_url + "%'"
        print("SQL: " + sql)
        db_wamap.executesql(sql)
        
        # Pull pdfs from imas_inlinetext.text
        t = "imas_inlinetext"
        c = "text"
        sql = "UPDATE " + t + " SET `" + c + "`=REPLACE(`" + c + "`, '" + old_url + "', '" + new_url + "') WHERE `" + c + "` like '%" + old_url + "%'"
        print("SQL: " + sql)
        db_wamap.executesql(sql)
        
        # Pull pdfs from imas_assessments.intro
        t = "imas_assessments"
        c = "intro"
        sql = "UPDATE " + t + " SET `" + c + "`=REPLACE(`" + c + "`, '" + old_url + "', '" + new_url + "') WHERE `" + c + "` like '%" + old_url + "%'"
        print("SQL: " + sql)
        db_wamap.executesql(sql)
        
        # Pull pdfs from imas_linkedtext.summary
        t = "imas_linkedtext"
        c = "summary"
        sql = "UPDATE " + t + " SET `" + c + "`=REPLACE(`" + c + "`, '" + old_url + "', '" + new_url + "') WHERE `" + c + "` like '%" + old_url + "%'"
        print("SQL: " + sql)
        db_wamap.executesql(sql)
        
        # Pull pdfs from imas_linkedtext.text
        t = "imas_linkedtext"
        c = "text"
        sql = "UPDATE " + t + " SET `" + c + "`=REPLACE(`" + c + "`, '" + old_url + "', '" + new_url + "') WHERE `" + c + "` like '%" + old_url + "%'"
        print("SQL: " + sql)
        db_wamap.executesql(sql)
        db_wamap.commit()
        
    db_wamap.close()
    
    # Have to call commit in tasks if changes made to the db
    db.commit()
    return ret


def refresh_all_ad_logins(run_from="UI"):
    # Go to the AD server and refresh all student and staff AD login times
    ret = ""
    
    # Might be longer running - make sure to commit so we don't leave databases locked
    db.commit()
    db_scheduler.commit()

    # Force AD to reload settings
    AD.Close()
    AD.Init()
    
    # Update the last login value for all users (students and faculty)
    if AD._ldap_enabled is not True:
        ret = "[AD Disabled]"
        return ret
    if AD.ConnectAD() is not True:
        ret = "[AD Connection Error]" + AD.GetErrorString()
        return ret
    
    # Grab list of students
    rows = db(db.student_info).select(db.student_info.user_id)
    for row in rows:
        # ret += "UID: " + row.user_id
        ll = Student.GetLastADLoginTime(row.user_id)
        #print(f"student {row.user_id} - {ll}")
        # if (ll == None):
        #    ret += "None"
        # else:
        #    ret += str(ll)
        db(db.student_info.user_id==row.user_id).update(ad_last_login=ll)
        db.commit()
    
    # Grab a list of faculty
    rows = db(db.faculty_info).select(db.faculty_info.user_id)
    for row in rows:
        # ret += "UID: " + row.user_id
        #print(f"FTrying: {row.user_id}")
        ll = Faculty.GetLastADLoginTime(row.user_id)
        # if (ll == None):
        #    ret += "None"
        # else:
        #    ret += str(ll)
        #print(f"faculty {row.user_id} - {ll}")
        db(db.faculty_info.user_id==row.user_id).update(ad_last_login=ll)
        db.commit()
    
    rows = None
    ad_errors = AD.GetErrorString()
    ret = "Done."
    
    # Have to call commit in tasks if changes made to the db
    db.commit()
    db_scheduler.commit()
    time.sleep(5)
    return ret

def flush_redis_keys():
    # Flush keys from redis server
    # Commonly needed when login information has been manipulated
    # such as during credentialing a student
    try:
        Canvas.FlushRedisKeys("*keys*")
    except Exception as ex:
        print("Error flushing redis keys! \n" + str(ex))
    # Slight pause - let scheduler grab output
    time.sleep(5)
    return True

def tag_media_in_class(media_id, class_name):
    row = db(db.media_files.media_guid==media_id).select().first()
    if row is None:
        # print("Invalid Media ID: " + str(media_id))
        return False
    
    # Add course name to tags
    tags = row['tags']
    if tags is None:
        tags = list()
    if class_name not in tags:
        tags.append(class_name)
        row.update_record(tags=tags)
        db.commit()
        save_media_file_json(media_id)
    return True

def tag_document_in_class(document_id, class_name):
    row = db(db.document_files.document_guid==document_id).select().first()
    if row is None:
        # print("Invalid Document ID: " + str(document_id))
        return False
    
    # Add course name to tags
    tags = row['tags']
    if tags is None:
        tags = list()
    if class_name not in tags:
        tags.append(class_name)
        row.update_record(tags=tags)
        db.commit()
        save_document_file_json(document_id)
    return True

def find_smc_media_in_text(class_id, class_name, search_text):
    import re
    links_found = 0
    if search_text is None:
        return 0

    # Regular expression to find google docs
    media_find_str = r'''(/static/media/[a-zA-Z0-9]{2}/|/media/player(\.load){0,1}/)([a-zA-Z0-9]+)(\?){0,1}'''
    document_find_str = r'''(/media/dl_document/)([a-zA-Z0-9]+)(\?){0,1}'''

    # Match examples
    # <iframe width="650" height="405" src="https://smc.ed/media/player.load/24bf1a954e3640f1bdcda6804f7d99c4" frameborder="0" allowfullscreen></iframe>
    # <iframe width="650" height="405" src="https://smc.ed/media/player.load/24bf1a954e3640f1bdcda6804f7d99c4?autoplay=true" frameborder="0" allowfullscreen></iframe>
    # https://smc.ed/media/player.load/24bf1a954e3640f1bdcda6804f7d99c4
    # https://smc.ed/media/player.load/24bf1a954e3640f1bdcda6804f7d99c4?autoplay=true
    # https://smc.ed/media/player/24bf1a954e3640f1bdcda6804f7d99c4
    # <iframe width="650" height="405" src="https://smc.ed/media/player/24bf1a954e3640f1bdcda6804f7d99c4" frameborder="0" allowfullscreen></iframe>
    # https://smc.ed/smc/static/media/24/24bf1a954e3640f1bdcda6804f7d99c4.mp4

    # <iframe src="https://smc.ed/smc/static/ViewerJS/index.html#/media/dl_document/3fa5529ded38433ebebe6e1cc41398e9" width="100%" height="720" allowfullscreen="allowfullscreen" webkitallowfullscreen="webkitallowfullscreen"></iframe>
    # https://smc.ed/media/dl_document/3fa5529ded38433ebebe6e1cc41398e9

    # Find media matches
    matches = re.finditer(media_find_str, search_text)
    for m in matches:
        links_found += 1

        # ID should be in group 3
        media_id = m.group(3)
        # print("Found Media ID: " + media_id)
        # Tag media w course info
        tag_media_in_class(media_id, class_name)


    # Find document matches
    matches = re.finditer(document_find_str, search_text)
    for m in matches:
        links_found += 1

        # ID should be in group 2
        document_id = m.group(2)
        # print("Found Document ID: " + document_id)
        # Tag it
        tag_document_in_class(document_id, class_name)

    return links_found

def canvas_tag_smc_resources(class_id, class_name):
    # print("canvas_tag_smc_resources " + str(class_id) + "/" + str(class_name))
    print("Processing " + str(class_name) + "/" + str(class_id))

    log_txt = ""

    # === Pull all pages and extract links ===
    items = Canvas.get_page_list_for_course(class_id)
    total_pages = len(items)
    total_pages_links = 0
    for i in items:
        orig_text = items[i]
        
        log_txt += "\n\nWorking on Page: " + str(i)
        links_found = find_smc_media_in_text(class_id, class_name, orig_text)
        total_pages_links += links_found
        log_txt += "\n - " + str(links_found) + " links found in text"


    # === Pull all quizzes and extract links ===
    items = Canvas.get_quiz_list_for_course(class_id)
    total_quizzes = len(items)
    total_quizzes_links = 0
    total_questions_links = 0
    for i in items:
        orig_text = items[i]
        log_txt += "\n\nWorking on Quiz: " + str(i)

        links_found = find_smc_media_in_text(class_id, class_name, orig_text)
        total_quizzes_links += links_found
        log_txt += "\n - " + str(links_found) + " links found in text"

        quiz_id = i
        # === Pull all questions and extract links ===
        q_items = Canvas.get_quiz_questions_for_quiz(class_id, quiz_id)
        total_questions = len(q_items)
        for q in q_items:
            q_orig_text = q_items[q]
            log_txt += "\n\n&nbsp;&nbsp;&nbsp;&nbsp;Working on question: " + str(q)

            links_found = find_smc_media_in_text(class_id, class_name, q_orig_text)
            total_questions_links += links_found
            log_txt += "\n - " + str(links_found) + " links found in text"


    # === Pull all discussion topics and extract links ===
    items = Canvas.get_discussion_list_for_course(class_id)
    total_discussions = len(items)
    total_discussions_links = 0
    for i in items:
        orig_text = items[i]
        log_txt += "\n\nWorking on Discussion: " + str(i)

        links_found = find_smc_media_in_text(class_id, class_name, orig_text)
        total_discussions_links += links_found
        log_txt += "\n - " + str(links_found) + " links found in text"
        
    
    # === Pull all assignments and extract links ===
    items = Canvas.get_assignment_list_for_course(class_id)
    total_assignments = len(items)
    total_assignments_links = 0
    for i in items:
        orig_text = items[i]
        log_txt += "\n\nWorking on Assignment: " + str(i)

        links_found = find_smc_media_in_text(class_id, class_name, orig_text)
        total_assignments_links += links_found
        log_txt += "\n - " + str(links_found) + " links found in text"
   
    total_all_links = total_pages_links + total_quizzes_links + total_questions_links + total_discussions_links + total_assignments_links
    print(
        "<b>SMC Links Found</b>\n" +
        "-----------------------------\n" +
        "Page Links                 {0}\n".format(total_pages_links) +
        "Quizz Links                {0}\n".format(total_quizzes_links) +
        " Quizz Question Links      {0}\n".format(total_questions_links) +
        "Discussion Links           {0}\n".format(total_discussions_links) +
        "Assignment Links           {0}\n".format(total_assignments_links) +
        "-----------------------------\n" +
        "Total Links                    {0}\n".format(total_all_links)
    )

    print(log_txt)
    # Slight pause so that output gets sent out
    time.sleep(2)
    return True

def process_youtube_queue(run_from=""):
    print(f"Processing youtube queue...")

    # See if there are any videos needing to download...
    try:

        # Get how many videos or captions need to dl
        needs_downloading = db((db.media_files.youtube_url!='') & (db.media_files.needs_downloading==True)).count()
        needs_caption_downloading = db((db.media_files.youtube_url!='') & (db.media_files.needs_caption_downloading==True)).count()
        # Mark none of the videos as currently downloading
        db(db.media_files).update(current_download=False)
        db.commit()

        if needs_downloading > 0:
            # Grab one, make it current, and start it downloading.
            
            next_row = db((db.media_files.needs_downloading==True) & (db.media_files.youtube_url!='')).select(
                orderby=[~db.media_files.needs_downloading, db.media_files.download_failures, ~db.media_files.modified_on]
                ).first()
            if next_row:
                try:
                    r = pull_youtube_video(next_row.youtube_url, next_row.media_guid)
                    if r == False:
                        # Unable to download video?
                        next_row = db(db.media_files.id==next_row.id).select().first()
                        if next_row.download_failures is None:
                            next_row.download_failures = 0
                        next_row.download_failures += 1
                        next_row.needs_downloading=False
                        next_row.needs_caption_downloading=False
                        next_row.update_record()
                        db.commit()
                except Exception as ex:
                    # Had issues downloading from youtube.
                    ## requery as row changed during pull youtube
                    next_row = db(db.media_files.id==next_row.id).select().first()
                    if next_row.download_failures is None:
                        next_row.download_failures = 0
                    next_row.download_failures += 1
                    # if next_row.download_failures > 5:
                    #     next_row.needs_downloading = False
                    next_row.update_record()
                    db.commit()
                
        elif needs_caption_downloading > 0:
            # Try to grab a set of captions for the video
            
            next_row = db((db.media_files.needs_caption_downloading==True) & (db.media_files.youtube_url!='')).select(
                orderby=[~db.media_files.needs_caption_downloading, db.media_files.download_failures, ~db.media_files.modified_on]
                ).first()
            if next_row:
                
                try:
                    r = pull_youtube_caption(next_row.youtube_url, next_row.media_guid)
                    if r == False:
                        # Unable to download caption?
                        next_row = db(db.media_files.id==next_row.id).select().first()
                        if next_row.download_failures is None:
                            next_row.download_failures = 0
                        next_row.download_failures += 1
                        next_row.needs_caption_downloading=False
                        next_row.update_record()
                        db.commit()
                except Exception as ex:
                    # Had issues downloading from youtube.
                    ## requery as row changed during pull
                    next_row = db(db.media_files.id==next_row.id).select().first()
                    if next_row.download_failures is None:
                        next_row.download_failures = 0
                    next_row.download_failures += 1
                    # if next_row.download_failures > 5:
                    #     next_row.needs_caption_downloading = False
                    next_row.update_record()
                    db.commit()
        else:
            print("All caught up, no videos needed downloading.")

    except Exception as ex:
        print(f"Unknown Exception trying to pull youtube videos or captions!\n{ex}\n{traceback.format_exc()}")
    
    return True

def cleanup_youtube_urls():
    # Many youtube urls end up with crap in them (e.g. html tags) try to clean them up.
    import re
    clean_tags = re.compile('<.*?>')

    media_files_count = 0
    yt_urls_fixed_count = 0

    media_files = db(db.media_files.youtube_url!='').select()
    for media_file in media_files:
        media_files_count += 1
        yt_url = media_file.youtube_url

        new_yt_url = re.sub(clean_tags, '', yt_url)
        if new_yt_url != yt_url:
            yt_urls_fixed_count += 1
            print(f"Fixed YT URL: {yt_url} -> {new_yt_url}")

            #media_file.youtube_url = yt_url
            media_file.update_record(youtube_url=new_yt_url)
            db.commit()

    print(f"Fixed {yt_urls_fixed_count} out of {media_files_count} youtube urls.")
    return


# Enable the scheduler
from gluon.scheduler import Scheduler

scheduler = Scheduler(db_scheduler, max_empty_runs=0, heartbeat=3,
                      group_names=['process_videos', 'create_home_directory', 'wamap_delete',
                                   'wamap_videos', 'misc', "download_videos", 'youtube_queue'],
                      tasks=dict(process_media_file=process_media_file,
                                 process_wamap_video_links=process_wamap_video_links,
                                 create_home_directory=create_home_directory,
                                 remove_old_wamap_video_files=remove_old_wamap_video_files,
                                 download_wamap_qimages=download_wamap_qimages,
                                 refresh_all_ad_logins=refresh_all_ad_logins,
                                 update_media_database_from_json_files=update_media_database_from_json_files,
                                 pull_youtube_video=pull_youtube_video,
                                 update_document_database_from_json_files=update_document_database_from_json_files,
                                 flush_redis_keys=flush_redis_keys,
                                 pull_youtube_caption=pull_youtube_caption,
                                 canvas_tag_smc_resources=canvas_tag_smc_resources,
                                 process_youtube_queue=process_youtube_queue,
                                 ))
current.scheduler = scheduler


# Add indexes to the scheduler database if needed
# Do we need to do initial init? (e.g. creating indexes.....)
db_scheduler_init_needed = cache.ram('db_scheduler_init_needed', lambda: True, time_expire=3600)
if db_scheduler_init_needed:
    db_scheduler.executesql('CREATE INDEX IF NOT EXISTS scheduler_task_idx ON scheduler_task (id, task_name, group_name, status, function_name);')
    db_scheduler.executesql('CREATE INDEX IF NOT EXISTS scheduler_task_last_run_time_idx ON scheduler_task (last_run_time);')
    db_scheduler.executesql('CREATE INDEX IF NOT EXISTS scheduler_task_vars_idx ON scheduler_task (vars);')
    db_scheduler.executesql('CREATE INDEX IF NOT EXISTS scheduler_run_idx ON scheduler_run (id, task_id, status);')
    db_scheduler.executesql('CREATE INDEX IF NOT EXISTS "scheduler_task_status_idx" ON "scheduler_task" ("task_name", "vars", "last_run_time")')
    db_scheduler.executesql('CREATE INDEX IF NOT EXISTS "scheduler_run_progress_idx" ON "scheduler_run" ("task_id", "run_output")')

# Make sure we schedule the YouTube queue to process a video every ?? seconds
time_to_run_youtube_queue = current.cache.ram('time_to_run_youtube_queue', lambda: True, time_expire=300)
#print(f"{time_to_run_youtube_queue}")
if time_to_run_youtube_queue == True:
    current.cache.ram('time_to_run_youtube_queue', lambda: False, time_expire=-1)

    # Kill old scheduled items so they can just go away...
    db_scheduler(
        (db_scheduler.scheduler_task.task_name=='pull_youtube_video') |
        (db_scheduler.scheduler_task.task_name=='pull_youtube_caption')
        ).delete()
    db_scheduler.commit()

    # Some old youtube urls end up with crap in them (e.g. html tags) - clean them up a little.
    cleanup_youtube_urls()
    
    # See if a task is already queued so we don't spam things
    #ts = scheduler.task_status((db_scheduler.scheduler_task.task_name=='process_youtube_queue'))
    ts = db_scheduler(
        (db_scheduler.scheduler_task.task_name=='process_youtube_queue') &
        ((db_scheduler.scheduler_task.status=='QUEUED') | (db_scheduler.scheduler_task.status=='RUNNING'))
        ).select(orderby=~db_scheduler.scheduler_task.id).first()
    #print(f"TS: {ts}")
    if not ts is None and (ts.status == "QUEUED" or ts.status == "RUNNING"):
        # We have the task queued, make sure to clean up old ones.
        db_scheduler(
            (db_scheduler.scheduler_task.task_name=='process_youtube_queue') &
            (db_scheduler.scheduler_task.status=='QUEUED') &
            (db_scheduler.scheduler_task.id!=ts.id)
            ).update(status='COMPLETED')
        db_scheduler.commit()
        pass
    else:
        # Add a new task
        print("Scheduling Youtube Queue...")
        # print(str(request.is_scheduler))
        # print(str(request))
        # Schedule the process
        result = scheduler.queue_task('process_youtube_queue', timeout=300, 
            sync_output=5, group_name="youtube_queue", repeats=0, period=120, pvars=dict(run_from='x_scheduler.py'))



# Make sure to run the ad login refresh every hour or so
refresh_ad_login = current.cache.ram('refresh_ad_login', lambda: True, time_expire=300)
if refresh_ad_login == True and request.is_scheduler is not True:
    # Set the current value to false so we don't need to refresh for a while
    current.cache.ram('refresh_ad_login', lambda: False, time_expire=-1)

    # See if a task is already queued so we don't spam things
    ts = scheduler.task_status((db_scheduler.scheduler_task.task_name=='refresh_all_ad_logins'))
    if not ts is None and ts.status == "QUEUED":
        #print("refresh_all_ad_logins - already queued, skipping.")
        #print(f"TS: {ts}")
        # Clean up old extras
        db_scheduler(
            (db_scheduler.scheduler_task.task_name=='refresh_all_ad_logins') &
            (db_scheduler.scheduler_task.status=='QUEUED') &
            (db_scheduler.scheduler_task.id!=ts.id)
            ).update(status='COMPLETED')
        db_scheduler.commit()
        pass
    else:
        # Add a new task
        # Update the last login value for all users (students and faculty)
        print("Queueing up refresh_all_ad_logins...")
        # print(str(request.is_scheduler))
        # print(str(request))
    
        # See if we have one already
        ts = db_scheduler(
            (db_scheduler.scheduler_task.task_name=='refresh_all_ad_logins') &
            ((db_scheduler.scheduler_task.status=='QUEUED') | (db_scheduler.scheduler_task.status=='RUNNING'))
            ).select(orderby=~db_scheduler.scheduler_task.id).first()
        if ts is None:
            # Schedule the process
            result = scheduler.queue_task('refresh_all_ad_logins', timeout=300, 
                sync_output=5, group_name="misc", repeats=0, period=600, pvars=dict(run_from='x_scheduler.py'))
            

    # Make sure to start the scheduler process
    # cmd = "/usr/bin/nohup /usr/bin/python " + os.path.join(request.folder, 'static/scheduler/start_misc_scheduler.py') + " > /dev/null 2>&1 &"
    # p = subprocess.Popen(cmd, shell=True, close_fds=True)


