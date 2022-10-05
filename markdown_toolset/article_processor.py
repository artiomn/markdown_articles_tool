import logging
from enum import Enum
from pathlib import Path
from string import Template
from time import strftime
from typing import Union, List

from .deduplicators.content_hash_dedup import ContentHashDeduplicator
from .deduplicators.name_hash_dedup import NameHashDeduplicator
from .out_path_maker import OutPathMaker
from .www_tools import is_url, download_from_url, get_filename_from_url, get_base_url, remove_protocol_prefix
from .image_downloader import ImageDownloader
from .formatters import FORMATTERS, get_formatter, format_article
from .transformers import TRANSFORMERS, transform_article


class DeduplicationVariant(Enum):
    DISABLED = 0,
    NAMES_HASHING = 1,
    CONTENT_HASH = 2


class ArticleProcessor:
    def __init__(self, skip_list: Union[str, List[str]],
                 article_file_path_or_url: str, downloading_timeout: int,
                 output_format: str, output_path: Union[Path, str],
                 remove_source: bool, images_public_path: Union[Path, str],
                 input_formats: List[str], skip_all_incorrect: bool,
                 deduplication_type: DeduplicationVariant,
                 images_dirname: Union[Path, str]):
        self._skip_list = skip_list
        self._article_file_path_or_url = article_file_path_or_url
        self._downloading_timeout = downloading_timeout
        self._output_format = output_format
        self._output_path = output_path
        self._remove_source = remove_source
        self._images_public_path = images_public_path
        self._input_formats = input_formats
        self._skip_all_incorrect = skip_all_incorrect
        self._deduplication_type = deduplication_type
        self._images_dirname = images_dirname

    def process(self):
        skip_list = self._process_skip_list()
        article_path, article_base_url = self._get_article()

        logging.info('File "%s" will be processed...', article_path)

        article_formatter = get_formatter(self._output_format, FORMATTERS)

        article_out_path = self._get_article_out_path(
            article_path=article_path,
            output_path=Path(self._output_path) if self._output_path is not None else None,
            file_format=article_formatter.format
        )

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

        deduplicator = None

        if DeduplicationVariant.CONTENT_HASH == self._deduplication_type:
            deduplicator = ContentHashDeduplicator(image_dir_name, image_public_path)
        elif DeduplicationVariant.NAMES_HASHING == self._deduplication_type:
            deduplicator = NameHashDeduplicator()
        elif DeduplicationVariant.DISABLED == self._deduplication_type:
            pass

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
            downloading_timeout=self._downloading_timeout,
            deduplicator=deduplicator
        )

        result = transform_article(article_path, self._input_formats, TRANSFORMERS, img_downloader)
        format_article(article_out_path, result, article_formatter)

        if self._remove_source and article_path != article_out_path:
            logging.info('Removing source file "%s"...', article_path)
            Path(article_path).unlink()

    def _process_skip_list(self):
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

    def _get_article(self):
        article_link = self._article_file_path_or_url

        if is_url(article_link):
            timeout = self._downloading_timeout
            if timeout < 0:
                timeout = None
            response = download_from_url(article_link, timeout=timeout)
            article_path = Path(get_filename_from_url(response))
            article_base_url = get_base_url(response)

            with open(article_path, 'wb') as article_file:
                article_file.write(response.content)
                article_file.close()
        else:
            article_path = Path(article_link).expanduser()
            article_base_url = str('/'.join(article_path.parts[:-1]))

        return article_path, article_base_url

    def _need_to_change_name(self, article_path, article_out_path) -> bool:
        return (article_path == article_out_path or article_out_path.exists()) and not self._remove_source

    @staticmethod
    def _make_new_filename(output_path, article_file_name, file_format):
        return output_path / f'{article_file_name}_{strftime("%Y%m%d_%H%M%S")}.{file_format}'

    def _get_article_out_path(self, article_path: Path, output_path: Path, file_format: str) -> Path:
        article_file_name = article_path.stem

        if output_path.is_dir():
            article_out_path = output_path / f'{article_file_name}.{file_format}'
            if self._need_to_change_name(article_path, article_out_path):
                article_out_path = self._make_new_filename(output_path, article_file_name, file_format)
        elif output_path.is_file() or not output_path.exists():
            article_out_path = output_path
            if self._need_to_change_name(article_path, article_out_path):
                article_out_path = self._make_new_filename(output_path.parent, article_file_name, file_format)
        else:
            raise FileNotFoundError(f'Output path "{output_path}" is incorrect!')

        return article_out_path
