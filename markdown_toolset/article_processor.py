import logging
from io import StringIO
from itertools import permutations
from pathlib import Path
from string import Template
from time import strftime
from typing import Union, List, Any, Tuple

from .article_downloader import ArticleDownloader
from .deduplicators import DeduplicationVariant, select_deduplicator
from .out_path_maker import OutPathMaker
from .www_tools import remove_protocol_prefix
from .image_downloader import ImageDownloader
from .formatters import FORMATTERS, get_formatter, format_article
from .transformers import TRANSFORMERS


IN_FORMATS_LIST = [f.format for f in TRANSFORMERS if f is not None]  # type: ignore
IN_FORMATS_LIST = [*IN_FORMATS_LIST, *('+'.join(i) for i in permutations(IN_FORMATS_LIST))]  # type: ignore
OUT_FORMATS_LIST = [f.format for f in FORMATTERS if f is not None]  # type: ignore


class ArticleProcessor:
    # TODO: Refactor this!
    # pylint: disable=too-many-instance-attributes, too-many-arguments
    def __init__(
        self,
        article_file_path_or_url: str,
        skip_list: Union[str, List[str]] = '',
        downloading_timeout: int = -1,
        output_format: str = OUT_FORMATS_LIST[0],
        output_path: Union[Path, str] = '',
        remove_source: bool = False,
        images_public_path: Union[Path, str] = '',
        input_formats: Tuple[str] = IN_FORMATS_LIST,  # type: ignore
        skip_all_incorrect: bool = False,
        download_incorrect_mime: bool = False,
        deduplication_type: DeduplicationVariant = DeduplicationVariant.DISABLED,
        images_dirname: Union[Path, str] = 'images',
        save_hierarchy: bool = False,
        replace_image_names: bool = False,
    ):
        self._article_formatter = get_formatter(output_format, FORMATTERS)
        self._article_downloader = ArticleDownloader(
            article_file_path_or_url,
            output_path or Path.cwd(),
            self._article_formatter,
            downloading_timeout,
            remove_source,
        )
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
        self._save_hierarchy = save_hierarchy
        self._img_downloader = None
        self._running = False
        self._replace_image_names = replace_image_names

    def process(self):
        try:
            self._running = True
            skip_list = self._process_skip_list_file()
            article_path, article_base_url, article_out_path = self._article_downloader.get_article()

            logging.info('File "%s" will be processed...', article_path)

            variables = {
                'article_name': article_out_path.stem,
                'time': strftime('%H%M%S'),
                'date': strftime('%Y%m%d'),
                'dt': strftime('%Y%m%d_%H%M%S'),
                'base_url': remove_protocol_prefix(article_base_url),
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
                article_file_path=article_out_path,
                article_base_url=article_base_url,
                img_dir_name=image_dir_name,
                img_public_path=image_public_path,
                save_hierarchy=self._save_hierarchy,
            )

            self._img_downloader = ImageDownloader(
                out_path_maker=out_path_maker,
                skip_list=skip_list,
                skip_all_errors=self._skip_all_incorrect,
                download_incorrect_mime_types=self._download_incorrect_mime,
                downloading_timeout=self._downloading_timeout,
                deduplicator=deduplicator,
                replace_image_names=self._replace_image_names,
            )

            result = self._transform_article(article_path, self._input_formats, TRANSFORMERS)

            # Format and save the article.
            format_article(article_out_path, result, self._article_formatter)
        finally:
            self._running = False

        return article_out_path

    @property
    def running(self) -> bool:
        return self._running

    def stop(self):
        logging.info('Article processing stopped.')
        self._running = False
        self._img_downloader.stop()

    def _transform_article(
        self, article_path: Path, input_format_list: Tuple[str], transformers_list: List[Any]
    ) -> str:
        """
        Download images and fix URL's.
        """
        transformers = [
            tr for ifmt in input_format_list for tr in transformers_list if tr is not None and tr.format == ifmt
        ]

        with open(article_path, encoding='utf8') as article_file:
            result = StringIO(article_file.read())

        for transformer in transformers:
            if not self._running:
                logging.debug('Article transforming was stopped forcibly.')
                break
            lines = transformer(result, self._img_downloader).run()
            result = StringIO(''.join(lines))

        return result.read()

    def _process_skip_list_file(self):
        skip_list = self._skip_list

        if isinstance(skip_list, str):
            if skip_list.startswith('@'):
                skip_list = skip_list[1:]
                logging.info('Reading skip list from a file "%s"...', skip_list)
                with open(Path(skip_list).expanduser(), encoding='utf8') as fsl:
                    skip_list = [s.strip() for s in fsl.readlines()]
            else:
                skip_list = [s.strip() for s in skip_list.split(',')]

        return skip_list
