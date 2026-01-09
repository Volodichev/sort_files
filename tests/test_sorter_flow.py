import shutil
from pathlib import Path

import config
from sorter import sort_files


def _copy_fixtures(target_dir: Path, filenames: list[str]) -> None:
    fixtures_dir = Path(__file__).parent
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        shutil.copy(fixtures_dir / name, target_dir / name)


def test_sort_files_moves_and_groups(tmp_path, monkeypatch):
    filenames = ['IMG_8089.JPG', 'IMG_8090.JPG', '1cde9h.jpg', 'Foto-0271_e1.jpg']
    source_dir = tmp_path / 'source'
    result_dir = tmp_path / 'result'

    _copy_fixtures(source_dir, filenames)

    # ensure predictable behaviour
    monkeypatch.setattr(config, 'GROUP_NO_EXIF', True, raising=False)

    sort_files(source_path=str(source_dir), result_path=str(result_dir))

    for name in filenames:
        assert not (source_dir / name).exists(), f'{name} должен быть перемещён'
        assert list(result_dir.rglob(name)), f'{name} не найден в целевой папке'

    no_exif = result_dir / config.NO_EXIF_FOLDER / '1cde9h.jpg'
    assert no_exif.exists()
