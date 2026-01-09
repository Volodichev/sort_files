import logging
import os
import time

import exifread
import piexif
from PIL import Image as PIL_Image
from PIL.ExifTags import TAGS as PIL_TAGS
from piexif import TAGS as PIEXIF_TAGS
from win32com.propsys import propsys, pscon

import config
from language_utils import contain_any, detect_languages
from timestamp_utils import make_timestamp

try:
    from pyexiv2 import Image as pyexiv2_Image
    HAS_PYEXIV2 = True
except Exception as e:  # библиотека может отсутствовать на Python 3.11
    HAS_PYEXIV2 = False
    logging.warning(f'pyexiv2 is not available, skip pyexiv2 exif reader: {e}')

import fs_utils


def get_exif(file_path: str, ext=None):
    """Return exif of file."""
    exifdata = ExifData(file_path=file_path, file_ext=ext)
    exifdata.get_exif()
    return exifdata


class ExifData:
    """Abstract dict-like class for EXIF data."""

    __slots__ = (
        'file_path',
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
        '__dict__',
    )

    def __init__(
        self,
        file_path=None,
        file_ext=None,
        file_type=None,
        date=None,
        height=None,
        width=None,
        brand=None,
        model=None,
        lens=None,
        size=None,
        is_screenshot=None,
    ):
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
        return (
            f'{type(self).__name__}({repr(self.file_path)}, {repr(self.file_ext)}, '
            f'{repr(self.file_type)}, {repr(self.date)}, {repr(self.height)}, '
            f'{repr(self.width)}, {repr(self.brand)}, {repr(self.model)}, '
            f'{repr(self.lens)}, {repr(self.size)}, {repr(self.is_screenshot)})'
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def change_value(self, key, value):
        """Custom change class value."""
        if key == 'date':
            if value:
                if value > 0 and (self.date is None or value < self.date):
                    self.date = int(value)
        elif key == 'is_screenshot':
            if not self.is_screenshot:
                self.is_screenshot = value
        else:
            last = self[key]
            if last is not None and last != value:
                logging.warning(f'change {key} from {last} to {value}')

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
        if self.file_type == 'photo':
            if int(self.size) > 15:
                self.get_exif_pil()
                if self.date is None and ext not in ('.gif',):
                    path, file = os.path.split(self.file_path)

                    langs = []
                    langs.extend(detect_languages(file))
                    langs.extend(detect_languages(path))
                    if not contain_any(langs, config.CYR_LANG):
                        # pyexiv2 can't open files with cyrillic paths
                        self.get_exif_pyexiv()

                if self.date is None and ext not in ('.png',):
                    self.get_exif_exifread()

                if self.date is None and ext in ('.jpg', '.tiff'):
                    self.get_exif_piexif()

        elif self.file_type in ('video', 'audio'):
            self.get_exif_win32com()

        if not config.GROUP_NO_EXIF:
            self.get_exif_os()

    def get_exif_win32com(self):
        """Get exif for media files (video, audio) by win32com."""
        value = None
        try:
            properties = propsys.SHGetPropertyStoreFromParsingName(self.file_path)
            value = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
        except Exception as e:
            logging.error(f"win32com: can't open file {self}\nerror: {e}")

        if value:
            self.change_value('date', make_timestamp(str(value)))

    def get_exif_pyexiv(self):
        """Get exif by pyexiv2."""
        if not HAS_PYEXIV2:
            return
        exif_dict = None
        try:
            i = pyexiv2_Image(self.file_path)
            exif_dict = i.read_all()
        except Exception as e:
            logging.error(f"pyexiv2: can't open file {self}\nerror: {e}")

        if exif_dict:
            for exif_tag in ('EXIF', 'XMP'):
                tags = exif_dict.get(exif_tag)
                if not tags:
                    continue
                for tag in tags.keys():
                    if tag in (
                        'Thumbnail',
                        'Exif.Thumbnail.JPEGInterchangeFormat',
                        'Exif.Thumbnail.XResolution',
                        'Exif.Thumbnail.Compression',
                        'Exif.Thumbnail.YResolution',
                        'Exif.Thumbnail.ResolutionUnit',
                        'Exif.Thumbnail.JPEGInterchangeFormatLength',
                    ):
                        continue

                    if tag in (
                        'Exif.Photo.DateTimeOriginal',
                        'Exif.Image.DateTime',
                        'Exif.Photo.DateTimeDigitized',
                    ):
                        value = tags.get(tag)
                        if value:
                            self.change_value('date', make_timestamp(str(value)))
                    elif tag == 'Xmp.exif.UserComment':
                        value = tags.get(tag)
                        if 'screenshot' in value.lower():
                            self.change_value('is_screenshot', True)
                    elif tag == 'Exif.Image.Make':
                        value = tags.get(tag)
                        self.change_value('brand', str(value))
                    elif tag == 'Exif.Image.Model':
                        value = tags.get(tag)
                        self.change_value('model', str(value))
                    elif tag == 'Exif.Photo.PixelXDimension':
                        value = tags.get(tag)
                        self.change_value('width', str(value))
                    elif tag == 'Exif.Photo.PixelYDimension':
                        value = tags.get(tag)
                        self.change_value('height', str(value))
                    elif tag == 'Exif.Photo.LensModel':
                        value = tags.get(tag)
                        self.change_value('lens', str(value))

    def get_exif_exifread(self):
        """Get exif by exifread (not PNG)."""
        tags = None
        try:
            with open(self.file_path, 'rb') as f:
                tags = exifread.process_file(f)
        except Exception as e:
            logging.error(f"exifread: can't open file {self}\nerror: {e}")

        if tags:
            for tag in tags.keys():
                if tag == 'Thumbnail':
                    continue

                if tag in ('Image DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized'):
                    value = tags.get(tag)
                    if value:
                        self.change_value('date', make_timestamp(str(value)))
                elif tag == 'UserComment':
                    value = str(tags.get(tag))
                    if 'screenshot' in value.lower():
                        self.change_value('is_screenshot', True)
                elif tag == 'Image Make':
                    value = tags.get(tag)
                    self.change_value('brand', str(value))
                elif tag == 'Image Model':
                    value = tags.get(tag)
                    self.change_value('model', str(value))
                elif tag == 'EXIF ExifImageWidth':
                    value = tags.get(tag)
                    self.change_value('width', str(value))
                elif tag == 'EXIF ExifImageLength':
                    value = tags.get(tag)
                    self.change_value('height', str(value))
                elif tag == 'EXIF LensModel':
                    value = tags.get(tag)
                    self.change_value('lens', str(value))

    def get_exif_piexif(self):
        """Get exif by piexif (only JPG & TIFF)."""
        data = None
        try:
            data = piexif.load(self.file_path)
        except Exception as e:
            logging.error(f"piexif: can't open file {self}\nerror: {e}")

        if data:
            for data_key in ('Exif', '0th', '1st', 'GPS', 'Interop'):
                dk = PIEXIF_TAGS.get(data_key)
                if not dk:
                    continue
                tags_key = data.get(data_key)
                if not tags_key:
                    continue
                for tag_key in tags_key.keys():
                    tk = dk.get(tag_key)
                    if not tk:
                        continue
                    tag = tk.get('name')
                    if not tag:
                        continue

                    value = tags_key.get(tag_key)
                    if tag == 'Thumbnail':
                        continue
                    if type(value) is bytes:
                        try:
                            value = value.decode('MacCyrillic')
                        except UnicodeDecodeError as e:
                            logging.exception(f'{value}\n decode error: {e}')
                            continue

                    if tag in ('DateTime', 'DateTimeOriginal', 'DateTimeDigitized'):
                        if value:
                            self.change_value('date', make_timestamp(str(value)))
                    elif tag == 'UserComment':
                        if isinstance(value, str) and 'screenshot' in value.lower():
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
        """Get exif by PIL."""
        info = None
        PIL_Image.MAX_IMAGE_PIXELS = None

        try:
            i = PIL_Image.open(self.file_path)
            info = i.getexif()
        except Exception as e:
            logging.error(f"PIL: can't open file {self}\nerror: {e}")

        if info:
            img_exif_dict = dict(info)
            for key, value in img_exif_dict.items():
                if key in PIL_TAGS:
                    tag = PIL_TAGS.get(key)
                    if tag == 'Thumbnail':
                        continue
                    if type(value) is bytes:
                        try:
                            value = value.decode('MacCyrillic')
                        except UnicodeDecodeError as e:
                            logging.exception(f'{value}\n decode error: {e}')

                    if tag in ('DateTime', 'DateTimeOriginal', 'DateTimeDigitized'):
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
        """Get data from OS (date)."""
        file_path = self.file_path
        try:
            self.change_value('date', os.path.getmtime(file_path))
            self.change_value('date', os.path.getctime(file_path))
        except OSError as e:
            logging.error(f"OS: can't open file {self}\nerror: {e}")
        except Exception as e:
            logging.error(f"OS: can't open file {self}\nerror: {e}")

    def get_size_os(self):
        """Get data from OS (size)."""
        self.change_value('size', int(os.path.getsize(self.file_path)))

    def is_same_with(self, file_exif):
        """Compare 2 exif."""
        if self.file_type == file_exif.file_type and self.date == file_exif.date:
            if (
                self.file_ext == file_exif.file_ext
                and self.height == file_exif.height
                and self.width == file_exif.width
                and self.brand == file_exif.brand
                and self.model == file_exif.model
                and self.lens == file_exif.lens
                and self.size == file_exif.size
            ):
                return True

        return False

    def make_new_path(self, path):
        """Custom creation a directory."""
        if self.is_screenshot:
            path = fs_utils.make_new_folder(path=path, folder_name=config.SCREENSHOTS_FOLDER)
        else:
            if self.date:
                try:
                    struct_time = time.localtime(self.date)
                    n = 0
                    while n < 3:
                        path = fs_utils.make_new_folder(path=path, folder_name=struct_time[n])
                        n += 1
                except Exception as e:
                    logging.info(f'Error in make_new_path: {self} error: {e}')

            else:
                path = fs_utils.make_new_folder(path=path, folder_name=config.NO_EXIF_FOLDER)

        return path
