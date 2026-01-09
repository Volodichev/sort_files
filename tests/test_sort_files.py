import os
import pytest

import timestamp_utils
import exif_utils


@pytest.fixture(scope="function", params=[
    ('2013-09-21 15:33:42+00:00', 1379766822),
    ('2013:05:16 19:04:43+03:00', 1368720283),
    ('1949-11-21 10:16:02+00:00', None),
    ('2013-05-16 19:04:43+03:00', 1368720283),
    ('0000-00-00 00:00:00+00:00', None),
    ('0000-00-00 00:00:00', None),
    ('2013:05:16 19:04:43', 1368720283),
    ('2013- 5-16 19: 4:43', 1368720283),
    ('2013: 5:16 19: 4:43', 1368720283),
    ('2013- 5-16T19: 4:43', 1368720283),
    ('2013: 5:16T19: 4:43', 1368720283),
    ('2009-08-23 19:48:00', 1251046080),
    ('2016-06-05T21:06:76', 1465150019),
    ('2015:11:21 10:16: 2', 1448090162),
    ('2015:11:21 10:16: ', 1448090161),
    ('1949-11-21 10:16:02', None),
    ('1899-12-29 21:00:00', None),
    (None, None)
])
def test_timestamp(request):
    return request.param


def test_organize_photos_make_timestamp(test_timestamp):
    (value, expected_output) = test_timestamp
    date_stamp = timestamp_utils.make_timestamp(value=value)
    print(f'\ninput: {value}, output: {date_stamp}, expected: {expected_output}')
    assert date_stamp == expected_output


# def test_media_sort():
#     sort_files.sort_files()


@pytest.fixture(scope="function", params=[
    ('IMG_8089.jpg', 1457123393),
    # Ожидаемое значение сверяем с фактическим минимальным датой из EXIF/OS.
    ('IMG_8090.jpg', 1465150019),
    ('1cde9h.jpg', None),
    ('Foto-0271_e1.jpg', 1368720283)
])
def test_file_paths(request):
    return request.param


def test_get_exif(test_file_paths):
    current_path = os.path.abspath(os.curdir)
    (value, expected_output) = test_file_paths
    base_dir = os.path.join(current_path, "tests")
    target = _find_case_insensitive(os.path.join(base_dir, value)) or os.path.join(base_dir, value)
    file_exif = exif_utils.get_exif(file_path=target)
    print(f'\ninput: {value}, resolved: {target}, output: {file_exif.date}, expected: {expected_output}')

    assert file_exif.date == expected_output


def _find_case_insensitive(path: str):
    """Поиск файла без учёта регистра (нужно для *nix, где тестовые имена в нижнем регистре)."""
    directory, name = os.path.dirname(path), os.path.basename(path).lower()
    try:
        for entry in os.listdir(directory or "."):
            if entry.lower() == name:
                return os.path.join(directory, entry)
    except FileNotFoundError:
        return None
    return None
