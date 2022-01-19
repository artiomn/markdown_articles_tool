from enum import Enum
import hashlib
from pathlib import Path
from typing import Optional, List

from .www_tools import is_url, get_filename_from_url, download_from_url


class DeduplicationVariant(Enum):
    DISABLED = 0,
    NAMES_HASHING = 1,
    CONTENT_HASH = 2


class ImageDownloader:
    """
    "Smart" images downloader.
    """

    # TODO: many parameters - refactor this.
    def __init__(self, article_path: Path, article_base_url: str = '', skip_list: Optional[List[str]] = None,
                 skip_all_errors: bool = False, img_dir_name: Path = Path('images'), img_public_path: Path = Path(''),
                 downloading_timeout: float = -1,
                 deduplication_variant: DeduplicationVariant = DeduplicationVariant.DISABLED,
                 process_local_images: bool = False):
        """
        :parameter article_path: path to the article file.
        :parameter article_base_url: URL to download article.
        :parameter skip_list: URLs of images to skip.
        :parameter skip_all_errors: if it's True, skip all errors and continue working.
        :parameter img_dir_name: relative path of the directory where image files will be downloaded.
        :parameter img_public_path: if set, will be used in the document instead of `img_dir_name`.
        :parameter downloading_timeout: if timeout =< 0 - infinite wait for the image downloading, otherwise wait for
                                        `downloading_timeout` seconds.
        :parameter deduplication_variant: type of the deduplication:
                                          NAMES_HASHING - file names will be sha1(image_content).
                                          CONTENT_HASH - first image name will be used.
        :parameter process_local_images: if True, local image files will be processed.
        """

        # TODO: rename parameters.
        self._img_dir_name = img_dir_name
        self._img_public_path = img_public_path
        self._article_file_path: Path = article_path
        self._article_base_url = article_base_url
        self._skip_list = set(skip_list) if skip_list is not None else []
        self._images_dir = self._article_file_path.parent / self._img_dir_name
        self._skip_all_errors = skip_all_errors
        self._downloading_timeout = downloading_timeout if downloading_timeout > 0 else None
        self._deduplication_variant = deduplication_variant
        self._process_local_images = process_local_images

    def download_images(self, images: List[str]) -> dict:
        """
        Download and save images from the list.

        :return URL -> file path mapping.
        """

        replacement_mapping = {}
        hash_to_path_mapping = {}
        skip_list = self._skip_list
        images_count = len(images)
        img_dir_name = self._img_dir_name
        img_public_path = self._img_public_path
        images_dir = self._images_dir
        deduplication_variant = self._deduplication_variant

        try:
            self._images_dir.mkdir(parents=True)
        except FileExistsError:
            # Existing directory is not error.
            pass

        for image_num, image_url in enumerate(images):
            assert image_url not in replacement_mapping.keys(), f'BUG: already downloaded image "{image_url}"...'

            if image_url in skip_list:
                # TODO: Replace with logging.
                print(f'Image {image_num + 1} ["{image_url}"] was skipped, because it\'s in the skip list...')
                continue

            image_path_is_url = is_url(image_url)
            if not image_path_is_url and not self._process_local_images:
                print(f'Image {image_num + 1} ["{image_url}"] has incorrect URL...')
                if self._article_base_url:
                    print(f'Trying to add base URL "{self._article_base_url}"...')
                    image_url = f'{self._article_base_url}/{image_url}'
                else:
                    print('Image downloading will be skipped...')
                    continue

            try:
                image_filename, image_content = \
                    self._get_remote_image(image_url, image_num, images_count) if image_path_is_url \
                    else ImageDownloader._get_local_image(Path(image_url))
            except Exception as e:
                if self._skip_all_errors:
                    print(f'Warning: can\'t get image {image_num + 1}, error: [{str(e)}], '
                          'but processing will be continued, because `skip_all_errors` flag is set')
                    continue
                raise

            if DeduplicationVariant.CONTENT_HASH == deduplication_variant:
                # TODO: process collisions (possibly).
                new_content_hash = hashlib.sha256(image_content).digest()
                existed_file_name = hash_to_path_mapping.get(new_content_hash)
                if existed_file_name is not None:
                    img_filename = existed_file_name
                    document_img_path = (img_public_path or img_dir_name) / img_filename
                    replacement_mapping.setdefault(image_url, document_img_path)
                    continue
                else:
                    hash_to_path_mapping[new_content_hash] = image_filename
            elif DeduplicationVariant.NAMES_HASHING == deduplication_variant:
                # TODO: replace sha-1, check for collisions.
                image_filename = f'{hashlib.sha1(image_content).hexdigest()}{Path(image_filename).suffix}'
            elif DeduplicationVariant.DISABLED == deduplication_variant:
                pass

            document_img_path = (img_public_path or img_dir_name) / image_filename
            image_filename, document_img_path = self._correct_paths(replacement_mapping, document_img_path, image_url,
                                                                    image_filename)

            real_image_path = images_dir / image_filename
            replacement_mapping.setdefault(image_url, '/'.join(document_img_path.parts))

            ImageDownloader._write_image(real_image_path, image_content)

        return replacement_mapping

    def _get_remote_image(self, image_url: str, img_num: int, img_count: int):
        print(f'Downloading image {img_num + 1} of {img_count} from "{image_url}"...')
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
        print(f'Image will be written to the file "{image_path}"...')
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
                document_img_path = (self._img_public_path or self._img_dir_name) / image_filename
                break

        return image_filename, document_img_path
