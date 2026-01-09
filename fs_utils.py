import logging
import os
import shutil
from typing import Iterable

import config
from language_utils import contain_any


def make_files_list(file: str, path: str) -> list[str]:
    """Make file list, if FIND_SETS_FILES add setting files."""
    files = [file]
    if config.FIND_SETS_FILES:
        file_name, file_ext = os.path.splitext(file)
        folder_elements = os.listdir(path)
        temp_files = []
        for temp_ext in config.SETTING_EXTENSIONS:
            temp_files.append(''.join((file_name, temp_ext)))
        temp_files = list(set(temp_files) & set(folder_elements))
        if temp_files:
            files.extend(temp_files)

    return files


def move_files(files: list, path: str, new_path: str) -> bool:
    """Move files to 'new_path' directory."""
    ans = False
    exist_folder_elements = get_folder_elements(new_path)

    for file in files:
        if file.lower() not in exist_folder_elements:
            file_path = os.path.join(path, file)
            try:
                shutil.move(file_path, new_path)
                ans = True
            except OSError as e:
                logging.error(f"can't move files {files} to {new_path} error: {e}")

    return ans


def make_new_folder(path: str, folder_name: str):
    """Custom creation a directory."""
    if folder_name is not None:
        folder_name = str(folder_name)
        path = os.path.join(path, folder_name)
        if not os.path.exists(path):
            os.mkdir(path)

    return path


def remove_file(path: str) -> bool:
    """Custom remove a file."""
    answer = False

    if os.path.exists(path):
        os.remove(path)
        answer = True

    return answer


def remove_folder(path: str) -> bool:
    """Custom remove a directory."""
    answer = False

    try:
        if os.path.exists(path):
            folder_elements = os.listdir(path)
            if not folder_elements:
                os.rmdir(path)
                answer = True
            else:
                logging.info(f"Не удалось удалить {path}\nеще не удалены: \n{folder_elements}")

        else:
            logging.error(f"\nНе существует: \n{path}\n \nxxxxx")

    except Exception as e:
        logging.error(f"\nНет доступа к \n{path}\nerror: {e} \n+++++")

    return answer


def get_folder_elements(path: str) -> list[str]:
    """Each string element convert to lowercase."""
    temp_list = os.listdir(path)
    for n, elem in enumerate(temp_list):
        elem = str(elem).lower()
        temp_list[n] = str(elem)
    return temp_list


def is_file_in_folder(file: str, path: str) -> bool:
    """Check file in folder."""
    folder_elements = get_folder_elements(path=path)
    files: Iterable[str] = (file, file.lower())
    return contain_any(files, folder_elements)


def duples_in_folder(new_path: str, file: str, file_exif=None):
    """What to do if file exist in folder."""
    # Local import to avoid circular dependency.
    from exif_utils import get_exif

    skip = False
    if file_exif is None:
        skip = True
    else:
        if is_file_in_folder(file=file, path=new_path):
            exist_file_path = os.path.join(new_path, file)
            exist_file_exif = get_exif(file_path=exist_file_path)

            if file_exif.is_same_with(exist_file_exif):
                skip = True
            else:
                file_name, file_ext = os.path.splitext(file)
                new_path = make_new_folder(path=new_path, folder_name=file_name)
                if is_file_in_folder(file=file, path=new_path):
                    skip = True

    return new_path, skip
