# -*- coding: utf-8 -*-

import os
import tempfile
import time
import uuid
import re
import glob
import mimetypes
from gluon.contrib.simplejson import loads, dumps
import requests

from ednet.canvas import Canvas
from pytube import YouTube



def index():
    ret = start_process_videos()
    
    query = (db.media_files)
    links = []
    if auth.has_membership('Faculty') or auth.has_membership('Administrators'):
        links.append(dict(header=T(''),body=lambda row: (
            A('[Edit]', _style='font-size: 10px; color: red;', _href=URL('media', 'edit_media', args=[row.media_guid], user_signature=True)),
            ' | ',
            A('[Delete]', _style='font-size: 10px; color: red;', _href=URL('media', 'delete_media', args=[row.media_guid], user_signature=True)),
            ) ) )
        #links.append(dict(header=T(''),body=lambda row:  ) )
    links.append(dict(header=T(''),body=lambda row: IMG(_src=get_cc_icon(row.media_guid), _style="width: 24px; height: auto; max-width: 24px;", _alt="Close Captioning Available")))
    links.append(dict(header=T(''),body=lambda row: A(IMG(_src=getMediaThumb(row.media_guid), _style="width: 128px; height: auto; max-width: 128px;"), _href=URL('media', 'player', args=[row.media_guid], user_signature=True)) ) )
    fields = [db.media_files.id, db.media_files.title, db.media_files.tags, db.media_files.description, db.media_files.media_guid, db.media_files.category] #[db.media_files.title]
    maxtextlengths = {'media_files.title': 150, 'media_files.tags': 50, 'media_files.description': 150}
    
    # Hide columns
    db.media_files.id.readable=False
    db.media_files.media_guid.readable=False
    db.media_files.width.readable=False
    db.media_files.height.readable=False
    db.media_files.original_file_name.readable=False
    db.media_files.media_type.readable=False
    db.media_files.quality.readable=False
    
    # rows = db(query).select()
    media_grid = SQLFORM.grid(query, editable=False, create=False, deletable=False,
                              csv=False, details=False,
                              searchable=True, orderby=[~db.media_files.modified_on],
                              fields=fields, paginate=15,
                              links=links, links_placement='left', links_in_grid=True,
                              maxtextlengths=maxtextlengths)
    
    return dict(media_grid=media_grid)

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def edit_media():
    media_guid = request.args(0)
    caption_files = dict()
    caption_upload_form = None

    if media_guid is None:
        form = "Invalid Media ID"
        return dict(form=form, caption_files=caption_files,
            caption_upload_form=caption_upload_form, media_guid=media_guid)

    media_file = db(db.media_files.media_guid==media_guid).select().first()
    if media_file is None:
        form = "Media ID Not Found!"
        return dict(form=form, caption_files=caption_files,
            caption_upload_form=caption_upload_form, media_guid=media_guid)
    
    db.media_files.id.readable=False
    form = SQLFORM(db.media_files, _name="edit_media", record=media_file,
        fields=['title', 'tags', 'description', 'category', 'youtube_url']).process(formname="edit_media")

    if form.accepted:
        # Commit info to the database (so it is updated when json file is generated)
        db.commit()
        # Make sure to write the updated media data to the json file
        save_media_file_json(media_guid)
        response.flash = "Saved!"
    elif form.errors:
        response.flash = "Error saving media info!"

    caption_upload_form = FORM(
        TABLE(
            TR(
                "Upload VTT or SRT file:",
                INPUT(_type="file", _name="caption_file", requires=IS_NOT_EMPTY()),
                ""
            ),
            TR(
                "Choose Language (2 letter code): ",
                INPUT(_type="text", _id="lang", _name="lang", requires=IS_NOT_EMPTY()),
                SELECT(
                    OPTION("[Common Languages]", _value=""),
                    OPTION("Chinese", _value="zh-Hans-CN"),
                    OPTION("English", _value="en"),
                    OPTION("French", _value="fr"),
                    OPTION("Russian", _value="ru"),
                    OPTION("Spanish", _value="es"),
                    OPTION("Taiwan", _value="zh-Hant-TW"),

                    _id="sel_lang", _value="",
                    _onchange="$('#lang').val( $('#sel_lang').val() );"
                )
            ),
            TR(
                "",
                INPUT(_type="submit", _value="Upload"),
                ""
            )
        ),
        _name="caption_upload"
    )

    if caption_upload_form.accepts(request, session, formname="caption_upload"):
        # Accepted - process file

        # Is this a VTT or SRT file?
        if not caption_upload_form.vars.caption_file.filename.lower().endswith("srt") and \
            not caption_upload_form.vars.caption_file.filename.lower().endswith("vtt"):
            response.flash = "Invalid File Type - Only VTT and SRT files supported!"
        else:
            # Good file name
            f = caption_upload_form.vars.caption_file.file
            f_name = caption_upload_form.vars.caption_file.filename
            if not save_media_caption_file(media_guid, caption_upload_form.vars.lang,
                f_name, f):
                response.flash = "Error saving file!"
            else:
                response.flash = "File Uploaded!"
    elif caption_upload_form.errors:
        response.flash = "Please supply a caption file (VTT or SRT) and the language it provides."
    

    caption_files = get_media_captions_list(media_guid)

    return dict(form=form, caption_files=caption_files,
            caption_upload_form=caption_upload_form, media_guid=media_guid)

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def delete_caption_file():
    response.view='generic.load'
    media_guid = request.vars['media_guid']
    lang = request.vars['lang']
    
    if media_guid == "":
        print("Can't delete w missing media_guid!")
        redirect(URL('media'))
    
    if lang == "":
        print("Can't delete w missing lang!")
        redirect(URL('media', 'edit_media', args=[media_guid]))
    
    # Get the media file
    caption_file = media_guid + "_" + lang
    srt_path = get_media_file_path(caption_file, ext="srt")
    vtt_path = get_media_file_path(caption_file, ext="vtt")

    if os.path.exists(srt_path):
        print("Found SRT file, removing: " + srt_path)
        os.unlink(srt_path)
    
    if os.path.exists(vtt_path):
        print("Found VTT file, removing: " + vtt_path)
        os.unlink(vtt_path)
    
    # Return us back to the edit page.
    redirect(URL('media', 'edit_media', args=[media_guid]))


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def edit_document():
    document_guid = request.args(0)

    if document_guid is None:
        form = "Invalid Document ID"
        return dict(form=form)

    document_file = db(db.document_files.document_guid==document_guid).select().first()
    if document_file is None:
        form = "Document ID Not Found!"
        return dict(form=form)

    db.document_files.id.readable=False
    form = SQLFORM(db.document_files, record=document_file,
        fields=['title', 'tags', 'description', 'category', 'source_url']).process()

    if form.accepted:
        # Commit info to the database (so it is updated when json file is generated)
        db.commit()
        # Make sure to write the updated media data to the json file
        save_document_file_json(document_guid)
        response.flash = "Saved!"
    elif form.errors:
        response.flash = "Error saving document info!"


    return dict(form=form)


def documents():
    query = (db.document_files)
    links = []
    if auth.has_membership('Faculty') or auth.has_membership('Administrators'):
        links.append(dict(header=T(''), body=lambda row: (
                A('[Edit]', _style='font-size: 10px; color: red;',
                    _href=URL('media', 'edit_document', args=[row.document_guid],
                    user_signature=True)),
                " | ",
                A('[Delete]', _style='font-size: 10px; color: red;',
                    _href=URL('media', 'delete_document', args=[row.document_guid],
                    user_signature=True))
                
                ) ) )
    links.append(dict(header=T(''), body=lambda row: A(TABLE(TR(
                                                TD(IMG(_src=getDocumentThumb(row.document_guid), _style="width: 24px;"),
                                                   _width=26),
                                                TD(LABEL(row.title), _align="left")
                                                )),
                                                _href=URL('media', 'view_document', args=[row.document_guid],
                                                user_signature=True))))
    fields = [db.document_files.id, db.document_files.title, db.document_files.tags, db.document_files.description,
              db.document_files.document_guid, db.document_files.category]  # [db.document_files.title]
    maxtextlengths = {'document_files.title': 150, 'document_files.tags': 50, 'document_files.description': 150}

    # Hide columns
    db.document_files.id.readable = False
    db.document_files.title.listable = False
    db.document_files.title.searchable = True
    db.document_files.document_guid.readable = False
    db.document_files.original_file_name.readable = False
    db.document_files.media_type.readable = False

    # rows = db(query).select()
    document_grid = SQLFORM.grid(query, editable=False, create=False, deletable=False,
                              csv=False, details=False,
                              searchable=True, orderby=[~db.document_files.modified_on],
                              fields=fields, paginate=15,
                              links=links, links_placement='left', links_in_grid=True,
                              maxtextlengths=maxtextlengths)

    return dict(document_grid=document_grid)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def playlists():
    
    query = (db.playlist.created_by==auth.user.id)
    fields = [db.playlist.title, db.playlist.id, db.playlist.playlist_guid, db.playlist.created_by]
    links = []
    # links = [(dict(header=T(''),body=lambda row: A('Re-Queue', _href=URL('media', 'reset_queued_item', args=[row.id], user_signature=True)) ) ),
    #         (dict(header=T('Task Status'),body=lambda row: getTaskStatus(row.id) ) ), ]
    
    db.playlist.id.readable=False
    db.playlist.playlist_guid.readable=False
    db.playlist.playlist_guid.writable=False
    db.playlist._singular="Playlist"
    db.playlist._plural="Playlist"
    # db.playlist_items._singular="Playlist Item"
    # db.playlist_items._plural="Playlist Items"
    
    headers = {}  # {'media_file_import_queue.modified_on':'Queued On' }
    # rows = db(query).select()
    playlist_grid = SQLFORM.grid(query,
                                 editable=True, create=dict(parent=False, child=True),
                                 deletable=True, csv=False,links=links,links_in_grid=True,
                                 details=False, searchable=False,
                                 orderby=[db.playlist.title], fields=fields, headers=headers)

    return dict(playlist_grid=playlist_grid)


def dl_media():
    message = ""
    movie_id = request.args(0)
    media_type = request.args(1)
    if movie_id is not None:
        movie_id = movie_id.strip()
        # Load the movie from the database
        prefix = movie_id[0:2]
        
        title = ""
        source_ogg = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".ogv")
        source_mp4 = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".mp4")
        source_mobile_mp4 = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".mobile.mp4")
        source_webm = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".webm")
        
        media_file = db(db.media_files.media_guid==movie_id).select().first()
        if media_file is not None:
            title = media_file.title
            description = media_file.description
            tags = ",".join(media_file.tags)
            views = media_file.views
        pass
        
        target_folder = os.path.join(request.folder, 'static')
        # target_folder='static'
        target_folder = os.path.join(target_folder, 'media')
        target_folder = os.path.join(target_folder, prefix)
        fname = os.path.join(target_folder, movie_id + "." +  media_type)
        save_fname = title + "." + media_type
        message = "Downloading " + fname
        try:
            return response.stream(open(fname, 'rb'), chunk_size=10**6, request=request,
                                   attachment=True, filename=save_fname)  # , headers=None)
        except Exception as ex:
            message = "Invalid File " + fname + " " + str(ex)
            pass
    else:
        movie_id = ""
    
    return dict(message=message)


def dl_document():
    message = ""
    document_id = request.args(0)
    if document_id is not None:
        document_id = document_id.strip()
        # Load the document from the database
        prefix = document_id[0:2]

        title = ""
        source_url = URL('static', 'documents' + "/" + prefix + "/" + document_id)

        document_file = db(db.document_files.document_guid == document_id).select().first()
        media_type = ""
        if document_file is not None:
            title = document_file.title
            description = document_file.description
            tags = ",".join(document_file.tags)
            views = document_file.views
            original_file_name = document_file.original_file_name
        pass
        p, media_type = os.path.splitext(original_file_name)
        mimetypes.init()
        try:
            content_type = mimetypes.types_map[media_type]
        except Exception as ex:
            content_type = "text/plain; err " + str(ex)
        media_type = media_type.replace(".", "")

        target_folder = os.path.join(request.folder, 'static')
        # target_folder='static'
        target_folder = os.path.join(target_folder, 'documents')
        target_folder = os.path.join(target_folder, prefix)
        fname = os.path.join(target_folder, document_id)
        save_fname = title + "." + media_type
        message = "Downloading " + fname
        response.headers['Content-Type'] = content_type
        try:
            return response.stream(open(fname, 'rb'), chunk_size=10 ** 6, request=request,
                                   attachment=True, filename=save_fname)  # , headers=None)
        except Exception as ex:
            message = "Invalid File " + fname + " " + str(ex)
            pass
    else:
        document_id = ""

    return dict(message=message)


def player():
    ret = ""  # start_process_videos()
    
    poster = URL('static', 'images') + 'media_file.png'
    source_ogg = ""
    source_mp4 = ""
    source_mobile_mp4 = ""
    source_webm = ""

    # This will be the rendered <track> tags
    subtitles_html = ""
   
    
    width = '640'  # '720' ,'640'
    height = '385'  # '433' ,'385'
    iframe_width = '650'  # '650'
    iframe_height = '405'  # '405'
    views = 0
    
    title = ""
    description = ""
    category = ""
    tags = ""
    youtube_url = ""
    # default to off
    autoplay = "false"
    if request.vars.autoplay == "true":
        # options for autoplay w videojs are:
        # any - try autoplay, then fall back to play muted
        # true - autoplay
        # play - run play() onload
        # muted - play muted
        autoplay = "any"
    
    is_mobile = request.vars.get('m', 'false')
    
    movie_id = request.args(0)
    if movie_id is not None:
        movie_id = movie_id.strip()
        # Load the movie from the database
        prefix = movie_id[0:2]
        poster = getMediaPoster(movie_id) # URL('static', 'media' + "/" + prefix + "/" + movie_id + ".poster.png")
        source_ogg = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".ogv")
        if is_mobile == "true":
            source_mp4 = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".mobile.mp4")
        else:
            source_mp4 = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".mp4")
        source_mobile_mp4 = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".mobile.mp4")
        source_webm = URL('static', 'media' + "/" + prefix + "/" + movie_id + ".webm")

        # Get list of vtt files
        vtt_files = get_media_captions_list(movie_id)
        
        # Build up the <tracks> tags
        for f in vtt_files:
            #<track kind="captions" src="source_en_subtitles"" srclang="en" label="English" default>
            default_txt = ""
            if f == "en":
                default_txt = "default"
            subtitles_html += "\n<track kind=\"captions\" src=\"" + \
                URL('static', 'media' + "/" + prefix + "/" + movie_id + "_" + f + ".vtt") \
                + "\" srclang=\"" + f + "\" label=\"" + vtt_files[f][1] + "\" " + default_txt + ">"

        
        media_file = db(db.media_files.media_guid==movie_id).select().first()
        if media_file is not None:
            title = media_file.title
            description = media_file.description
            category = media_file.category
            tags = ",".join(media_file.tags)
            views = media_file.views
            youtube_url = media_file.youtube_url
            if youtube_url is None:
                youtube_url = ""
            if views is None:
                views = 0
            db(db.media_files.media_guid == movie_id).update(views=views+1)
            db.commit()
        pass
    else:
        movie_id = ""
    
    return dict(poster=poster, source_ogg=source_ogg, source_mp4=source_mp4,
                source_mobile_mp4=source_mobile_mp4, source_webm=source_webm,
                movie_id=movie_id, width=width, height=height, title=title,
                description=description, tags=tags, autoplay=autoplay,
                iframe_width=iframe_width, iframe_height=iframe_height, views=views,
                category=category, youtube_url=youtube_url,
                subtitles_html=subtitles_html )


def view_document():
    width = '100%'  # '724'  # '640'  # '720' ,'640'
    height = '700'  # '385'  # '433' ,'385'
    iframe_width = '100%'  # '734'  # '650'
    iframe_height = '720'  # '405'
    views = 0

    title = ""
    description = ""
    tags = ""
    original_file_name = ""
    # default to off

    document_id = request.args(0)
    if document_id is not None:
        document_id = document_id.strip()
        # Load the doc from the database
        prefix = document_id[0:2]
        poster = getDocumentThumb(document_id)  # URL('static', 'media' + "/" + prefix + "/" + movie_id + ".poster.png")
        # source_doc = URL('static', 'documents/' + prefix + "/" + document_id)
        source_doc = URL('media', 'dl_document/' + document_id)

        document_file = db(db.document_files.document_guid == document_id).select().first()
        if document_file is not None:
            title = document_file.title
            description = document_file.description
            tags = ",".join(document_file.tags)
            original_file_name = document_file.original_file_name
            views = document_file.views
            if views is None:
                views = 0
            db(db.document_files.document_guid == document_id).update(views=views + 1)
        pass
    else:
        document_id = ""

    can_preview = False
    is_image = False
    dl_link = A('Download', _href=URL('media', 'dl_document', args=[document_id]))
    preview_extensions = ["pdf", "odt", "fodt", "ott", "odp", "fodp", "otp", "ods", "fods", "ots"]
    image_extensions = ["jpg", "png", "gif"]

    p, media_type = os.path.splitext(original_file_name)
    media_type = media_type.replace(".", "").lower()

    if media_type in preview_extensions:
        can_preview = True
    if media_type in image_extensions:
        is_image = True

    return dict(source_doc=source_doc, poster=poster,
                document_id=document_id, width=width, height=height, title=title,
                description=description, tags=tags,
                iframe_width=iframe_width, iframe_height=iframe_height, views=views,
                can_preview=can_preview, is_image=is_image, dl_link=dl_link)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators') or
               auth.has_membership('Media Upload'))
def upload_media():
    ret = start_process_videos()
    
    # rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.media_file_import_queue, showid=False,
                   fields=['title', 'description', 'category', 'tags', 'youtube_url', 'media_file' ],
                   _name="queue_media").process(formname="queue_media")

    if form.accepted:
        # Saved
        new_id = form.vars.id
        original_file_name = form.vars.media_file
        db(db.media_file_import_queue.id == new_id).update(original_file_name=original_file_name)
        db.commit()
        result = scheduler.queue_task('process_media_file', pvars=dict(media_id=new_id), timeout=18000,
                                      immediate=True, sync_output=5, group_name="process_videos")
        response.flash = "Media File Queued!"  # + str(result)
        pass
    elif form.errors:
        response.flash = "Error! "  # + str(form.errors)
    else:
        # response.flash = "Process Queue: " + str(ret)
        pass

    ret = ""
    return dict(form=form, ret=ret)


@auth.requires(auth.has_membership('Faculty') or
               auth.has_membership('Administrators') or auth.has_membership('Media Upload'))
def upload_document():
    last_doc = ""
    w2py_folder = request.env.web2py_path
    app_folder = os.path.join(w2py_folder, "applications", "smc")

    form = SQLFORM(db.document_import_queue, showid=False,
                   fields=['title', 'description', 'category', 'tags', 'document_file'],
                   _name="queue_document").process(formname="queue_document")

    if form.accepted:
        # Saved
        new_id = form.vars.id
        original_file_name = form.vars.document_file
        db(db.document_import_queue.id == new_id).update(original_file_name=original_file_name)
        db.commit()
        document_file = db(db.document_import_queue.id == new_id).select().first()

        # Copy the file to the documents folder
        tmp_path = db.document_import_queue.document_file.retrieve_file_properties(
            db.document_import_queue(new_id).document_file)['path']
        # NOTE Has stupid databases/../uploads in the path, replace databases/../ with nothing
        tmp_path = tmp_path.replace("\\", "/").replace('databases/../', '')
        uploads_folder = os.path.join(w2py_folder, tmp_path)
        input_file = os.path.join(uploads_folder, document_file.document_file).replace("\\", "/")

        file_guid = document_file.document_guid.replace('-', '')

        target_folder = os.path.join(app_folder, 'static')

        target_folder = os.path.join(target_folder, 'documents')

        file_prefix = file_guid[0:2]

        target_folder = os.path.join(target_folder, file_prefix)
        target_file = os.path.join(target_folder, file_guid).replace("\\", "/")

        try:
            os.makedirs(target_folder)
        except OSError as message:
            pass

        # Copy the file
        try:
            shutil.copyfile(input_file, target_file)
        except Exception as ex:
            err = "ERROR COPYING FILE! " + str(ex)

        db.document_files.insert(title=document_file.title,
                                 document_guid=document_file.document_guid.replace('-', ''),
                                 description=document_file.description,
                                 original_file_name=document_file.original_file_name,
                                 media_type=document_file.media_type,
                                 category=document_file.category,
                                 tags=document_file.tags,
                                 )

        # media_file.update(status='done')
        db(db.document_import_queue.id == new_id).delete()

        db.commit()

        # Dump meta data to the folder along side the files
        # This can be used for export/import
        meta = {'title': document_file.title, 'document_guid': document_file.document_guid.replace('-', ''),
                'description': document_file.description, 'original_file_name': document_file.original_file_name,
                'media_type': document_file.media_type, 'category': document_file.category,
                'tags': dumps(document_file.tags)}

        meta_json = dumps(meta)
        #f = os.open(target_file + ".json", os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        #os.write(f, meta_json)
        #os.close(f)
        f = open(target_file + ".json", "w")
        f.write(meta_json)
        f.close()

        last_doc = A(document_file.title, _href=URL('media', 'view_document', args=[file_guid]))

        response.flash = "Document Uploaded"  # + str(result)
        pass
    elif form.errors:
        response.flash = "Error! "  # + str(form.errors)
    else:
        # response.flash = "Process Queue: " + str(ret)
        pass

    ret = ""
    return dict(form=form, ret=ret, last_doc=last_doc)


@auth.requires(auth.has_membership('Faculty') or
               auth.has_membership('Administrators') or
               auth.has_membership('Media Upload'))
def multi_upload_media():
    ret = start_process_videos()
    
    # rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.media_file_import_queue, showid=False,
                   fields=['title', 'description', 'category', 'tags', 'media_file'],
                   _name="queue_media").process(formname="queue_media")

    if form.accepted:
        # Saved
        new_id = form.vars.id
        original_file_name = form.vars.media_file
        db(db.media_file_import_queue.id==new_id).update(original_file_name=original_file_name)
        db.commit()
        result = scheduler.queue_task('process_media_file', pvars=dict(media_id=new_id),
                                      timeout=18000, immediate=True, sync_output=5, group_name="process_videos")
        response.flash = "Media File Queued!"  # + str(result)
        pass
    elif form.errors:
        response.flash = "Error! "  # + str(form.errors)
    else:
        # response.flash = "Process Queue: " + str(ret)
        pass

    ret = ""
    return dict(form=form, ret=ret)


@auth.requires(auth.has_membership('Faculty') or
               auth.has_membership('Administrators') or
               auth.has_membership('Media Upload'))
def upload_ajax_callback():
    return response.json({'success': 'true'})


@auth.requires(auth.has_membership('Faculty') or
               auth.has_membership('Administrators') or
               auth.has_membership('Media Upload'))
def process_queue():
    ret = start_process_videos()
    
    query = (db.media_file_import_queue)
    fields = [db.media_file_import_queue.title, db.media_file_import_queue.status,
              db.media_file_import_queue.modified_on,  db.media_file_import_queue.id,
              db.media_file_import_queue.media_guid]
    links = [
            (dict(header=T('Title'), body=lambda row: A(row.title,
                                                        _href=(URL('media', 'player', extension=False) + "/"
                                                               + row.media_guid), _target='blank'))),
            (dict(header=T('Status'), body=lambda row: DIV(getTaskStatus(row.id), BR(), A('Re-Queue',
                 _href=URL('media', 'reset_queued_item', args=[row.id], user_signature=True))))),
            (dict(header=T('Queued On'), body=lambda row: row.modified_on)),
            (dict(header=T('Progress'), body=lambda row: getTaskProgress(row.id))),
            ]
    
    db.media_file_import_queue.id.readable = False
    db.media_file_import_queue.media_guid.readable = False
    db.media_file_import_queue.modified_on.readable = True
    db.media_file_import_queue.status.readable = False
    db.media_file_import_queue.title.readable = False
    db.media_file_import_queue.modified_on.readable = False
    headers = {'media_file_import_queue.modified_on': 'Queued On'}
    
    maxtextlengths = {'media_file_import_queue.title': 80, 'media_file_import_queue.media_guid': 80}
    
    # rows = db(query).select()
    process_grid = SQLFORM.grid(query, editable=False, create=False, deletable=True, csv=False,
                                links=links, links_in_grid=True, details=False, searchable=False,
                                orderby=[~db.media_file_import_queue.modified_on], fields=fields,
                                headers=headers, maxtextlengths=maxtextlengths)
    return dict(process_grid=process_grid)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators') or auth.has_membership('Media Upload'))
def reset_queued_item():
    ret = start_process_queue()
    media_id = request.args(0)
    
    if media_id > 0:
        # Kill any existing tasks
        q1 = '{"media_id": "' + str(media_id) + '"}'
        q2 = '{"media_id": ' + str(media_id) + '}'
        db_scheduler((db_scheduler.scheduler_task.vars==q1) | (db_scheduler.scheduler_task.vars==q2)).delete()
        # Start a new task
        result = scheduler.queue_task('process_media_file', pvars=dict(media_id=media_id),
                                      timeout=18000, immediate=True, sync_output=5, group_name="process_videos")
        response.flash = "Media File Queued!"  # + str(result)
    redirect(URL('media', 'upload_media.html'))


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def delete_media():
    media_guid = request.args(0)
    if media_guid is None:
        redirect(URL('media', 'index'))
        return None
    media_file = db(db.media_files.media_guid==media_guid).select().first()
    if media_file is None:
        redirect(URL('media', 'index'))
        return None
    media_title = media_file.title
    delete_button = SQLFORM.factory(submit_button="Delete Media File",
                                    _name="delete_media_file").process(formname="delete_media_file")
    
    if delete_button.accepted:
        # Delete DB entries
        db(db.media_files.media_guid==media_guid).delete()
        # Remove files
        file_prefix = media_guid[0:2]
        target_folder = os.path.join(request.folder, 'static')
        target_folder = os.path.join(target_folder, 'media')
        target_folder = os.path.join(target_folder, file_prefix)
        
        try:
            os.remove(os.path.join(target_folder, media_guid + ".webm"))
        except OSError:
            pass
        try:
            os.remove(os.path.join(target_folder, media_guid + ".ogv"))
        except OSError:
            pass
        try:
            os.remove(os.path.join(target_folder, media_guid + ".mp4"))
        except:
            pass
        try:
            os.remove(os.path.join(target_folder, media_guid + ".mobile.mp4"))
        except:
            pass
        try:
            os.remove(os.path.join(target_folder, media_guid + ".json"))
        except:
            pass
        try:
            os.remove(os.path.join(target_folder, media_guid + ".poster.png"))
        except:
            pass
        try:
            os.remove(os.path.join(target_folder, media_guid + ".thumb.png"))
        except:
            pass
        
        response.flash = "Media File Deleted"  # + str(ret)
        redirect(URL('media', 'index'))
        return None
    
    return dict(media_title=media_title, delete_button=delete_button)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def delete_document():
    document_guid = request.args(0)
    if document_guid is None:
        redirect(URL('media', 'documents'))
        return None
    document_file = db(db.document_files.document_guid == document_guid).select().first()
    if document_file is None:
        redirect(URL('media', 'documents'))
        return None
    document_title = document_file.title
    delete_button = SQLFORM.factory(submit_button="Delete Document",
                                    _name="delete_document_file").process(formname="delete_document_file")

    if delete_button.accepted:
        # Delete DB entries
        db(db.document_files.document_guid == document_guid).delete()
        # Remove files
        file_prefix = document_guid[0:2]
        target_folder = os.path.join(request.folder, 'static')
        target_folder = os.path.join(target_folder, 'documents')
        target_folder = os.path.join(target_folder, file_prefix)

        try:
            os.remove(os.path.join(target_folder, document_guid))
        except OSError:
            pass
        try:
            os.remove(os.path.join(target_folder, document_guid + ".json"))
        except:
            pass
        try:
            os.remove(os.path.join(target_folder, document_guid + ".thumb.png"))
        except:
            pass

        response.flash = "Document File Deleted"  # + str(ret)
        redirect(URL('media', 'documents'))
        return None

    return dict(document_title=document_title, delete_button=delete_button)


def wmplay():    
    poster = ""  # URL('static', 'projekktor-1.3.09') + '/media/intro.png'
    source_ogg = URL('static', 'projekktor-1.3.09') + '/media/intro.ogv'
    source_mp4 = URL('static', 'projekktor-1.3.09') + '/media/intro.mp4'
    source_mobile_mp4 = URL('static', 'projekktor-1.3.09') + '/media/intro.mp4'
    source_webm = URL('static', 'projekktor-1.3.09') + '/media/intro.webm'
    
    width = '640'  # '720' ,'640'
    height = '385'  # '433' ,'385'
    iframe_width = '650'  # '650'
    iframe_height = '405'  # '405'
    views = 0
    
    title = ""
    description = ""
    tags = ""
    autoplay = "false"
    if request.vars.autoplay == "true":
        autoplay = "true"
    
    is_mobile = request.vars.get('m', 'false')
    
    movie_id = request.args(0)
    if movie_id is not None:
        # Load the movie from the database
        source_mp4 = URL('static', 'media/wamap/wamap_' + str(movie_id) + ".mp4")
    else:
        movie_id = ""
    
    return dict(poster=poster, source_ogg=source_ogg, source_mp4=source_mp4, source_mobile_mp4=source_mobile_mp4,
                source_webm=source_webm, movie_id=movie_id, width=width, height=height, title=title,
                description=description, tags=tags, autoplay=autoplay, iframe_width=iframe_width,
                iframe_height=iframe_height)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def wamap_import():
    # Number of new vids found
    new_vids = 0
    
    download_wamap = SQLFORM.factory(submit_button="Run WAMAP Import Tool",
                                     _name="download_wamap").process(formname="download_wamap")
    
    result = None
    if download_wamap.accepted:
        result = find_wamap_videos()  # wamap_import_run()
        response.flash = "WAMAP download started - videos being processed."  # + str(ret)
    
    return dict(download_wamap=download_wamap, wamap_rows=new_vids)


def fix_previous_wamap_import_video_links():
    # Put previous wamap import video links back
    changed = []
    changed_count = 0
    db_wamap = DAL('mysql://smc:aaaaaaa!!@wamap.correctionsed.com/imathsdb')
    
    rows = db(db.wamap_questionset).select()
    for row in rows:
        # Update extref fields back to original if they contain admin.correctionsed.com/wamap/
        sql = "UPDATE imas_questionset SET extref='" + row.extref_field + "' WHERE id='" + \
              str(row.wamap_id) + "' and extref LIKE '%admin.correctionsed.com/media/wamap/%'"
        db_wamap.executesql(sql)
        changed.append(sql)
    
    db_wamap.close()
    
    # Run a delete scheduler so that it removes the old files
    result = scheduler.queue_task('remove_old_wamap_video_files', timeout=18000, repeats=1,
                                  period=0, immediate=True, sync_output=5, group_name="wamap_delete")
    
    # Start the scheduler process
    ret = start_process_queue_wamap_delete()
    
    return changed


def find_wamap_videos():
    # Make sure we put old links back
    ret = fix_previous_wamap_import_video_links()
    ret = []  # Clear so we don't return changed array
    
    # Check for videos that have already been downloaded and make sure the links are added in the
    # database
    # Starts in the Controllers folder
    w2py_folder = os.path.abspath(__file__)
    # print "Running File: " + app_folder
    w2py_folder = os.path.dirname(w2py_folder)
    # app folder
    w2py_folder = os.path.dirname(w2py_folder)
    app_folder = w2py_folder
    # Applications folder
    w2py_folder = os.path.dirname(w2py_folder)
    # Root folder
    w2py_folder = os.path.dirname(w2py_folder)
    # print "W2Py Folder: " + w2py_folder
    
    # Ensure the wamap folder exists
    wamap_folder = os.path.join(app_folder, "static")
    wamap_folder = os.path.join(wamap_folder, "media")
    wamap_folder = os.path.join(wamap_folder, "wamap")
    pdfs_folder = os.path.join(wamap_folder, "pdfs")
    
    if os.path.isdir(wamap_folder) is not True:
        os.mkdir(wamap_folder)
    if os.path.isdir(pdfs_folder) is not True:
        os.mkdir(pdfs_folder)
    
    # Get a list of link files
    os.chdir(wamap_folder)
    links = glob.glob("*.link")
    offline_update_vids_imported = 0
    offline_update_ret = ""
    offline_update_vid_count = len(links)
    for link in links:
        ret.append(link)
        # See if this item is in the database
        p = os.path.join(wamap_folder, link)
        try:
            json_data = open(p).read()
            dat = loads(json_data)
            v = db(db.wamap_videos.source_url==dat["yt_url"]).select().first()
            if v is None:
                db.wamap_videos.insert(source_url=dat["yt_url"], media_guid=dat["media_guid"], new_url='')
                offline_update_vids_imported += 1
                offline_update_ret += " Link inserted: " + dat["yt_url"]
            else:
                offline_update_ret += " Link exists: " + dat["yt_url"]
                # If link exists, make sure the guid matches the link file in case it generated a new guid
                db(db.wamap_videos.source_url==dat["yt_url"]).update(media_guid=dat["media_guid"])
            db.commit()
        except:
            offline_update_ret += " Error reading link: " + dat["yt_url"]
            pass
    
    db.commit()
    
    # Look for for video files in the wamap db tables
    vid_count = 0
    duplicates = 0
    
    db_wamap = DAL('mysql://smc:aaaaaaa!!@wamap.correctionsed.com/imathsdb')
    
    # Fix a few links that are incorrect
    # youtube link w out the http:// in imas_questionset.extref
    db_wamap.executesql("UPDATE imas_questionset SET " +
                        "`extref`=REPLACE(`extref`, 'video!!www.yout', 'video!!http://www.yout') " +
                        " WHERE `extref` like '%video!!www.yout%' ")

    # Adjust IFrame links in some places so they match up better with videos
    # <iframe src="https://admin.correctionsed.com/media/wmplay/45390ef384be4107a7bf2c2da31ce79a"
    #  width="560" height="315">
    # Change out 560x315 and 420x315 for ---> 655x410
    # fix iframe src w // instad of http://
    # imas_inlinetext.text
    table_name = "imas_inlinetext"
    col_name = "text"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name +
                        "` like '%src=\"//www.yout%' ")
    # imas_questionset.qtext
    table_name = "imas_questionset"
    col_name = "qtext"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name +
                        "` like '%src=\"//www.yout%' ")
    # imas_questionset.extref
    table_name = "imas_questionset"
    col_name = "extref"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name +
                        "` like '%src=\"//www.yout%' ")
    # imas_questionset.control
    table_name = "imas_questionset"
    col_name = "control"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name +
                        "` like '%src=\"//www.yout%' ")
    # imas_assessments.intro
    table_name = "imas_assessments"
    col_name = "intro"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name +
                        "` like '%src=\"//www.yout%' ")
    # imas_linkedtext.summary
    table_name = "imas_linkedtext"
    col_name = "summary"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name +
                        "` like '%src=\"//www.yout%' ")
    # imas_linkedtext.text
    table_name = "imas_linkedtext"
    col_name = "text"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name +
                        "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name +
                        "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name +
                        "` like '%src=\"//www.yout%' ")
    
    db_wamap.commit()
    
    # Get a list of link files for PDFS
    os.chdir(pdfs_folder)
    links = glob.glob("*.link")
    offline_update_pdfs_imported = 0
    offline_pdf_update_ret = ""
    offline_update_pdf_count = len(links)
    for link in links:
        ret.append(link)
        # See if this item is in the database
        p = os.path.join(pdfs_folder, link)
        try:
            json_data=open(p).read()
            dat = loads(json_data)
            v = db(db.wamap_pdfs.source_url==dat["source_url"]).select().first()
            if v is None:
                db.wamap_pdfs.insert(source_url=dat["source_url"], media_guid=dat["media_guid"], new_url='')
                offline_update_pdfs_imported += 1
                offline_pdf_update_ret += " Link inserted: " + dat["source_url"]
            else:
                offline_pdf_update_ret += " Link exists: " + dat["source_url"]
                # If link exists, make sure the guid matches the link file in case it generated a new guid
                db(db.wamap_pdfs.source_url==dat["source_url"]).update(media_guid=dat["media_guid"])
            db.commit()
        except:
            offline_pdf_update_ret += " Error reading link: " + dat["source_url"]
            pass
    
    db.commit()

    # Pull PDF links
    pdf_url_list = []
    # Pull pdfs from imas_questionset.extref
    rows = db_wamap.executesql("select id, extref from imas_questionset where extref like '%pdf%' ")
    for row in rows:
        urls = getPDFURLS(row[1])
        pdf_url_list.extend(urls)
    
    # Pull pdfs from imas_questionset.control
    rows = db_wamap.executesql("select id, control from imas_questionset where control like '%pdf%' ")
    for row in rows:
        urls = getPDFURLS(row[1])
        pdf_url_list.extend(urls)
    
    # Pull pdfs from imas_questionset.qtext
    rows = db_wamap.executesql("select id, qtext from imas_questionset where qtext like '%pdf%' ")
    for row in rows:
        urls = getPDFURLS(row[1])
        pdf_url_list.extend(urls)
    
    # Pull pdfs from imas_inlinetext.text
    rows = db_wamap.executesql("select id, `text` from imas_inlinetext where `text` like '%pdf%' ")
    for row in rows:
        urls = getPDFURLS(row[1])
        pdf_url_list.extend(urls)
    
    # Pull pdfs from imas_assessments.intro
    rows = db_wamap.executesql("select id, intro from imas_assessments where intro like '%pdf%' ")
    for row in rows:
        urls = getPDFURLS(row[1])
        pdf_url_list.extend(urls)
    
    # Pull pdfs from imas_linkedtext.summary
    rows = db_wamap.executesql("select id, summary from imas_linkedtext where summary like '%pdf%' ")
    for row in rows:
        urls = getPDFURLS(row[1])
        pdf_url_list.extend(urls)
    
    # Pull pdfs from imas_linkedtext.text
    rows = db_wamap.executesql("select id, `text` from imas_linkedtext where `text` like '%pdf%' ")
    for row in rows:
        urls = getPDFURLS(row[1])
        pdf_url_list.extend(urls)
    
    # Add the pdfs into our wamap_pdfs table if they don't already exist
    new_pdfs = 0
    pdf_duplicates = 0
    for u in pdf_url_list:
        v = db(db.wamap_pdfs.source_url==u).select().first()
        if v is None:
            new_pdfs += 1
            db.wamap_pdfs.insert(source_url=u, media_guid=str(uuid.uuid4()).replace('-', ''), new_url='')
        else:
            pdf_duplicates += 1
    # Clear the processed flag so they all get checked
    db(db.wamap_pdfs).update(downloaded=False)
    db.commit()
    
    url_list = []
    
    # Pull videos from imas_questionset.extref
    rows = db_wamap.executesql("select id, extref from imas_questionset where extref like '%youtu%' ")
    for row in rows:
        urls = getURLS(row[1])
        url_list.extend(urls)
    
    # Pull videos from imas_questionset.control
    rows = db_wamap.executesql("select id, control from imas_questionset where control like '%youtu%' ")
    for row in rows:
        urls = getURLS(row[1])
        url_list.extend(urls)
    
    # Pull videos from imas_questionset.qtext
    rows = db_wamap.executesql("select id, qtext from imas_questionset where qtext like '%youtu%' ")
    for row in rows:
        urls = getURLS(row[1])
        url_list.extend(urls)
    
    # Pull videos from imas_inlinetext.text
    rows = db_wamap.executesql("select id, `text` from imas_inlinetext where `text` like '%youtu%' ")
    for row in rows:
        urls = getURLS(row[1])
        url_list.extend(urls)
    
    # Pull videos from imas_assessments.intro
    rows = db_wamap.executesql("select id, intro from imas_assessments where intro like '%youtu%' ")
    for row in rows:
        urls = getURLS(row[1])
        url_list.extend(urls)
    
    # Pull videos from imas_linkedtext.summary
    rows = db_wamap.executesql("select id, summary from imas_linkedtext where summary like '%youtu%' ")
    for row in rows:
        urls = getURLS(row[1])
        url_list.extend(urls)
    
    # Pull videos from imas_linkedtext.text
    rows = db_wamap.executesql("select id, `text` from imas_linkedtext where `text` like '%youtu%' ")
    for row in rows:
        urls = getURLS(row[1])
        url_list.extend(urls)

    vid_count = len(url_list)
    
    # Get qimages entries so we can download them
    rows = db_wamap.executesql("select id, qsetid, var, filename, alttext from `imas_qimages`")
    for row in rows:
        qi = db(db.wamap_qimages.source_id==row[0]).select().first()
        if qi is None:
            # Entry isn't there, insert it
            db.wamap_qimages.insert(source_id=row[0],
                                    source_qsetid=row[1],
                                    source_var=row[2],
                                    source_filename=row[3],
                                    source_alttext=row[4],
                                    downloaded=False
                )
        else:
            # Entry is there, update it
            db(db.wamap_qimages.source_id==row[0]).update(
                source_qsetid=row[1],
                source_var=row[2],
                source_filename=row[3],
                source_alttext=row[4],
                downloaded=False)
        db.commit()
    rows = None
    
    db_wamap.close()
    
    # Start the task to download the qimages
    result = scheduler.queue_task('download_wamap_qimages', timeout=18000, repeats=1, period=0, immediate=True,
                                  sync_output=5, group_name="wamap_videos")

    new_vids = 0
    
    # Add the videos into our wamap_videos table if they don't already exist
    for u in url_list:
        v = db(db.wamap_videos.source_url==u).select().first()
        if v is None:
            new_vids += 1
            db.wamap_videos.insert(source_url=u, media_guid=str(uuid.uuid4()).replace('-', ''), new_url='')
        else:
            duplicates += 1
    # Clear the processed flag so they all get checked
    db(db.wamap_videos).update(downloaded=False)
        
    # Start the task to download youtube videos and update links
    result = scheduler.queue_task('process_wamap_video_links', timeout=18000,
                                  repeats=(db(db.wamap_videos).count()/50)+1, period=0, immediate=True,
                                  sync_output=5, group_name="wamap_videos")
    
    db.commit()
    
    # Start the scheduler process
    start_wamap_videos()
    
    url_list = []  # Clear so we don't see debug info
    
    return locals()


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def utilities():
    # Just a landing page
    return dict()


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def yt_requeue():
    """
        Re-queue any failed youtube video downloads - good for dealing with 429 failures
    :return:
    """
    msg = ""

    # Get a list of media files w yt links
    media_files = db((db.media_files.youtube_url is not None) &
                     (db.media_files.youtube_url is not False) &
                     (db.media_files.youtube_url != "")).select()
    for m in media_files:
        file_guid = m["media_guid"]
        if is_media_file_present(file_guid) is not True:
            # Media file isn't here? Re-schedule the task
            msg += "Re-queue missing YT File : " + m["youtube_url"] + " <br />"
            result = scheduler.queue_task('pull_youtube_video', pvars=dict(yt_url=m["youtube_url"],
                                                                           media_guid=file_guid
                                                                           ),
                                          timeout=18000, immediate=True, sync_output=3,
                                          group_name="download_videos", retry_failed=30, period=300)

        if is_media_captions_present(file_guid) is not True:
            # Re-queue captions
            msg += "Re-queue missing YT Captions : " + m["youtube_url"] + " <br />"
            result = scheduler.queue_task('pull_youtube_caption', pvars=dict(yt_url=m["youtube_url"],
                                                                            media_guid=file_guid
                                                                            ),
                                            timeout=18000, immediate=True, sync_output=3,
                                            group_name="download_videos", retry_failed=30, period=300)


    response.flash = "YouTube downloads re-queued."
    return dict(msg=XML(msg))


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def scan_media_files():
    # Find all media files and make sure they are in the database.
    form = SQLFORM.factory(submit_button="Import Media/Document Files", _name="run_import").process(
        formname="run_import")
    if form.accepted:
        # Look for videos
        result = scheduler.queue_task('update_media_database_from_json_files', pvars=dict(), timeout=18000,
                                      immediate=True, sync_output=5, group_name="process_videos")
        # Look for documents
        result = scheduler.queue_task('update_document_database_from_json_files', pvars=dict(), timeout=18000,
                                      immediate=True, sync_output=5, group_name="process_videos")
        response.flash = "Import process started!"  # + str(result)

    return dict(form=form)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def wamap_import_run():
    result = find_wamap_videos()  # wamap_import_run()
    return True
    
    # DEPRECATED - use find_wamap_videos
 
    # Number of new vids found
    new_vids = 0
    
    db_wamap = DAL('mysql://smc:aaaaaaa!!@wamap.correctionsed.com/imathsdb')
    rows = db_wamap.executesql("select id, extref from imas_questionset where extref != ''")
    for row in rows:
        # Add each of these rows to the wamap videos queue
        v = db(db.wamap_questionset.wamap_id==row[0]).select().first()
        if v is None:
            # Doesn't exist yet
            new_vids += 1
            db.wamap_questionset.insert(wamap_id=row[0], extref_field=row[1])
    db_wamap.close()
    
    # Start the task to download youtube videos
    db(db.wamap_questionset).update(processed=False)
    result = scheduler.queue_task('process_wamap_video_links', timeout=18000,
                                  repeats=(db(db.wamap_questionset).count()/50), period=0, immediate=True)
        
    return dict(new_vids=new_vids)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def wamap_import_status():
    # Number of new vids found
    new_vids = 0
    
    processed_vids = db(db.wamap_videos.downloaded==True).count()
    total_vids = db(db.wamap_videos).count()
    process_status = str(processed_vids) + " of " + str(total_vids) + " videos processed."
    return dict(process_status=process_status)


def start_process_queue():
    return "Deprecated"
    # Start the worker process
    cmd = "/usr/bin/nohup /usr/bin/python " + os.path.join(request.folder, 'static/scheduler/start_scheduler.py') + \
          " > /dev/null 2>&1 &"
    p = subprocess.Popen(cmd, shell=True, close_fds=True)
    ret = ""
    # ret = p.wait()
    # ret = p.communicate()[0]
    # p.wait()
    # time.sleep(2)
    # p.kill()
    # ret = ""
    return ret


def start_process_queue_wamap_delete():
    # Start the worker process
    # cmd = "/usr/bin/nohup /usr/bin/python " + \
    # os.path.join(request.folder, 'static/scheduler/start_wamap_delete_scheduler.py') + " > /dev/null 2>&1 &"
    # p = subprocess.Popen(cmd, shell=True, close_fds=True)
    ret = ""
    # ret = p.wait()
    # ret = p.communicate()[0]
    # p.wait()
    # time.sleep(2)
    # p.kill()
    # ret = ""
    return ret


def start_process_videos():
    # Start the worker process
    # cmd = "/usr/bin/nohup /usr/bin/python " + \
    # os.path.join(request.folder, 'static/scheduler/start_process_video_scheduler.py') + " > /dev/null 2>&1 &"
    # p = subprocess.Popen(cmd, shell=True, close_fds=True)
    ret = ""
    # ret = p.wait()
    # ret = p.communicate()[0]
    # p.wait()
    # time.sleep(2)
    # p.kill()
    # ret = ""
    return ret


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def start_wamap_videos():
    # Start the worker process
    # cmd = "/usr/bin/nohup /usr/bin/python " + \
    # os.path.join(request.folder, 'static/scheduler/start_wamap_videos_scheduler.py') + " > /dev/null 2>&1 &"
    # p = subprocess.Popen(cmd, shell=True, close_fds=True)
    ret = ""
    # ret = p.wait()
    # ret = p.communicate()[0]
    # p.wait()
    # time.sleep(2)
    # p.kill()
    # ret = ""
    return ret


def getMediaThumb(media_guid):
    if media_guid is None or media_guid == "":
        return ""

    prefix = media_guid[0:2]
    url = URL('static', 'media/' + prefix + '/' + media_guid + '.thumb.png')
    thumb = get_media_file_path(media_guid, ".thumb.png")
    if os.path.exists(thumb) is not True:
        url = URL('static', 'images/media_file.png')
    return url


def getDocumentThumb(document_guid):
    if document_guid is None or document_guid == "":
        return ""
    prefix = document_guid[0:2]
    url = URL('static', 'documents/' + prefix + '/' + document_guid + '.thumb.png')
    thumb = get_document_file_path(document_guid, ".thumb.png")

    if os.path.exists(thumb) is not True:
        url = URL('static', 'images/document_file.png')
    return url


def getMediaPoster(media_guid):
    if media_guid is None or media_guid =="":
        return ""
    prefix = media_guid[0:2]
    url = URL('static', 'media/' + prefix + '/' + media_guid + '.poster.png')
    thumb = get_media_file_path(media_guid, ".thumb.png")
    if os.path.exists(thumb) is not True:
        url = URL('static', 'images/media_file.png')
    return url


def getYouTubeTaskStatus(media_guid):
    q1 = '"media_guid": "' + str(media_guid) + '"'
    q2 = '"media_guid": ' + str(media_guid) + ''
    task = db_scheduler(db_scheduler.scheduler_task.vars.contains(q1) |
                        db_scheduler.scheduler_task.vars.contains(q2)).select(
        orderby=db_scheduler.scheduler_task.last_run_time).first()
    ret = "<not run>"
    if task is not None:
        ret = str(task.status) + " (" + str(task.last_run_time) + ")"
    return ret


def getYouTubeTaskProgress(media_guid):
    ret = ""

    q1 = '"media_guid": "' + str(media_guid) + '"'
    q2 = '"media_guid": ' + str(media_guid) + ''
    task = db_scheduler(db_scheduler.scheduler_task.vars.contains(q1) |
                        db_scheduler.scheduler_task.vars.contains(q2)).select(join=db_scheduler.scheduler_run.on(
        db_scheduler.scheduler_task.id == db_scheduler.scheduler_run.task_id),
        orderby=db_scheduler.scheduler_task.last_run_time).first()
    ret = ""
    if task is not None:
        # Get the output from the run record
        ret = str(task.scheduler_run.run_output)

    return ret


def getTaskStatus(media_id):
    q1 = '{"media_id": "' + str(media_id) + '"}'
    q2 = '{"media_id": ' + str(media_id) + '}'
    task = db_scheduler((db_scheduler.scheduler_task.vars==q1) |
                        (db_scheduler.scheduler_task.vars==q2)).select(
                        orderby=db_scheduler.scheduler_task.last_run_time).first()
    ret = "<not run>"
    if task is not None:
        ret = str(task.status) + " (" + str(task.last_run_time) + ")"
    return ret


def getTaskProgress(media_id):
    ret = ""
    
    q1 = '{"media_id": "' + str(media_id) + '"}'
    q2 = '{"media_id": ' + str(media_id) + '}'
    task = db_scheduler((db_scheduler.scheduler_task.vars==q1) |
                        (db_scheduler.scheduler_task.vars==q2)).select(join=db_scheduler.scheduler_run.on(
                         db_scheduler.scheduler_task.id==db_scheduler.scheduler_run.task_id),
                         orderby=db_scheduler.scheduler_task.last_run_time).first()
    ret = ""
    if task is not None:
        # Get the output from the run record
        ret = str(task.scheduler_run.run_output)
    
    return ret


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def conversion():
    # Landing Page
    return dict()


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def pull_from_youtube():
    # Form to pull videos from youtube
    # NOTE - only works when online

    return dict()


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def pull_from_youtube_step_1():
    form = FORM(TABLE(TR("YouTube Link: ", INPUT(_type="text", _name="yt_url", requires=IS_NOT_EMPTY())),
                      TR("", INPUT(_type="submit", _value="Next"))), keepvalues=True, _name="yt_step1")

    if form.process(formname="yt_step1").accepted:
        yt_url = form.vars.yt_url

        if yt_url is None:
            response.flash = "Invalid YouTube URL"
            return dict(form1=form)

        # Check if this video exists in the database already
        vid = db(db.media_files.youtube_url==yt_url).select().first()
        if vid is not None:
            # Video exists already
            response.flash = "Video already in SMC!"

            # Pull caption file if it doesn't exist?
            caption_result = scheduler.queue_task('pull_youtube_caption',
                pvars=dict(yt_url=yt_url, media_guid=vid.media_guid),
                timeout=90, immediate=True, sync_output=2,
                group_name="download_videos", retry_failed=30, period=300)

        else:
            redirect(URL('media', 'pull_from_youtube_step_2.load', vars=dict(yt_url=yt_url), user_signature=True))
    elif form.errors:
        response.flash = "Form has errors!"

    return dict(form1=form)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def pull_from_youtube_step_2():
    yt_url = request.vars.yt_url
    if yt_url is not None:
        session.yt_url = yt_url
    else:
        yt_url = session.yt_url

    yt = None
    stream = None
    res = ''
    try:
        # Get yt video info
        yt, stream, res = find_best_yt_stream(yt_url)

    except Exception as ex:
        response.flash = "Error getting YouTube Video - Are you online?"  # + str(yt_url) + " " + str(ex)
        return dict(form2=XML("<span style='color: red; font-weight:bold;'>" +
                              "Error Downloading video</span> (" + str(yt_url) +
                              ") - reload page and try again.<br /> " +
                              "<span style='font-size: 10px; font-weight: bold;'>" +
                              "Error: " +
                              str(ex) + "</span>"))

    if yt is None:
        return dict(form2=XML("<span style='color: red; font-weight:bold;'>" +
                              "Error finding video</span> (" + str(yt_url) +
                              ") - reload page and try again.<br /> " +
                              "<span style='font-size: 10px; font-weight: bold;'>" +
                              "Error: yt is none! Unable to get yt info for link " +
                              str(yt) + "/" + str(stream) + "/" + str(res) + "</span>"))

    # NOTE - Need form name separate from other steps for form to work properly
    form = FORM(TABLE(TR("YouTube Link:", INPUT(_type="text", _name="yt_url", _value=yt_url, _readonly=True)),
                      TR("Title:", INPUT(_type="text", _name="title", _value=yt.title, requires=IS_NOT_EMPTY())),
                      TR("Description:", TEXTAREA(_name="desc", value=yt.description)),
                      TR("Category:", INPUT(_type="text", _name="category")),
                      # TR("Keywords:", INPUT(_type="text", _name="keywords", value=    yt.keywords)),
                      TR("", INPUT(_type="submit", _value="Download"))),
                # INPUT(_type="hidden", _value=res, _name="res"),
                # INPUT(_type="hidden", _value=yt.thumbnail_url, _name="thumbnail_url"),
                # hidden=dict(res=res, thumbnail_url=yt.thumbnail_url),
                keepvalues=True, _name="yt_step2",
                _action=URL('media', 'pull_from_youtube_step_2.load', user_signature=True))

    if form.process(formname="yt_step2").accepted:
        # Start download or get current db entry for this video
        # media_file = queue_up_yt_video(yt_url, yt, res, form.vars.category)
        media_file = queue_up_yt_video(yt_url, form.vars.category)
        # Override the values we collected
        media_file.update_record(title=form.vars.title, description=form.vars.desc, category=form.vars.category)
        db.commit()

        response.flash = 'Video queued for download.'  # + str(result)

        # Show a start over button
        form = A('Download another video', _href=URL('media', 'pull_from_youtube.html   '))
    elif form.errors:
        response.flash = "ERROR " + str(form.errors)
    else:
        # response.flash = "Input your desired info and download the video."
        pass

    return dict(form2=form)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def pull_from_youtube_download_queue():

    query = (db.media_files.youtube_url != "")
    fields = [db.media_files.title, db.media_files.needs_downloading,
              db.media_files.modified_on, db.media_files.id,
              db.media_files.media_guid]
    links = [
        (dict(header=T('Title'), body=lambda row: A(row.title,
                                                    _href=(URL('media', 'player', extension=False) + "/"
                                                           + row.media_guid), _target='blank'))),
        (dict(header=T('Status'), body=lambda row: DIV(getYouTubeTaskStatus(row.media_guid), ))),  # BR(), A('Re-Queue',
                                                                              #        _href=URL('media',
                                                                              #                  'reset_queued_item',
                                                                              #                  args=[row.id],
                                                                              #                  user_signature=True))))),
        (dict(header=T('Queued On'), body=lambda row: row.modified_on)),
        # Check if getTaskProgress is generic enough for this too?
        (dict(header=T('Progress'), body=lambda row: getYouTubeTaskProgress(row.media_guid))),
    ]

    db.media_files.id.readable = False
    db.media_files.media_guid.readable = False
    db.media_files.modified_on.readable = True
    db.media_files.needs_downloading.readable = False
    db.media_files.title.readable = False
    db.media_files.modified_on.readable = False
    headers = {'media_files.modified_on': 'Queued On'}

    maxtextlengths = {'media_files.title': 80, 'media_files.media_guid': 80}

    # rows = db(query).select()
    process_grid = SQLFORM.grid(query, editable=False, create=False, deletable=False, csv=False,
                                links=links, links_in_grid=True, details=False, searchable=False,
                                orderby=[~db.media_files.modified_on], fields=fields,
                                headers=headers, maxtextlengths=maxtextlengths)
    return dict(process_grid=process_grid)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace():
    Canvas.Init()
    server_url = Canvas._canvas_server_url

    # TODO - Force module reload so we don't have to kill python process
    # import module_reload
    # reload_str = ""
    # reload_str = module_reload.ReloadModules()
    # Make sure we init the module
    # Canvas.Init()

    return dict(server_url=server_url)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_step_1():
    # Force canvasinit to rerun
    Canvas.Close()
    Canvas.Init()
    course_list = []
    course_dict = dict()

    if Canvas._canvas_integration_enabled is not True:
        form = "<b style='color: red; font-size: 48px;'>Canvas Integration needs to be Enabled in the admin menu before this tool will work.</b>"
        return dict(form1=XML(form))

    courses = Canvas.get_courses_for_faculty(auth.user.username)

    sorted_course_dict = dict()
    for c in courses:
        sorted_course_dict[courses[c]] = str(c)
        course_dict[str(c)] = courses[c]
    # Sort the keys and add them to the select list
    for k in sorted(sorted_course_dict.keys()):    
        course_list.append(OPTION(str(k), _value=str(sorted_course_dict[k])))

    course_select = SELECT(course_list, _name="current_course", _id="current_course", _style="width: 600px;")

    form = FORM(TABLE(TR("Choose a course: ", course_select),
                      TR("", INPUT(_type="submit", _value="Next"))), _name="fr_step1").process(formname="fr_step1",
                                                                                               keepvalues=True)

    if form.accepted:
        #try:
        # Make sure the course ID is an ID.
        is_id = False
        try:
            c_id = int(form.vars.current_course)
            is_id = True
        except:
            is_id = False
        
        if is_id is True:
            cname = course_dict[str(form.vars.current_course)]
            cid = form.vars.current_course
            redirect(URL("find_replace_step_2.load", vars=dict(current_course=cid,
                                                            current_course_name=cname)))
        else:
            response.flash = "Invalid Course Id! " + str(form.vars.current_course)
        #except Exception as ex:
        #    response.flash="Invalid course id " + str(form.vars.current_course) + str(ex) #+ str(course_dict)
        
        # reload_str = form.vars.current_course

    return dict(form1=form)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_step_2():
    server_url = Canvas._canvas_server_url

    current_course = request.vars.current_course
    current_course_name = request.vars.current_course_name

    if current_course is not None:
        session.fr_current_course = current_course
    else:
        current_course = session.fr_current_course

    if current_course_name is not None:
        session.fr_current_course_name = current_course_name
    else:
        current_course_name = session.fr_current_course_name

    if current_course is None:
        redirect(URL("find_replace.html"))

    fr_options = dict(
        auto_youtube_tool="YouTube -> SMC Links (ONLY WORKS ONLINE)",
        auto_google_docs_tool="Google Docs -> SMC Links (ONLY WORKS ONLINE)",
        custom_regex="Custom Find/Replace",
    )

    option_list = []
    for o in fr_options:
        option_list.append(OPTION(fr_options[o], _value=o))

    options_select = SELECT(option_list, _name="fr_option", _style="width: 600px;")

    form2 = FORM(TABLE(TR("Choose Tool: ", options_select),
                       TR("", INPUT(_type="submit", _value="Next"))),
                 _action=URL('media', 'find_replace_step_2.load', user_signature=True)).process(keepvalues=True)

    if form2.accepted:
        # Save which option and redirect to that page
        if form2.vars.fr_option == "auto_youtube_tool":
            redirect(URL('media', 'find_replace_step_youtube.load', user_signature=True))
            pass
        elif form2.vars.fr_option == "auto_google_docs_tool":
            # response.flash = "Google"
            redirect(URL('media', 'find_replace_google.load', user_signature=True))
            pass
        elif form2.vars.fr_option == "custom_regex":
            # response.flash = "RegEx"
            redirect(URL('media', 'find_replace_step_custom_regex.load', user_signature=True))
            pass
        else:
            response.flash = "Unknown Option!"
        pass

    return dict(form2=form2, current_course=current_course, current_course_name=current_course_name,
                server_url=server_url)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_google():
    server_url = Canvas._canvas_server_url

    current_course = request.vars.current_course
    current_course_name = request.vars.current_course_name

    if current_course is not None:
        session.fr_current_course = current_course
    else:
        current_course = session.fr_current_course

    if current_course_name is not None:
        session.fr_current_course_name = current_course_name
    else:
        current_course_name = session.fr_current_course_name

    if current_course is None:
        redirect(URL("find_replace.html"))

    options = dict(
        docx="Word Doc (.docx - no preview)",
        epub="EPub (.epub - works w animations, no preview)",
        html="HTML (html/zipped - no preview)",
        odt="Open Document Format (.odt - preview available)",
        pdf="Adobe PDF (.pdf - preview available)",
        rtf="Rich Text Format (.rtf - no preview)",
        txt="Plain Text (.txt - no preview)",
    )

    option_list = []
    for o in options:
        option_list.append(OPTION(options[o], _value=o))

    options_select = SELECT(option_list, _name="export_option", _style="width: 600px;")

    form1 = FORM(TABLE(TR("Export As Format: ", options_select),
                       TR("", INPUT(_type="submit", _value="GO"))),
                 _action=URL('media', 'find_replace_google.load', user_signature=True)).process(keepvalues=True)

    find_replace_results = ""

    if form1.accepted:
        export_format = form1.vars.export_option
        find_replace_results = find_replace_google_run(current_course, current_course_name, export_format)
        # response.flash = "Not enabled yet!"

    return dict(form1=form1, current_course=current_course, current_course_name=current_course_name,
                server_url=server_url, find_replace_results=XML(find_replace_results))


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_google_run(current_course, current_course_name, export_format):
    ret = "Running...<br /><br />"

    # Regular expression to find google docs
    find_str = r'''https://(drive|docs)[.]google[.]com/(document/d/|open[?]{1}id=)([a-zA-Z0-9_-]+)(/edit(\?usp=sharing){0,1}){0,1}'''

    # Match examples
    # https://docs.google.com/document/d/1Tx2zl16Kq024p6ILySB_quGayhYcctL-MboJIYiWivY/edit?usp=sharing
    # https://docs.google.com/document/d/1xpw_s4zLo3ZZj_CoD40BVClUFsvVomEu8vE6zL7WUKY
    # https://drive.google.com/open?id=1BGj4VKH0fGeBuriIWcc0i3VoH5-wfKU1aXNYB58nV4I
    # https://docs.google.com/document/d/1OQsvGI78tDvTulzoo1o-I4yOL3yqLh1PlY9vLz1bosI/edit

    # === Pull all pages and extract links ===
    items = Canvas.get_page_list_for_course(current_course)
    total_pages = len(items)
    for i in items:
        orig_text = items[i]
        new_text = orig_text
        page_changed = False
        ret += "<br />Working on Page: " + str(i)

        matches = re.finditer(find_str, new_text)
        match_count = 0
        for m in matches:
            match_count += 1
            # Dl this doc and then do a replace.
            doc_url = m.group(0)
            print("found url: " + str(doc_url))
            smc_url = find_replace_google_download_doc(current_course_name, export_format, doc_url)
            if smc_url != "":
                new_text = new_text.replace(doc_url, smc_url)
                page_changed = True
            else:
                print("error getting smc url for google doc " + str(doc_url))

        # Update page
        if page_changed is True:
            new_item = dict()
            new_item["wiki_page[body]"] = new_text
            Canvas.update_page_for_course(current_course, i, new_item)
            ret += " page updated with " + str(match_count) + " changes."
        else:
            ret += " no links found."

    # === Pull all quizzes and extract links ===
    items = Canvas.get_quiz_list_for_course(current_course)
    total_quizzes = len(items)
    for i in items:
        orig_text = items[i]
        new_text = orig_text
        page_changed = False
        ret += "<br />Working on Quiz: " + str(i)

        matches = re.finditer(find_str, new_text)
        match_count = 0
        for m in matches:
            match_count += 1
            # Dl this doc and then do a replace.
            doc_url = m.group(0)
            print("found url: " + str(doc_url))
            smc_url = find_replace_google_download_doc(current_course_name, export_format, doc_url)
            if smc_url != "":
                new_text = new_text.replace(doc_url, smc_url)
                page_changed = True
            else:
                print("error getting smc url for google doc " + str(doc_url))

        # Update
        if page_changed is True:
            new_item = dict()
            new_item["quiz[description]"] = new_text
            Canvas.update_quiz_for_course(current_course, i, new_item)
            ret += " quiz updated with " + str(match_count) + " changes."
        else:
            ret += " no links found."

        quiz_id = i
        # === Pull all questions and extract links ===
        q_items = Canvas.get_quiz_questions_for_quiz(current_course, quiz_id)
        total_questions = len(q_items)
        for q in q_items:
            q_orig_text = q_items[q]
            q_new_text = q_orig_text
            q_page_changed = False
            ret += "<br />&nbsp;&nbsp;&nbsp;&nbsp;Working on question: " + str(q)

            q_matches = re.finditer(find_str, q_new_text)
            q_match_count = 0
            for q_m in q_matches:
                q_match_count += 1
                # Dl this doc and then do a replace.
                q_doc_url = q_m.group(0)
                print("found url: " + str(q_doc_url))
                q_smc_url = find_replace_google_download_doc(current_course_name, export_format, q_doc_url)
                if q_smc_url != "":
                    q_new_text = q_new_text.replace(q_doc_url, q_smc_url)
                    q_page_changed = True
                else:
                    print("error getting smc url for google doc " + str(q_doc_url))

            # Update page
            if q_page_changed is True:
                new_item = dict()
                new_item["question[question_text]"] = q_new_text
                Canvas.update_quiz_question_for_course(current_course, quiz_id, q, new_item)
                ret += " question updated with " + str(q_match_count) + " changes."
            else:
                ret += " no links found."

    # === Pull all discussion topics and extract links ===
    items = Canvas.get_discussion_list_for_course(current_course)
    total_dicussions = len(items)
    for i in items:
        orig_text = items[i]
        new_text = orig_text
        page_changed = False
        ret += "<br />Working on Discussion: " + str(i)

        matches = re.finditer(find_str, new_text)
        match_count = 0
        for m in matches:
            match_count += 1
            # Dl this doc and then do a replace.
            doc_url = m.group(0)
            print("found url: " + str(doc_url))
            smc_url = find_replace_google_download_doc(current_course_name, export_format, doc_url)
            if smc_url != "":
                new_text = new_text.replace(doc_url, smc_url)
                page_changed = True
            else:
                print("error getting smc url for google doc " + str(doc_url))

        # Update page
        if page_changed is True:
            new_item = dict()
            new_item["message"] = new_text
            Canvas.update_discussion_for_course(current_course, i, new_item)
            ret += " discussion updated with " + str(match_count) + " changes."
        else:
            ret += " no links found."

    # === Pull all assignments and extract links ===
    items = Canvas.get_assignment_list_for_course(current_course)
    total_assignments = len(items)
    for i in items:
        orig_text = items[i]
        new_text = orig_text
        page_changed = False
        ret += "<br />Working on Assignment: " + str(i)

        matches = re.finditer(find_str, new_text)
        match_count = 0
        for m in matches:
            match_count += 1
            # Dl this doc and then do a replace.
            doc_url = m.group(0)
            print("found url: " + str(doc_url))
            smc_url = find_replace_google_download_doc(current_course_name, export_format, doc_url)
            if smc_url != "":
                new_text = new_text.replace(doc_url, smc_url)
                page_changed = True
            else:
                print("error getting smc url for google doc " + str(doc_url))

        # Update page
        if page_changed is True:
            new_item = dict()
            new_item["assignment[description]"] = new_text
            Canvas.update_assignment_for_course(current_course, i, new_item)
            ret += " assignment updated with " + str(match_count) + " changes."
        else:
            ret += " no links found."

    ret += "<br /><br /><b>Done!</b>"
    return ret


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_google_re_download_docs():
    response.view = 'generic.html'
    # Go through all documents and ensure that the document has been downloaded - if not, do so now

    ret = ""
    (w2py_folder, applications_folder, app_folder) = get_app_folders()

    # Get full list of docs in the database
    docs = db(db.document_files).select()
    for d in docs:
        ret += "<br />Checking doc: " + d["title"]

        original_file_name = d['original_file_name']
        (root_file_name, export_format) = os.path.splitext(original_file_name)
        export_format = export_format.replace(".", "")  # remove the .

        # get the local file path and see if it exists

        # static/documents/01/010102alj29v.... (no file extension)
        # generate new uuid
        file_guid = d['document_guid']
        # print("File GUID: " + str(file_guid))
        target_folder = os.path.join(app_folder, 'static', 'documents')

        file_prefix = file_guid[0:2]

        target_folder = os.path.join(target_folder, file_prefix)

        if os.path.exists(target_folder) is not True:
            try:
                # Ensure the prefix folder exists - ok if this is an exception
                os.makedirs(target_folder)
            except OSError as message:
                pass

        target_file = os.path.join(target_folder, file_guid).replace("\\", "/")

        # Write the JSON file
        output_meta = target_file + ".json"

        meta = {'title': d['title'], 'document_guid': file_guid,
                'description': d['description'], 'original_file_name': d['original_file_name'],
                'media_type': d['media_type'], 'category': d['category'],
                'tags': d['tags'], 'google_url': d['google_url']}

        meta_json = dumps(meta)

        try:
            #f = os.open(output_meta, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
            #os.write(f, meta_json)
            #os.close(f)
            f = open(output_meta, "w")
            f.write(meta_json)
            f.close()
        except Exception as ex:
            print("ERROR SAVING JSON for google doc download " + str(output_meta) + " - " + str(ex))
            ret += " ---- ERROR SAVING JSON " + str(ex)

        if os.path.exists(target_file):
            ret += " - File already downloaded... " + file_guid
            continue

        g_url = d["google_url"]
        if g_url is None:
            ret += " - no google url " + file_guid
            continue

        # Need the document id from the google url
        # Regular expression to pull out the id
        find_str = r'''https://(drive|docs)[.]google[.]com/(document/d/|open[?]{1}id=)([a-zA-Z0-9_-]+)(/edit(\?usp=sharing){0,1}){0,1}'''
        matches = re.search(find_str, g_url)

        if matches is None:
            ret += " - No google doc id found in " + str(g_url)
            print("INVALID Google URL - NO ID FOUND " + str(g_url))
            continue

        # Grab the ID from the match
        doc_id = matches.group(3)
        # Make export link
        export_url = "https://docs.google.com/document/export?format=epub&id=" + str(doc_id)

        ret += " - pulling from " + str(export_url)
        print("Pulling google doc: " + export_url)

        # Download the file
        try:
            #req = urllib.urlopen(export_url)
            req = requests.get(export_url, stream=True)
            with open(target_file, 'wb') as f:
                for block in req.iter_content(1024):
                    f.write(block)

            # NOTE - Just re-downloading - don't need the rest of this.
            # Should have file name in the content-disposition header
            # content-disposition: attachment; filename="WB-CapitalLettersPunctuation.epub";
            # filename*=UTF-8''WB%20-%20Capital%20Letters%20%26%20Punctuation.epub
            # content_type = str(req.info()['Content-Type'])
            # content_disposition = str(req.info()['content-disposition'])
            # split the content-disposition into parts and find the original filename
            # parts = content_disposition.split("; ")
            # for part in parts:
            #    if "filename=" in part:
            #        parts2 = part.split("=")
            #        p = parts2[1]
            #        p = p.strip('"')  # strip off "s
            #        if p is not None and p != "":
            #            original_file_name = p
            #            break

        except Exception as ex:
            print("Error trying to save google doc file: " + str(export_url) + " - " + str(ex))
            ret += " --- ERROR " + str(export_url) + " - " + str(ex)
            continue

    return ret

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def test_find_replace_google_download_doc():
    response.view = "generic.json"
    current_course = "392419000000128"
    export_format = "pdf"
    doc_url = "Click this link: <a href=\"https://docs.google.com/document/d/1Tx2zl16Kq024p6ILySB_quGayhYcctL-MboJIYiWivY/edit?usp=sharing\" >LINK</a>"
    ret = find_replace_google_download_doc(current_course, export_format, doc_url)

    return locals()

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_google_download_doc(current_course_name, export_format, doc_url):
    # Will return the new SMC url or empty string if an error occurs
    ret = ""

    # Check if exists - return smc link if it does
    row = db(db.document_files.google_url == doc_url).select().first()
    if row is not None:
        ret = URL('media', 'dl_document', args=[row.document_guid], scheme=True, host=True)
        print("Google Doc Already Downloaded: " + str(ret))
        return ret

    # Regular expression to pull out the id
    find_str = r'''https://(drive|docs)[.]google[.]com/(document/d/|open[?]{1}id=)([a-zA-Z0-9_-]+)(/edit(\?usp=sharing){0,1}){0,1}'''
    matches = re.search(find_str, doc_url)

    if matches is None:
        msg = "No google doc id found in " + str(doc_url)
        print(msg)
        return ret

    # Grab the ID from the match
    doc_id = matches.group(3)

    if export_format == "":
        export_format = "epub"

    # Make export link
    export_url = "https://docs.google.com/document/export?format=" + export_format + "&id=" + str(doc_id)

    print("Pulling google doc: " + export_url)

    # Figure out a local file name
    (w2py_folder, applications_folder, app_folder) = get_app_folders()

    # static/documents/01/010102alj29v.... (no file extension)
    # generate new uuid
    file_guid = str(uuid.uuid4()).replace('-', '')
    # print("File GUID: " + str(file_guid))
    target_folder = os.path.join(app_folder, 'static', 'documents')

    file_prefix = file_guid[0:2]

    target_folder = os.path.join(target_folder, file_prefix)
    # print("Target Dir: " + target_folder)

    try:
        os.makedirs(target_folder)
    except OSError as message:
        pass

    target_file = os.path.join(target_folder, file_guid).replace("\\", "/")

    original_file_name = file_guid + "." + export_format

    # Download the file
    try:
        #req = urllib.urlopen(export_url)
        req = requests.get(export_url, stream=True)
        with open(target_file, 'wb') as f:
            for block in req.iter_content(1024):
                f.write(block)

        # Should have file name in the content-disposition header
        # content-disposition: attachment; filename="WB-CapitalLettersPunctuation.epub";
        # filename*=UTF-8''WB%20-%20Capital%20Letters%20%26%20Punctuation.epub
        content_type = str(req.headers['Content-Type'])
        content_disposition = str(req.headers['content-disposition'])
        # split the content-disposition into parts and find the original filename
        parts = content_disposition.split("; ")
        for part in parts:
            if "filename=" in part:
                parts2 = part.split("=")
                p = parts2[1]
                p = p.strip('"')  # strip off "s
                if p is not None and p != "":
                    original_file_name = p
                    break

    except Exception as ex:
        print("Error trying to save google doc file: " + str(export_url) + " - " + str(ex))
        return ret

    # Now add the info to the database.
    output_meta = target_file + ".json"
    # Save JSON info
    # Pull the extension off the original filename
    title, ext = os.path.splitext(original_file_name)
    description = "Pulled from google docs (" + str(doc_url) + ") for course " + str(current_course_name)
    media_type = "document"
    category = current_course_name
    tags = []

    meta = {'title': title, 'document_guid': file_guid,
            'description': description, 'original_file_name': original_file_name,
            'media_type': media_type, 'category': category,
            'tags': dumps(tags), 'google_url': doc_url}

    meta_json = dumps(meta)

    try:
        #f = os.open(output_meta, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        #os.write(f, meta_json)
        #os.close(f)
        f = open(output_meta, "w")
        f.write(meta_json)
        f.close()
    except Exception as ex:
        print("ERROR SAVING JSON for google doc download " + str(output_meta) + " - " + str(ex))

    # Store this file in the database
    db.document_files.insert(document_guid=file_guid, title=title, description=description,
                             original_file_name=original_file_name, media_type=media_type,
                             category=category, tags=tags, google_url=doc_url)
    db.commit()

    ret = URL('media', 'dl_document', args=[file_guid], scheme=True, host=True)
    return ret


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_post_process_text(course_id, txt):
    # Deal with left over cleaup for find/replace

    # Find canvas file ids.
    pattern = re.compile("<CANVAS_FILE_ID__(.*)__>")

    match = pattern.search(txt)
    while match is not None:
        # Lookup the found file(s)
        file_name = match.group(1)
        file_id = Canvas.get_id_for_filename(course_id, file_name)

        # replace the original tag w the file id
        txt = txt.replace("<CANVAS_FILE_ID__" + file_name + "__>", str(file_id))
        match = pattern.search(txt)

    # Find quizlet IDs  <FLASH_CARD_LINK___2130943___()___>
    pattern = re.compile("<FLASH_CARD_LINK___([0-9]+)___([a-zA-Z0-9]+)___>")
    match = pattern.search(txt)
    while match is not None:
        # Run code to pull info for quizlet
        q_id = match.group(1)
        q_type = match.group(2)

        try:
            if pull_single_quizlet_url(q_id, q_type) is True:
                # Succeeded, replace original link w new link.
                smc_url = URL('media', 'flashcard_player.load', args=[str(q_id), str(q_type)],
                              extension=False, host=True, scheme=True)
                txt = txt.replace(match.group(0), smc_url)
            else:
                print("----> Error pulling quizlet: " + str(q_id))
                error_text = "ERROR_PULLING_QUIZLET_" + str(q_id)
                txt = txt.replace(match.group(0), error_text)
        except Exception as ex:
            print("----> Unknown Exception pulling quizlet data " + str(q_id) + "\n" + str(ex))
            break

        match = pattern.search(txt)

    return txt


# This should be public
def flashcard_player():
    ret = dict()
    ret["error_msg"] = ""
    ret["json_str"] = dumps(dict())

    flashcard_id = request.args(0)
    if flashcard_id is None:
        ret["error_msg"] = "Flashcard Not Found!"
        return ret

    (w2py_folder, applications_folder, app_folder) = get_app_folders()

    # flashcards folder
    flashcards_folder = os.path.join(app_folder, 'static', 'media', 'flashcards')

    item_folder = os.path.join(flashcards_folder, flashcard_id)

    # Open the json file
    json_file = os.path.join(item_folder, 'data.json')
    if os.path.exists(json_file) is not True:
        ret["error_msg"] = "JSON Data does not exist!"
        return ret

    json_f = open(json_file, "r")
    json_str = json_f.read()
    json_f.close()

    js_data = None
    try:
        js_data = loads(json_str)
    except Exception as ex:
        # Invalid json?
        ret["error_msg"] = "Invalid JSON data! " + str(ex)
        return ret

    # ret["error_msg"] = json_file
    ret["json_str"] = XML(json_str)

    # Not working?
    # response.js = "alert('test')"  # "flashcard_data = " + json_str + ";\n"

    return ret

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def test_pull_single_quizlet_url():
    response.view = "generic.json"
    q_id = request.args(0)
    q_type = request.args(1)

    ret = pull_single_quizlet_url(q_id, q_type)
    return locals()

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def pull_single_quizlet_url(q_id, q_type):
    # Fill in headers with public stuff so it looks good
    headers = dict()
    headers['accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"
    # Don't want compression here
    #headers['accept-encoding'] = "gzip, deflate"
    headers['accept-language'] = "en-US,en;q=0.9,es;q=0.8"
    headers['cache-control'] = "max-age=0"
    headers['user-agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"

    # Pull data for a quizlet url - includes json, pics, and mp3s
    ret = False
    (w2py_folder, applications_folder, app_folder) = get_app_folders()

    # flashcards folder
    flashcards_folder = os.path.join(app_folder, 'static', 'media', 'flashcards')

    # item folder
    item_folder = os.path.join(flashcards_folder, str(q_id))

    if os.path.exists(item_folder) is not True:
        os.makedirs(item_folder)

    # Pull the embed url
    q_url = "https://quizlet.com/" + q_id + "/flashcards/embed"
    resp = requests.get(q_url, headers=headers)
    html = resp.text # content.decode('utf-8')  # text
    #print("HTML: " + html)

    # Find the json data
    # Now strip out the json data - we want the json between these
    #find_str = r'''<script\.window\.Quizlet\["cardsModeData"\] = (.*); QLoad\("Quizlet\.cardsModeData"\);</script>'''
    find_str = r'''window\.Quizlet\["assistantModeData"\] = (.*); QLoad\("Quizlet\.assistantModeData"\);\}'''
    m = re.search(find_str, html)
    if m is None:
        print("-----> No flashcard data found at " + q_url)
        return

    js_string = str(m.group(1))
    # print(js_string)

    js_data = loads(js_string)

    # print("JS Data: " + str(js_data))
    # Copy settings - new format changed all these
    js_data["id"] = str(js_data['studyableId'])
    js_data["url"] = str(js_data['studyablePath'])
    js_data["wordLabel"] = "English"
    js_data["definitionLabel"] = "Photos"
    js_data['sets'] = js_data['setList']

    id = str(js_data['id'])
    url = str(js_data['url'])
    word_label = str(js_data['wordLabel'])
    definition_label = str(js_data['definitionLabel'])
    sets = js_data['sets']
    terms = js_data['terms']

    # Now pull terms found
    for t in terms:
        # COPY SETTINGS - Make sure these exist for each term - new format changed things
        t['photo'] = str(t['_imageUrl'])
        t['quiz_id'] = str(t['setId'])
        t['term_lang'] = ""
        t['def_lang'] = ""
        t['word_audio'] = str(t['_wordAudioUrl'])
        t['has_word_custom_audio'] = "false"
        if str(t['wordCustomAudioId']) != "null":
            t['has_word_custom_audio'] = "true"
        t['def_audio'] = str(t['_definitionAudioUrl'])
        t['has_def_custom_audio'] = "false"
        if str(t['definitionCustomAudioId']) != "null":
            t['has_def_custom_audio'] = "true"
        t['can_edit'] = 'false'


        t_id = str(t['id'])
        t_quiz_id = str(t['quiz_id'])
        t_photo = str(t['photo'])
        t_word = str(t['word'])
        t_definition = str(t['definition'])
        t_term_lang = str(t['term_lang'])
        t_def_lant = str(t['def_lang'])
        t_word_audio = str(t['word_audio'])
        t_has_word_custom_audio = str(t['has_word_custom_audio'])
        t_def_audio = str(t['def_audio'])
        t_has_def_custom_audio = str(t['has_def_custom_audio'])
        t_can_edit = str(t['can_edit'])

        # print("Found Term: " + t_word)
        # print("\tSaving QL Pics and MP3s...")

        photo_file = os.path.join(item_folder, str(t_id))
        t['local_photo'] = pull_ql_image(headers, q_url, photo_file, t_photo)

        word_file = os.path.join(item_folder, str(t_id) + ".word.mp3")
        pull_ql_audio(headers, q_url, word_file, t_word_audio)

        def_file = os.path.join(item_folder, str(t_id) + ".def.mp3")
        pull_ql_audio(headers, q_url, def_file, t_def_audio)

    # print("Saving JSON data for: " + str(q_id))
    json_path = os.path.join(item_folder, 'data.json')

    f = open(json_path, 'w+')
    f.write(dumps(js_data))
    f.close()

    ret = True

    return ret


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def pull_ql_audio(headers, quizlet_url, save_path, url):
    if url is None or url == 'None' or len(url) < 1 or url == 'False':
        # No audio url.
        return

    # Make sure to add referer for this request or it will fail
    h = headers.copy()
    h['Referer'] = quizlet_url

    pull_url = url
    if 'http' not in url:
        pull_url = "https://quizlet.com" + url

    if os.path.exists(save_path):
        print("--> QL MP3 ALREADY DOWNLOADED " + pull_url)
        return
    else:
        print("--> DOWNLOADING QL MP3: " + pull_url)

    # Pull the image from the url and save it locally
    r = requests.get(pull_url, headers=h)

    f_path = save_path
    f = open(f_path, "wb+")
    f.write(r.content)
    f.close()
    # print("MP3 Done: " + pull_url)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def pull_ql_image(headers, quizlet_url, save_path, image_data):
    if len(image_data) < 1 or image_data == "False":
        # No image data
        return ""

    # Make sure to add referer for this request or it will fail
    h = headers.copy()
    h['Referer'] = quizlet_url

    # Image data looks like: 3,pBj7uiWsawC-9EuYswJrCw,jpg,960x720
    # transform it to this form: https://o.quizlet.com/pBj7uiWsawC-9EuYswJrCw_b.jpg
    if "http" not in image_data:
        parts = image_data.split(",")
        pull_url = "https://o.quizlet.com/" + parts[1] + "_b." + parts[2]
        # Add extention on (.jpg ?)
        f_path = save_path + "." + parts[2]
    else:
        pull_url = image_data
        bname = os.path.basename(image_data)
        f_path = save_path + os.path.splitext(bname)[1]
   

    if os.path.exists(f_path):
        print("--> QL PIC ALREADY DOWNLOADED " + pull_url)
        return os.path.basename(f_path)
    else:
        print("--> DOWNLOADING QL PIC: " + pull_url)

    # Pull the image from the url and save it locally
    r = requests.get(pull_url, headers=h)

    # Save the image
    f = open(f_path, "wb+")
    f.write(r.content)
    f.close()
    # print("---> Pic DONE: " + pull_url)
    return os.path.basename(f_path)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_step_custom_regex_run(current_course, find_pattern, replace_pattern, update_canvas=False):
    ret = ""

    ret += "<h2>Searching with pattern: </h2> <b>Find</b>(" + \
           find_pattern.replace(">", "&gt;").replace("<", "&lt;") + \
           ") / <b>Replace</b> (" + replace_pattern.replace(">", "&gt;").replace("<", "&lt;") + ") " + \
           "<p><b>Note:</b> Local URLs may not work in this view but work fine when viewed from Canvas.</p><hr/>"

    style = "width: 100%; height: 800px; overflow: auto; display: none; border: 1px solid black;"

    # === Get the list of pages ===
    pages = Canvas.get_page_list_for_course(current_course)
    total_pages = len(pages)
    ret += "<h3>Pages Searched: " + str(total_pages) + "</h3>" + \
           "<div onclick='$(\"#show_hide_pages\").toggle();' style='cursor: pointer;'><h4>PAGES PROCESSED: " + \
           "<span style='font-size:8px;'>(click to open/close)</span></h4></div>" + \
           "<div id='show_hide_pages' style='" + style + "'>"
    inc = 0
    for p in pages:
        inc += 1
        p_orig_text = pages[p]
        if p_orig_text is None:
            p_orig_text = ""
        p_new_text, subs = re.subn(find_pattern, replace_pattern, p_orig_text)
        p_new_text = find_replace_post_process_text(current_course, p_new_text)

        ret += "<H5><div onclick='$(\"#show_hide_" + str(inc) + "\").toggle();' style='cursor: pointer;'>PAGE: " + p + \
               " - " + str(subs) + " replacements. <span style='font-size:8px;'>(click to open/close)</span></div></H5>"

        ret += "<div id='show_hide_" + str(inc) + "' style='" + style + "'>"
        ret += "<h2>OLD PAGE</h2>"
        ret += "<code>" + p_orig_text + "</code>"
        ret += "<hr />"
        ret += "<h2>NEW PAGE</h2>"
        ret += "<code>" + p_new_text + "</code>"
        ret += "</div>"

        if subs > 0 or p_orig_text != p_new_text:
            # Update the page in canvas
            new_page = dict()
            new_page["wiki_page[body]"] = p_new_text

            if update_canvas is True:
                result = Canvas.update_page_for_course(current_course, p, new_page)
            else:
                result = "Not Updating!"
            # ret += result

    # Close the show/hide for all pages
    ret += "</div><hr />"

    # === Work on list of quizzes ===
    quizzes = Canvas.get_quiz_list_for_course(current_course)
    total_quizzes = len(quizzes)
    ret += "<h3>Searched " + str(total_quizzes) + " quizzes</h3>" + \
           "<div onclick='$(\"#show_hide_quizzes\").toggle();' style='cursor: pointer;'><h4>QUIZZES PROCESSED:" + \
           "<span style='font-size:8px;'>(click to open/close)</span></h4></div>" + \
           "<div id='show_hide_quizzes' style='" + style + "'>"
    inc = 0
    for q in quizzes:
        inc += 1
        total_qq_replacements = 0
        quiz_id = q
        q_orig_text = quizzes[q]
        if q_orig_text is None:
            q_orig_text = ""
        q_new_text, subs = re.subn(find_pattern, replace_pattern, q_orig_text)
        q_new_text = find_replace_post_process_text(current_course, q_new_text)

        ret += "<H5><div onclick='$(\"#show_hide_q_" + str(inc) + "\").toggle();' style='cursor: pointer;'>quiz: " + \
               str(q) + " - " + str(subs) + "/<QQ_COUNT_" + str(quiz_id) + "> matches. " + \
               "<span style='font-size:8px;'>(click to open/close)</span></div></H5>"

        ret += "<div id='show_hide_q_" + str(inc) + "' style='" + style + "'>"
        ret += "<h2>OLD QUIZ DESCRIPTION</h2>"
        ret += "<code>" + q_orig_text + "</code>"
        ret += "<hr />"
        ret += "<h2>NEW QUIZ DESCRIPTION</h2>"
        ret += "<code>" + q_new_text + "</code>"

        if subs > 0 or q_orig_text != q_new_text:
            # Update the page in canvas
            new_page = dict()
            new_page["quiz[body]"] = q_new_text
            result = ""
            if update_canvas is True:
                result = Canvas.update_quiz_for_course(current_course, quiz_id, new_page)
            else:
                result = "NOT UPDATING!"
            ret += "UPDATE quiz RESULT: " + str(result)

        quiz_questions = Canvas.get_quiz_questions_for_quiz(current_course, quiz_id)
        total_questions = len(quiz_questions)
        qq_inc = 0
        for qq in quiz_questions:
            qq_inc += 1
            qq_id = qq
            qq_orig_text = quiz_questions[qq]
            if qq_orig_text is None:
                qq_orig_text = ""
            qq_new_text, subs = re.subn(find_pattern, replace_pattern, qq_orig_text)
            qq_new_text = find_replace_post_process_text(current_course, qq_new_text)

            style = "width: 100%; height: 800px; overflow: auto; display: none; border: 1px solid black;"
            ret += "<H5><div onclick='$(\"#show_hide_qq_" + str(
                qq_id) + "\").toggle();' style='cursor: pointer;'>QUESTION: " + \
                str(qq_id) + " - " + str(subs) + " matches. " + \
                "<span style='font-size:8px;'>(click to open/close)</span></div></H5>"

            ret += "<div id='show_hide_qq_" + str(qq_id) + "' style='" + style + "'>"
            ret += "<h2>OLD QUESTION TEXT</h2>"
            ret += "<code>" + qq_orig_text + "</code>"
            ret += "<hr />"
            ret += "<h2>NEW QUESTION TEXT</h2>"
            ret += "<code>" + qq_new_text + "</code>"
            ret += "</div>"

            # this should be a match/change
            # if qq_id == 999999000006926:
            #    from gluon.debug import dbg
            #    dbg.set_trace()  # stop here!

            if subs > 0 or qq_orig_text != qq_new_text:
                total_qq_replacements += 1
                new_page = dict()
                new_page["id"] = qq_id
                new_page["quiz_id"] = quiz_id
                new_page["question[question_text]"] = qq_new_text
                result = ""
                if update_canvas is True:
                    result = Canvas.update_quiz_question_for_course(current_course, quiz_id, qq_id, new_page)
                else:
                    result = "NOT UPDATING!"
                ret += "UPDATE QUESTION RESULT: " + str(result)

        # Enter question replacements so we can see how many matches there were
        ret = ret.replace("<QQ_COUNT_" + str(quiz_id) + ">", str(total_qq_replacements))

        ret += "</div>"

    # Close show/hide for all quizzes
    ret += "</div>"

    # === Get the list of discussion topics ===
    canvas_items = Canvas.get_discussion_list_for_course(current_course)
    total_items = len(canvas_items)
    ret += "<h3>Discussion Topics Searched: " + str(total_items) + "</h3>" + \
           "<div onclick='$(\"#show_hide_discussions\").toggle();' style='cursor: pointer;'><h4>DISCUSSIONS PROCESSED: " + \
           "<span style='font-size:8px;'>(click to open/close)</span></h4></div>" + \
           "<div id='show_hide_discussions' style='" + style + "'>"
    inc = 0
    for p in canvas_items:
        inc += 1
        p_orig_text = canvas_items[p]
        if p_orig_text is None:
            p_orig_text = ""
        p_new_text, subs = re.subn(find_pattern, replace_pattern, p_orig_text)
        p_new_text = find_replace_post_process_text(current_course, p_new_text)

        ret += "<H5><div onclick='$(\"#show_hide_discussions_" + str(inc) + \
               "\").toggle();' style='cursor: pointer;'>DISCUSSION: " + str(p) + \
               " - " + str(subs) + " replacements. <span style='font-size:8px;'>(click to open/close)</span></div></H5>"

        ret += "<div id='show_hide_discussions_" + str(inc) + "' style='" + style + "'>"
        ret += "<h2>OLD DISCUSSION</h2>"
        ret += "<code>" + p_orig_text + "</code>"
        ret += "<hr />"
        ret += "<h2>NEW DISCUSSION</h2>"
        ret += "<code>" + p_new_text + "</code>"
        ret += "</div>"

        if subs > 0 or p_orig_text != p_new_text:
            # Update the discussion in canvas
            new_page = dict()
            new_page["message"] = p_new_text

            if update_canvas is True:
                result = Canvas.update_discussion_for_course(current_course, p, new_page)
            else:
                result = "Not Updating!"
            # ret += result

    # Close the show/hide for all discussion topics
    ret += "</div><hr />"

    # === Get the list of assignments ===
    canvas_items = Canvas.get_assignment_list_for_course(current_course)
    total_items = len(canvas_items)
    ret += "<h3>Assignments Searched: " + str(total_items) + "</h3>" + \
           "<div onclick='$(\"#show_hide_assignments\").toggle();' style='cursor: pointer;'><h4>ASSIGNMENTS PROCESSED: " + \
           "<span style='font-size:8px;'>(click to open/close)</span></h4></div>" + \
           "<div id='show_hide_assignments' style='" + style + "'>"
    inc = 0
    for p in canvas_items:
        inc += 1
        p_orig_text = canvas_items[p]
        if p_orig_text is None:
            p_orig_text = ""
        p_new_text, subs = re.subn(find_pattern, replace_pattern, p_orig_text)
        p_new_text = find_replace_post_process_text(current_course, p_new_text)

        ret += "<H5><div onclick='$(\"#show_hide_assignments_" + str(inc) + \
               "\").toggle();' style='cursor: pointer;'>ASSIGNMENT: " + str(p) + \
               " - " + str(subs) + " replacements. <span style='font-size:8px;'>(click to open/close)</span></div></H5>"

        ret += "<div id='show_hide_assignments_" + str(inc) + "' style='" + style + "'>"
        ret += "<h2>OLD ASSIGNMENT</h2>"
        ret += "<code>" + p_orig_text + "</code>"
        ret += "<hr />"
        ret += "<h2>NEW ASSIGNMENT</h2>"
        ret += "<code>" + p_new_text + "</code>"
        ret += "</div>"

        if subs > 0 or p_orig_text != p_new_text:
            # Update the discussion in canvas
            new_page = dict()
            new_page["assignment[description]"] = p_new_text

            if update_canvas is True:
                result = Canvas.update_assignment_for_course(current_course, p, new_page)
            else:
                result = "Not Updating!"
            # ret += result

    # Close the show/hide for all assignments
    ret += "</div><hr />"

    return ret


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_step_custom_regex():
    ret = ""

    form2 = None
    form3 = None

    server_url = Canvas._canvas_server_url

    current_course = request.vars.current_course
    current_course_name = request.vars.current_course_name

    if current_course is not None:
        session.fr_current_course = current_course
    else:
        current_course = session.fr_current_course

    if current_course_name is not None:
        session.fr_current_course_name = current_course_name
    else:
        current_course_name = session.fr_current_course_name

    if current_course is None:
        redirect(URL("find_replace.html"))

    # Make a form with the Find and Replace boxes
    form2 = FORM(TABLE(TR("Find Pattern: ", INPUT(_type="text", _name="find_pattern")),
                       TR("Replace Pattern: ", INPUT(_type="text", _name="replace_pattern")),
                       TR(XML("Write Changes <span style='color: red; font-size:10px;'>" +
                              "(check this to update canvas)</span>: "),
                          INPUT(_type="checkbox", _name="write_changes", value='')),
                       TR("", INPUT(_type="submit", _value="GO"))),
                 _action=URL('media', 'find_replace_step_custom_regex.load', user_signature=True),
                 _name="form2").process(keepvalues=True, formname="form2")

    pre_defined_patterns = {
        "Change Host Links - (smc.sbctc... -> smc.ed)": ["smc.sbctc.correctionsed.com", "smc.ed"],
        "Change Host Links - (smc.ed -> smc.sbctc...)": ["smc.ed", "smc.sbctc.correctionsed.com"],
        "IDEA - Listen Audio (change media tag to correct url)":
            [r'''<audio .* src=["'](.*)/courses/([0-9]+)/media_download\?entryId=(m-[0-9a-zA-Z]+)(.*)redirect=1(["']) .*>.*</audio>''',
             r'''<audio controls="controls"><source src="\1/courses/\2/files/<CANVAS_FILE_ID__\3__>/download?download_frd=1" orig_filename="\3" /></audio>'''],
        "Quizlet Flashcards (download data and use local player)":
            [r'''https://(www\.)?quizlet\.com/([0-9]+)/([a-zA-Z]+)/embed''',
             r'''<FLASH_CARD_LINK___\2___\3___>'''],
        "Fix Failed Quizlet Imports":
            [r'''ERROR_PULLING_QUIZLET_([0-9]+)''',
            r'''https://quizlet.com/\1/flashcards/embed'''],
    }

    patterns_list = []
    for p in pre_defined_patterns:
        patterns_list.append(OPTION(p, _value=p))

    pre_defined_patterns_select = SELECT(patterns_list, _name="pattern_option", _style="width: 400px;")

    form3 = FORM(TABLE(TR(pre_defined_patterns_select),
                       TR(XML("Write Changes <span style='color: red; font-size:10px;'>" +
                              "(check this to update canvas)</span>: "),
                          INPUT(_type="checkbox", _name="write_changes", value='')),
                       TR(INPUT(_type="submit", _value="GO"))
                       ),
                 _action=URL('media', 'find_replace_step_custom_regex.load', user_signature=True),
                 _name="form3").process(keepvalues=True, formname="form3")

    if form2.accepted:
        # Note - leaving write_changes unchecked w an empty replace should be "find only"
        if form2.vars.find_pattern != "":  # and form2.vars.replace_pattern != "":
            # Run find/replace pattern
            find_pattern = form2.vars.find_pattern
            replace_pattern = form2.vars.replace_pattern

            write_changes = False
            if form2.vars.write_changes is not None:
                # print("write changes")
                write_changes = True

            ret = find_replace_step_custom_regex_run(current_course, find_pattern, replace_pattern, write_changes)

        # elif form2.vars.find_pattern != "" and form2.vars.replace_pattern == "":
        #    response.flash = "Find only not done."
        else:
            response.flash = "Please enter a find pattern to search for."

        pass

    if form3.accepted:
        if form3.vars.pattern_option != "":
            # Grab the find/replace patterns
            find_pattern = pre_defined_patterns[form3.vars.pattern_option][0]
            replace_pattern = pre_defined_patterns[form3.vars.pattern_option][1]

            write_changes = False
            if form3.vars.write_changes is not None:
                write_changes = True

            ret = find_replace_step_custom_regex_run(current_course, find_pattern, replace_pattern, write_changes)
        else:
            response.flash = "Please select an option to search for."

    return dict(form2=form2, current_course=current_course, current_course_name=current_course_name,
                server_url=server_url, find_replace_results=XML(ret), form3=form3)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_step_youtube():
    server_url = Canvas._canvas_server_url

    current_course = request.vars.current_course
    current_course_name = request.vars.current_course_name

    if current_course is not None:
        session.fr_current_course = current_course
    else:
        current_course = session.fr_current_course

    if current_course_name is not None:
        session.fr_current_course_name = current_course_name
    else:
        current_course_name = session.fr_current_course_name

    if current_course is None:
        redirect(URL("find_replace.html"))

    # Total of ALL urls
    total_urls = 0

    # === FIND PAGE URLS FOR YT ===
    yt_urls = dict()
    pages = Canvas.get_page_list_for_course(current_course)

    for p in pages:
        urls = getURLS(pages[p])
        if len(urls) > 0:
            total_urls += len(urls)
            yt_urls[p] = urls

    session.yt_page_urls = yt_urls
    session.yt_page_urls_curr_pos = 0

    # === FIND QUIZ URLS FOR YT ===
    yt_urls = dict()
    # Set some values for sub queries for questions
    session.yt_question_urls = dict()
    session.yt_question_curls_curr_pos = 0

    items = Canvas.get_quiz_list_for_course(current_course)

    for i in items:
        urls = getURLS(items[i])
        if len(urls) > 0:
            total_urls += len(urls)
            yt_urls[i] = urls

        # Now pull for each question
        question_yt_urls = dict()
        questions = Canvas.get_quiz_questions_for_quiz(current_course, i)
        for q in questions:
            question_urls = getURLS(questions[q])
            if len(question_urls) > 0:
                total_urls += len(question_urls)
                question_yt_urls[q] = question_urls

        # Add the questions to the main list
        session.yt_question_urls[i] = question_yt_urls

    session.yt_quiz_urls = yt_urls
    session.yt_quiz_urls_curr_pos = 0

    # === FIND DISCUSSION TOPIC URLS FOR YT ===
    yt_urls = dict()
    items = Canvas.get_discussion_list_for_course(current_course)

    for i in items:
        urls = getURLS(items[i])
        if len(urls) > 0:
            total_urls += len(urls)
            yt_urls[i] = urls

    session.yt_discussion_urls = yt_urls
    session.yt_discussion_urls_curr_pos = 0

    # === FIND ASSIGNMENT URLS FOR YT ===
    yt_urls = dict()
    items = Canvas.get_assignment_list_for_course(current_course)

    for i in items:
        urls = getURLS(items[i])
        if len(urls) > 0:
            total_urls += len(urls)
            yt_urls[i] = urls

    session.yt_assignment_urls = yt_urls
    session.yt_assignment_urls_curr_pos = 0

    session.yt_urls_curr_pos = 0
    session.yt_urls_total_len = total_urls
    session.yt_urls_msg = ""
    session.yt_urls_status = ""
    session.yt_urls_error_msg = ""

    return dict(form=yt_urls, current_course=current_course, current_course_name=current_course_name,
                server_url=server_url)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_step_youtube_progress():
    # Run one dl operation per view
    msg = ""

    current_course = session.fr_current_course
    current_course_name = session.fr_current_course_name

    finished = False
    # Process a page
    if len(session.yt_page_urls) > 0:
        page_url, yt_urls = session.yt_page_urls.popitem()
        for yt_url in yt_urls:
            session.yt_urls_curr_pos += 1
            msg = "<br />Processing " + str(yt_url)

            try:
                # Get yt video info
                # session.yt_urls_error_msg += "A"
                # yt, stream, res = find_best_yt_stream(yt_url)
                # session.yt_urls_error_msg += "AB"

                # Start download or get current db entry for this video
                # media_file = queue_up_yt_video(yt_url, yt, res, current_course_name)
                media_file = queue_up_yt_video(yt_url, current_course_name)
                # session.yt_urls_error_msg += "B"
                vid_guid = media_file.media_guid
                # title = media_file.title
                # description = media_file.description
                # category = media_file.category
                # tags = media_file.tags

                # Now replace the value in the canvas page
                smc_url = URL('media', 'player', args=[vid_guid], host=True)
                msg += "Replacing " + str(yt_url) + " with " + str(smc_url)

                Canvas.replace_value_in_course_page(current_course, page_url, yt_url, smc_url)
                pass
            except Exception as ex:
                session.yt_urls_error_msg += "<br/>\nError getting video " + str(yt_url) + " -> " + str(ex)
    elif len(session.yt_quiz_urls) > 0:
        quiz_id, yt_urls = session.yt_quiz_urls.popitem()
        for yt_url in yt_urls:
            session.yt_urls_curr_pos += 1
            msg = "<br />Processing " + str(yt_url)

            try:
                # Get yt video info
                # session.yt_urls_error_msg += "A"
                # yt, stream, res = find_best_yt_stream(yt_url)
                # session.yt_urls_error_msg += "AB"

                # Start download or get current db entry for this video
                # media_file = queue_up_yt_video(yt_url, yt, res, current_course_name)
                media_file = queue_up_yt_video(yt_url, current_course_name)
                # session.yt_urls_error_msg += "B"
                vid_guid = media_file.media_guid
                # title = media_file.title
                # description = media_file.description
                # category = media_file.category
                # tags = media_file.tags

                # Now replace the value in the canvas page
                smc_url = URL('media', 'player', args=[vid_guid], host=True)
                msg += "Replacing " + str(yt_url) + " with " + str(smc_url)

                Canvas.replace_value_in_quiz_page(current_course, quiz_id, yt_url, smc_url)
                pass
            except Exception as ex:
                session.yt_urls_error_msg += "<br/>\nError getting video " + str(yt_url) + " -> " + str(ex)
    elif len(session.yt_question_urls) > 0:
        # Questions are 2 level array - yt_question_urls[quiz_id][question_id]=urls
        # pop one question
        question_id = 0
        yt_urls = dict()
        quiz_id = 0
        while question_id < 1 and len(session.yt_question_urls) > 0:
            # Pull the next question urls - remove quiz from array if empty
            for quiz_id in session.yt_question_urls:
                if len(session.yt_question_urls[quiz_id]) < 1:
                    # No sub items, remove it
                    del session.yt_question_urls[quiz_id]
                    break  # Jump to next while loop

                # Get the question, then bump out of the loop so we move on
                question_id, yt_urls = session.yt_question_urls[quiz_id].popitem()
                break

        # Should have the current question, the urls, and the quiz for it
        for yt_url in yt_urls:
            session.yt_urls_curr_pos += 1
            msg = "<br />Processing " + str(yt_url)

            try:
                # Get yt video info
                # session.yt_urls_error_msg += "A"
                # yt, stream, res = find_best_yt_stream(yt_url)
                # session.yt_urls_error_msg += "AB"

                # Start download or get current db entry for this video
                # media_file = queue_up_yt_video(yt_url, yt, res, current_course_name)
                media_file = queue_up_yt_video(yt_url, current_course_name)
                # session.yt_urls_error_msg += "B"
                vid_guid = media_file.media_guid
                # title = media_file.title
                # description = media_file.description
                # category = media_file.category
                # tags = media_file.tags

                # Now replace the value in the canvas page
                smc_url = URL('media', 'player', args=[vid_guid], host=True)
                msg += "Replacing " + str(yt_url) + " with " + str(smc_url)

                Canvas.replace_value_in_question_page(current_course, quiz_id, question_id, yt_url, smc_url)
                pass
            except Exception as ex:
                session.yt_urls_error_msg += "<br/>\nError getting video " + str(yt_url) + " -> " + str(ex)

    elif len(session.yt_discussion_urls) > 0:
        discussion_id, yt_urls = session.yt_discussion_urls.popitem()
        for yt_url in yt_urls:
            session.yt_discussion_urls_curr_pos += 1
            msg = "<br />Processing " + str(yt_url)

            try:
                # Get yt video info
                # session.yt_urls_error_msg += "A"
                # yt, stream, res = find_best_yt_stream(yt_url)
                # session.yt_urls_error_msg += "AB"

                # Start download or get current db entry for this video
                # media_file = queue_up_yt_video(yt_url, yt, res, current_course_name)
                media_file = queue_up_yt_video(yt_url, current_course_name)
                # session.yt_urls_error_msg += "B"
                vid_guid = media_file.media_guid
                # title = media_file.title
                # description = media_file.description
                # category = media_file.category
                # tags = media_file.tags

                # Now replace the value in the canvas page
                smc_url = URL('media', 'player', args=[vid_guid], host=True)
                msg += "Replacing " + str(yt_url) + " with " + str(smc_url)

                Canvas.replace_value_in_discussion_page(current_course, discussion_id, yt_url, smc_url)
                pass
            except Exception as ex:
                session.yt_urls_error_msg += "<br/>\nError getting video " + str(yt_url) + " -> " + str(ex)

    elif len(session.yt_assignment_urls) > 0:
        assignment_id, yt_urls = session.yt_assignment_urls.popitem()
        for yt_url in yt_urls:
            session.yt_urls_curr_pos += 1
            msg = "<br />Processing " + str(yt_url)

            try:
                # Get yt video info
                # session.yt_urls_error_msg += "A"
                # yt, stream, res = find_best_yt_stream(yt_url)
                # session.yt_urls_error_msg += "AB"

                # Start download or get current db entry for this video
                # media_file = queue_up_yt_video(yt_url, yt, res, current_course_name)
                media_file = queue_up_yt_video(yt_url, current_course_name)
                # session.yt_urls_error_msg += "B"
                vid_guid = media_file.media_guid
                # title = media_file.title
                # description = media_file.description
                # category = media_file.category
                # tags = media_file.tags

                # Now replace the value in the canvas page
                smc_url = URL('media', 'player', args=[vid_guid], host=True)
                msg += "Replacing " + str(yt_url) + " with " + str(smc_url)

                Canvas.replace_value_in_assignment_page(current_course, assignment_id, yt_url, smc_url)
                pass
            except Exception as ex:
                session.yt_urls_error_msg += "<br/>\nError getting video " + str(yt_url) + " -> " + str(ex)
    else:
        # No more of anything to process
        msg = "<br /><br /><b>Finished!</b>"
        finished = True

    session.yt_urls_msg += msg

    if finished is not True:
        session.yt_urls_status = str(session.yt_urls_curr_pos) + " of " + str(session.yt_urls_total_len) + \
            " videos processed..."
    else:
        session.yt_urls_status = ""

    if finished is not True:
        response.js = "web2py_component('" + \
                      URL('media', 'find_replace_step_youtube_progress.load', user_signature=True) +\
                      "', 'process_queue_view');"
    else:
        # response.js = "$('#process_queue_progress_img').hide();"
        response.js = "$('#process_queue_progress_img').hide();"

    return dict(output=XML(session.yt_urls_msg), status=XML(session.yt_urls_status),
                errors=XML(session.yt_urls_error_msg))


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_step_youtube_progress_dl_queue():
    query = (db.media_files.youtube_url != "")
    fields = [db.media_files.title, db.media_files.needs_downloading,
              db.media_files.modified_on, db.media_files.id,
              db.media_files.media_guid]
    links = [
        (dict(header=T('Title'), body=lambda row: A(row.title,
                                                    _href=(URL('media', 'player', extension=False) + "/"
                                                           + row.media_guid), _target='blank'))),
        (dict(header=T('Status'), body=lambda row: DIV(getYouTubeTaskStatus(row.media_guid), ))),  # BR(), A('Re-Queue',
        #        _href=URL('media',
        #                  'reset_queued_item',
        #                  args=[row.id],
        #                  user_signature=True))))),
        (dict(header=T('Queued On'), body=lambda row: row.modified_on)),
        # Check if getTaskProgress is generic enough for this too?
        (dict(header=T('Progress'), body=lambda row: getYouTubeTaskProgress(row.media_guid))),
    ]

    db.media_files.id.readable = False
    db.media_files.media_guid.readable = False
    db.media_files.modified_on.readable = True
    db.media_files.needs_downloading.readable = False
    db.media_files.title.readable = False
    db.media_files.modified_on.readable = False
    headers = {'media_files.modified_on': 'Queued On'}

    maxtextlengths = {'media_files.title': 80, 'media_files.media_guid': 80}

    # rows = db(query).select()
    process_grid = SQLFORM.grid(query, editable=False, create=False, deletable=False, csv=False,
                                links=links, links_in_grid=True, details=False, searchable=False,
                                orderby=[~db.media_files.modified_on], fields=fields,
                                headers=headers, maxtextlengths=maxtextlengths)

    response.js = "setTimeout(function() {web2py_component('" + \
                  URL('media', 'find_replace_step_youtube_progress_dl_queue.load', user_signature=True) + \
                  "', 'process_queue_view_dl_progress');}, 3000);"
    return dict(process_grid=process_grid)
