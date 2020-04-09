# -*- coding: utf-8 -*-

import os
import time
import subprocess
from gluon.contrib.simplejson import loads, dumps
import sys
import shutil

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
    # NOTE - Leave off!! - will override web2py request object
    #from urllib import request

    def install_proxy(proxy_handler):
        proxy_support = request.ProxyHandler(proxy_handler)
        opener = request.build_opener(proxy_support)
        request.install_opener(opener)

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
    cpus -= 2
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
    # webm_ret = p.communicate()[0]
    
    # Do OGV
    # cmd = ffmpeg + " -y -i '" + input_file + "' -vcodec libtheora -qscale 6
    # -acodec libvorbis -ab 192k -vf scale='640:-1' '" + output_ogv + "'"
    # cmd = ffmpeg + " -y -i '" + input_file + "' -vcodec libtheora -qscale:v 5
    # -acodec libvorbis -ab 128k '" + output_ogv + "'"
    # print("Creating OGV..."  + " [" + str(time.time()) + "]")
    print("!clear!10%")
    # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    # ogv_ret = p.communicate()[0]

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
    mp4_ret = p.communicate()[0]
    
    # Do MP4 with mobile quality
    cmd = ffmpeg + " -y -i \"" + input_file + \
          "\" -vcodec libx264 -preset slow -movflags faststart -profile main -crf 20 -acodec " +\
          acodec + " -ab 128k -vf scale='2*trunc(oh*a/2):480' -threads " + str(cpus) + " \"" +\
          output_mobile_mp4 + "\""
    # print("Creating mobile MP4..."  + " [" + str(time.time()) + "]")
    print("!clear!70%")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    mp4_ret += p.communicate()[0]

    # Generate poster image
    cmd = ffmpeg + " -y -ss 5 -i \"" + input_file + "\" -vf  \"thumbnail,scale=640:-1\" -frames:v 1 \"" + output_poster + "\""
    # print("Creating poster image..." + " [" + str(time.time()) + "]")
    print("!clear!85%")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    poster_ret = p.communicate()[0]
    
    # Generate thumbnail image
    cmd = ffmpeg + " -y -ss 5 -i \"" + input_file + "\" -vf  \"thumbnail,scale=128:-1\" -frames:v 1 \"" + output_thumb + "\""
    # print("Creating thumbnail image..."  + " [" + str(time.time()) + "]")
    print("!clear!95%")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    thumb_ret = p.communicate()[0]

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


def find_best_yt_stream(yt_url):
    yt = None
    res = '480p'

    if yt_url is None:
        print("ERROR: yt_url was none?")
        yt_url = ""

    # print("Looking for YT: " + yt_url)

    if session.yt_urls_error_msg is None:
        session.yt_urls_error_msg = ""

    # Change out embed for watch so the link works properly
    try:
        yt = YouTube(yt_url.replace("/embed/", "/watch?v="))
    except HTTPError as ex:
        if ex.code == 429:
            # Need to try again later
            # Pass this exception up the stack
            raise ex
    except Exception as ex:
        msg = "Bad YT URL? " + yt_url + " -- " + str(ex)
        session.yt_urls_error_msg += msg
        print(msg)

    s = None
    try:
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
    except Exception as ex:
        msg = "Error grabbing yt video info! " + str(ex)
        session.yt_urls_error_msg += msg
        print(msg)

    stream = s
    return yt, stream, res


def pull_youtube_video(yt_url, media_guid):
    # Download the specified movie.
    had_errors = False

    # Pull the db info
    media_file = db(db.media_files.media_guid==media_guid).select().first()
    if media_file is None:
        print("ERROR - Unable to find a db record for " + str(media_guid))
        return False

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
    output_mp4_filename = file_guid  # Note - don't add mp4 as yt will do that
    output_meta = target_file + ".json"
    output_poster = target_file + ".poster.png"
    output_thumb = target_file + ".thumb.png"

    from pytube import YouTube
    try:
        yt, stream, res = find_best_yt_stream(yt_url)
    except HTTPError as ex:
        if ex.code == 429:
            # Too many requests - have this try again later...

            sleep_time = 300  # sleep for 5 mins?
            if "Retry-After" in ex.headers:
                sleep_time = int(ex.headers["Retry-After"])
            print("Too many requests - sleeping for a few... " + str(sleep_time))
            # print("Too many requests! " + str(ex.headers["Retry-After"]))
            time.sleep(sleep_time)
            raise Exception("HTTP 429 - Retry after sleep")
            return False
        else:
            print("Unknown HTTP error? " + str(ex))
            return False

    try:
        print("Downloading " + str(yt_url))
        stream.download(output_path=target_folder, filename=output_mp4_filename)  # put in folder name
        print("Download Complete!")
    except HTTPError as ex:
        if ex.code == 429:
            # Too many requests - have this try again later...

            sleep_time = 300  # sleep for 5 mins?
            if "Retry-After" in ex.headers:
                sleep_time = int(ex.headers["Retry-After"])
            print("Too many requests - sleeping for a few... " + str(sleep_time))
            # print("Too many requests! " + str(ex.headers["Retry-After"]))
            time.sleep(sleep_time)
            raise Exception("HTTP 429 - Retry after sleep")
            return False
        else:
            print("Unknown HTTP error? " + str(ex))
            return False
    except Exception as ex:
        # TODO - Schedule it to try again? Or just let it die?
        print("Error Downloading YouTube Video!  Are you online? " + str(ex))
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
            tn = urllib.urlopen(thumbnail_url)
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
                thumb_ret = p.communicate()[0]
            except Exception as ex:
                print("Error generating thumbnail: " + str(output_thumb) + " - " + str(ex))

            # Generate poster image
            cmd = ffmpeg + " -y -ss 5 -i \"" + input_file + "\" -vf  \"thumbnail,scale=640:-1\" -frames:v 1 \"" + \
                output_poster + "\""
            # print("Creating poster image..." + " [" + str(time.time()) + "]")
            print("Generating Poster Image...")
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                poster_ret = p.communicate()[0]
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

    # Have to call commit in tasks if changes made to the db
    db.commit()

    # Throw a little delay in here to help keep from getting blocked by youtube
    time.sleep(30)
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
                    yt = YouTube()
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
            urllib.urlretrieve(source_url, local_path)
            if '<title>404' in open(local_path).read():
                # Didn't find, try dl from amazonaws
                urllib.urlretrieve(s3_source_url, local_path)
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
            urllib.urlretrieve(source_url, local_path)
            if '<title>404' in open(local_path).read():
                # Didn't find, try dl from amazonaws
                # print("404 getting " + source_url)
                urllib.urlretrieve(alt_source_url, local_path)
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
            urllib.urlretrieve(source_url, local_path)
            if '<title>404' in open(local_path).read():
                print("404 getting " + source_url)
                # Didn't find, try dl from amazonaws
                # urllib.urlretrieve(s3_source_url, local_path)
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
        ll = Faculty.GetLastADLoginTime(row.user_id)
        # if (ll == None):
        #    ret += "None"
        # else:
        #    ret += str(ll)
        db(db.faculty_info.user_id==row.user_id).update(ad_last_login=ll)
        db.commit()
    
    rows = None
    ad_errors = AD.GetErrorString()
    ret = "Done."
    
    # Have to call commit in tasks if changes made to the db
    db.commit()
    return ret


# Enable the scheduler
from gluon.scheduler import Scheduler

scheduler = Scheduler(db_scheduler, max_empty_runs=0, heartbeat=3,
                      group_names=['process_videos', 'create_home_directory', 'wamap_delete',
                                   'wamap_videos', 'misc', "download_videos"],
                      tasks=dict(process_media_file=process_media_file,
                                 process_wamap_video_links=process_wamap_video_links,
                                 create_home_directory=create_home_directory,
                                 remove_old_wamap_video_files=remove_old_wamap_video_files,
                                 download_wamap_qimages=download_wamap_qimages,
                                 refresh_all_ad_logins=refresh_all_ad_logins,
                                 update_media_database_from_json_files=update_media_database_from_json_files,
                                 pull_youtube_video=pull_youtube_video,
                                 update_document_database_from_json_files=update_document_database_from_json_files,
                                 ))
current.scheduler = scheduler


# Make sure to run the ad login refresh every hour or so
refresh_ad_login = current.cache.ram('refresh_ad_login', lambda: True, time_expire=60*60)
if refresh_ad_login is True and request.is_scheduler is not True:
    # Set the current value to false so we don't need to refresh for a while
    current.cache.ram('refresh_ad_login', lambda: False, time_expire=-1)
    # Update the last login value for all users (students and faculty)
    AD.Init() # Make sur AD settings are loaded
    print("Queueing up refresh_all_ad_logins...")
    # print(str(request.is_scheduler))
    # print(str(request))
    if AD._ldap_enabled is not True:
        # Not enabled, skip
        print("AD Not enabled, skipping refresh_all_ad_logins...")
    else:
        # Schedule the process
        result = scheduler.queue_task('refresh_all_ad_logins', timeout=1200, 
            sync_output=5, group_name="misc", repeats=1, period=0, pvars=dict(run_from='x_scheduler.py'))
        
    
    # Make sure to start the scheduler process
    # cmd = "/usr/bin/nohup /usr/bin/python " + os.path.join(request.folder, 'static/scheduler/start_misc_scheduler.py') + " > /dev/null 2>&1 &"
    # p = subprocess.Popen(cmd, shell=True, close_fds=True)
