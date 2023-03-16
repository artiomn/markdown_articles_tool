"""
Images extractor from HTML document.
"""
import logging
from abc import ABC
from html.parser import HTMLParser
from typing import List, TextIO, Dict

__all__ = ['ArticleTransformer']


class HTMLImageURLGrabber(HTMLParser, ABC):
    def __init__(self):
        super().__init__()
        self._image_urls: List[str] = []

    def handle_starttag(self, tag, attrs):
        if 'img' == tag:
            logging.info('Image was found...')
            for a in attrs:
                if 'src' == a[0] and a[1] is not None:
                    img_url = a[1]
                    logging.debug('Image URL: %s...', img_url)
                    self._image_urls.append(img_url)
                    break

    @property
    def image_urls(self) -> List[str]:
        return self._image_urls


class ArticleTransformer:
    """
    HTML article transformation class.
    """

    format = 'html'

    def __init__(self, article_stream: TextIO, image_downloader):
        self._image_downloader = image_downloader
        self._article_stream = article_stream
        self._start_pos = self._article_stream.tell()
        self._html_images = HTMLImageURLGrabber()
        self._image_downloader = image_downloader
        self._replacement_mapping: Dict[str, str] = {}

    def _read_article(self) -> List[str]:
        self._html_images.feed(self._article_stream.read())
        images = self._html_images.image_urls
        logging.info('Images links count = %d', len(images))

        return images

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

    def run(self):
        """
        Run article conversion.
        """

        self._replacement_mapping = self._image_downloader.download_images(self._read_article())
        return self._fix_document_urls()
