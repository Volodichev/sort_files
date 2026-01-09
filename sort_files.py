import argparse
import sys

import config
import version
from sorter import sort_files


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description='Сортировка фото/видео по дате съёмки или EXIF.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('-s', '--source', help='Папка с исходными файлами')
    parser.add_argument('-r', '--result', help='Папка, куда складывать отсортированные файлы')
    parser.add_argument(
        '--no-group-no-exif',
        action='store_true',
        help='Не складывать файлы без EXIF в отдельную папку (использовать дату ОС).',
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s v{version.VERSION}')

    args, unknown = parser.parse_known_args(argv)
    args._legacy_no_ex = 'no_ex' in unknown

    unknown = [item for item in unknown if item != 'no_ex']
    if unknown:
        parser.error(f"Неизвестные аргументы: {' '.join(unknown)}")

    return args


def main(argv: list[str] | None = None):
    argv = sys.argv[1:] if argv is None else argv
    args = _parse_args(argv)

    if args.no_group_no_exif or args._legacy_no_ex:
        config.set_group_no_exif(False)

    sort_files(source_path=args.source, result_path=args.result)


if __name__ == '__main__':
    main()
