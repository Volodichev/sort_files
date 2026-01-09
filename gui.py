import os
import sys
from typing import Iterable

from PyQt6 import QtCore, QtWidgets

import config
import version
from sorter import sort_files


def _normalize_extensions(raw: str, default: Iterable[str]) -> tuple[str, ...]:
    """Convert comma/semicolon separated extensions to a normalized tuple."""
    items: list[str] = []
    for chunk in raw.replace(';', ',').split(','):
        ext = chunk.strip()
        if not ext:
            continue
        if not ext.startswith('.'):
            ext = f'.{ext}'
        items.append(ext.lower())

    if not items:
        return tuple(default)
    # drop duplicates, keep order
    seen = set()
    ordered: list[str] = []
    for ext in items:
        if ext not in seen:
            ordered.append(ext)
            seen.add(ext)
    return tuple(ordered)


def _parse_csv(raw: str) -> list[str]:
    """Split comma/semicolon separated strings, strip empties."""
    return [part.strip() for part in raw.replace(';', ',').split(',') if part.strip()]


class SortWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal()
    failed = QtCore.pyqtSignal(str)

    def __init__(self, source_path: str, result_path: str):
        super().__init__()
        self.source_path = source_path
        self.result_path = result_path

    def run(self) -> None:
        try:
            if not os.path.exists(self.result_path):
                os.makedirs(self.result_path, exist_ok=True)
            sort_files(source_path=self.source_path, result_path=self.result_path)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
        else:
            self.finished.emit()


class SortFilesWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_version = getattr(version, 'VERSION', '1.0.0')
        self.setWindowTitle(f'Sort Files v{self.app_version}')
        self.worker: SortWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)

        layout = QtWidgets.QVBoxLayout()
        central.setLayout(layout)

        version_label = QtWidgets.QLabel(f'Версия: {self.app_version}')
        layout.addWidget(version_label)

        form = QtWidgets.QFormLayout()

        self.source_edit = QtWidgets.QLineEdit(self._default_source_path())
        self.result_edit = QtWidgets.QLineEdit(self._default_result_path())

        self.extensions_edit = QtWidgets.QLineEdit(', '.join(config.SUPPORTED_EXTENSIONS))
        self.setting_ext_edit = QtWidgets.QLineEdit(', '.join(config.SETTING_EXTENSIONS))

        self.find_sets_checkbox = QtWidgets.QCheckBox('Искать вспомогательные файлы (.AAE, .THM)')
        self.find_sets_checkbox.setChecked(bool(config.FIND_SETS_FILES))

        self.group_no_exif_checkbox = QtWidgets.QCheckBox('Складывать без EXIF в отдельную папку')
        self.group_no_exif_checkbox.setChecked(bool(config.GROUP_NO_EXIF))

        self.languages_edit = QtWidgets.QLineEdit(', '.join(config.CYR_LANG))
        self.screenshots_edit = QtWidgets.QLineEdit(config.SCREENSHOTS_FOLDER)
        self.no_exif_edit = QtWidgets.QLineEdit(config.NO_EXIF_FOLDER)
        self.temp_edit = QtWidgets.QLineEdit(config.TEMP_FOLDER)
        self.log_file_edit = QtWidgets.QLineEdit(config.LOG_FILE)

        form.addRow('Папка source', self._with_browse(self.source_edit, self._choose_source))
        form.addRow('Папка result', self._with_browse(self.result_edit, self._choose_result))
        form.addRow('Виды файлов', self.extensions_edit)
        form.addRow('Служебные расширения', self.setting_ext_edit)
        form.addRow(self.find_sets_checkbox)
        form.addRow(self.group_no_exif_checkbox)
        form.addRow('Языки для проверки пути', self.languages_edit)
        form.addRow('Папка для скриншотов', self.screenshots_edit)
        form.addRow('Папка без EXIF', self.no_exif_edit)
        form.addRow('Временная папка', self.temp_edit)
        form.addRow('Имя файла лога', self.log_file_edit)

        layout.addLayout(form)

        self.status_label = QtWidgets.QLabel('')
        layout.addWidget(self.status_label)

        buttons = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton('Запустить сортировку')
        self.start_button.clicked.connect(self._start_sorting)
        buttons.addWidget(self.start_button)

        self.close_button = QtWidgets.QPushButton('Выход')
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.close_button)

        layout.addLayout(buttons)

    def _with_browse(self, edit: QtWidgets.QLineEdit, handler) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(hlayout)

        hlayout.addWidget(edit)
        btn = QtWidgets.QPushButton('...')
        btn.setFixedWidth(32)
        btn.clicked.connect(handler)
        hlayout.addWidget(btn)
        return widget

    def _choose_source(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Выберите папку source', self.source_edit.text() or os.getcwd()
        )
        if path:
            self.source_edit.setText(path)

    def _choose_result(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Выберите папку result', self.result_edit.text() or os.getcwd()
        )
        if path:
            self.result_edit.setText(path)

    def _default_source_path(self) -> str:
        return os.path.join(os.path.abspath(os.curdir), config.SOURCE_FOLDER)

    def _default_result_path(self) -> str:
        return os.path.join(os.path.abspath(os.curdir), config.RESULT_FOLDER)

    def _apply_config(self) -> None:
        config.SUPPORTED_EXTENSIONS = _normalize_extensions(
            self.extensions_edit.text(), config.SUPPORTED_EXTENSIONS
        )
        config.SETTING_EXTENSIONS = _normalize_extensions(
            self.setting_ext_edit.text(), config.SETTING_EXTENSIONS
        )
        config.FIND_SETS_FILES = self.find_sets_checkbox.isChecked()
        config.set_group_no_exif(self.group_no_exif_checkbox.isChecked())
        langs = _parse_csv(self.languages_edit.text())
        if langs:
            config.CYR_LANG = langs

        screenshots_folder = self.screenshots_edit.text().strip()
        if screenshots_folder:
            config.SCREENSHOTS_FOLDER = screenshots_folder

        no_exif_folder = self.no_exif_edit.text().strip()
        if no_exif_folder:
            config.NO_EXIF_FOLDER = no_exif_folder

        temp_folder = self.temp_edit.text().strip()
        if temp_folder:
            config.TEMP_FOLDER = temp_folder

        log_file = self.log_file_edit.text().strip()
        if log_file:
            config.LOG_FILE = log_file

    def _start_sorting(self) -> None:
        source_path = self.source_edit.text().strip()
        result_path = self.result_edit.text().strip()

        if not source_path or not os.path.isdir(source_path):
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Укажите существующую папку source.')
            return

        if not result_path:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Укажите папку result.')
            return

        self._apply_config()

        self.start_button.setEnabled(False)
        self.status_label.setText('Сортировка запущена...')

        self.worker = SortWorker(source_path=source_path, result_path=result_path)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_finished(self) -> None:
        self.status_label.setText('Готово')
        QtWidgets.QMessageBox.information(self, 'Готово', 'Сортировка завершена.')
        self.start_button.setEnabled(True)
        self.worker = None

    def _on_failed(self, message: str) -> None:
        self.status_label.setText('Ошибка')
        QtWidgets.QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка:\n{message}')
        self.start_button.setEnabled(True)
        self.worker = None


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = SortFilesWindow()
    window.resize(640, 420)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
