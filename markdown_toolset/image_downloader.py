import logging
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List

from .deduplicators.deduplicator import Deduplicator
from .out_path_maker import OutPathMaker
from .www_tools import is_url, get_filename_from_url, download_from_url


class ImageDownloader:
    """
    "Smart" images downloader.
    """

    def __init__(self,
                 out_path_maker: OutPathMaker,
                 skip_list: Optional[List[str]] = None,
                 skip_all_errors: bool = False,
                 download_incorrect_mime_types: bool = False,
                 downloading_timeout: float = -1,
                 deduplicator: Optional[Deduplicator] = None):
        """
        :parameter out_path_maker: image local path creating strategy.
        :parameter skip_list: URLs of images to skip.
        :parameter skip_all_errors: if it's True, skip all errors and continue working.
        :parameter downloading_timeout: if timeout =< 0 - infinite wait for the image downloading, otherwise wait for
                                        `downloading_timeout` seconds.
        :parameter download_incorrect_mime_types: download images even if MIME type can't be identified.
        :parameter deduplicator: file deduplicator object.
        """

        self._out_path_maker = out_path_maker
        self._skip_list = set(skip_list) if skip_list is not None else []
        self._skip_all_errors = skip_all_errors
        self._downloading_timeout = downloading_timeout if downloading_timeout > 0 else None
        self._download_incorrect_mime_types = download_incorrect_mime_types
        self._deduplicator = deduplicator

    def download_images(self, images: List[str]) -> dict:
        """
        Download and save images from the list.

        :return URL -> file path mapping.
        """

        replacement_mapping = {}

        images_count = len(images)

        for image_num, image_url in enumerate(images):
            assert image_url not in replacement_mapping.keys(), f'BUG: already downloaded image "{image_url}"...'

            if self._need_to_skip_url(image_url):
                logging.debug('Image %d downloading was skipped...', image_num + 1)
                continue

            image_path_is_url = is_url(image_url)

            if not image_path_is_url:
                logging.warning('Image %d ["%s"] probably has incorrect URL...', image_num + 1, image_url)

                if self._out_path_maker.article_base_url:
                    logging.debug('Trying to add base URL "%s"...', self._out_path_maker.article_base_url)
                    image_download_url = f'{self._out_path_maker.article_base_url}/{image_url}'
                else:
                    image_download_url = str(Path(self._out_path_maker.article_file_path).parent/image_url)
            else:
                image_download_url = image_url

            try:
                mime_type, _ = mimetypes.guess_type(image_download_url)
                logging.debug('"%s" MIME type = %s', image_download_url, mime_type)

                if not self._download_incorrect_mime_types and mime_type is None:
                    logging.warning('Image "%s" has incorrect MIME type and will not be downloaded!',
                                    image_download_url)
                    continue

                image_filename, image_content = \
                    self._get_remote_image(image_download_url, image_num, images_count) if image_path_is_url \
                    else ImageDownloader._get_local_image(Path(image_download_url))

                if image_filename is None:
                    logging.warning('Empty image filename, probably this is incorrect link: "%s".', image_download_url)
                    continue
            except Exception as e:
                if self._skip_all_errors:
                    logging.warning('Can\'t get image %d, error: [%s], '
                                    'but processing will be continued, because `skip_all_errors` flag is set',
                                    image_num + 1, str(e))
                    continue
                raise

            self._out_path_maker.make_directories(Path(image_url).parent)

            if self._deduplicator is not None:
                result, image_filename = self._deduplicator.deduplicate(image_url, image_filename, image_content,
                                                                        replacement_mapping)
                if not result:
                    continue

            document_img_path = self._out_path_maker.get_document_img_path(image_filename)
            image_filename, document_img_path = self._fix_paths(replacement_mapping, document_img_path, image_url,
                                                                image_filename)

            real_image_path = self._out_path_maker.get_real_path(image_url, image_filename)
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

        if image_path.exists():
            logging.info('Image "%s" already exists and will not be written...', image_path)
            return

        logging.info('Image will be written to the file "%s"...', image_path)
        with open(image_path, 'wb') as image_file:
            image_file.write(data)
            image_file.close()

    def _fix_paths(self, replacement_mapping, document_img_path, img_url, image_filename):
        """
        Fix path if a file with the similar name exists already.
        """

        # Images can have similar name, but different URLs, but I want to save original filename, if possible.
        for url, path in replacement_mapping.items():
            if document_img_path == path and img_url != url:
                image_filename = f'{hashlib.md5(img_url.encode()).hexdigest()}_{image_filename}'
                document_img_path = self._out_path_maker.get_document_img_path(image_filename)
                break

        return image_filename, document_img_path
