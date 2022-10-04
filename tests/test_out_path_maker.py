from pathlib import Path

from markdown_toolset.out_path_maker import OutPathMaker


class TestOutPathMaker:
    def setup(self):
        self._image_filename = 'image.png'
        self._image_relative_path = 'url/to/image'

    def _wo_hier_tester(self, opm):
        opm.save_hierarchy = False

        assert opm.get_real_path('url/to/image', self._image_filename) == \
               Path(opm.images_dir) / self._image_filename

    def _with_hier_path_tester(self, opm):
        opm.save_hierarchy = True

        image_relative_path, image_absolute_path = self._image_relative_path, f'/{self._image_relative_path}'

        # relative path:
        # /home/artiom/images/url/to/image/image.png
        assert opm.get_real_path(image_relative_path, self._image_filename) ==\
               Path(opm.images_dir) / image_relative_path / self._image_filename

        # absolute path:
        # /home/artiom/images/url/to/image/image.png
        assert opm.get_real_path(image_absolute_path, self._image_filename) ==\
               Path(opm.images_dir) / image_relative_path / self._image_filename

        assert opm.get_real_path(f'{opm.article_base_url}/{image_relative_path}', self._image_filename) ==\
               Path(opm.images_dir) / image_relative_path / self._image_filename

    def _with_hier_url_tester(self, opm, site_url, include_site_url=True):
        opm.save_hierarchy = True

        image_relative_path, image_absolute_path = self._image_relative_path, f'/{self._image_relative_path}'

        base_image_url = f'{site_url}/{image_relative_path}' if include_site_url else image_relative_path
        image_absolute_http_url = f'http://{base_image_url}'
        image_absolute_https_url = f'https://{base_image_url}'
        image_absolute_https_uc_url = f'HTTPS://{base_image_url}'

        # url:
        # /home/artiom/images/notagoogle.com/url/to/image/image.png
        for url in [image_absolute_http_url, image_absolute_https_url, image_absolute_https_uc_url]:
            assert opm.get_real_path(url, self._image_filename) ==\
                Path(opm.images_dir) / base_image_url / self._image_filename

    def test_local_path_maker_without_hier(self):
        opm = OutPathMaker(
            article_file_path=Path('/home/artiom/my_article.md'),
            article_base_url='/home/artiom',
            img_dir_name=Path('/home/artiom/images')
        )

        self._wo_hier_tester(opm)

    def test_url_path_maker_without_hier(self):
        opm = OutPathMaker(
            article_file_path=Path('/home/artiom/my_article.md'),
            article_base_url='https://artiomsoft.ru',
            img_dir_name=Path('/home/artiom/images')
        )

        self._wo_hier_tester(opm)

    def test_local_path_maker_paths_with_hier(self):
        opm = OutPathMaker(
            article_file_path=Path('/home/artiom/my_article.md'),
            article_base_url='/home/artiom',
            img_dir_name=Path('/home/artiom/images')
        )

        self._with_hier_path_tester(opm)

    def test_url_path_maker_paths_with_hier(self):
        opm = OutPathMaker(
            article_file_path=Path('/home/artiom/my_article.md'),
            article_base_url='https://artiomsoft.ru',
            img_dir_name=Path('/home/artiom/images')
        )

        self._with_hier_path_tester(opm)

    def test_local_path_maker_urls_with_hier(self):
        opm = OutPathMaker(
            article_file_path=Path('/home/artiom/my_article.md'),
            article_base_url='/home/artiom',
            img_dir_name=Path('/home/artiom/images')
        )

        self._with_hier_url_tester(opm, 'notagoogle.com')

    def test_url_path_maker_urls_with_hier(self):
        opm = OutPathMaker(
            article_file_path=Path('/home/artiom/my_article.md'),
            article_base_url='https://artiomsoft.ru',
            img_dir_name=Path('/home/artiom/images')
        )

        self._with_hier_url_tester(opm, 'notagoogle.com')
        # Image Url started with site URL.
        self._with_hier_url_tester(opm, 'artiomsoft.com', False)
