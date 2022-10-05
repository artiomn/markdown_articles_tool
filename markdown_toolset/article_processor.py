import logging
from itertools import permutations
from pathlib import Path
from string import Template
from time import strftime
from typing import Union, List

from .article_downloader import ArticleDownloader
from .deduplicators import DeduplicationVariant, select_deduplicator
from .out_path_maker import OutPathMaker
from .www_tools import remove_protocol_prefix
from .image_downloader import ImageDownloader
from .formatters import FORMATTERS, get_formatter, format_article
from .transformers import TRANSFORMERS, transform_article

IN_FORMATS_LIST = [f.format for f in TRANSFORMERS if f is not None]
IN_FORMATS_LIST = [*IN_FORMATS_LIST, *('+'.join(i) for i in permutations(IN_FORMATS_LIST))]
OUT_FORMATS_LIST = [f.format for f in FORMATTERS if f is not None]


class ArticleProcessor:
    def __init__(self, article_file_path_or_url: str,
                 skip_list: Union[str, List[str]] = '', downloading_timeout: int = -1,
                 output_format: str = OUT_FORMATS_LIST[0], output_path: Union[Path, str] = Path.cwd(),
                 remove_source: bool = False, images_public_path: Union[Path, str] = '',
                 input_formats: List[str] = tuple(IN_FORMATS_LIST), skip_all_incorrect: bool = False,
                 download_incorrect_mime: bool = False,
                 deduplication_type: DeduplicationVariant = DeduplicationVariant.DISABLED,
                 images_dirname: Union[Path, str] = 'images'):
        self._article_formatter = get_formatter(output_format, FORMATTERS)
        self._article_downloader = ArticleDownloader(article_file_path_or_url, output_path,
                                                     self._article_formatter, downloading_timeout, remove_source)
        self._skip_list = skip_list
        self._downloading_timeout = downloading_timeout
        self._output_format = output_format
        self._remove_source = remove_source
        self._images_public_path = images_public_path
        self._input_formats = input_formats
        self._skip_all_incorrect = skip_all_incorrect
        self._download_incorrect_mime = download_incorrect_mime
        self._deduplication_type = deduplication_type
        self._images_dirname = images_dirname

    def process(self):
        skip_list = self._process_skip_list_file()
        article_path, article_base_url, article_out_path = self._article_downloader.get_article()

        logging.info('File "%s" will be processed...', article_path)

        variables = {
            'article_name': article_out_path.stem,
            'time': strftime('%H%M%S'),
            'date': strftime('%Y%m%d'),
            'dt': strftime('%Y%m%d_%H%M%S'),
            'base_url': remove_protocol_prefix(article_base_url)
        }

        image_public_path = Template(self._images_public_path).safe_substitute(**variables)
        logging.info('Image public path: %s', image_public_path)

        image_dir_name = Path(Template(self._images_dirname).safe_substitute(**variables))
        image_public_path = None if not image_public_path else Path(image_public_path)

        if self._deduplication_type == DeduplicationVariant.CONTENT_HASH:
            deduplicator = select_deduplicator(self._deduplication_type, image_dir_name, image_public_path)
        else:
            deduplicator = select_deduplicator(self._deduplication_type)

        out_path_maker = OutPathMaker(
            article_file_path=article_path,
            article_base_url=article_base_url,
            img_dir_name=image_dir_name,
            img_public_path=image_public_path
        )

        img_downloader = ImageDownloader(
            out_path_maker=out_path_maker,
            skip_list=skip_list,
            skip_all_errors=self._skip_all_incorrect,
            download_incorrect_mime_types=self._download_incorrect_mime,
            downloading_timeout=self._downloading_timeout,
            deduplicator=deduplicator
        )

        result = transform_article(article_path, self._input_formats, TRANSFORMERS, img_downloader)
        format_article(article_out_path, result, self._article_formatter)

    def _process_skip_list_file(self):
        skip_list = self._skip_list

        if isinstance(skip_list, str):
            if skip_list.startswith('@'):
                skip_list = skip_list[1:]
                logging.info('Reading skip list from a file "%s"...', skip_list)
                with open(Path(skip_list).expanduser(), 'r') as fsl:
                    skip_list = [s.strip() for s in fsl.readlines()]
            else:
                skip_list = [s.strip() for s in skip_list.split(',')]

        return skip_list
