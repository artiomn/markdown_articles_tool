import hashlib
from pathlib import Path
from typing import Tuple

from .deduplicator import Deduplicator


class NameHashDeduplicator(Deduplicator):
    def deduplicate(self, image_url, image_filename, image_content, replacement_mapping) -> Tuple[bool, str]:
        # TODO: replace sha-1, check for collisions.
        return True, f'{hashlib.sha1(image_content).hexdigest()}{Path(image_filename).suffix}'
