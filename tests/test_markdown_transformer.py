from pathlib import Path

from markdown_toolset.image_downloader import ImageLink
from markdown_toolset.transformers.md.transformer import ArticleTransformer


class TestMarkdownTransformer:
    def setup_method(self):
        basedir = Path(__file__).parent
        self._article_path = basedir / 'data' / 'important_links.md'
        self._article_out_path = basedir / 'playground' / 'important_links_new.md'

    def test_image_links_extraction(self):
        true_result = [
            ImageLink('https://www.google.com/'),
            ImageLink('https://github.com/artiomn/markdown_articles_tool'),
            ImageLink('https://iiincorrect_link_url_which_doesn\'t_exists.png/image.jpg'),
            ImageLink('https://avatars.githubusercontent.com/u/32387838', (300, None)),
            ImageLink('https://avatars.githubusercontent.com/u/32387838?s=80&v=4', (300, None)),
            ImageLink('https://avatars.githubusercontent.com/u/32387838?s=80', (1000, 10)),
            ImageLink('./pic/pic1_50.png', (100, 20)),
            ImageLink('./pic/pic1s.png', (250, None)),
            ImageLink('./pic/pic1s.png', (None, 250)),
        ]

        true_result.sort(key=lambda link: str(link))

        with open(self._article_path) as article_file:
            md_transformer = ArticleTransformer(article_file, None)
            result = list(md_transformer._read_article())

            for i in result:
                print(i, i.new_size)

            assert len(result) == len(true_result)

            result.sort(key=lambda link: str(link))

            for i in range(len(true_result)):
                assert true_result[i] == result[i]
