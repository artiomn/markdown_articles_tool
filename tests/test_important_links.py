import io
from pathlib import Path
import pytest

from markdown_toolset.article_processor import ArticleProcessor
from markdown_toolset.string_tools import is_binary_same, compare_files


class TestImportantLinks:
    def setup_method(self):
        basedir = Path(__file__).parent
        self._article_path = basedir / 'data' / 'important_links.md'
        self._article_out_path = basedir / 'playground' / 'important_links_new.md'

        self._incorrect_article_text = '''
Important link to remember: ![](https://www.google.com/)
![](https://github.com/artiomn/markdown_articles_tool)
![](https://iiincorrect_link_url_which_doesn't_exists.png/image.jpg)

My avatar scaled to 300 pixels width: ![](https://avatars.githubusercontent.com/u/32387838 =300x)
![Valid URL](https://avatars.githubusercontent.com/u/32387838?s=80&v=4 =300x)
![Resizing](https://avatars.githubusercontent.com/u/32387838?s=80 =1000x0010)

# Resize

![](./pic/pic1_50.png =100x20)

# You can skip the HEIGHT

![](./pic/pic1s.png =250x)

# And Width

![](./pic/pic1s.png =x250)

'''

    # def teardown_method(self):
    #     self._article_out_path.unlink(missing_ok=True)

    def test_article_processor_save_links(self):
        ap = ArticleProcessor(
            article_file_path_or_url=self._article_path.as_posix(),
            output_path=self._article_out_path.as_posix(),
            downloading_timeout=1,
            skip_all_incorrect=True,
            download_incorrect_mime=False,
        )
        ap.process()
        assert self._compare_articles()

    @pytest.mark.skip(reason='Need to improve')
    def test_article_processor_replace_links(self):
        ap = ArticleProcessor(
            article_file_path_or_url=self._article_path.as_posix(),
            output_path=self._article_out_path.as_posix(),
            downloading_timeout=1,
            skip_all_incorrect=True,
            download_incorrect_mime=True,
        )
        ap.process()
        #
        # assert not self._compare_articles()

        with open(self._article_out_path, 'rb') as f:
            try:
                assert is_binary_same(io.BytesIO(self._incorrect_article_text.encode()), f)
            finally:
                f.close()

    def _compare_articles(self):
        return compare_files(self._article_path, self._article_out_path)
