#!/usr/bin/python3

"""
Simple script to download images and replace image links in markdown documents.
"""

import argparse
from io import StringIO
from itertools import permutations
from pathlib import Path
from string import Template

from mimetypes import types_map
from time import strftime
from typing import List

from pkg.transformers.md.transformer import ArticleTransformer as MarkdownArticleTransformer
from pkg.transformers.html.transformer import ArticleTransformer as HTMLArticleTransformer
from pkg.image_downloader import ImageDownloader
from pkg.www_tools import is_url, get_base_url, get_filename_from_url, download_from_url
from pkg.formatters.simple import SimpleFormatter
from pkg.formatters.html import HTMLFormatter

try:
    from pkg.formatters.pdf import PDFFormatter
except ModuleNotFoundError:
    PDFFormatter = None


__version__ = '0.0.7'

TRANSFORMERS = [MarkdownArticleTransformer, HTMLArticleTransformer]
FORMATTERS = [SimpleFormatter, HTMLFormatter, PDFFormatter]

del types_map['.jpe']


def transform_article(article_path: str, input_format_list: List[str], img_downloader: ImageDownloader) -> str:
    """
    Download images and fix URL's.
    """
    transformers = [tr for ifmt in input_format_list
                    for tr in TRANSFORMERS if tr is not None and tr.format == ifmt]

    with open(article_path, 'r', encoding='utf8') as article_file:
        result = StringIO(article_file.read())

    for transformer in transformers:
        lines = transformer(result, img_downloader).run()
        result = StringIO(''.join(lines))

    return result.read()


def get_formatter(output_format: str):
    formatter = [f for f in FORMATTERS if f is not None and f.format == output_format]
    assert len(formatter) == 1
    formatter = formatter[0]

    return formatter


def get_article_out_path(article_path: Path, output_path: Path, file_format: str, remove_source: bool) -> Path:
    article_file_name = article_path.stem
    article_out_path = output_path if output_path else article_path.parent / f'{article_file_name}.{file_format}'

    if article_path == article_out_path and not remove_source:
        article_out_path = article_path.parent / f'{article_file_name}_{strftime("%Y%m%d_%H%M%S")}.{file_format}'

    return article_out_path


def format_article(article_out_path: str, article_text: str, formatter) -> None:
    """
    Save article in the selected format.
    """

    print(f'Writing file into "{article_out_path}"...')

    with open(article_out_path, 'wb') as outfile:
        outfile.write(formatter.write(article_text))


def main(arguments):
    """
    Entrypoint.
    """

    print(f'Markdown tool version {__version__} started...')

    article_link = arguments.article_file_path_or_url
    if is_url(article_link):
        timeout = arguments.downloading_timeout
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

    skip_list = arguments.skip_list
    skip_all = arguments.skip_all_incorrect

    print(f'File "{article_path}" will be processed...')

    if isinstance(skip_list, str):
        if skip_list.startswith('@'):
            skip_list = skip_list[1:]
            print(f'Reading skip list from a file "{skip_list}"...')
            with open(Path(skip_list).expanduser(), 'r') as fsl:
                skip_list = [s.strip() for s in fsl.readlines()]
        else:
            skip_list = [s.strip() for s in skip_list.split(',')]

    article_formatter = get_formatter(arguments.output_format)

    article_out_path = get_article_out_path(
        article_path=article_path,
        output_path=Path(arguments.output_path) if arguments.output_path is not None else None,
        file_format=article_formatter.format,
        remove_source=arguments.remove_source
    )

    variables = {
        'article_name': article_out_path.stem,
        'time': strftime('%H%M%S'),
        'date': strftime('%Y%m%d'),
        'dt': strftime('%Y%m%d_%H%M%S'),
        'base_url': article_base_url.lstrip('https://').lstrip('http://')
    }

    print(f'Image public path: {Template(arguments.images_public_path).safe_substitute(**variables)}')

    img_downloader = ImageDownloader(
        article_path=article_path,
        article_base_url=article_base_url,
        skip_list=skip_list,
        skip_all_errors=skip_all,
        img_dir_name=Path(Template(arguments.images_dirname).safe_substitute(**variables)),
        img_public_path=Path(Template(arguments.images_public_path).safe_substitute(**variables)),
        downloading_timeout=arguments.downloading_timeout,
        deduplication=arguments.dedup_with_hash
    )

    result = transform_article(article_path, arguments.input_format.split('+'), img_downloader)

    format_article(article_out_path, result, article_formatter)

    if arguments.remove_source and article_path != article_out_path:
        print(f'Removing source file "{article_path}"...')
        Path(article_path).unlink()

    print('Processing finished successfully...')


if __name__ == '__main__':
    in_format_list = [f.format for f in TRANSFORMERS if f is not None]
    in_format_list = [*in_format_list, *('+'.join(i) for i in permutations(in_format_list))]
    out_format_list = [f.format for f in FORMATTERS if f is not None]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('article_file_path_or_url', type=str,
                        help='path to the article file in the Markdown format')
    parser.add_argument('-D', '--dedup-with-hash', default=False, action='store_true',
                        help='Deduplicate images, using content hash')
    parser.add_argument('-d', '--images-dirname', default='images',
                        help='Folder in which to download images '
                             '(possible variables: $article_name, $time, $date, $dt, $base_url)')
    parser.add_argument('-a', '--skip-all-incorrect', default=False, action='store_true',
                        help='skip all incorrect images')
    parser.add_argument('-s', '--skip-list', default=None,
                        help='skip URL\'s from the comma-separated list (or file with a leading \'@\')')
    parser.add_argument('-i', '--input-format', default='md', choices=in_format_list,
                        help='input format')
    parser.add_argument('-o', '--output-format', default=out_format_list[0], choices=out_format_list,
                        help='output format')
    parser.add_argument('-p', '--images-public-path', default='',
                        help='Public path to the folder of downloaded images '
                             '(possible variables: $article_name, $time, $date, $dt, $base_url)')
    parser.add_argument('-R', '--remove-source', default=False, action='store_true',
                        help='Remove or replace source file')
    parser.add_argument('-t', '--downloading-timeout', type=float, default=-1,
                        help='how many seconds to wait before downloading will be failed')
    parser.add_argument('-O', '--output-path', type=str, help='article output file name')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}', help='return version number')

    args = parser.parse_args()

    main(args)
