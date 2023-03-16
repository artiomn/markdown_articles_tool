from pathlib import Path

from markdown_toolset.article_downloader import ArticleDownloader
from markdown_toolset.formatters import FORMATTERS, get_formatter


class TestArticleDownloader:
    def setup_method(self):
        basedir = Path(__file__).parent
        self._article_path = basedir / 'data' / 'article.md'
        self._article_out_path = basedir / 'playground' / 'article.md'
        self._article_formatter = get_formatter('md', FORMATTERS)
        # logging.root.setLevel(logging.DEBUG)

    def test_article_downloader(self):
        """
        This is the **downloader** test.

        Local article **will not** be copied.
        Copying and other stuff will be done by the processor and other modules.
        """
        article_downloader = ArticleDownloader(
            article_url=self._article_path.as_posix(),
            output_path=self._article_out_path,
            article_formatter=self._article_formatter,
        )
        article_path, article_base_url, article_out_path = article_downloader.get_article()

        assert article_base_url == self._article_path.parent.as_posix()
        assert article_path.as_posix() == self._article_path.as_posix()
        # MUST NOT be exists.
        assert not article_out_path.exists()
