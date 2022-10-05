#!/usr/bin/python3

"""
Tool for the downloading Markdown articles, replace image links and save the article in the selected format.
"""

import argparse
from argparse import RawDescriptionHelpFormatter, SUPPRESS, ZERO_OR_MORE, OPTIONAL

import logging

from mimetypes import types_map
from pathlib import Path

from markdown_toolset.article_processor import ArticleProcessor, DeduplicationVariant,\
    IN_FORMATS_LIST, OUT_FORMATS_LIST

from markdown_toolset.__version__ import __version__


del types_map['.jpe']


class CustomArgumentDefaultsHelpFormatter(RawDescriptionHelpFormatter):
    """Help message formatter which adds default values to argument help.

    Only the name of this class is considered a public API. All the methods
    provided by the class are considered an implementation detail.
    """

    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help:
            if action.default is not SUPPRESS:
                defaulting_nargs = [OPTIONAL, ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += ' (default: %(default)s)'
        return help


def main(arguments):
    """
    Entrypoint.
    """

    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d.%m.%Y %H:%M:%S',
                        level='DEBUG' if arguments.verbose else 'INFO')

    print(f'Markdown tool version {__version__} started...')

    if arguments.process_local_images:
        print('--process_local_images is deprecated and will be disabled in the next version!')

    processor = ArticleProcessor(article_file_path_or_url=arguments.article_file_path_or_url,
                                 skip_list=arguments.skip_list,
                                 downloading_timeout=arguments.downloading_timeout,
                                 output_format=arguments.output_format,
                                 output_path=getattr(arguments, 'output_path', Path.cwd()),
                                 remove_source=arguments.remove_source,
                                 images_public_path=getattr(arguments, 'images_public_path', ''),
                                 input_formats=arguments.input_format.split('+'),
                                 skip_all_incorrect=arguments.skip_all_incorrect,
                                 download_incorrect_mime=arguments.download_incorrect_mime,
                                 deduplication_type=getattr(DeduplicationVariant, arguments.deduplication_type.upper()),
                                 images_dirname=arguments.images_dirname)

    processor.process()

    print('Processing finished successfully...')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='markdown_tool',
        epilog='Use tool at your own risk!',
        description=f'{__doc__}Version: {__version__}',
        formatter_class=CustomArgumentDefaultsHelpFormatter
    )
    parser.add_argument('article_file_path_or_url', type=str,
                        help='path to the article file in the Markdown format')
    parser.add_argument('-D', '--deduplication-type', choices=[i.name.lower() for i in DeduplicationVariant],
                        default='disabled', help='Deduplicate images, using content hash or SHA1(image_name)')
    parser.add_argument('-d', '--images-dirname', default='images',
                        help='Folder in which to download images '
                             '(possible variables: $article_name, $time, $date, $dt, $base_url)')
    parser.add_argument('-a', '--skip-all-incorrect', default=False, action='store_true',
                        help='skip all incorrect images')
    parser.add_argument('-E', '--download-incorrect-mime', default=False, action='store_true',
                        help='download "images" with unrecognized MIME type')
    parser.add_argument('-s', '--skip-list', default=None,
                        help='skip URL\'s from the comma-separated list (or file with a leading \'@\')')
    parser.add_argument('-i', '--input-format', default='md', choices=IN_FORMATS_LIST,
                        help='input format')
    parser.add_argument('-l', '--process-local-images', default=False, action='store_true',
                        help='[DEPRECATED] Process local images')
    parser.add_argument('-n', '--replace-image-names', default=False, action='store_true',
                        help='Replace image names, using content hash')
    parser.add_argument('-o', '--output-format', default=OUT_FORMATS_LIST[0], choices=OUT_FORMATS_LIST,
                        help='output format')
    parser.add_argument('-p', '--images-public-path', default=SUPPRESS,
                        help='Public path to the folder of downloaded images '
                             '(possible variables: $article_name, $time, $date, $dt, $base_url)')
    # TODO: Replace this with variables.
    parser.add_argument('-P', '--prepend-images-with-path', default=False, action='store_true',
                        help='Save relative images paths')
    parser.add_argument('-R', '--remove-source', default=False, action='store_true',
                        help='Remove or replace source file')
    parser.add_argument('-t', '--downloading-timeout', type=float, default=-1,
                        help='how many seconds to wait before downloading will be failed')
    parser.add_argument('-O', '--output-path', type=str, help='article output file name or path', default=SUPPRESS)
    parser.add_argument('--verbose', '-v', default=False, action='store_true',
                        help='More verbose logging')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}', help='return version number')

    args = parser.parse_args()

    main(args)
