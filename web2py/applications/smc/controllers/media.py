# -*- coding: utf-8 -*-
import os
import tempfile
import time
import uuid
import re
import glob
import mimetypes
from gluon.contrib.simplejson import loads, dumps

from ednet.canvas import Canvas

from pytube import YouTube


def index():
    ret = start_process_videos()
    
    query = (db.media_files)
    links = []
    if auth.has_membership('Faculty') or auth.has_membership('Administrators'):
        links.append(dict(header=T(''),body=lambda row: A('[Delete]', _style='font-size: 10px; color: red;', _href=URL('media', 'delete_media', args=[row.media_guid], user_signature=True)) ) )
    links.append(dict(header=T(''),body=lambda row: A(IMG(_src=getMediaThumb(row.media_guid), _style="width: 128px;"), _href=URL('media', 'player', args=[row.media_guid], user_signature=True)) ) )
    fields = [db.media_files.id, db.media_files.title, db.media_files.tags, db.media_files.description, db.media_files.media_guid, db.media_files.category] #[db.media_files.title]
    maxtextlengths = {'media_files.title': '150', 'media_files.tags': '50', 'media_files.description': '150'}
    
    # Hide columns
    db.media_files.id.readable=False
    db.media_files.media_guid.readable=False
    db.media_files.width.readable=False
    db.media_files.height.readable=False
    db.media_files.original_file_name.readable=False
    db.media_files.media_type.readable=False
    db.media_files.quality.readable=False
    
    # rows = db(query).select()
    media_grid = SQLFORM.grid(query,editable=False, create=False, deletable=False,
                              csv=False, details=False,
                              searchable=True, orderby=[~db.media_files.modified_on],
                              fields=fields, paginate=15,
                              links=links, links_placement='left', links_in_grid=True,
                              maxtextlengths=maxtextlengths)
    
    return dict(media_grid=media_grid)


def documents():

    query = (db.document_files)
    links = []
    if auth.has_membership('Faculty') or auth.has_membership('Administrators'):
        links.append(dict(header=T(''), body=lambda row: A('[Delete]', _style='font-size: 10px; color: red;',
                                                    _href=URL('media', 'delete_document', args=[row.document_guid],
                                                    user_signature=True))))
    links.append(dict(header=T(''), body=lambda row: A(TABLE(TR(
                                                TD(IMG(_src=getDocumentThumb(row.document_guid), _style="width: 24px;"),
                                                   _width=26),
                                                TD(LABEL(row.title), _align="left")
                                                )),
                                                _href=URL('media', 'view_document', args=[row.document_guid],
                                                user_signature=True))))
    fields = [db.document_files.id, db.document_files.title, db.document_files.tags, db.document_files.description,
              db.document_files.document_guid, db.document_files.category]  # [db.document_files.title]
    maxtextlengths = {'document_files.title': '150', 'document_files.tags': '50', 'document_files.description': '150'}

    # Hide columns
    db.document_files.id.readable = False
    db.document_files.title.readable = False
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
    ret = start_process_videos()
    
    poster = URL('static', 'projekktor-1.3.09') + '/media/intro.png'
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
    # default to off
    autoplay = "false"
    if request.vars.autoplay == "true":
        autoplay = "true"
    
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
        
        media_file = db(db.media_files.media_guid==movie_id).select().first()
        if media_file is not None:
            title = media_file.title
            description = media_file.description
            tags = ",".join(media_file.tags)
            views = media_file.views
            if views is None:
                views = 0
            db(db.media_files.media_guid == movie_id).update(views=views+1)
        pass
    else:
        movie_id = ""
    
    return dict(poster=poster, source_ogg=source_ogg, source_mp4=source_mp4,
                source_mobile_mp4=source_mobile_mp4, source_webm=source_webm,
                movie_id=movie_id, width=width, height=height, title=title,
                description=description, tags=tags, autoplay=autoplay,
                iframe_width=iframe_width, iframe_height=iframe_height, views=views)


def view_document():

    width = '100%' # '724'  # '640'  # '720' ,'640'
    height = '700'  # '385'  # '433' ,'385'
    iframe_width = '100%' # '734'  # '650'
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
    dl_link = A('Download', _href=URL('media','dl_document', args=[document_id]))
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


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators') or auth.has_membership('Media Upload'))
def upload_media():
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
        result = scheduler.queue_task('process_media_file', pvars=dict(media_id=new_id), timeout=18000, immediate=True, sync_output=5, group_name="process_videos")
        response.flash = "Media File Queued!"  # + str(result)
        pass
    elif form.errors:
        response.flash = "Error! "  # + str(form.errors)
    else:
        # response.flash = "Process Queue: " + str(ret)
        pass

    ret = ""
    return dict(form=form, ret=ret)


@auth.requires(
    auth.has_membership('Faculty') or auth.has_membership('Administrators') or auth.has_membership('Media Upload'))
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
        f = os.open(target_file + ".json", os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        os.write(f, meta_json)
        os.close(f)

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
    
    maxtextlengths = {'media_file_import_queue.title': '80', 'media_file_import_queue.media_guid': '80'}
    
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


def getURLS(txt):
    # Extract the list of urls from the string
    ret = []
    # pat = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
    pat = re.compile(
                     'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                    )
    res = pat.findall(txt)
    for r in res:
        if 'youtu' in r:
            ret.append(r)
    return ret


def getPDFURLS(txt):
    # Extract the list of urls from the string
    ret = []
    # pat = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
    pat = re.compile(
                     'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                    )
    res = pat.findall(txt)
    # pdf, swf, png, doc, ?
    for r in res:
        if 'pdf' in r:
            ret.append(r)
    return ret


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def utilities():
    # Just a landing page
    return locals()


def scan_media_files():
    # Find all media files and make sure they are in the database.
    form = SQLFORM.factory(submit_button="Import Videos", _name="import_videos").process(
        formname="import_videos")
    if form.accepted:
        result = scheduler.queue_task('update_media_database_from_json_files', pvars=dict(), timeout=18000,
                                      immediate=True, sync_output=5, group_name="process_videos")
        response.flash = "Import process started!"  # + str(result)

    return dict(form=form)


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
    if media_guid is None or media_guid =="":
        return ""
    prefix = media_guid[0:2]
    url = URL('static', 'media/' + prefix + '/' + media_guid + '.thumb.png')
    thumb = os.path.join(request.folder, 'static')
    thumb = os.path.join(thumb, 'media')
    thumb = os.path.join(thumb, prefix)
    thumb = os.path.join(thumb, media_guid)
    thumb += '.thumb.png'
    if os.path.exists(thumb) is not True:
        url = URL('static', 'images/media_file.png')
    return url


def getDocumentThumb(document_guid):
    if document_guid is None or document_guid == "":
        return ""
    prefix = document_guid[0:2]
    url = URL('static', 'documents/' + prefix + '/' + document_guid + '.thumb.png')
    thumb = os.path.join(request.folder, 'static')
    thumb = os.path.join(thumb, 'documents')
    thumb = os.path.join(thumb, prefix)
    thumb = os.path.join(thumb, document_guid)
    thumb += '.thumb.png'
    if os.path.exists(thumb) is not True:
        url = URL('static', 'images/document_file.png')
    return url


def getMediaPoster(media_guid):
    if media_guid is None or media_guid =="":
        return ""
    prefix = media_guid[0:2]
    url = URL('static', 'media/' + prefix + '/' + media_guid + '.poster.png')
    thumb = os.path.join(request.folder, 'static')
    thumb = os.path.join(thumb, 'media')
    thumb = os.path.join(thumb, prefix)
    thumb = os.path.join(thumb, media_guid)
    thumb += '.thumb.png'
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
                              ") - reload page and try again.<br /> " + \
                              "<span style='font-size: 10px; font-weight: bold;'>" + \
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
                keepvalues=True, _name="yt_step2", _action=URL('media', 'pull_from_youtube_step_2.load'))

    if form.process(formname="yt_step2").accepted:
        # Start download or get current db entry for this video
        media_file = queue_up_yt_video(yt_url, yt, res, form.vars.category)
        # Override the values we collected
        media_file.update_record(title=form.vars.title, description=form.vars.desc)
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

    maxtextlengths = {'media_files.title': '80', 'media_files.media_guid': '80'}

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
    course_list = []
    course_dict = dict()

    courses = Canvas.get_courses_for_faculty(auth.user.username)

    for c in courses:
        course_dict[str(c)] = courses[c]
        course_list.append(OPTION(courses[c], _value=c))

    course_select = SELECT(course_list, _name="current_course", _id="current_course", _style="width: 600px;")

    form = FORM(TABLE(TR("Choose A Course: ", course_select),
                      TR("", INPUT(_type="submit", _value="Next"))), _name="fr_step1").process(formname="fr_step1")

    if form.accepted:
        cname = course_dict[str(form.vars.current_course)]
        cid = form.vars.current_course
        redirect(URL("find_replace_step_2.load", vars=dict(current_course=cid,
                                                           current_course_name=cname)))
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
                 _action=URL('media', 'find_replace_step_2.load')).process()

    if form2.accepted:
        # Save which option and redirect to that page
        if form2.vars.fr_option == "auto_youtube_tool":
            redirect(URL('media', 'find_replace_step_youtube.load'))
            pass
        elif form2.vars.fr_option == "auto_google_docs_tool":
            response.flash = "Google"
            pass
        elif form2.vars.fr_option == "custom_regex":
            # response.flash = "RegEx"
            redirect(URL('media', 'find_replace_step_custom_regex.load'))
            pass
        else:
            response.flash = "Unknown Option!"
        pass

    return dict(form2=form2, current_course=current_course, current_course_name=current_course_name,
                server_url=server_url)


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

    return txt


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def find_replace_step_custom_regex_run(current_course, find_pattern, replace_pattern, update_canvas=False):
    ret = ""

    ret += "<h2>Searching with pattern: </h2> <b>Find</b>(" + \
           find_pattern.replace(">", "&gt;").replace("<", "&lt;") + \
           ") / <b>Replace</b> (" + replace_pattern.replace(">", "&gt;").replace("<", "&lt;") + ") " + \
           "<p><b>Note:</b> Local URLs may not work in this view but work fine when viewed from Canvas.</p><hr/>"

    style = "width: 100%; height: 800px; overflow: auto; display: none; border: 1px solid black;"

    # Get the list of pages
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

    # Work on list of quizzes
    quizzes = Canvas.get_quizz_list_for_course(current_course)
    total_quizzes = len(quizzes)
    ret += "<h3>Searched " + str(total_quizzes) + " quizzes</h3>" + \
           "<div onclick='$(\"#show_hide_quizzes\").toggle();' style='cursor: pointer;'><h4>QUIZZES PROCESSED:" + \
           "<span style='font-size:8px;'>(click to open/close)</span></h4></div>" + \
           "<div id='show_hide_quizzes' style='" + style + "'>"
    inc = 0
    for q in quizzes:
        inc += 1
        total_qq_replacements = 0
        quizz_id = q
        q_orig_text = quizzes[q]
        q_new_text, subs = re.subn(find_pattern, replace_pattern, q_orig_text)
        q_new_text = find_replace_post_process_text(current_course, q_new_text)

        ret += "<H5><div onclick='$(\"#show_hide_q_" + str(inc) + "\").toggle();' style='cursor: pointer;'>QUIZZ: " + \
               str(q) + " - " + str(subs) + "/<QQ_COUNT_" + str(quizz_id) + "> matches. " + \
               "<span style='font-size:8px;'>(click to open/close)</span></div></H5>"

        ret += "<div id='show_hide_q_" + str(inc) + "' style='" + style + "'>"
        ret += "<h2>OLD QUIZZ DESCRIPTION</h2>"
        ret += "<code>" + q_orig_text + "</code>"
        ret += "<hr />"
        ret += "<h2>NEW QUIZZ DESCRIPTION</h2>"
        ret += "<code>" + q_new_text + "</code>"

        if subs > 0 or q_orig_text != q_new_text:
            # Update the page in canvas
            new_page = dict()
            new_page["quiz[body]"] = q_new_text
            result = ""
            if update_canvas is True:
                result = Canvas.update_quizz_for_course(current_course, quizz_id, new_page)
            else:
                result = "NOT UPDATING!"
            ret += "UPDATE QUIZZ RESULT: " + str(result)

        quizz_questions = Canvas.get_quizz_questions_for_quizz(current_course, quizz_id)
        total_questions = len(quizz_questions)
        qq_inc = 0
        for qq in quizz_questions:
            qq_inc += 1
            qq_id = qq
            qq_orig_text = quizz_questions[qq]
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
                new_page["quizz_id"] = quizz_id
                new_page["question[question_text]"] = qq_new_text
                result = ""
                if update_canvas is True:
                    result = Canvas.update_quizz_question_for_course(current_course, quizz_id, qq_id, new_page)
                else:
                    result = "NOT UPDATING!"
                ret += "UPDATE QUESTION RESULT: " + str(result)

        # Enter question replacements so we can see how many matches there were
        ret = ret.replace("<QQ_COUNT_" + str(quizz_id) + ">", str(total_qq_replacements))

        ret += "</div>"

    # Close show/hide for all quizzes
    ret += "</div>"

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
                 _action=URL('media', 'find_replace_step_custom_regex.load'),
                 _name="form2").process(keepvalues=True, formname="form2")

    pre_defined_patterns = {
        "Change Host Links - (smc.sbctc... -> smc.ed)": ["smc.sbctc.correctionsed.com", "smc.ed"],
        "Change Host Links - (smc.ed -> smc.sbctc...)": ["smc.ed", "smc.sbctc.correctionsed.com"],
        "IDEA - Listen Audio (change media tag to correct url)":
            [r'''<audio .* src=["'](.*)/courses/([0-9]+)/media_download\?entryId=(m-[0-9a-zA-Z]+)(.*)redirect=1(["']) .*>.*</audio>''',
             r'''<audio controls="controls"><source src="\1/courses/\2/files/<CANVAS_FILE_ID__\3__>/download?download_frd=1" orig_filename="\3" /></audio>'''],
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
                 _action=URL('media', 'find_replace_step_custom_regex.load'),
                 _name="form3").process(keepvalues=True, formname="form3")

    if form2.accepted:
        # Note - leaving write_changes unchecked w an empty replace should be "find only"
        if form2.vars.find_pattern != "":  # and form2.vars.replace_pattern != "":
            # Run find/replace pattern
            find_pattern = form2.vars.find_pattern
            replace_pattern = form2.vars.replace_pattern

            write_changes = False
            if form2.vars.write_changes is not None:
                print("write changes")
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

    # Find all known instances of youtube links in the canvas course.
    yt_urls = dict()
    pages = Canvas.get_page_list_for_course(current_course)
    total_urls = 0
    for p in pages:
        urls = getURLS(pages[p])
        if len(urls) > 0:
            total_urls += len(urls)
            yt_urls[p] = urls

    session.yt_urls = yt_urls
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
    if len(session.yt_urls) < 1:
        msg = "<br /><br /><b>Finished!</b>"
        finished = True
    else:
        page_url, yt_urls = session.yt_urls.popitem()
        for yt_url in yt_urls:
            session.yt_urls_curr_pos += 1
            msg = "<br />Processing " + str(yt_url)

            try:
                # Get yt video info
                # session.yt_urls_error_msg += "A"
                yt, stream, res = find_best_yt_stream(yt_url)
                # session.yt_urls_error_msg += "AB"

                # Start download or get current db entry for this video
                media_file = queue_up_yt_video(yt_url, yt, res, current_course_name)
                # session.yt_urls_error_msg += "B"
                vid_guid = media_file.media_guid
                title = media_file.title
                description = media_file.description
                category = media_file.category
                tags = media_file.tags

                # Now replace the value in the canvas page
                smc_url = URL('media', 'player', args=[vid_guid], host=True)
                msg += "Replacing " + str(yt_url) + " with " + str(smc_url)

                Canvas.replace_value_in_course_page(current_course, page_url, yt_url, smc_url)
                pass
            except Exception as ex:
                session.yt_urls_error_msg += "<br/>\nError getting video " + str(yt_url) + " -> " + str(ex)

    session.yt_urls_msg += msg

    session.yt_urls_status = str(session.yt_urls_curr_pos) + " of " + str(session.yt_urls_total_len) + \
                             " videos processed..."

    if finished is not True:
        response.js = "web2py_component('" + URL('media', 'find_replace_step_youtube_progress.load') +\
                      "', target='process_queue_view');"
    else:
        response.js = "$('#process_queue_progress_img').hide();"

    return dict(output=XML(session.yt_urls_msg), status=XML(session.yt_urls_status), errors=XML(session.yt_urls_error_msg))


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

    maxtextlengths = {'media_files.title': '80', 'media_files.media_guid': '80'}

    # rows = db(query).select()
    process_grid = SQLFORM.grid(query, editable=False, create=False, deletable=False, csv=False,
                                links=links, links_in_grid=True, details=False, searchable=False,
                                orderby=[~db.media_files.modified_on], fields=fields,
                                headers=headers, maxtextlengths=maxtextlengths)

    response.js = "setTimeout(function() {web2py_component('" + URL('media', 'find_replace_step_youtube_progress_dl_queue.load') + \
                  "', target='process_queue_view_dl_progress');}, 6000);"
    return dict(process_grid=process_grid)


def queue_up_yt_video(yt_url, yt, res, category=None):
    # Find the current video, or queue it up for download and return the db info

    vid_guid = str(uuid.uuid4()).replace('-', '')
    title = yt.title
    description = yt.description
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

        yt_thumbnail = None
        try:
            yt_thumbnail = yt.thumbnail_url
        except:
            pass

        result = scheduler.queue_task('pull_youtube_video', pvars=dict(yt_url=yt_url,
                                                                       media_guid=vid_guid,
                                                                       res=res,
                                                                       thumbnail_url=yt_thumbnail),
                                      timeout=18000, immediate=True, sync_output=5,
                                      group_name="download_videos")

        # Make sure to grab the new record now that it has been inserted
        media_file = db(db.media_files.youtube_url == yt_url).select().first()
    else:
        # Video exists, just return the db record
        pass

    return media_file


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
