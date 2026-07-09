"""
Deduplicators base class.
"""

from abc import abstractmethod, ABC
from typing import Tuple


class Deduplicator(ABC):
    """
    Base abstract class for the all deduplicators.
    """

    @abstractmethod
    def deduplicate(self, image_url, image_filename, image_content, replacement_mapping) -> Tuple[bool, str]:
        """
        Deduplication method.

        :param image_url: URL of the image file.
        :param image_filename: name of the image file to replace.
        :param image_content: content of the image file to replace.
        :param replacement_mapping: mapping content or name to new name.

        :returns: (dedup flag, new filename).
        """
        raise NotImplementedError
