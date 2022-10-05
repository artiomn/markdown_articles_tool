import logging
from pathlib import Path
from typing import Optional, Union

from markdown_toolset.www_tools import is_url, remove_protocol_prefix


class OutPathMaker:
    """
    Get image output path.
    """

    def __init__(self, article_file_path: Path,
                 article_base_url: str = '',
                 img_dir_name: Path = Path('images'),
                 img_public_path: Optional[Path] = None,
                 save_hierarchy: bool = False):
        """
        :parameter article_file_path: path to the article file.
        :parameter article_base_url: URL to download article.
        :parameter img_dir_name: relative path of the directory where image files will be downloaded.
        :parameter img_public_path: if set, will be used in the document instead of `img_dir_name`.
        :parameter save_hierarchy: if set, remote hierarchy will be used for the save image locally.
        """

        logging.debug('Article file path = "%s", base URL = "%s"', article_file_path, article_base_url)

        self._article_file_path: Path = article_file_path
        self._article_base_url = article_base_url
        self._img_dir_name = img_dir_name
        self._images_dir = self._article_file_path.parent / self._img_dir_name
        self._img_public_path = img_public_path
        self._save_hierarchy = save_hierarchy

    @property
    def save_hierarchy(self) -> bool:
        return self._save_hierarchy

    @save_hierarchy.setter
    def save_hierarchy(self, save_hierarchy: bool):
        self._save_hierarchy = save_hierarchy

    @property
    def article_base_url(self) -> str:
        return self._article_base_url

    @property
    def article_file_path(self) -> Path:
        return self._article_file_path

    @property
    def images_dir(self):
        return self._images_dir

    def get_real_path(self, image_url: str, image_filename: Union[str, Path]) -> Path:
        """
        Return image path where image will be written.
        """

        # Case 0: doesn't save path hierarchy:
        if not self._save_hierarchy:
            return self._images_dir / image_filename

        base_url = self._article_base_url
        base_url_without_prefix = remove_protocol_prefix(base_url)

        if is_url(base_url):
            # Remote article.
            if is_url(image_url):
                iu_without_prefix = remove_protocol_prefix(image_url)
                if iu_without_prefix.startswith(base_url_without_prefix):
                    # In the article subdirectory.
                    iu_without_prefix = self._make_relative(iu_without_prefix.removeprefix(base_url_without_prefix))
                result = Path(iu_without_prefix)
            else:
                # Remove leading domain name.
                bu = '/'.join(Path(base_url_without_prefix).parts[1:])

                iu = Path(image_url)
                if iu.is_absolute():
                    result = iu.relative_to(bu) if iu.is_relative_to(bu) else self._make_relative(iu)
                else:
                    result = iu
        else:
            # Local article.
            iup = Path(remove_protocol_prefix(image_url))
            if iup.is_absolute():
                if iup.is_relative_to(base_url):
                    iup = iup.relative_to(base_url)
                else:
                    iup = self._make_relative(iup)

            result = iup

        return self._images_dir / result.as_posix() / image_filename

    def get_document_img_path(self, image_filename):
        return (self._img_public_path if self._img_public_path is not None
                else self._img_dir_name) / image_filename

    def make_directories(self, path: Optional[Path] = None):
        """
        Create directories hierarchy, started from images directory.
        """

        try:
            dir_hier = self._images_dir / path if path is not None else self._images_dir
            dir_hier.mkdir(parents=True)
        except FileExistsError:
            # Existing directory is not error.
            pass

    @staticmethod
    def _make_relative(p: Union[Path, str]):
        if isinstance(p, str):
            p = Path(p)

        return Path('/'.join(p.parts[1:])) if p.is_absolute() else p
