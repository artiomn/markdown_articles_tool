#!/usr/bin/python3

"""
Simple script to download images and replace image links in markdown documents.
"""

import argparse
from mimetypes import guess_extension, types_map
import os
import re
import requests
import sys
import unicodedata

from typing import Optional, List

from pkg.transformers.md.transformer import ArticleTransformer


del types_map['.jpe']


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """

    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub('[^\w\s-]', '', value.decode()).strip().lower()
    value = re.sub('[-\s]+', '-', value)

    return value


def get_filename_from_url(req: requests.Response) -> Optional[str]:
    """
    Get filename from url and, if not found, try to get from content-disposition.
    """

    result = None
    if req.url.find('/'):
        result = req.url.rsplit('/', 1)[1]
    else:
        cd = req.headers.get('content-disposition')

        if cd is None:
            return None

        fname = re.findall('filename=(.+)', cd)

        if len(fname) == 0:
            return None

        result = fname[0]

    f_name, f_ext = os.path.splitext(result)

    if not f_ext:
        result = f'{slugify(f_name)}{guess_extension(req.headers["content-type"].partition(";")[0].strip())}'
    else:
        result = f'{slugify(f_name)}.{slugify(f_ext)}'

    return result


class ImageDownloader:
    def __init__(self, article_path: str, skip_list: Optional[List[str]] = None, skip_all: bool = False, img_dirname: str = 'images', img_publicpath: str = ''):
        self.img_dirname = img_dirname
        self.img_publicpath = img_publicpath
        self._article_file_path = article_path
        self._skip_list = sorted(skip_list) if skip_list is not None else []
        self._imgs_dir = os.path.join(os.path.dirname(self._article_file_path), self.img_dirname)
        self._skip_all = skip_all

    def download_images(self, images: List[str]) -> dict:
        path_join = os.path.join
        img_dirname = self.img_dirname
        img_publicpath = self.img_publicpath
        imgs_dir = self._imgs_dir
        replacement_mapping = {}
        skip_list = self._skip_list
        img_count = len(images)

        try:
            os.makedirs(self._imgs_dir)
        except FileExistsError:
            # Existing directory is not error.
            pass

        for img_num, img_url in enumerate(images):
            assert img_url not in replacement_mapping.keys(), f'BUG: already downloaded image "{img_url}"...'

            if img_url in skip_list:
                print(f'Image {img_num + 1} ["{img_url}"] was skipped, because it\'s in the skip list...')
                continue

            if not img_url.startswith('http'):
                print(f'Image {img_num + 1} ["{img_url}"] was skipped, because it has incorrect URL...')
                continue

            print(f'Downloading image {img_num + 1} of {img_count} from "{img_url}"...')

            try:
                try:
                    img_response = requests.get(img_url, allow_redirects=True)
                except requests.exceptions.SSLError:
                    print('Incorrect SSL certificate, trying to download without verifying...')
                    img_response = requests.get(img_url, allow_redirects=True, verify=False)

                if img_response.status_code != 200:
                    raise OSError(str(img_response))
            except Exception as e:
                if self._skip_all:
                    print(f'Warning: can\'t download image {img_num + 1}, error: [{str(e)}], '
                          'but processing will be continued, because `skip_all` flag is set')
                    continue
                raise

            img_filename = get_filename_from_url(img_response)
            img_path = path_join(imgs_dir, img_filename)
            print(f'Image will be written to the file "{img_path}"...')
            replacement_mapping.setdefault(img_url, path_join(img_publicpath or img_dirname, img_filename))

            with open(img_path, 'wb') as img_file:
                img_file.write(img_response.content)
                img_file.close()

        return replacement_mapping


def main(args):
    """
    Entrypoint.
    """

    article_file = os.path.expanduser(args.article_file_path)
    skip_list = args.skip_list
    skip_all = args.skip_all_incorrect

    print('Processing started...')

    if isinstance(skip_list, str):
        if skip_list.startswith('@'):
            skip_list = skip_list[1:]
            print(f'Reading skip list from a file "{skip_list}"...')
            with open(os.path.expanduser(skip_list), 'r') as fsl:
                skip_list = [s.strip() for s in fsl.readlines()]
        else:
            skip_list = [s.strip() for s in skip_list.split(',')]

    ArticleTransformer(article_file,
                       ImageDownloader(
                           article_file,
                           skip_list,
                           skip_all,
                           args.images_dirname,
                           args.images_publicpath
                           )
                       ).run()

    print('Processing finished successfully...')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('article_file_path', type=str,
                        help='an integer for the accumulator')
    parser.add_argument('-s', '--skip-list', default=None,
                        help='skip URL\'s from the comma-separated list (or file with a leading \'@\')')
    parser.add_argument('-d', '--images-dirname', default='images',
                        help='Folder in which to download images')
    parser.add_argument('-p', '--images-publicpath', default='',
                        help='Public path to the folder of downloaded images')
    parser.add_argument('-a', '--skip-all-incorrect', default=False, action='store_true',
                        help='skip all incorrect images')

    args = parser.parse_args()

    main(args)

