import logging
import os
import sys

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
    source_path = os.path.abspath(source_path)

    if result_path is None:
        result_path = make_new_folder(path=current_path, folder_name=config.RESULT_FOLDER)
    else:
        result_path = os.path.abspath(result_path)
        os.makedirs(result_path, exist_ok=True)

    print(f'Поиск файлов в {source_path}')

    if path_contains_cyrillic(source_path, source_path):
        print(f'Path contains invalid symbols {source_path}')
        sys.exit()

    folders: list[str] = []
    files_with_path: list[tuple[str, str]] = []

    for path, _, folder_files in os.walk(top=source_path, topdown=False):
        if path != source_path:
            folders.append(path)

        for file in folder_files:
            if file.lower().endswith(config.SUPPORTED_EXTENSIONS):
                files_with_path.append((path, file))

    print(f'{len(files_with_path)} files found')

    for path, file in tqdm(files_with_path, desc='move files', ncols=100):
        file_path = os.path.join(path, file)

        files = make_files_list(file=file, path=path)
        file_exif = get_exif(file_path=file_path)
        new_path = file_exif.make_new_path(path=result_path)

        new_path, skip = duples_in_folder(new_path=new_path, file=file, file_exif=file_exif)
        if skip:
            logging.info(f'DUPLICATE: {path} ({files}) already in {new_path}')
            continue

        if move_files(files=files, path=path, new_path=new_path):
            logging.info(f'Moved: {path} ({files}) -> {new_path}')

    not_removed_paths: list[str] = []
    for path in tqdm(sorted(set(folders), key=len, reverse=True), desc='remove folders:', ncols=100):
        if not remove_folder(path):
            not_removed_paths.append(path)

    if not_removed_paths:
        not_removed_paths = ',\n'.join(not_removed_paths)
        print(f'The following folders are not empty:\n{not_removed_paths}')
