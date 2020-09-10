#!/usr/bin/python3

"""
Simple script to download images and replace image links in markdown documents.
"""

import argparse
import os

from mimetypes import types_map

from pkg.transformers.md.transformer import ArticleTransformer
from pkg.image_downloader import ImageDownloader
from pkg.www_tools import is_url, get_filename_from_url, download_from_url


__version__ = '0.0.3'


del types_map['.jpe']


def main(arguments):
    """
    Entrypoint.
    """

    article_link = arguments.article_file_path_or_url
    if is_url(article_link):
        response = download_from_url(article_link, timeout=arguments.downloading_timeout)
        article_path = get_filename_from_url(response)

        with open(article_path, 'wb') as article_file:
            article_file.write(response.content)
            article_file.close()
    else:
        article_path = os.path.expanduser(article_link)

    skip_list = arguments.skip_list
    skip_all = arguments.skip_all_incorrect

    print('Processing started...')

    if isinstance(skip_list, str):
        if skip_list.startswith('@'):
            skip_list = skip_list[1:]
            print(f'Reading skip list from a file "{skip_list}"...')
            with open(os.path.expanduser(skip_list), 'r') as fsl:
                skip_list = [s.strip() for s in fsl.readlines()]
        else:
            skip_list = [s.strip() for s in skip_list.split(',')]

    ArticleTransformer(article_path,
                       ImageDownloader(
                           article_path=article_path,
                           skip_list=skip_list,
                           skip_all_errors=skip_all,
                           img_dir_name=arguments.images_dirname,
                           img_public_path=arguments.images_publicpath,
                           downloading_timeout=arguments.downloading_timeout,
                           deduplication=arguments.dedup_with_hash
                           )
                       ).run()

    print('Processing finished successfully...')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('article_file_path_or_url', type=str,
                        help='path to the article file in the Markdown format')
    parser.add_argument('-s', '--skip-list', default=None,
                        help='skip URL\'s from the comma-separated list (or file with a leading \'@\')')
    parser.add_argument('-d', '--images-dirname', default='images',
                        help='Folder in which to download images')
    parser.add_argument('-p', '--images-publicpath', default='',
                        help='Public path to the folder of downloaded images')
    parser.add_argument('-a', '--skip-all-incorrect', default=False, action='store_true',
                        help='skip all incorrect images')
    parser.add_argument('-t', '--downloading-timeout', type=float, default=-1,
                        help='how many seconds to wait before downloading will be failed')
    parser.add_argument('-D', '--dedup-with-hash', default=False, action='store_true',
                        help='Deduplicate images, using content hash')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}', help='return version number')

    args = parser.parse_args()

    main(args)
