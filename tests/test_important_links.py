import io
from pathlib import Path

from markdown_toolset.article_processor import ArticleProcessor
from markdown_toolset.string_tools import is_binary_same


class TestImportantLinks:
    def setup(self):
        basedir = Path(__file__).parent
        self._article_path = basedir / 'data' / 'important_links.md'
        self._article_out_path = basedir / 'playground' / 'important_links_new.md'

        self._incorrect_article_text =\
            'Important link to remember: ![](https://www.google.com/)\n' \
            ' ![](images/markdown_articles_tool.html)\n' \
            ' ![](https://iiincorrect_link_url_which_doesn\'t_exists.png/image.jpg)\n'

    def teardown(self):
        self._article_out_path.unlink()

    def test_article_processor_save_links(self):
        ap = ArticleProcessor(article_file_path_or_url=self._article_path.as_posix(),
                              output_path=self._article_out_path.as_posix(),
                              skip_all_incorrect=True,
                              download_incorrect_mime=False)
        ap.process()
        assert self._compare_articles()

    def test_article_processor_replace_links(self):
        ap = ArticleProcessor(article_file_path_or_url=self._article_path.as_posix(),
                              output_path=self._article_out_path.as_posix(),
                              skip_all_incorrect=True,
                              download_incorrect_mime=True)
        ap.process()

        assert not self._compare_articles()

        with open(self._article_out_path, 'rb') as f:
            assert is_binary_same(io.BytesIO(self._incorrect_article_text.encode()), f)

    def _compare_articles(self):
        with open(self._article_path, 'rb') as f1:
            with open(self._article_out_path, 'rb') as f2:
                return is_binary_same(f1, f2)
