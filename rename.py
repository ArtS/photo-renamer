#!/usr/bin/env python
import argparse
from glob import glob
import exifread
import os

def rename(path):
    files = []
    for file in os.listdir(path):
        fPath, nameOnly = os.path.split(file)
        if nameOnly.lower().endswith('.jpg') or nameOnly.lower().endswith('.png'):
            files.append(os.path.join(path, file))

    for file in files:
        exif = None
        with open(file, 'rb') as f:
            exif = exifread.process_file(f)

        if exif is None:
            print('%s has no Exif, skipping' % file)
            continue

        keyStr = 'EXIF DateTimeOriginal'
        if not exif.has_key(keyStr):
            print('%s has no date tag, skipping' % file)
            #print(exif)
            continue

        datetime = exif[keyStr]

        datetime = datetime.values
        if len(datetime) != 19:
            print('Invalid datetime')
            continue

        fPath, nameOnly = os.path.split(file)
        if nameOnly.lower().endswith('.jpg'):
            ext = 'jpg'
        elif nameOnly.lower().startswith('.png'):
            ext = 'png'
        else:
            path, ext = os.path.splitext(file)

        newFileName = '%s.%s' % (datetime.replace(':', '.'), ext)
        newPathFileName = os.path.join(os.path.dirname(file), newFileName)

        if os.path.exists(newPathFileName):
            continue

        print('Renaming %s to %s' % (file, newPathFileName))
        os.rename(file, newPathFileName)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('path', metavar='path', type=str,
                         help='folder to path with photos')
    args = parser.parse_args()
    rename(**vars(args))
