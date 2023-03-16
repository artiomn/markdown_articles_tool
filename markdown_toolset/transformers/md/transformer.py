"""
Images extractor from markdown document.
"""
import logging
import re

from typing import List, TextIO, Dict
import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

__all__ = ['ArticleTransformer']

from markdown_toolset.image_downloader import ImageLink


class ImgExtractor(Treeprocessor):
    def run(self, root):
        """
        Find all images and append to markdown.images.
        """

        self.md.images = [image.get('src') for image in root.findall('.//img')]


class ImgExtExtension(Extension):
    def extendMarkdown(self, md, **argv):  # noqa: signature redefinition by design.
        del argv
        img_ext = ImgExtractor(md)
        md.treeprocessors.register(img_ext, 'imgext', 20)


class ArticleTransformer:
    """
    Markdown article transformation class.
    """

    format = 'md'
    __md_image_link_regex = re.compile(r'(?P<link>^\S+)(?: +=(?P<w>\d+)?x(?P<h>\d+)?)?$', re.IGNORECASE)

    def __init__(self, article_stream: TextIO, image_downloader):
        self._image_downloader = image_downloader
        self._article_stream = article_stream
        self._start_pos = self._article_stream.tell()
        self._md_conv = markdown.Markdown(extensions=[ImgExtExtension(), 'md_in_html'])
        self._md_conv.images = []  # type: ignore
        self._replacement_mapping: Dict[str, str] = {}

    def run(self):
        """
        Run article conversion.
        """

        self._replacement_mapping = self._image_downloader.download_images(self._read_article())
        res = self._fix_document_urls()

        return res

    def _read_article(self) -> List[ImageLink]:
        self._md_conv.convert(self._article_stream.read())
        logging.info('Images links count = %d', len(self._md_conv.images))  # type: ignore

        image_links = []

        for il in self._md_conv.images:  # type: ignore
            result = self.__md_image_link_regex.search(il)
            if result is None:
                logging.warning('Link "%s" is possibly incorrect!', il)
                image_links.append(ImageLink(il))
            else:
                groups = result.groupdict()

                def fix_n(n):
                    return None if n is None else int(n)

                w = fix_n(groups.get('w'))
                h = fix_n(groups.get('h'))

                image_links.append(ImageLink(groups['link']) if w == h == -1 else ImageLink(groups['link'], (w, h)))

        return image_links

    def _fix_document_urls(self) -> List[str]:
        logging.debug('Replacing images urls in the document...')
        replacement_mapping = self._replacement_mapping
        lines = []
        self._article_stream.seek(self._start_pos)
        for line in self._article_stream:
            for src, target in replacement_mapping.items():
                line = line.replace(src, str(target))
            lines.append(line)

        return lines
