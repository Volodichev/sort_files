# !/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import logging
import shutil
import time
import sys
import os
import re

from PIL.ExifTags import TAGS as PIL_TAGS
from PIL import Image as PIL_Image

from win32com.propsys import propsys, pscon
from pyexiv2 import Image as pyexiv2_Image
from piexif import TAGS as PIEXIF_TAGS
from tqdm import tqdm
import exifread
import piexif

from langdetect import detect, detect_langs
from transliterate import translit

SUPPORTED_EXTENSIONS = (
    '.jpg', '.png', '.gif', '.bmp', '.tiff', '.psd',
    '.mov', '.avi', '.mp4',
    '.mp3', '.m4a'
)
SETTING_EXTENSIONS = ('.AAE', '.aae', '.THM', '.thm')

FIND_SETS_FILES = True  # example .AAE, .THM
GROUP_NO_EXIF = True  # /result/no_exif
CYR_LANG = ['bg', 'ru', 'uk', 'mk', 'et', 'me', 'sr']

SCREENSHOTS_FOLDER = 'screenshots'
NO_EXIF_FOLDER = 'no_exif'
RESULT_FOLDER = 'result'
SOURCE_FOLDER = 'source'
TEMP_FOLDER = 'TEMPS'
LOG_FILE = 'log.log'

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# '
                           u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO, filename=LOG_FILE)


def sort_files(source_path=None, result_path=None):
    """
    Sort files with SUPPORTED_EXTENSIONS by creation date and
    put them to directories Year/Month/Day by exif  Date

    If file already exists in folder leave in in the source

    file = 'example.jpg'
    file_name = 'example'
    file_ext = '.jpg'
    file_path = 'C:\\users\\example.jpg'
    """

    current_path = os.path.abspath(os.curdir)
    if source_path is None:
        source_path = os.path.join(current_path, SOURCE_FOLDER)
    if result_path is None:
        result_path = make_new_folder(path=current_path, folder_name=RESULT_FOLDER)

    print(f'Search files in {source_path}')

    if contain_any(detect_languages(source_path), CYR_LANG):
        print(f'Path contains invalid symbols {source_path}')
        sys.exit()

    paths = []
    files_with_path = []

    for path, dirs, folder_files in os.walk(top=source_path, topdown=False):
        if path != source_path:
            paths.append(path)

        folder_files = filter(lambda f: f.lower().endswith(SUPPORTED_EXTENSIONS), folder_files)
        for file in folder_files:
            files_with_path.append({'path': path, 'file': file})

    # files_with_path.sort(key=lambda f: f['path'], reverse=True)
    fl_count = len(files_with_path)
    print(f'{fl_count} files found')

    for n in tqdm(range(0, fl_count), desc=f'move files', ncols=100):
        filedict = files_with_path[n-1]
        file = filedict['file']
        path = filedict['path']
        file_path = os.path.join(path, file)

        files = make_files_list(file=file, path=path)
        file_exif = get_exif(file_path=file_path)
        new_path = file_exif.make_new_path(path=result_path)
        if new_path == result_path:
            continue

        new_path, skip = duples_in_folder(new_path=new_path, file=file, file_exif=file_exif)
        if skip:
            logging.info(f'DUPLICATE: {path} ({files}) already in {new_path}')
            continue

        if move_files(files=files, path=path, new_path=new_path):
            logging.info(f'Moved: {path} ({files}) -> {new_path}')

    not_removed_paths = list(set(paths))

    for n in tqdm(range(0, len(paths)), desc=f'remove folders:', ncols=100):
        path = paths[n-1]
        if path in not_removed_paths:
            if remove_folder(path):
                not_removed_paths.remove(path)

    if not_removed_paths:
        not_removed_paths = ',\n'.join(not_removed_paths)
        print(f'This folders are not empty:\n{not_removed_paths}')


def contain_any(a_list: (list, set), b_list: (list, set)):
    """INNER JOIN of 2 lists(sets)"""
    return len(list(set(a_list) & set(b_list))) > 0


def duples_in_folder(new_path: str, file: str, file_exif=None):
    """What to do if file exist in folder"""
    skip = False
    if file_exif is None:
        skip = True
    else:
        if is_file_in_folder(file=file, path=new_path):
            # file with same name exist in new folder
            exist_file_path = os.path.join(new_path, file)
            exist_file_exif = get_exif(file_path=exist_file_path)

            if file_exif.is_same_with(exist_file_exif):
                # file has same name and same data
                skip = True

            else:
                # file has only same name
                file_name, file_ext = os.path.splitext(file)
                new_path = make_new_folder(path=new_path, folder_name=file_name)
                if is_file_in_folder(file=file, path=new_path):
                    skip = True

    return new_path, skip


def is_file_in_folder(file: str, path: str):
    """Check file in folder"""
    folder_elements = get_folder_elements(path=path)
    files = (file, file.lower())
    return contain_any(files, folder_elements)


def detect_languages(value: str, source_path=None):
    """Detect language of string"""

    langs = []
    if os.path.isdir(value):
        t_path = value
        t_folder = True
        while t_folder:
            if source_path and os.path.samefile(t_path, source_path):
                break

            t_path, t_folder = os.path.split(t_path)
            if re.findall(r'[^\W\d]', t_folder):
                for detect_lang in detect_langs(t_folder):
                    langs.append(str(detect_lang.lang))
    else:
        if re.findall(r'[^\W\d]', value):

            try:
                langs.append(str(detect(value)))
                for detect_lang in detect_langs(value):
                    langs.append(str(detect_lang.lang))
            except Exception as e:
                logging.error(f'Can\'t detect language: ({value})\nerror: {e}')

    return set(langs)


def make_files_list(file: str, path: str):
    """Make file list, if FIND_SETS_FILES add setting files"""
    files = [file]
    if FIND_SETS_FILES:
        file_name, file_ext = os.path.splitext(file)
        folder_elements = os.listdir(path)
        temp_files = []
        for temp_ext in SETTING_EXTENSIONS:
            temp_files.append(''.join((file_name, temp_ext)))
        temp_files = list(set(temp_files) & set(folder_elements))
        if temp_files:
            files.extend(temp_files)

    return files


def translit_name(value: str, from_ru=None):
    """Transliterate string"""
    lang = 'ru'
    if re.findall(r'[^\W\d]', value):
        if from_ru:
            value = translit(value=value, language_code=lang, reversed=from_ru)
        elif not from_ru:
            value = translit(value=value, language_code=lang, reversed=from_ru)

    return value


def move_files(files: list, path: str, new_path: str):
    """Move files to 'new_path' directory"""
    ans = False
    exist_folder_elements = get_folder_elements(new_path)

    for file in files:
        if file.lower() not in exist_folder_elements:
            file_path = os.path.join(path, file)
            try:
                shutil.move(file_path, new_path)
                ans = True
            except OSError as e:
                logging.error(f'can\'t move files {files} to {new_path}\nerror: {e}')

    return ans


def make_new_folder(path: str, folder_name: str):
    """Custom creation a directory"""
    if folder_name is not None:
        folder_name = str(folder_name)

        path = os.path.join(path, folder_name)
        if not os.path.exists(path):
            os.mkdir(path)

    return path


def remove_file(path: str):
    """Custom remove a file"""
    answer = False

    if os.path.exists(path):
        os.remove(path)
        answer = True

    return answer


def remove_folder(path: str):
    """Custom remove a directory"""
    answer = False

    try:
        if os.path.exists(path):
            folder_elements = os.listdir(path)
            if not folder_elements:
                os.rmdir(path)
                answer = True
            else:
                logging.info(f'Не удалось удалить {path}\nеще не удалены: \n{folder_elements}')

        else:
            logging.error(f'\nНе существует: \n{path}\n \nxxxxx')

    except Exception as e:
        logging.error(f'\nНет доступа к \n{path}\nerror: {e} \n+++++')

    return answer


def get_folder_elements(path: str):
    """Each string element convert to lowercase"""
    temp_list = os.listdir(path)
    for n, elem in enumerate(temp_list):
        elem = str(elem).lower()
        temp_list[n] = str(elem)
    return temp_list


def make_timestamp(value: str):
    """ Construct timestamp from different datetime """
    values = []
    date_value = None
    date_stamp = None
    date_start = 315522000

    splitter = None
    try:
        if value:
            if re.match(r'\d{4}[-:]?.\d[-:]?.\d[ T]?.{,2}:.{,2}:.{,2}', value):
                values.append(value[:10])
                values.append(value[11:19])
                values.append(value[20:])
                if re.match(r'\d{4}-.\d-.\d[ T]?.{,2}:.{,2}:.{,2}', value):
                    splitter = '-'
                elif re.match(r'\d{4}:.\d:.\d[ T]?.{,2}:.{,2}:.{,2}', value):
                    splitter = ':'

                if splitter:
                    dt = values[0].split(splitter)
                    yy = int(dt[0])
                    if yy > 1980:
                        mm = int(dt[1])
                        if mm < 1 or mm > 12:
                            mm = 1

                        dd = int(dt[2])
                        if dd < 1 or dd > 31:
                            dd = 1

                        d = datetime.date(yy, mm, dd)
                        tm = values[1].split(':')
                        # gmt = values[2]

                        sh = tm[0]
                        if not sh.isspace():
                            h = int(sh)
                            if h > 23:
                                h = 23
                            elif h < 0:
                                h = 1
                        else:
                            h = 0

                        sm = tm[1]
                        if not sm.isspace():
                            m = int(sm)
                            if m > 59:
                                m = 59
                            elif m < 0:
                                m = 1
                        else:
                            m = 0

                        st = tm[2]
                        if not st.isspace():
                            s = int(st)
                            if s > 59:
                                s = 59
                            elif s < 0:
                                s = 1
                        else:
                            s = 1

                        t = datetime.time(h, m, s)
                        date_value = datetime.datetime.combine(d, t)

            if date_value:
                date_stamp = int(date_value.timestamp())
                if int(date_stamp) < date_start:
                    date_stamp = None

    except Exception as e:
        print(f'can\'t convert {value} to .timestamp {date_stamp} \nerror: {e}')
        logging.error(f'can\'t convert {value} to .timestamp {date_stamp} \nerror: {e}')

    return date_stamp


def get_exif(file_path: str, ext=None):
    """Return exif of file"""
    exifdata = ExifData(file_path=file_path, file_ext=ext)
    exifdata.get_exif()

    return exifdata


class ExifData:
    """
    Abstract dict-like class for EXIF data
    """
    __slots__ = ('file_path',
                 'file_ext',
                 'file_type',
                 'date',
                 'height',
                 'width',
                 'brand',
                 'model',
                 'lens',
                 'size',
                 'is_screenshot',
                 '__dict__')

    def __init__(self, file_path=None, file_ext=None, file_type=None, date=None,
                 height=None, width=None, brand=None, model=None, lens=None,
                 size=None, is_screenshot=None):

        self.file_path = file_path
        self.file_ext = file_ext
        self.file_type = file_type
        self.date = date
        self.height = height
        self.width = width
        self.brand = brand
        self.model = model
        self.lens = lens
        self.size = size
        self.is_screenshot = is_screenshot

    def __repr__(self):
        return f'{type(self).__name__}({repr(self.file_path)}, ' \
               f'{repr(self.file_ext)}, {repr(self.file_type)}, ' \
               f'{repr(self.date)}, {repr(self.height)}, ' \
               f'{repr(self.width)}, {repr(self.brand)}, ' \
               f'{repr(self.model)}, {repr(self.lens)}, ' \
               f'{repr(self.size)}, {repr(self.is_screenshot)})'

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def change_value(self, key, value):
        """Custom change class value"""
        if key == 'date':
            if value:
                if value > 0 and (self.date is None or value < self.date):
                    self.date = int(value)
        elif key == 'is_screenshot':
            if not self.is_screenshot:
                self.is_screenshot = value
        else:
            if self[key] is not None and self[key] != value:
                last = self[key]
                logging.warning(f'change {key} from {last} to {value}')  # Сообщение критическое

            self[key] = value

    def get_exif(self):
        """
        Custom exif information by
        pyexiv2, PIL, exifread and piexif libraries.
        """
        if self.file_ext is None:
            f, self.file_ext = os.path.splitext(self.file_path)

        ext = self.file_ext.lower()
        if ext in ('.jpg', '.png', '.gif', '.bmp', '.psd', '.tiff'):
            self.file_type = 'photo'
        elif ext in ('.mp4', '.mov', '.avi'):
            self.file_type = 'video'
        elif ext in ('.mp3', '.m4a'):
            self.file_type = 'audio'
        else:
            self.file_type = 'other'

        self.get_size_os()
        if self.file_type is 'photo':
            if int(self.size) > 15:
                self.get_exif_pil()
                if self.date is None and ext not in ('.gif',):
                    path, file = os.path.split(self.file_path)

                    langs = []
                    langs.extend(detect_languages(file))
                    langs.extend(detect_languages(path))
                    if not contain_any(langs, CYR_LANG):
                        self.get_exif_pyexiv()

                if self.date is None and ext not in ('.png',):
                    self.get_exif_exifread()

                if self.date is None and ext in ('.jpg', '.tiff'):
                    self.get_exif_piexif()

        elif self.file_type is 'video' or self.file_type is 'audio':
            self.get_exif_win32com()

        if not GROUP_NO_EXIF:
            self.get_exif_os()

    def get_exif_win32com(self):
        """get exif for media files (video, audio) by win32com"""
        value = None
        try:
            properties = propsys.SHGetPropertyStoreFromParsingName(self.file_path)
            # title = properties.GetValue(pscon.PKEY_Title).GetValue()
            value = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
        except Exception as e:
            logging.error(f'win32com: can\'t open file {self}\nerror: {e}')

        if value:
            self.change_value('date', make_timestamp(str(value)))

    def get_exif_pyexiv(self):
        """get exif by pyexiv2"""
        exif_dict = None
        try:
            i = pyexiv2_Image(self.file_path)
            exif_dict = i.read_all()
        except Exception as e:
            logging.error(f'pyexiv2: can\'t open file {self}\nerror: {e}')

        if exif_dict:
            for exif_tag in ('EXIF', 'XMP'):
                tags = exif_dict[exif_tag]
                for tag in tags.keys():
                    if tag == 'Thumbnail' or tag == 'Exif.Thumbnail.XResolution' or \
                            tag == 'Exif.Thumbnail.YResolution' or tag == 'Exif.Thumbnail.ResolutionUnit' or \
                            tag == 'Exif.Thumbnail.JPEGInterchangeFormat' or tag == 'Exif.Thumbnail.Compression' or \
                            tag == 'Exif.Thumbnail.JPEGInterchangeFormatLength':
                        continue

                    if tag == 'Exif.Image.DateTime' or \
                            tag == 'Exif.Photo.DateTimeOriginal' or \
                            tag == 'Exif.Photo.DateTimeDigitized':

                        value = tags[tag]
                        if value:
                            self.change_value('date', make_timestamp(str(value)))
                    elif tag == 'Xmp.exif.UserComment':
                        value = tags[tag]
                        if 'screenshot' in value.lower():
                            self.change_value('is_screenshot', True)
                    elif tag == 'Exif.Image.Make':
                        value = tags[tag]
                        self.change_value('brand', str(value))
                    elif tag == 'Exif.Image.Model':
                        value = tags[tag]
                        self.change_value('model', str(value))
                    elif tag == 'Exif.Photo.PixelXDimension':
                        value = tags[tag]
                        self.change_value('width', str(value))
                    elif tag == 'Exif.Photo.PixelYDimension':
                        value = tags[tag]
                        self.change_value('height', str(value))
                    elif tag == 'Exif.Photo.LensModel':
                        value = tags[tag]
                        self.change_value('lens', str(value))

    def get_exif_exifread(self):
        """get exif by exifread (not PNG)')"""
        tags = None
        try:
            with open(self.file_path, 'rb') as f:
                tags = exifread.process_file(f)
        except Exception as e:
            logging.error(f'exifread: can\'t open file {self}\nerror: {e}')

        if tags:
            for tag in tags.keys():
                if tag == 'Thumbnail':
                    continue

                if tag == 'Image DateTime' or \
                        tag == 'EXIF DateTimeOriginal' or \
                        tag == 'EXIF DateTimeDigitized':
                    value = tags[tag]
                    if value:
                        self.change_value('date', make_timestamp(str(value)))
                elif tag == 'UserComment':
                    value = str(tags[tag])
                    if 'screenshot' in value.lower():
                        self.change_value('is_screenshot', True)
                elif tag == 'Image Make':
                    value = tags[tag]
                    self.change_value('brand', str(value))
                elif tag == 'Image Model':
                    value = tags[tag]
                    self.change_value('model', str(value))
                elif tag == 'EXIF ExifImageWidth':
                    value = tags[tag]
                    self.change_value('width', str(value))
                elif tag == 'EXIF ExifImageLength':
                    value = tags[tag]
                    self.change_value('height', str(value))
                elif tag == 'EXIF LensModel':
                    value = tags[tag]
                    self.change_value('lens', str(value))

    def get_exif_piexif(self):
        """get exif by piexif (only JPG & TIFF)"""
        data = None
        try:
            data = piexif.load(self.file_path)
        except Exception as e:
            logging.error(f'piexif: can\'t open file {self}\nerror: {e}')

        if data:
            for data_key in ('Exif', '0th', '1st', 'GPS', 'Interop'):
                tags_key = data[data_key]
                for tag_key in tags_key.keys():
                    tag = PIEXIF_TAGS[data_key][tag_key]['name']
                    value = tags_key[tag_key]
                    if tag == 'Thumbnail':
                        continue
                    if type(value) is bytes:
                        try:
                            value = value.decode('MacCyrillic')
                        except UnicodeDecodeError as e:
                            logging.exception(f'{value}\n decode error: {e}')

                    if tag == 'DateTime' or \
                            tag == 'DateTimeOriginal' or \
                            tag == 'DateTimeDigitized':
                        if value:
                            self.change_value('date', make_timestamp(str(value)))
                    elif tag == 'UserComment':
                        if 'screenshot' in value.lower():
                            self.change_value('is_screenshot', True)
                    elif tag == 'Make':
                        self.change_value('brand', str(value))
                    elif tag == 'Model':
                        self.change_value('model', str(value))
                    elif tag == 'PixelXDimension':
                        self.change_value('width', str(value))
                    elif tag == 'PixelYDimension':
                        self.change_value('height', str(value))
                    elif tag == 'LensModel':
                        self.change_value('lens', str(value))

    def get_exif_pil(self):
        """get exif by PIL"""
        info = None
        PIL_Image.MAX_IMAGE_PIXELS = None

        try:
            i = PIL_Image.open(self.file_path)
            info = i.getexif()
        except Exception as e:
            logging.error(f'PIL: can\'t open file {self}\nerror: {e}')

        if info:
            img_exif_dict = dict(info)
            for key, value in img_exif_dict.items():
                if key in PIL_TAGS:
                    tag = PIL_TAGS[key]
                    if tag == 'Thumbnail':
                        continue
                    if type(value) is bytes:
                        try:
                            value = value.decode('MacCyrillic')
                        except UnicodeDecodeError as e:
                            logging.exception(f'{value}\n decode error: {e}')

                    if tag == 'DateTime' or \
                            tag == 'DateTimeOriginal' or \
                            tag == 'DateTimeDigitized':
                        if value:
                            self.change_value('date', make_timestamp(str(value)))
                    elif tag == 'UserComment':
                        if 'screenshot' in value.lower():
                            self.change_value('is_screenshot', True)
                    elif tag == 'Make':
                        self.change_value('brand', str(value))
                    elif tag == 'Model':
                        self.change_value('model', str(value))
                    elif tag == 'ExifImageWidth':
                        self.change_value('width', str(value))
                    elif tag == 'ExifImageHeight':
                        self.change_value('height', str(value))
                    elif tag == 'LensModel':
                        self.change_value('lens', str(value))

    def get_exif_os(self):
        """get data from OS (date)"""
        file_path = self.file_path
        try:
            self.change_value('date', os.path.getmtime(file_path))
            self.change_value('date', os.path.getctime(file_path))
        except OSError as e:
            logging.error(f'OS: can\'t open file {self}\nerror: {e}')
        except Exception as e:
            logging.error(f'OS: can\'t open file {self}\nerror: {e}')

    def get_size_os(self):
        """get data from OS (size)"""
        self.change_value('size', int(os.path.getsize(self.file_path)))

    def is_same_with(self, file_exif):
        """Compare 2 exif"""
        if self.file_type == file_exif.file_type and \
                self.date == file_exif.date:

            if self.file_ext == file_exif.file_ext and \
                    self.height == file_exif.height and \
                    self.width == file_exif.width and \
                    self.brand == file_exif.brand and \
                    self.model == file_exif.model and \
                    self.lens == file_exif.lens and \
                    self.size == file_exif.size:
                return True

        return False

    def make_new_path(self, path):
        """Custom creation a directory"""
        if self.is_screenshot:
            path = make_new_folder(path=path, folder_name=SCREENSHOTS_FOLDER)
        else:
            if self.date:
                try:
                    struct_time = time.localtime(self.date)
                    n = 0
                    while n < 3:
                        path = make_new_folder(path=path, folder_name=struct_time[n])
                        n += 1
                except Exception as e:
                    logging.info(f'Error in make_new_path: {self} error: {e}')

            else:
                path = make_new_folder(path=path, folder_name=NO_EXIF_FOLDER)

        return path


if __name__ == '__main__':
    for param in sys.argv:
        if param == 'no_ex':
            GROUP_NO_EXIF = False

    sort_files()
