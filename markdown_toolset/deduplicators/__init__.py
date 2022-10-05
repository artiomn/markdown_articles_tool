from enum import Enum

from markdown_toolset.deduplicators.content_hash_dedup import ContentHashDeduplicator
from markdown_toolset.deduplicators.name_hash_dedup import NameHashDeduplicator


class DeduplicationVariant(Enum):
    DISABLED = 0,
    NAMES_HASHING = 1,
    CONTENT_HASH = 2


DEDUP_MAP = {
    DeduplicationVariant.CONTENT_HASH: ContentHashDeduplicator,
    DeduplicationVariant.NAMES_HASHING: NameHashDeduplicator,
    DeduplicationVariant.DISABLED: None,
}


def select_deduplicator(deduplication_variant: DeduplicationVariant, *args, **kwargs):
    dedup_class = DEDUP_MAP[deduplication_variant]

    return dedup_class(*args, **kwargs) if dedup_class is not None else None


__all__ = [DeduplicationVariant, select_deduplicator]
