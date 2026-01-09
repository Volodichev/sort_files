import logging
import os
import sys
from typing import Iterable

from tqdm import tqdm

import config
from exif_utils import get_exif
from fs_utils import (
    duples_in_folder,
    make_files_list,
    make_new_folder,
    move_files,
    remove_folder,
)
from language_utils import path_contains_cyrillic


def sort_files(source_path=None, result_path=None):
    """
    Sort files with SUPPORTED_EXTENSIONS by creation date and
    put them to directories Year/Month/Day by exif Date.
    """
    current_path = os.path.abspath(os.curdir)
    if source_path is None:
        source_path = os.path.join(current_path, config.SOURCE_FOLDER)
    if result_path is None:
        result_path = make_new_folder(path=current_path, folder_name=config.RESULT_FOLDER)

    print(f'Search files in {source_path}')

    if path_contains_cyrillic(source_path, source_path):
        print(f'Path contains invalid symbols {source_path}')
        sys.exit()

    paths: list[str] = []
    files_with_path = []

    for path, dirs, folder_files in os.walk(top=source_path, topdown=False):
        if path != source_path:
            paths.append(path)

        folder_files = filter(lambda f: f.lower().endswith(config.SUPPORTED_EXTENSIONS), folder_files)
        for file in folder_files:
            files_with_path.append({'path': path, 'file': file})

    fl_count = len(files_with_path)
    print(f'{fl_count} files found')

    for n in tqdm(range(0, fl_count), desc=f'move files', ncols=100):
        filedict = files_with_path[n - 1]
        file = filedict.get('file')
        path = filedict.get('path')
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
        path = paths[n - 1]
        if path in not_removed_paths:
            if remove_folder(path):
                not_removed_paths.remove(path)

    if not_removed_paths:
        not_removed_paths = ',\n'.join(not_removed_paths)
        print(f'This folders are not empty:\n{not_removed_paths}')
