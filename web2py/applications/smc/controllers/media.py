# -*- coding: utf-8 -*-
import os
import time
import uuid
import re
import glob
from gluon.contrib.simplejson import loads, dumps

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
                                 deletable=True,csv=False,links=links,links_in_grid=True,
                                 details=False,searchable=False,
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

    width = '640'  # '720' ,'640'
    height = '385'  # '433' ,'385'
    iframe_width = '650'  # '650'
    iframe_height = '405'  # '405'
    views = 0

    title = ""
    description = ""
    tags = ""
    # default to off

    document_id = request.args(0)
    if document_id is not None:
        document_id = document_id.strip()
        # Load the doc from the database
        prefix = document_id[0:2]
        poster = getDocumentThumb(document_id)  # URL('static', 'media' + "/" + prefix + "/" + movie_id + ".poster.png")
        source_doc = URL('static', 'documents/' + prefix + "/" + document_id)

        document_file = db(db.document_files.document_guid == document_id).select().first()
        if document_file is not None:
            title = document_file.title
            description = document_file.description
            tags = ",".join(document_file.tags)
            views = document_file.views
            if views is None:
                views = 0
            db(db.document_files.document_guid == document_id).update(views=views + 1)
        pass
    else:
        document_id = ""

    return dict(source_doc=source_doc, poster=poster,
                document_id=document_id, width=width, height=height, title=title,
                description=description, tags=tags,
                iframe_width=iframe_width, iframe_height=iframe_height, views=views)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators') or auth.has_membership('Media Upload'))
def upload_media():
    ret = start_process_videos()
    
    # rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.media_file_import_queue, showid=False,
                   fields=['title', 'description', 'category', 'tags', 'media_file'],
                   _name="queue_media").process(formname="queue_media")
    
    import_form = SQLFORM.factory(submit_button="Import Videos", _name="import_videos").process(formname="import_videos")
    if import_form.accepted:
        result = scheduler.queue_task('update_media_database_from_json_files', pvars=dict(), timeout=18000, immediate=True, sync_output=5, group_name="process_videos")
        response.flash = "Import process started!"  # + str(result)
        
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
    return dict(form=form, ret=ret, import_form=import_form)


@auth.requires(
    auth.has_membership('Faculty') or auth.has_membership('Administrators') or auth.has_membership('Media Upload'))
def upload_document():
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

        response.flash = "Document Uploaded"  # + str(result)
        pass
    elif form.errors:
        response.flash = "Error! "  # + str(form.errors)
    else:
        # response.flash = "Process Queue: " + str(ret)
        pass

    ret = ""
    return locals()  # dict(form=form, ret=ret)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators') or auth.has_membership('Media Upload'))
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


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators') or auth.has_membership('Media Upload'))    
def upload_ajax_callback():
    return response.json({ 'success': 'true'})


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators') or auth.has_membership('Media Upload'))
def process_queue():
    ret = start_process_videos()
    
    query = (db.media_file_import_queue)
    fields = [db.media_file_import_queue.title, db.media_file_import_queue.status, db.media_file_import_queue.modified_on,  db.media_file_import_queue.id, db.media_file_import_queue.media_guid]
    links = [
            (dict(header=T('Title'), body=lambda row: A(row.title, _href=(URL('media', 'player', extension=False) + "/" + row.media_guid) , _target='blank'  ) ) ),
            (dict(header=T('Status'),body=lambda row: DIV( getTaskStatus(row.id), BR(), A('Re-Queue', _href=URL('media', 'reset_queued_item', args=[row.id], user_signature=True)) ) ) ),
            (dict(header=T('Queued On'), body=lambda row: row.modified_on  ) ),
            (dict(header=T('Progress'), body=lambda row: getTaskProgress(row.id) ) ),
            ]
    
    db.media_file_import_queue.id.readable=False
    db.media_file_import_queue.media_guid.readable=False
    db.media_file_import_queue.modified_on.readable=True
    db.media_file_import_queue.status.readable=False
    db.media_file_import_queue.title.readable=False
    db.media_file_import_queue.modified_on.readable=False    
    headers = {'media_file_import_queue.modified_on':'Queued On' }
    
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
        
        response.flash = "Media File Deleted" # + str(ret)
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
    
    return dict(poster=poster, source_ogg=source_ogg, source_mp4=source_mp4, source_mobile_mp4=source_mobile_mp4, source_webm=source_webm, movie_id=movie_id, width=width, height=height, title=title,description=description, tags=tags, autoplay=autoplay, iframe_width=iframe_width, iframe_height=iframe_height)


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
        sql = "UPDATE imas_questionset SET extref='" + row.extref_field + "' WHERE id='" + str(row.wamap_id) + "' and extref LIKE '%admin.correctionsed.com/media/wamap/%'"
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
    db_wamap.executesql("UPDATE imas_questionset SET `extref`=REPLACE(`extref`, 'video!!www.yout', 'video!!http://www.yout') WHERE `extref` like '%video!!www.yout%' ")

    # Adjust IFrame links in some places so they match up better with videos
    # <iframe src="https://admin.correctionsed.com/media/wmplay/45390ef384be4107a7bf2c2da31ce79a"
    #  width="560" height="315">
    # Change out 560x315 and 420x315 for ---> 655x410
    # fix iframe src w // instad of http://
    # imas_inlinetext.text
    table_name = "imas_inlinetext"
    col_name = "text"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name + "` like '%src=\"//www.yout%' ")
    # imas_questionset.qtext
    table_name = "imas_questionset"
    col_name = "qtext"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name + "` like '%src=\"//www.yout%' ")
    # imas_questionset.extref
    table_name = "imas_questionset"
    col_name = "extref"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name + "` like '%src=\"//www.yout%' ")
    # imas_questionset.control
    table_name = "imas_questionset"
    col_name = "control"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name + "` like '%src=\"//www.yout%' ")
    # imas_assessments.intro
    table_name = "imas_assessments"
    col_name = "intro"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name + "` like '%src=\"//www.yout%' ")
    # imas_linkedtext.summary
    table_name = "imas_linkedtext"
    col_name = "summary"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name + "` like '%src=\"//www.yout%' ")
    # imas_linkedtext.text
    table_name = "imas_linkedtext"
    col_name = "text"
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"560\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"560\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'width=\"420\" height=\"315\"', 'width=\"655\" height=\"410\"') WHERE `" + col_name + "` like '%width=\"420\" height=\"315\"%' ")
    db_wamap.executesql("UPDATE " + table_name + " SET `" + col_name + "`=REPLACE(`" + col_name + "`, 'src=\"//www.yout', 'src=\"http://www.yout') WHERE `" + col_name + "` like '%src=\"//www.yout%' ")
    
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
    result = scheduler.queue_task('process_wamap_video_links', timeout=18000, repeats=(db(db.wamap_questionset).count()/50), period=0, immediate=True)
        
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
    cmd = "/usr/bin/nohup /usr/bin/python " + os.path.join(request.folder, 'static/scheduler/start_scheduler.py') + " > /dev/null 2>&1 &"
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
    # cmd = "/usr/bin/nohup /usr/bin/python " + os.path.join(request.folder, 'static/scheduler/start_wamap_delete_scheduler.py') + " > /dev/null 2>&1 &"
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
    # cmd = "/usr/bin/nohup /usr/bin/python " + os.path.join(request.folder, 'static/scheduler/start_process_video_scheduler.py') + " > /dev/null 2>&1 &"
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
    # cmd = "/usr/bin/nohup /usr/bin/python " + os.path.join(request.folder, 'static/scheduler/start_wamap_videos_scheduler.py') + " > /dev/null 2>&1 &"
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


def getTaskStatus(media_id):
    q1 = '{"media_id": "' + str(media_id) + '"}'
    q2 = '{"media_id": ' + str(media_id) + '}'
    task = db_scheduler((db_scheduler.scheduler_task.vars==q1) | (db_scheduler.scheduler_task.vars==q2)).select(orderby=db_scheduler.scheduler_task.last_run_time).first()
    ret = "<not run>"
    if task is not None:
        ret = str(task.status) + " (" + str(task.last_run_time) + ")"
    return ret


def getTaskProgress(media_id):
    ret = ""
    
    q1 = '{"media_id": "' + str(media_id) + '"}'
    q2 = '{"media_id": ' + str(media_id) + '}'
    task = db_scheduler((db_scheduler.scheduler_task.vars==q1) | (db_scheduler.scheduler_task.vars==q2)).select(join=db_scheduler.scheduler_run.on(db_scheduler.scheduler_task.id==db_scheduler.scheduler_run.task_id), orderby=db_scheduler.scheduler_task.last_run_time).first()
    ret = ""
    if task is not None:
        # Get the output from the run record
        ret = str(task.scheduler_run.run_output)
    
    return ret
