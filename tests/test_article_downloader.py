from pathlib import Path

from markdown_toolset.article_downloader import ArticleDownloader
from markdown_toolset.formatters import get_formatter, FORMATTERS
from markdown_toolset.string_tools import is_binary_same


class TestArticleDownloader:
    def setup(self):
        basedir = Path(__file__).parent
        self._article_path = basedir / 'data' / 'article.md'
        self._article_out_path = basedir / 'playground' / 'article.md'
        self._article_formatter = get_formatter('md', FORMATTERS)
        # logging.root.setLevel(logging.DEBUG)

    def teardown(self):
        # self._article_out_path.unlink()
        pass

    def test_article_downloader(self):
        # Local article **will not** be copied.
        article_downloader = ArticleDownloader(
            article_url=self._article_path.as_posix(),
            output_path=self._article_out_path,
            article_formatter=self._article_formatter)
        article_path, article_base_url, article_out_path = article_downloader.get_article()

        assert article_base_url == self._article_path.parent.as_posix()
        assert article_path.as_posix() == self._article_path.as_posix()

    def _compare_articles(self, out_path):
        with open(self._article_path, 'rb') as f1:
            with open(out_path, 'rb') as f2:
                return is_binary_same(f1, f2)
