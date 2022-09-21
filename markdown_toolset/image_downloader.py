import logging
import hashlib
from pathlib import Path
from typing import Optional, List

from .deduplicators.deduplicator import Deduplicator
from .out_path_maker import OutPathMaker
from .www_tools import is_url, get_filename_from_url, download_from_url


class ImageDownloader:
    """
    "Smart" images downloader.
    """

    # TODO: many parameters - refactor this.
    def __init__(self,
                 out_path_maker: OutPathMaker,
                 skip_list: Optional[List[str]] = None,
                 skip_all_errors: bool = False,
                 downloading_timeout: float = -1,
                 deduplicator: Optional[Deduplicator] = None):
        """
        :parameter article_path: path to the article file.
        :parameter article_base_url: URL to download article.
        :parameter skip_list: URLs of images to skip.
        :parameter skip_all_errors: if it's True, skip all errors and continue working.
        :parameter img_dir_name: relative path of the directory where image files will be downloaded.
        :parameter img_public_path: if set, will be used in the document instead of `img_dir_name`.
        :parameter downloading_timeout: if timeout =< 0 - infinite wait for the image downloading, otherwise wait for
                                        `downloading_timeout` seconds.
        :parameter deduplicator: file deduplicator object.
        :parameter process_local_images: if True, local image files will be processed.
        """

        # TODO: rename parameters.
        self._out_path_maker = out_path_maker
        self._skip_list = set(skip_list) if skip_list is not None else []
        self._skip_all_errors = skip_all_errors
        self._downloading_timeout = downloading_timeout if downloading_timeout > 0 else None
        self._deduplicator = deduplicator

    def download_images(self, images: List[str]) -> dict:
        """
        Download and save images from the list.

        :return URL -> file path mapping.
        """

        replacement_mapping = {}

        images_count = len(images)
        images_dir = self._out_path_maker._images_dir

        try:
            self._out_path_maker._images_dir.mkdir(parents=True)
        except FileExistsError:
            # Existing directory is not error.
            pass

        for image_num, image_url in enumerate(images):
            assert image_url not in replacement_mapping.keys(), f'BUG: already downloaded image "{image_url}"...'

            if self._need_to_skip_url(image_url):
                logging.debug('Image %d downloading was skipped...', image_num + 1)
                continue

            image_path_is_url = is_url(image_url)

            if not image_path_is_url:
                logging.warning('Image %d ["%s"] probably has incorrect URL...', image_num + 1, image_url)

                if self._out_path_maker._article_base_url:
                    logging.debug('Trying to add base URL "%s"...', self._out_path_maker._article_base_url)
                    image_url = f'{self._out_path_maker._article_base_url}/{image_url}'
                else:
                    image_url = str(Path(self._out_path_maker._article_file_path).parent/image_url)

            try:
                image_filename, image_content = \
                    self._get_remote_image(image_url, image_num, images_count) if image_path_is_url \
                    else ImageDownloader._get_local_image(Path(image_url))
            except Exception as e:
                if self._skip_all_errors:
                    logging.warning('Can\'t get image %d, error: [%s], '
                                    'but processing will be continued, because `skip_all_errors` flag is set',
                                    image_num + 1, str(e))
                    continue
                raise

            if self._deduplicator is not None:
                result, image_filename = self._deduplicator.deduplicate(image_url, image_filename, image_content,
                                                                        replacement_mapping)
                if not result:
                    continue

            document_img_path = self._get_document_img_path(image_filename)
            image_filename, document_img_path = self._correct_paths(replacement_mapping, document_img_path, image_url,
                                                                    image_filename)

            real_image_path = images_dir / image_filename
            replacement_mapping.setdefault(image_url, '/'.join(document_img_path.parts))

            ImageDownloader._write_image(real_image_path, image_content)

        return replacement_mapping

    def _need_to_skip_url(self, image_url: str) -> bool:
        """
        Returns True, if the image doesn't need to be downloaded.
        """

        if image_url in self._skip_list:
            logging.debug('Image ["%s"] was skipped, because it\'s in the skip list...', image_url)
            return True

        return False

    def _get_document_img_path(self, image_filename):
        return (self._out_path_maker._img_public_path if self._out_path_maker._img_public_path is not None
                else self._out_path_maker._img_dir_name) / image_filename

    def _get_remote_image(self, image_url: str, img_num: int, img_count: int):
        logging.info('Downloading image %d of %d from "%s"...', img_num + 1, img_count, image_url)
        img_response = download_from_url(image_url, self._downloading_timeout)

        return get_filename_from_url(img_response), img_response.content

    @staticmethod
    def _get_local_image(image_path: Path):
        with open(image_path, 'rb') as in_file:
            image_content = in_file.read()

        return image_path.name, image_content

    @staticmethod
    def _write_image(image_path: Path, data: bytes):
        """
        Write image data into the file.
        """

        # TODO: check if image already exists.
        logging.info('Image will be written to the file "%s"...', image_path)
        with open(image_path, 'wb') as image_file:
            image_file.write(data)
            image_file.close()

    def _correct_paths(self, replacement_mapping, document_img_path, img_url, image_filename):
        """
        Fix path if a file with the similar name exists already.
        """

        # Images can have similar name, but different URLs, but I want to save original filename, if possible.
        for url, path in replacement_mapping.items():
            if document_img_path == path and img_url != url:
                image_filename = f'{hashlib.md5(img_url.encode()).hexdigest()}_{image_filename}'
                document_img_path = self._get_document_img_path(image_filename)
                break

        return image_filename, document_img_path
