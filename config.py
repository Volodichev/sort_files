import logging

SUPPORTED_EXTENSIONS = (
    '.jpg', '.png', '.gif', '.bmp', '.tiff', '.psd', '.dng',
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

logging.basicConfig(
    format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(message)s',
    level=logging.INFO,
    filename=LOG_FILE,
)


def set_group_no_exif(value: bool) -> None:
    """Allow toggling grouping without EXIF data."""
    global GROUP_NO_EXIF
    GROUP_NO_EXIF = bool(value)
