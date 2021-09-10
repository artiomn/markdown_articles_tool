"""
Images extractor from markdown document.
"""

import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
from typing import List, TextIO, Set

__all__ = ['ArticleTransformer']


class ImgExtractor(Treeprocessor):
    def run(self, doc):
        """
        Find all images and append to markdown.images.
        """

        self.md.images = []
        for image in doc.findall('.//img'):
            self.md.images.append(image.get('src'))


class ImgExtExtension(Extension):
    def extendMarkdown(self, md, md_globals):  # noqa: signature redefinition by design.
        img_ext = ImgExtractor(md)
        md.treeprocessors.register(img_ext, 'imgext', 20)


class ArticleTransformer:
    """
    Markdown article transformation class.
    """

    format = 'md'

    def __init__(self, article_stream: TextIO, image_downloader):
        self._image_downloader = image_downloader
        self._article_stream = article_stream
        self._start_pos = self._article_stream.tell()
        self._md_conv = markdown.Markdown(extensions=[ImgExtExtension(), 'md_in_html'])
        self._md_conv.images = []
        self._replacement_mapping = {}

    def _read_article(self) -> Set[str]:
        self._md_conv.convert(self._article_stream.read())
        print(f'Images links count = {len(self._md_conv.images)}')
        images = set(self._md_conv.images)
        print(f'Unique images links count = {len(images)}')

        return images

    def _fix_document_urls(self) -> List[str]:
        print('Replacing images urls in the document...')
        replacement_mapping = self._replacement_mapping
        lines = []
        self._article_stream.seek(self._start_pos)
        for line in self._article_stream:
            for src, target in replacement_mapping.items():
                line = line.replace(src, str(target))
            lines.append(line)

        return lines

    def run(self):
        """
        Run article conversion.
        """

        self._replacement_mapping = self._image_downloader.download_images(self._read_article())
        return self._fix_document_urls()
