import hashlib
from pathlib import Path
from typing import Tuple

from .deduplicator import Deduplicator


class ContentHashDeduplicator(Deduplicator):
    def __init__(self, img_dir_name: Path, img_public_path: Path):
        self._hash_to_path_mapping = {}
        self._img_dir_name = img_dir_name
        self._img_public_path = img_public_path

    def deduplicate(self, image_url, image_filename, image_content, replacement_mapping) -> Tuple[bool, str]:
        # TODO: process collisions (possibly).
        new_content_hash = hashlib.sha256(image_content).digest()
        existed_file_name = self._hash_to_path_mapping.get(new_content_hash)
        if existed_file_name is not None:
            img_filename = existed_file_name
            document_img_path = (self._img_public_path or self._img_dir_name) / img_filename
            replacement_mapping.setdefault(image_url, document_img_path)
            return False, img_filename
        else:
            self._hash_to_path_mapping[new_content_hash] = image_filename

        return True, image_filename
