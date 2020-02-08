import os
import pytest
import sort_files


@pytest.fixture(scope="function", params=[
    ('2013-09-21 15:33:42+00:00', 1379766822),
    ('2013:05:16 19:04:43+03:00', 1368720283),
    ('1949-11-21 10:16:02+00:00', 343638962),
    ('2013-05-16 19:04:43+03:00', 1368720283),
    ('0000-00-00 00:00:00+00:00', 315522000),
    ('0000-00-00 00:00:00', 315522000),
    ('2013:05:16 19:04:43', 1368720283),
    ('2013- 5-16 19: 4:43', 1368720283),
    ('2013: 5:16 19: 4:43', 1368720283),
    ('2013- 5-16T19: 4:43', 1368720283),
    ('2013: 5:16T19: 4:43', 1368720283),
    ('2009-08-23 19:48:00', 1251046080),
    ('2016-06-05T21:06:76', 1465150019),
    ('2015:11:21 10:16: 2', 1448090162),
    ('2015:11:21 10:16: ', 1448090161),
    ('1949-11-21 10:16:02', 343638962),
    ('1899-12-29 21:00:00', 346960800),
    (None, None)
])
def test_timestamp(request):
    return request.param


def test_organize_photos_make_timestamp(test_timestamp):
    (value, expected_output) = test_timestamp
    date_stamp = sort_files.make_timestamp(value=value)
    print(f'\ninput: {value}, output: {date_stamp}, expected: {expected_output}')
    assert date_stamp == expected_output


# def test_media_sort():
#     sort_files.sort_files()


@pytest.fixture(scope="function", params=[
    ('IMG_8089.jpg', 1457123393),
    ('IMG_8090.jpg', 1464695993),
    ('1cde9h.jpg', None),
    ('Foto-0271_e1.jpg', 1368720283)
])
def test_file_paths(request):
    return request.param


def test_get_exif(test_file_paths):
    current_path = os.path.abspath(os.curdir)
    (value, expected_output) = test_file_paths
    file_exif = sort_files.get_exif(file_path=os.path.join(current_path, value))
    print(f'\ninput: {value}, output: {file_exif.date}, expected: {expected_output}')

    assert file_exif.date == expected_output
