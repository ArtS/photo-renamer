#!/usr/bin/env python3
import argparse
import exifread
import os
import re
from datetime import timezone

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

pattern = re.compile('(.*)_(\d+)$')

def get_new_unique_filename(pathName, n=0):
    if not os.path.exists(pathName):
        return pathName

    fPath, nameAndExt = os.path.split(pathName)
    origFileName, ext = os.path.splitext(nameAndExt)

    baseFileName = ''
    parsedFileName = pattern.findall(origFileName)
    if parsedFileName:
        baseFileName = parsedFileName[0][0]
        n = int(parsedFileName[0][1])
    else:
        baseFileName = origFileName

    n = n + 1

    newName = '%s_%s%s' % (baseFileName, n, ext)
    return get_new_unique_filename(os.path.join(fPath, newName), n)

def get_media_files(path, allFileNames, exts):
    files = []
    for file in allFileNames:
        fPath, nameOnly = os.path.split(file)
        for ext in exts:
            if nameOnly.lower().endswith(ext.lower()):
                files.append(os.path.join(path, file))
                break
    return files

def get_media_files_recursive(path, is_recursive, exts):
    print('processing: %s' % path)
    files = []

    for root, subdirs, allFileNames in os.walk(path):
        print('Root: ', root)
        if (not is_recursive and root != '.'):
            print('Skipping %s as not recursive', root)
            continue
        files.extend(get_media_files(root, allFileNames, exts))

    return files


def normalise_datetime(date_time):
    return date_time.replace('-', '.').replace(':', '.')


def try_get_exif_tag(file_name, tag_name, exif):
    if tag_name not in exif:
        print('%s has no tag "%s"' % (file_name, tag_name))
        return None

    return exif[tag_name]


def get_image_file_created_date_time(file_name):

    exif = None
    with open(file_name, 'rb') as f:
        exif = exifread.process_file(f)

    if exif is None:
        print('%s has no Exif, skipping' % file_name)
        return None

    #for k in exif:
    #    print('%s: %s' % (k, exif[k]))

    key_str = 'EXIF DateTimeOriginal'
    created_date_time = try_get_exif_tag(file_name, key_str, exif)

    fallback_key_str = 'Image DateTime'
    if not created_date_time or created_date_time.values == '0000:00:00 00:00:00':
        created_date_time = try_get_exif_tag(file_name, fallback_key_str, exif)

    if not created_date_time:
        #print(exif)
        return None

    created_date_time = created_date_time.values
    if len(created_date_time) != 19:
        print('Invalid created_date_time: %s' % file_name)
        return None

    return created_date_time.replace(':', '.')


def get_video_file_created_date_time(file_name):
    parser = createParser(file_name)

    metadata = extractMetadata(parser, 1.0)
    if not metadata:
        return None

    m_item = metadata.getItems('creation_date')
    utc_dt = m_item.values[0].value
    local_dt = utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

    return local_dt.strftime('%Y.%m.%d %H.%M.%S')


def is_image_file(ext):
    return ext.lower() in ['.png', '.jpg', '.jpeg']


def get_file_created_date_time(file_name):

    _, ext = os.path.splitext(file_name)

    if is_image_file(ext):
        return get_image_file_created_date_time(file_name)
        pass
    else:
        return get_video_file_created_date_time(file_name)


def rename_photos(path, is_real_rename, is_recursive):
    files = get_media_files_recursive(path, is_recursive, ['png', 'jpg', 'jpeg', 'm4v', 'mp4', 'mov', 'mpg'])

    for file_name in files:

        created_date_time = get_file_created_date_time(file_name)
        if created_date_time is None:
            continue

        _, ext = os.path.splitext(file_name)
        new_file_name = '%s%s' % (created_date_time, ext.lower())
        new_path_file_name = os.path.join(os.path.dirname(file_name), new_file_name)

        if new_path_file_name == file_name:
            #print('No need to rename, skipping...')
            continue

        if os.path.exists(new_path_file_name):
            print('Would rename %s to %s but it already exists, generating new name...' % (file_name, new_path_file_name))
            new_path_file_name = get_new_unique_filename(new_path_file_name)

        print('%s -> %s' % (file_name, os.path.split(new_path_file_name)[1]))
        print('%s -> %s' % (os.path.split(file_name)[1], os.path.split(new_path_file_name)[1]))

        if is_real_rename:
            os.rename(file_name, new_path_file_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # store_true sets true only when option is specifies
    parser.add_argument('--recursive', action='store_true',
                         help='Process all folders and subfolders in the given path')
    parser.add_argument('--rename', action='store_true',
                         help='Actually rename, don''t just do a dry run')
    parser.add_argument('path', metavar='/path/to/folder/', type=str,
                         help='folder to path with photos')
    args = parser.parse_args()
    rename_photos(args.path, args.rename, args.recursive)
