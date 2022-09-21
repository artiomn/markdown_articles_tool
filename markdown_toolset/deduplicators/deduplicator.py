"""
Deduplicators base class.
"""

from abc import abstractmethod, ABC


class Deduplicator(ABC):
    """
    Base abstract class for the all deduplicators.
    """

    @abstractmethod
    def deduplicate(self, image_url, image_filename, image_content, replacement_mapping) -> bool:
        pass
