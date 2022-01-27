[![Python application](https://github.com/artiomn/markdown_images_downloader/workflows/Python%20application/badge.svg)](https://github.com/artiomn/markdown_articles_tool/actions/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://opensource.org/licenses/MIT)
[![Stargazers](https://img.shields.io/github/stars/artiomn/markdown_images_downloader.svg)](https://github.com/artiomn/markdown_images_downloader/stargazers)
[![Forks](https://img.shields.io/github/forks/artiomn/markdown_images_downloader.svg)](https://github.com/artiomn/markdown_images_downloader/network/members)
[![Latest Release](https://img.shields.io/github/v/release/artiomn/markdown_images_downloader.svg)](https://github.com/artiomn/markdown_images_downloader/releases)


# Markdown articles tool 0.0.9

Free command line utility, written in Python, designed to help you manage online and downloaded Markdown documents (e.g., articles).
The Markdown Articles Tool is available for macOS, Windows, and Linux. 

Tool can be used:

- To download markdown text with images with images and:
  * Find all links to images, download images and fix links in the document.
  * Can skip broken links.
  * Deduplicate similar images by content hash or using hash as a name.
- Support images, linked with HTML `<img>` tag.
- Support local image files.
- Convert Markdown documents to:
  * HTML.
  * PDF.
  * Or save in the plain Markdown.

Also, if you want to use separate functions, you can just import the package.


## Changes

`-D` (deduplication) option was changed in the version 0.0.8. Now option is not boolean, it has several values: "disabled", "names_hashing", "content_hash".
  Long option name was changed too: now it's `deduplication-type`.


## Possibly bugs

Deduplication can replace not similar images. Probability of this is very low, but it's possible. Will be fixed in the next version.


## Installation

### From the repository

You need Python 3.8+.
Run:

```
git clone "https://github.com/artiomn/markdown_articles_tool"
pip3 install -r markdown_articles_tool/requirements.txt
```

### From the [PIP](https://pypi.org/project/markdown-tool/)

```
pip3 install markdown-tool
```


## Usage

Syntax:

```
usage: markdown_tool.py [-h] [-D {disabled,names_hashing,content_hash}] [-d IMAGES_DIRNAME] [-a] [-s SKIP_LIST] [-i {md,html,md+html,html+md}] [-l] [-n] [-o {md,html}] [-p IMAGES_PUBLIC_PATH] [-R] [-t DOWNLOADING_TIMEOUT] [-O OUTPUT_PATH] [--version] article_file_path_or_url

Script to download images and replace image links in markdown documents.

positional arguments:
  article_file_path_or_url
                        path to the article file in the Markdown format

optional arguments:
  -h, --help            show this help message and exit
  -D {disabled,names_hashing,content_hash}, --deduplication-type {disabled,names_hashing,content_hash}
                        Deduplicate images, using content hash or SHA1(image_name)
  -d IMAGES_DIRNAME, --images-dirname IMAGES_DIRNAME
                        Folder in which to download images (possible variables: $article_name, $time, $date, $dt, $base_url)
  -a, --skip-all-incorrect
                        skip all incorrect images
  -s SKIP_LIST, --skip-list SKIP_LIST
                        skip URL's from the comma-separated list (or file with a leading '@')
  -i {md,html,md+html,html+md}, --input-format {md,html,md+html,html+md}
                        input format
  -l, --process-local-images
                        Process local images
  -n, --replace-image-names
                        Replace image names, using content hash
  -o {md,html}, --output-format {md,html}
                        output format
  -p IMAGES_PUBLIC_PATH, --images-public-path IMAGES_PUBLIC_PATH
                        Public path to the folder of downloaded images (possible variables: $article_name, $time, $date, $dt, $base_url)
  -R, --remove-source   Remove or replace source file
  -t DOWNLOADING_TIMEOUT, --downloading-timeout DOWNLOADING_TIMEOUT
                        how many seconds to wait before downloading will be failed
  -O OUTPUT_PATH, --output-path OUTPUT_PATH
                        article output file name
  --version             return version number
```

Example 1:

```
./markdown_tool.py nc-1-zfs/article.md
```

Example 2:

```
./markdown_tool.py not-nas/sov/article.md -o html -s "http://www.ossec.net/_images/ossec-arch.jpg" -a
```

Example 3 (run on a folder):

```
find content/ -name "*.md" | xargs -n1 ./markdown_tool.py
```

