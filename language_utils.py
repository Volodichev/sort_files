import logging
import os
import re
from typing import Iterable, Set

from langdetect import detect, detect_langs

import config


def contain_any(a_list: Iterable, b_list: Iterable) -> bool:
    """INNER JOIN of two iterables."""
    return bool(set(a_list) & set(b_list))


def detect_languages(value: str, source_path: str | None = None) -> Set[str]:
    """Detect languages used in a string or path."""
    langs: list[str] = []
    if os.path.isdir(value):
        t_path = value
        t_folder = True
        while t_folder:
            if source_path and os.path.samefile(t_path, source_path):
                break
            t_path, t_folder = os.path.split(t_path)
            if re.findall(r'[^_\W\d]', t_folder):
                try:
                    for detect_lang in detect_langs(t_folder):
                        langs.append(str(detect_lang.lang))
                except Exception as e:
                    logging.error(f"Can't detect language in path chunk: ({t_folder}) error: {e}")
    else:
        if re.findall(r'[^_\W\d]', value):
            try:
                langs.append(str(detect(value)))
                for detect_lang in detect_langs(value):
                    langs.append(str(detect_lang.lang))
            except Exception as e:
                logging.error(f"Can't detect language: ({value}) error: {e}")

    return set(langs)


def path_contains_cyrillic(path: str, source_path: str | None = None) -> bool:
    """Check path for Cyrillic languages defined in config.CYR_LANG."""
    return contain_any(detect_languages(path, source_path), config.CYR_LANG)
