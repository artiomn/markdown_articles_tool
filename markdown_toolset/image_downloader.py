import hashlib
import logging
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple, Union, Dict

from PIL import Image

from .deduplicators.deduplicator import Deduplicator
from .out_path_maker import OutPathMaker
from .www_tools import download_from_url, get_filename_from_url, is_url, remove_protocol_prefix, split_file_ext
from .string_tools import is_binary_same


class ImageLink:
    """Downloading link or path with parameters."""

    def __init__(self, link: str, new_size: Optional[Tuple[Optional[int], Optional[int]]] = None):
        """
        :parameter link: link to the image.

        :parameter rescale: new image size in pixels.
        """
        self._link = link
        self._new_size = new_size

    @property
    def need_rescaling(self) -> bool:
        return self._new_size is not None and (self._new_size[0] is not None or self._new_size[1] is not None)

    @property
    def new_size(self) -> Tuple[int, int]:
        return self._new_size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImageLink):
            raise NotImplementedError

        if self._link != other._link:
            return False

        if self.need_rescaling == other.need_rescaling:
            if not self.need_rescaling:
                return True

            return self.new_size[0] == other.new_size[0] and self._new_size[1] == other.new_size[1]

        return False

    def __hash__(self):
        return hash(f'{id(self)}{str(self)}{self._new_size}')

    def __str__(self) -> str:
        return self._link

    def __repr__(self):
        return f'{self.__class__.__name__} object at {hex(id(self))}: {str(self)} [{self._new_size}]'


class ImageDownloader:
    """ "Smart" images downloader."""

    def __init__(
        self,
        out_path_maker: OutPathMaker,
        skip_list: Optional[List[str]] = None,
        skip_all_errors: bool = False,
        download_incorrect_mime_types: bool = False,
        downloading_timeout: float = -1,
        deduplicator: Optional[Deduplicator] = None,
        replace_image_names: bool = False,
    ):
        """
        :parameter out_path_maker: image local path creating strategy.

        :parameter skip_list: URLs of images to skip.
        :parameter skip_all_errors: if it's True, skip all errors and continue working.
        :parameter downloading_timeout: if timeout =< 0 - infinite wait for the image downloading, otherwise wait for
                                        `downloading_timeout` seconds.
        :parameter download_incorrect_mime_types: download images even if MIME type can't be identified.
        :parameter deduplicator: file deduplicator object.
        :parameter replace_image_names: replace image names with hash.
        """

        self._out_path_maker = out_path_maker
        self._skip_list = set(skip_list) if skip_list is not None else []
        self._skip_all_errors = skip_all_errors
        self._downloading_timeout = downloading_timeout if downloading_timeout > 0 else None
        self._download_incorrect_mime_types = download_incorrect_mime_types
        self._deduplicator = deduplicator
        self._running = False
        self._replace_image_names = replace_image_names

    # pylint: disable=R0912(too-many-branches)
    def download_images(self, images: List[Union[str, ImageLink]]) -> dict:
        """
        Download and save images from the list.

        :return URL -> file path mapping.
        """

        replacement_mapping: Dict[str, str] = {}

        images_count = len(images)

        # TODO: Refactor this.
        try:
            self._running = True
            for image_num, image_link in enumerate(images):
                if not self._running:
                    logging.debug('Images downloading was stopped forcibly')
                    break

                image_url = str(image_link)

                assert image_url not in replacement_mapping, f'BUG: already downloaded image "{image_url}"...'

                if self._need_to_skip_url(image_url):
                    logging.debug('Image %d downloading was skipped...', image_num + 1)
                    continue

                if not is_url(image_url):
                    logging.warning('Image %d ["%s"] probably has incorrect URL...', image_num + 1, image_url)

                    if self._out_path_maker.article_base_url:
                        logging.debug('Trying to add base URL "%s"...', self._out_path_maker.article_base_url)
                        image_download_url = f'{self._out_path_maker.article_base_url}/{image_url}'
                    else:
                        image_download_url = str(Path(self._out_path_maker.article_file_path).parent / image_url)
                else:
                    image_download_url = image_url

                try:
                    mime_type, _ = mimetypes.guess_type(image_download_url)
                    logging.debug('"%s" MIME type = %s', image_download_url, mime_type)

                    if not self._download_incorrect_mime_types and mime_type is None:
                        logging.warning(
                            'Image "%s" has incorrect MIME type and will not be downloaded!', image_download_url
                        )
                        continue

                    logging.debug('Image is URL: %s', is_url(image_download_url))

                    image_filename, image_content = (
                        self._get_remote_image(image_download_url, image_num, images_count)
                        if is_url(image_download_url)
                        else ImageDownloader._get_local_image(Path(image_download_url))
                    )

                    logging.debug('Guessed image filename: %s', image_filename)

                    if image_filename is None:
                        logging.warning(
                            'Empty image filename, probably this is incorrect link: "%s".', image_download_url
                        )
                        continue

                    if self._replace_image_names:
                        _, image_ext = split_file_ext(image_filename)
                        image_content_hash = hashlib.sha384(image_content).hexdigest()
                        logging.debug('Image content hash: %s', image_filename)
                        image_filename = f'{image_content_hash}.{image_ext}'

                except Exception as e:
                    if self._skip_all_errors:
                        logging.warning(
                            'Can\'t get image %d, error: [%s], '
                            'but processing will be continued, because `skip_all_errors` flag is set',
                            image_num + 1,
                            str(e),
                        )
                        continue
                    raise

                if self._deduplicator is not None:
                    if not (isinstance(image_link, ImageLink) and image_link.need_rescaling):
                        result, image_filename = self._deduplicator.deduplicate(
                            image_url, image_filename, image_content, replacement_mapping
                        )
                        if not result:
                            continue

                image_local_url, real_image_path = self._get_real_path(image_url, image_filename)

                if self._replace_image_names and real_image_path.exists():
                    # Image by this content hash exists, but possibly this is a collision.
                    with open(real_image_path, 'rb') as real_file:
                        if not is_binary_same(real_file, BytesIO(image_content)):
                            # Fix collision, changing name.
                            img_num: int = 0
                            while real_image_path.exists():
                                numerated_image_filename = f'{image_num}{image_filename}'
                                real_image_path = self._out_path_maker.get_real_path(
                                    image_local_url, numerated_image_filename
                                )
                                img_num += 1

                            image_filename = numerated_image_filename

                self._update_mapping(image_url, image_local_url, image_filename, replacement_mapping)
                self._write_image(real_image_path, image_content, image_link)
        finally:
            logging.info('Finished images downloading.')
            self._running = False

        return replacement_mapping

    @property
    def running(self) -> bool:
        return self._running

    def stop(self):
        logging.info('Images downloading stopped.')
        self._running = False

    @staticmethod
    def _resize_image(image_content: bytes, new_size, filename):
        img = Image.open(BytesIO(image_content))
        # img = Image.frombuffer(image_content)

        w = new_size[0]
        if w is None:
            w = img.width

        h = new_size[1]
        if h is None:
            h = img.height

        img = img.resize((w, h))
        logging.debug('Saving resized image to the %s', filename)
        img.save(filename)

    def _get_real_path(self, image_url, image_filename):
        """Get real image path."""
        image_local_url = Path(remove_protocol_prefix(image_url)).parent.as_posix()
        real_image_path = self._out_path_maker.get_real_path(image_local_url, image_filename)

        logging.debug('Real image path = "%s", image filename = "%s"', real_image_path, image_filename)

        return image_local_url, real_image_path

    def _update_mapping(self, image_url, image_local_url, image_filename, replacement_mapping):
        """Update replacement mapping."""
        document_img_path = self._out_path_maker.get_document_img_path(image_local_url, image_filename)
        image_filename, document_img_path = self._fix_paths(
            replacement_mapping, document_img_path, image_url, image_filename
        )
        replacement_mapping.setdefault(image_url, '/'.join(document_img_path.parts))

        logging.debug(
            'Document image path = "%s", image filename = "%s"',
            document_img_path,
            image_filename,
        )

    def _make_directories(self, path: Optional[Path] = None):
        """Create directories hierarchy, started from images directory."""

        try:
            dir_hier = self._out_path_maker.images_dir / path if path is not None else self._out_path_maker.images_dir
            dir_hier.mkdir(parents=True)
        except FileExistsError:
            # Existing directory is not error.
            pass

    def _need_to_skip_url(self, image_url: str) -> bool:
        """Returns True, if the image doesn't need to be downloaded."""

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

    def _write_image(self, image_path: Path, data: bytes, image_link: Union[ImageLink, str]):
        """Write image data into the file."""

        if image_path.exists():
            logging.info('Image "%s" already exists and will not be written...', image_path)
            return

        self._make_directories(image_path.parent)

        logging.info('Image will be written to the file "%s"...', image_path)

        if isinstance(image_link, ImageLink) and image_link.need_rescaling:
            logging.debug('Rescaling image to %dx%d', *image_link.new_size)
            self._resize_image(data, image_link.new_size, image_path)
        else:
            with open(image_path, 'wb') as image_file:
                image_file.write(data)
                image_file.close()

    def _fix_paths(self, replacement_mapping, document_img_path, img_url, image_filename):
        """Fix path if a file with the similar name exists already."""

        # Images can have similar name, but different URLs, but I want to save original filename, if possible.
        for url, path in replacement_mapping.items():
            if document_img_path == path and img_url != url:
                image_filename = f'{hashlib.sha256(img_url.encode()).hexdigest()}_{image_filename}'
                document_img_path = self._out_path_maker.get_document_img_path(img_url, image_filename)
                break

        return image_filename, document_img_path
