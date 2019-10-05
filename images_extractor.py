#!/usr/bin/python3

"""
Simple script to download images and replace image links in markdown documents.
"""

import argparse
import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagPattern
from mimetypes import guess_extension, types_map
import os
import re
import requests
import sys
import unicodedata

from typing import Optional, List, NoReturn


del types_map['.jpe']


class ImgExtractor(Treeprocessor):
    def run(self, doc):
        """
        Find all images and append to markdown.images.
        """

        self.md.images = []
        for image in doc.findall('.//img'):
            self.md.images.append(image.get('src'))


class ImgExtExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        img_ext = ImgExtractor(md)
        md.treeprocessors.register(img_ext, 'imgext', 20)


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


class ArticleTransformer:
    """
    Markdown article transformation class.
    """

    img_dirname = 'images'

    def __init__(self, article_path: str, skip_list: Optional[List[str]] = None):
        self._article_file_path = article_path
        self._skip_list = sorted(skip_list) if skip_list is not None else []
        self._imgs_dir = os.path.join(os.path.dirname(self._article_file_path), self.img_dirname)
        self._md_conv = markdown.Markdown(extensions=[ImgExtExtension()])
        self._replacement_mapping = {}

    def _read_article(self) -> List[str]:
        with open(self._article_file_path, 'r') as m_file:
            self._md_conv.convert(m_file.read())

        print(f'Images links count = {len(self._md_conv.images)}')
        images = set(self._md_conv.images)
        print(f'Unique images links count = {len(images)}')

        return images

    def _download_images(self, images: List[str]) -> NoReturn:
        path_join = os.path.join
        img_dirname = self.img_dirname
        imgs_dir = self._imgs_dir
        replacement_mapping = self._replacement_mapping
        skip_list = self._skip_list

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

            print(f'Downloading image {img_num + 1} from "{img_url}"...')
            try:
                img_response = requests.get(img_url, allow_redirects=True)
            except requests.exceptions.SSLError:
                print('Incorrect SSL certificate, trying to download without verifying...')
                img_response = requests.get(img_url, allow_redirects=True, verify=False)

            if img_response.status_code != 200:
                raise OSError(str(img_response))

            img_filename = get_filename_from_url(img_response)
            img_path = path_join(imgs_dir, img_filename)
            print(f'Image will be written to the file "{img_path}"...')
            replacement_mapping.setdefault(img_url, path_join(img_dirname, img_filename))

            with open(img_path, 'wb') as img_file:
                img_file.write(img_response.content)
                img_file.close()

    def _fix_document_urls(self) -> NoReturn:
        print('Replacing images urls in the document...')
        replacement_mapping = self._replacement_mapping
        lines = []
        with open(self._article_file_path, 'r') as infile:
            for line in infile:
                for src, target in replacement_mapping.items():
                    line = line.replace(src, target)
                lines.append(line)

        with open(self._article_file_path, 'w') as outfile:
            for line in lines:
                outfile.write(line)

    def run(self):
        """
        Run article conversion.
        """

        self._download_images(self._read_article())
        self._fix_document_urls()


def main(args):
    """
    Entrypoint.
    """

    article_file = os.path.expanduser(args.article_file_path)
    skip_list = args.skip_list

    print('Processing started...')

    if isinstance(skip_list, str):
        if skip_list.startswith('@'):
            skip_list = skip_list[1:]
            print(f'Reading skip list from a file "{skip_list}"...')
            with open(os.path.expanduser(skip_list), 'r') as fsl:
                skip_list = [s.strip() for s in fsl.readlines()]
        else:
            skip_list = [s.strip() for s in skip_list.split(',')]

    ArticleTransformer(article_file, skip_list).run()

    print('Processing finished successfully...')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('article_file_path', type=str,
                        help='an integer for the accumulator')
    parser.add_argument('-s', '--skip-list', default=None,
                        help='skip URL\'s from this list (or file with a leading \'@\')')

    args = parser.parse_args()

    main(args)

