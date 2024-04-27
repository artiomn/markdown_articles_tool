"""
Some functions useful for the working with URLs and network.
"""
import logging

from typing import Optional
from mimetypes import guess_extension
import os
import re
from urllib.parse import urlparse, urlunparse
import requests

from .string_tools import slugify


NECESSARY_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0'}

__protocol_prefix_replace_regex = re.compile(r'^\s*(:?(?:(?:http|ftp)+s?|file)://)', re.IGNORECASE)
__protocol_prefix_slashes_replace_regex = re.compile(r'^\s*:?//', re.IGNORECASE)


def is_url(url: str, allowed_url_prefixes=('http', 'ftp', 'https', 'ftps')) -> bool:
    """
    Check url for prefix match.
    """

    l_url = url.lower()
    for prefix in set(allowed_url_prefixes):
        if l_url.startswith(prefix.lower()):
            return True

    return False


def remove_protocol_prefix(url: str) -> str:
    """
    Remove prefixes like http, ftp, HTTPS, and other from the URL.
    """

    return __protocol_prefix_slashes_replace_regex.sub('', str(urlunparse(urlparse(url)._replace(scheme=''))))


def download_from_url(url: str, timeout: float = None):
    """
    Download file from the URL.
    :param url: URL to download.
    :param timeout: timeout before fail.
    :raise OSError: when HTTP status is not 200.
    """

    # todo: Add urlparse()?
    url = url.split()[0]

    try:
        response = requests.get(url, allow_redirects=True, timeout=timeout, headers=NECESSARY_HEADERS)
    except requests.exceptions.SSLError:
        logging.warning('Incorrect SSL certificate, trying to download without verifying...')
        response = requests.get(
            url, allow_redirects=True, verify=False, timeout=timeout, headers=NECESSARY_HEADERS  # nosec
        )

    if not response.ok:
        # HTTP status code >= 400.
        raise OSError(str(response))

    return response


def get_filename_from_url(req: requests.Response) -> Optional[str]:
    """
    Get filename from url and, if not found, try to get from content-disposition.
    """

    logging.debug('URL from request: %s', req.url)

    if req and req.url.find('/'):
        result = urlparse(req.url).path
        logging.debug('Filename from URL: %s', result)
    else:
        cd = req.headers.get('content-disposition')

        if cd is None:
            return None

        file_name = re.findall('filename=(.+)', cd)

        logging.debug('Filename from "filename=" part: %s', file_name)

        if len(file_name) == 0:
            return None

        result = file_name[0]

    f_name, f_ext = os.path.splitext(result)

    if f_name == '':
        return None

    result = (
        f'{slugify(f_name)}{guess_extension(req.headers["content-type"].partition(";")[0].strip())}'
        if not f_ext
        else f'{slugify(f_name)}.{slugify(f_ext)}'
    )

    return result


def get_base_url(req: requests.Response) -> Optional[str]:
    """
    Get base URL from url.
    """

    if req and req.url.find('/'):
        return req.url.rsplit('/', 1)[0]

    return None
