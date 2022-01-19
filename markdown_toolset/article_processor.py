from pathlib import Path
from string import Template
from time import strftime
from typing import Union, List

from .www_tools import is_url, download_from_url, get_filename_from_url, get_base_url
from .image_downloader import ImageDownloader, DeduplicationVariant
from .formatters import FORMATTERS, get_formatter, format_article
from .transformers import TRANSFORMERS, transform_article


class ArticleProcessor:
    def __init__(self, skip_list: Union[str, List[str]],
                 article_file_path_or_url: str, downloading_timeout: int,
                 output_format: str, output_path: Union[Path, str],
                 remove_source: bool, images_public_path: Union[Path, str],
                 input_formats: List[str], skip_all_incorrect: bool,
                 deduplication_type: DeduplicationVariant,
                 process_local_images: bool, images_dirname: Union[Path, str]):
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
        self._process_local_images = process_local_images
        self._images_dirname = images_dirname

    def process(self):
        skip_list = self._process_skip_list()
        article_path, article_base_url = self._get_article()

        print(f'File "{article_path}" will be processed...')

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
            'base_url': article_base_url.lstrip('https://').lstrip('http://')
        }

        print(f'Image public path: {Template(self._images_public_path).safe_substitute(**variables)}')

        img_downloader = ImageDownloader(
            article_path=article_path,
            article_base_url=article_base_url,
            skip_list=skip_list,
            skip_all_errors=self._skip_all_incorrect,
            img_dir_name=Path(Template(self._images_dirname).safe_substitute(**variables)),
            img_public_path=Path(Template(self._images_public_path).safe_substitute(**variables)),
            downloading_timeout=self._downloading_timeout,
            deduplication_variant=self._deduplication_type,
            process_local_images=self._process_local_images
        )

        result = transform_article(article_path, self._input_formats, TRANSFORMERS, img_downloader)
        format_article(article_out_path, result, article_formatter)

        if self._remove_source and article_path != article_out_path:
            print(f'Removing source file "{article_path}"...')
            Path(article_path).unlink()

    def _process_skip_list(self):
        skip_list = self._skip_list

        if isinstance(skip_list, str):
            if skip_list.startswith('@'):
                skip_list = skip_list[1:]
                print(f'Reading skip list from a file "{skip_list}"...')
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
            article_base_url = ''

        return article_path, article_base_url

    def _get_article_out_path(self, article_path: Path, output_path: Path, file_format: str) -> Path:
        article_file_name = article_path.stem
        article_out_path = output_path if output_path else article_path.parent / f'{article_file_name}.{file_format}'

        if article_path == article_out_path and not self._remove_source:
            article_out_path = article_path.parent / f'{article_file_name}_{strftime("%Y%m%d_%H%M%S")}.{file_format}'

        return article_out_path
