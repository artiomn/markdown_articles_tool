#!/usr/bin/python3

"""
Simple script to download images and replace image links in markdown documents.
"""

import argparse
from itertools import permutations

from mimetypes import types_map

from markdown_toolset.article_processor import ArticleProcessor
from markdown_toolset.image_downloader import DeduplicationVariant

from markdown_toolset.formatters import FORMATTERS
from markdown_toolset.transformers import TRANSFORMERS

from markdown_toolset.__version__ import __version__


del types_map['.jpe']


def main(arguments):
    """
    Entrypoint.
    """

    print(f'Markdown tool version {__version__} started...')

    processor = ArticleProcessor(skip_list=arguments.skip_list,
                                 article_file_path_or_url=arguments.article_file_path_or_url,
                                 downloading_timeout=arguments.downloading_timeout,
                                 output_format=arguments.output_format,
                                 output_path=arguments.output_path,
                                 remove_source=arguments.remove_source,
                                 images_public_path=arguments.images_public_path,
                                 input_formats=arguments.input_format.split('+'),
                                 skip_all_incorrect=arguments.skip_all_incorrect,
                                 deduplication_type=getattr(DeduplicationVariant, arguments.deduplication_type.upper()),
                                 process_local_images=arguments.process_local_images,
                                 images_dirname=arguments.images_dirname)

    processor.process()

    print('Processing finished successfully...')


if __name__ == '__main__':
    in_format_list = [f.format for f in TRANSFORMERS if f is not None]
    in_format_list = [*in_format_list, *('+'.join(i) for i in permutations(in_format_list))]
    out_format_list = [f.format for f in FORMATTERS if f is not None]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('article_file_path_or_url', type=str,
                        help='path to the article file in the Markdown format')
    parser.add_argument('-D', '--deduplication-type', choices=[i.name.lower() for i in DeduplicationVariant],
                        default='disabled', help='Deduplicate images, using content hash or SHA1(image_name)')
    parser.add_argument('-d', '--images-dirname', default='images',
                        help='Folder in which to download images '
                             '(possible variables: $article_name, $time, $date, $dt, $base_url)')
    parser.add_argument('-a', '--skip-all-incorrect', default=False, action='store_true',
                        help='skip all incorrect images')
    parser.add_argument('-s', '--skip-list', default=None,
                        help='skip URL\'s from the comma-separated list (or file with a leading \'@\')')
    parser.add_argument('-i', '--input-format', default='md', choices=in_format_list,
                        help='input format')
    parser.add_argument('-l', '--process-local-images', default=False, action='store_true',
                        help='Process local images')
    parser.add_argument('-n', '--replace-image-names', default=False, action='store_true',
                        help='Replace image names, using content hash')
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
