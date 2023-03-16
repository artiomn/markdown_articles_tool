from pathlib import Path

import pytest
from PIL import Image

from markdown_toolset.image_downloader import ImageDownloader, ImageLink
from markdown_toolset.out_path_maker import OutPathMaker
from markdown_toolset.string_tools import compare_files


class TestImageDownloader:
    def setup_method(self):
        basedir = Path(__file__).parent
        self._article_images_path = basedir / 'data' / 'img'
        self._article_base_path = basedir / 'data'
        self._article_out_path = basedir / 'playground' / 'article.md'
        self._images_out_path = self._article_out_path.parent / 'images'

        self._image_filename = 'test_avatar.png'
        self._image_in_relpath = f'{self._article_images_path.name}/{self._image_filename}'
        self._out_image_filepath = self._images_out_path / self._image_filename

    # def teardown_method(self):
    #     if self._out_image_filepath.exists():
    #         self._out_image_filepath.unlink()

    @pytest.fixture(autouse=True)
    def remove_target_image(self):
        if self._out_image_filepath.exists():
            self._out_image_filepath.unlink()
        yield

    def test_local_downloading(self):
        out_path_maker = OutPathMaker(
            article_file_path=self._article_out_path,
            article_base_url=str(self._article_base_path),
            img_dir_name=self._images_out_path,
            img_public_path=Path('images'),
            save_hierarchy=False,
        )

        image_downloader = ImageDownloader(
            out_path_maker=out_path_maker,
            skip_list=[],
            skip_all_errors=False,
            download_incorrect_mime_types=True,
            downloading_timeout=-1,
            deduplicator=None,
        )

        image_downloader.download_images([self._image_in_relpath])

        assert compare_files(self._article_images_path / self._image_filename, self._out_image_filepath)

    def test_resizing(self):
        out_path_maker = OutPathMaker(
            article_file_path=self._article_out_path,
            article_base_url=str(self._article_base_path),
            img_dir_name=self._images_out_path,
            img_public_path=Path('images'),
            save_hierarchy=False,
        )

        image_downloader = ImageDownloader(
            out_path_maker=out_path_maker,
            skip_list=[],
            skip_all_errors=False,
            download_incorrect_mime_types=True,
            downloading_timeout=-1,
            deduplicator=None,
        )

        w, h = 100, 200

        image_downloader.download_images([ImageLink(self._image_in_relpath, new_size=(w, h))])

        assert not compare_files(self._article_images_path / self._image_filename, self._out_image_filepath)
        img = Image.open(self._out_image_filepath)
        assert img.width == w
        assert img.height == h
