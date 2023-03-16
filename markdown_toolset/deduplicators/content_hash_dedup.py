import hashlib
import logging
from io import BytesIO
from pathlib import Path
from typing import Tuple, Optional, Dict, Union

from .deduplicator import Deduplicator
from ..string_tools import is_binary_same


class ContentHashDeduplicator(Deduplicator):
    """
    Reliable images deduplicator using content hash.
    """

    def __init__(self, img_dir_name: Path, img_public_path: Optional[Path]):
        self._hash_to_path_mapping: Dict[bytes, Union[Path, str]] = {}
        self._img_dir_name = img_dir_name
        self._img_public_path = img_public_path

    def deduplicate(self, image_url, image_filename, image_content, replacement_mapping) -> Tuple[bool, str]:
        new_content_hash = hashlib.sha256(image_content).digest()
        existed_file_name = self._hash_to_path_mapping.get(new_content_hash)
        # TODO: не работает!!!
        if existed_file_name is not None:
            document_img_path = (
                self._img_public_path if self._img_public_path else self._img_dir_name
            ) / existed_file_name
            logging.debug(
                'ContentHashDeduplicator: existed filename = "%s", document image path = "%s"',
                existed_file_name,
                document_img_path,
            )
            with open(document_img_path, 'rb') as cur_image:
                # Test for the collisions prevention.
                if is_binary_same(BytesIO(image_content), cur_image):
                    logging.debug('Images with the names "%s" and "%s" are similar', existed_file_name, image_filename)
                    replacement_mapping.setdefault(image_url, document_img_path)
                    return False, str(existed_file_name)

        self._hash_to_path_mapping[new_content_hash] = image_filename

        return True, image_filename
