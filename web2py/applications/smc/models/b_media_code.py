# -*- coding: utf-8 -*-

"""
    Functions/helpers for media files, helps minimize the footprint of the media controller file
"""

import os
import tempfile
import time
import uuid
import re
import glob
import mimetypes
from gluon.contrib.simplejson import loads, dumps
import requests
from langcodes import *
import webvtt
import traceback

from ednet.canvas import Canvas

from pytube import YouTube
#import pytube

def get_youtube_proxies():
    query = (db.youtube_proxy_list.enabled==True)
    # Random order so you get a possible different item from the list each time
    rows = db(query).select(orderby='<random>')
    ret = None
    for row in rows:
        if ret is None:
            ret = {}
        
        ret[row["protocol"]] = row["proxy_url"]

    return ret

def get_flashcards_folder_path(flashcard_id):
    (w2py_folder, applications_folder, app_folder) = get_app_folders()
    flashcards_folder = os.path.join(app_folder, "static/media/flashcards")

    target_folder = os.path.join(flashcards_folder, str(flashcard_id))

    if os.path.exists(target_folder) is not True:
        try:
            os.makedirs(target_folder)
        except OSError as message:
            pass

    return target_folder.replace("\\", "/")


def get_document_file_path(file_guid, ext=""):
    # Make sure there is a "." at the beginning if an extension is requested
    if len(ext) > 0 and ext.startswith(".") is not True:
        ext = "." + ext

    (w2py_folder, applications_folder, app_folder) = get_app_folders()
    docs_folder = os.path.join(app_folder, "static/documents")

    file_guid = file_guid.replace('-', '')
    file_prefix = file_guid[0:2]

    target_folder = os.path.join(docs_folder, file_prefix)

    if os.path.exists(target_folder) is not True:
        try:
            os.makedirs(target_folder)
        except OSError as message:
            pass

    target_file = os.path.join(target_folder, file_guid + ext).replace("\\", "/")

    return target_file


def get_media_file_path(file_guid, ext="mp4"):
    # Make sure we have a . at the beginning
    if ext.startswith(".") is not True:
        ext = "." + ext

    (w2py_folder, applications_folder, app_folder) = get_app_folders()
    media_folder = os.path.join(app_folder, "static/media")

    file_guid = file_guid.replace('-', '')
    file_prefix = file_guid[0:2]

    target_folder = os.path.join(media_folder, file_prefix)

    if os.path.exists(target_folder) is not True:
        try:
            os.makedirs(target_folder)
        except OSError as message:
            pass

    target_file = os.path.join(target_folder, file_guid + ext).replace("\\", "/")

    return target_file


def is_media_file_present(file_guid):
    """
    Check the static folder to see if this file is there or not
    :param file_guid:
    :return:
    """
    path = get_media_file_path(file_guid)

    return os.path.exists(path)

def get_lang_name(lang):
    """
    Find the country label for the provided language
    """
    ret = None

    try:
        l = Language.get(lang)
        d = l.describe()
        ret = ""
        if 'language' in d:
            ret += d['language']
        if 'script' in d:
            ret += " (" + d['script'] + ")"
        if 'territory' in d:
            ret += " (" + d['territory'] + ")"
    except:
        pass

    if ret is None:
        ret = ""
    return ret

def save_media_caption_file(file_guid, language, file_name, f_handle):
    """
    Save caption file to the proper 
    """
    ret = False
    print("Trying to save caption file: " + file_guid + "/" + language + "/" + \
        file_name)

    try:
        file_name = os.path.basename(file_name)
        parts = os.path.splitext(file_name)

        dest_path = get_media_file_path(file_guid)
        dest_path = dest_path.replace(".mp4", "_" + language + parts[1].lower())

        out_file = open(dest_path, 'wb')
        out_file.write(f_handle.read())
        out_file.close()

        # Do we need to convert to VTT?
        if dest_path.lower().endswith("srt"):
            vtt = webvtt.from_srt(dest_path)
            output_caption_file = dest_path.replace("srt", "vtt")
            vtt.save(output_caption_file)
            #print("Saved " + language + " to " + output_caption_file)

        ret = True
    except Exception as ex:
        print("Error saving caption file! " + file_guid + "/" + dest_path + "/" + language + "\n" + str(ex))
    
    return ret

def get_media_captions_list(file_guid):
    """
    Get the list of vtt files
    """
    ret = dict()
    path = get_media_file_path(file_guid)
    vtt_folder = os.path.dirname(path)
    with os.scandir(vtt_folder) as it:
        for entry in it:
            if file_guid in entry.name and entry.is_file() and entry.name.endswith('.vtt'):
                # Found a VTT file, assume we are good.
                # Get language
                try:
                    lang = os.path.splitext(entry.name)[0]
                    lang = lang.split("_")[1]

                    lang_name = get_lang_name(lang)

                    ret[lang] = (entry.name, lang_name)
                except Exception as ex:
                    print("Error splitting caption name?" + str(entry.name))
                    
    return ret

def is_media_captions_present(file_guid):
    """
    Are the caption files present?
    """
    cap_files = get_media_captions_list(file_guid)
    if len(cap_files) > 0:
        return True

    return False

def get_cc_icon(file_guid):
    # Return a Xed cc pic or a good cc pic depending on the state of cc files for this movie.
    ret = URL('static', 'images/no_cc.png')

    if is_media_captions_present(file_guid):
        ret = URL('static', 'images/cc.png')

    return ret


def load_media_file_json(file_guid):
    """
    Load the json file and update the database using this information
    :param file_guid:
    :return:
    """

    json_file = get_media_file_path(file_guid, ".json")

    if os.path.exists(json_file) is not True:
        print("Invalid Media JSON file: " + str(json_file))
        return False

    print("Found Media Json File: ", json_file)

    # Open the json file
    try:
        f = open(json_file, "r")
        tmp = f.read()
        meta = loads(tmp)
        f.close()

        fields = ['title', 'media_guid', 'description', 'category', 'tags', 'width', 'height', 'quality', 'media_type', 'youtube_url']
        for f in fields:
            if f not in meta:
                if f == "tags":
                    meta[f] = "[]"
                else:
                    meta[f] = ""
        
        if type(meta['tags']) is list:
            # Need to convert to string for later
            meta['tags'] = dumps(meta['tags'])
            
        # See if the item is in the database
        item = db.media_files(media_guid=meta['media_guid'])
        if item is None:
            # Record not found!
            print("Record not found: ", meta['media_guid'])
            db.media_files.insert(media_guid=meta['media_guid'], title=meta['title'], description=meta['description'],
                                  category=meta['category'], tags=loads(meta['tags']), width=meta['width'],
                                  height=meta['height'], quality=meta['quality'], media_type=meta['media_type'],
                                  youtube_url=meta['youtube_url'])
            db.commit()
        else:
            print("Record FOUND: ", meta['media_guid'])
            item.update_record(title=meta['title'], description=meta['description'], category=meta['category'],
                               tags=loads(meta['tags']), width=meta['width'], height=meta['height'],
                               quality=meta['quality'], media_type=meta['media_type'],
                               youtube_url=meta['youtube_url'])
            db.commit()
    except Exception as ex:
        print("Error processing media file: ", json_file, str(ex))
        # db.rollback()

    return True


def save_media_file_json(file_guid):
    """
    Store/update the json meta data for this file
    :param file_guid:
    :return:
    """

    # Get the db info for this file
    media_file = db(db.media_files.media_guid==file_guid).select().first()
    if media_file is None:
        print("Error - media file doesn't exist " + str(file_guid))
        return False

    # Get the json file path for this file
    json_path = get_media_file_path(file_guid, ".json")

    meta = {'title': media_file.title, 'media_guid': media_file.media_guid.replace('-', ''),
            'description': media_file.description, 'original_file_name': media_file.original_file_name,
            'media_type': media_file.media_type, 'category': media_file.category,
            'tags': dumps(media_file.tags), 'width': media_file.width,
            'height': media_file.height, 'quality': media_file.quality,
            'youtube_url': media_file.youtube_url}

    try:
        meta_json = dumps(meta)
        #f = os.open(json_path, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        #os.write(f, meta_json)
        #os.close(f)
        f = open(json_path, "w")
        f.write(meta_json)
        f.close()
    except Exception as ex:
        print("Exception saving media json " + str(file_guid) + " => " + str(ex))
        return False

    return True


def load_document_file_json(file_guid):
    """
    Load the json file and update the database using this information
    :param file_guid:
    :return:
    """

    json_file = get_document_file_path(file_guid, ".json")

    if os.path.exists(json_file) is not True:
        print("Invalid Document JSON file: " + str(json_file))
        return False

    print("Found Document Json File: ", json_file)

    # Open the json file
    try:
        f = open(json_file, "r")
        tmp = f.read()
        meta = loads(tmp)
        f.close()

        fields = ['document_guid', 'title', 'description', 'original_file_name', 'media_type', 'category', 'tags', 'source_url']
        for f in fields:
            if f not in meta:
                if f == "tags":
                    meta[f] = "[]"
                else:
                    meta[f] = ""
        
        if type(meta['tags']) is list:
            # Need to convert to string for later
            meta['tags'] = dumps(meta['tags'])

        # See if the item is in the database
        item = db.document_files(document_guid=meta['document_guid'])
        if item is None:
            # Record not found!
            print("Record not found: ", meta['document_guid'] + str(meta))
            db.document_files.insert(document_guid=meta['document_guid'], title=meta['title'], description=meta['description'],
                                  original_file_name=meta['original_file_name'],
                                  category=meta['category'], tags=loads(meta['tags']), media_type=meta['media_type'],
                                  source_url=meta['source_url'])
            db.commit()
        else:
            print("Record FOUND: ", meta['document_guid'])
            item.update_record(title=meta['title'], description=meta['description'], category=meta['category'],
                               tags=loads(meta['tags']), media_type=meta['media_type'],
                               source_url=meta['source_url'], original_file_name=meta['original_file_name'])
            db.commit()
    except Exception as ex:
        print("Error processing document file: ", json_file, str(ex))
        traceback.print_exc()
        # db.rollback()

    # Make sure to release the lock on this db
    db.commit()
    return True


def save_document_file_json(file_guid):
    """
    Store/update the json meta data for this file
    :param file_guid:
    :return:
    """

    # Get the db info for this file
    document_file = db(db.document_files.document_guid==file_guid).select().first()
    if document_file is None:
        print("Error - document file doesn't exist " + str(file_guid))
        return False

    # Get the json file path for this file
    json_path = get_document_file_path(file_guid, ".json")

    meta = {'title': document_file.title, 'document_guid': document_file.document_guid.replace('-', ''),
            'description': document_file.description, 'original_file_name': document_file.original_file_name,
            'media_type': document_file.media_type, 'category': document_file.category,
            'tags': dumps(document_file.tags), 'source_url': document_file.source_url}

    try:
        meta_json = dumps(meta)
        f = open(json_path, "w")
        f.write(meta_json)
        f.close()
    except Exception as ex:
        print("Exception saving document json " + str(file_guid) + " => " + str(ex))
        return False

    return True


def queue_up_yt_video(yt_url, category=None):
    # Find the current video, or queue it up for download and return the db info
    vid_guid = str(uuid.uuid4()).replace('-', '')
    title = "Downloading from: " + yt_url
    description = ""
    if category is None:
        category = "YouTube"
    tags = ["YouTube"]
    media_file = db(db.media_files.youtube_url == yt_url).select().first()
    if media_file is None:
        # Create db entry
        db.media_files.insert(title=title, youtube_url=yt_url,
                              description=description, original_file_name=title,
                              category=category, tags=tags,
                              media_guid=vid_guid, needs_downloading=True)
        db.commit()

        # Launch the background process to download the video
        result = scheduler.queue_task('pull_youtube_video', pvars=dict(yt_url=yt_url,
                                                                       media_guid=vid_guid
                                                                       ),
                                      timeout=18000, immediate=True, sync_output=2,
                                      group_name="download_videos", retry_failed=30, period=300)

        # Launch background process to download caption files
        caption_result = scheduler.queue_task('pull_youtube_caption',
            pvars=dict(yt_url=yt_url, media_guid=vid_guid),
            timeout=90, immediate=True, sync_output=5,
            group_name="download_videos", retry_failed=30, period=300)

        # Make sure to grab the new record now that it has been inserted
        media_file = db(db.media_files.youtube_url == yt_url).select().first()
    else:
        # Video exists, just return the db record
        pass

    return media_file


def find_ffmpeg():
    # Find the ffmpeg folder and return it
    (w2py_folder, applications_folder, app_folder) = get_app_folders()

    acodec = "aac"

    # Find ffmpeg binary
    ffmpeg = "/usr/bin/ffmpeg"
    if os.path.isfile(ffmpeg) is not True:
        ffmpeg = "/usr/local/bin/ffmpeg"
    if os.path.isfile(ffmpeg) is not True:
        # Try windows path
        ffmpeg = os.path.join(w2py_folder, "ffmpeg", "bin", "ffmpeg.exe")
        acodec = "libvo_aacenc"
    if os.path.isfile(ffmpeg) is not True:
        ret = "ERROR - NO FFMPEG APP FOUND! " + ffmpeg
        ffmpeg = None
        acodec = None
        print(ret)
        # raise an exception so it is marked as failed
        # failed to find, will return None now

    return ffmpeg, acodec


def getURLS(txt):
    if txt is None:
        txt = ""
    # Extract the list of urls from the string
    ret = []
    # pat = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)
    # (?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)
    # |[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
    pat = re.compile(
                     'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                    )
    res = pat.findall(txt)
    for r in res:
        if 'youtu' in r:
            ret.append(r)
    return ret


def getPDFURLS(txt):
    if txt is None:
        txt = ""
    # Extract the list of urls from the string
    ret = []
    # pat = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)
    # (?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|
    # [^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
    pat = re.compile(
                     'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                    )
    res = pat.findall(txt)
    # pdf, swf, png, doc, ?
    for r in res:
        if 'pdf' in r:
            ret.append(r)
    return ret

