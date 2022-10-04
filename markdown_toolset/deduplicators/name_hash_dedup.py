import hashlib
from pathlib import Path
from typing import Tuple

from .deduplicator import Deduplicator


class NameHashDeduplicator(Deduplicator):
    def deduplicate(self, image_url, image_filename, image_content, replacement_mapping) -> Tuple[bool, str]:
        # TODO: check for collisions.
        result = f'{hashlib.sha256(image_content).hexdigest()}{Path(image_filename).suffix}'

        return True, result
