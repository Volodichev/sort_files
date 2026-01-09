import sys

import config
from sorter import sort_files


def main():
    for param in sys.argv:
        if param == 'no_ex':
            config.set_group_no_exif(False)
    sort_files()


if __name__ == '__main__':
    main()
