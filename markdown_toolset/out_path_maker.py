from pathlib import Path
from typing import Optional


class OutPathMaker:
    """
    Get image output path.
    """

    def __init__(self, article_path: Path,
                 article_base_url: str = '',
                 img_dir_name: Path = Path('images'),
                 img_public_path: Optional[Path] = None):
        self._article_file_path: Path = article_path
        self._article_base_url = article_base_url
        self._img_dir_name = img_dir_name
        self._images_dir = self._article_file_path.parent / self._img_dir_name
        self._img_public_path = img_public_path

    def get_path(self) -> Path:
        pass
