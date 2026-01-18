import logging

PHOTO_EXTENSIONS = ('.jpg', '.png', '.gif', '.bmp', '.psd', '.tiff', '.heic')
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')
AUDIO_EXTENSIONS = ('.mp3', '.m4a')
SUPPORTED_EXTENSIONS = PHOTO_EXTENSIONS + VIDEO_EXTENSIONS + AUDIO_EXTENSIONS
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

logging.basicConfig(
    format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(message)s',
    level=logging.INFO,
    filename=LOG_FILE,
)


def set_group_no_exif(value: bool) -> None:
    """Allow toggling grouping without EXIF data."""
    global GROUP_NO_EXIF
    GROUP_NO_EXIF = bool(value)
