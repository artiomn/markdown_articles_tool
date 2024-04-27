[![Python package](https://github.com/artiomn/markdown_images_downloader/workflows/Python%20package/badge.svg)](https://github.com/artiomn/markdown_articles_tool/actions/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://opensource.org/licenses/MIT)
[![Stargazers](https://img.shields.io/github/stars/artiomn/markdown_images_downloader.svg)](https://github.com/artiomn/markdown_images_downloader/stargazers)
[![Forks](https://img.shields.io/github/forks/artiomn/markdown_images_downloader.svg)](https://github.com/artiomn/markdown_images_downloader/network/members)
[![Latest Release](https://img.shields.io/github/v/release/artiomn/markdown_images_downloader.svg)](https://github.com/artiomn/markdown_images_downloader/releases)


# Markdown articles tool 0.1.3

Free command line utility, written in Python, designed to help you manage online and downloaded Markdown documents (e.g., articles).
The Markdown Articles Tool is available for macOS, Windows, and Linux.

Tool can be used:

- To download Markdown documents with images and:
  * Find all image links, download images and fix links in the document.
  * Can skip broken links.
  * Deduplicate similar images by content hash or using hash as a name.
- Support images, linked with HTML `<img>` tag.
- Support local image files.
- Convert Markdown documents to:
  * HTML.
  * PDF.
  * Or save in the plain Markdown.

Also, if you want to use separate functions, you can just import the package.


## Installation

### From the repository

**You need Python 3.9+.**

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
markdown_tool [options] <article_file_path_or_url>

options:
  -h, --help            show this help message and exit
  -D {disabled,names_hashing,content_hash}, --deduplication-type {disabled,names_hashing,content_hash}
                        Deduplicate images, using content hash or SHA1(image_name) (default: disabled)
  -d IMAGES_DIRNAME, --images-dirname IMAGES_DIRNAME
                        Folder in which to download images (possible variables: $article_name, $time, $date, $dt, $base_url) (default: images)
  -a, --skip-all-incorrect
                        skip all incorrect images (default: False)
  -E, --download-incorrect-mime
                        download "images" with unrecognized MIME type (default: False)
  -s SKIP_LIST, --skip-list SKIP_LIST
                        skip URL's from the comma-separated list (or file with a leading '@') (default: None)
  -i {md,html,md+html,html+md}, --input-format {md,html,md+html,html+md}
                        input format (default: md)
  -l, --process-local-images
                        [DEPRECATED] Process local images (default: False)
  -n, --replace-image-names
                        Replace image names, using content hash (default: False)
  -o {md,html}, --output-format {md,html}
                        output format (default: md)
  -p IMAGES_PUBLIC_PATH, --images-public-path IMAGES_PUBLIC_PATH
                        Public path to the folder of downloaded images (possible variables: $article_name, $time, $date, $dt, $base_url)
  -P, --prepend-images-with-path
                        Save relative images paths (default: False)
  -R, --remove-source   Remove or replace source file (default: False)
  -t DOWNLOADING_TIMEOUT, --downloading-timeout DOWNLOADING_TIMEOUT
                        how many seconds to wait before downloading will be failed (default: -1)
  -O OUTPUT_PATH, --output-path OUTPUT_PATH
                        article output file name or path
  --verbose, -v         More verbose logging (default: False)
  --version             return version number
```

Run example 1:

```
./markdown_tool.py nc-1-zfs/article.md
```

Run example 2:

```
./markdown_tool.py not-nas/sov/article.md -o html -s "http://www.ossec.net/_images/ossec-arch.jpg" -a
```

Run example 3 (run on a folder):

```
find content/ -name "*.md" | xargs -n1 ./markdown_tool.py
```


## Changes

### 0.1.3

- Mostly technical fixes, necessary to work GUI tool.
- Now the tool has [Qt-based GUI](https://github.com/artiomn/mat_gui).


### 0.1.2

- `-l, --process-local-images` deprecated from the version 0.1.2 and will not work: local images will always be processed.
- Images with unrecognized MIME type will not be downloaded by default (use `-E` to disable this behaviour).
- New option `-P, --prepend-images-with-path` changes image output path structure. If this option is enabled,
  "remote" image path will be saved in the local directory structure.
- Code was significantly refactored.
- Some auto tests were added.


### 0.0.8

`-D` (deduplication) option was changed in the version 0.0.8. Now option is not boolean, it has several values: "disabled", "names_hashing", "content_hash".
  Long option name was changed too: now it's `deduplication-type`.


# Internals

Tools is a pipeline, which get Markdown form the source and process them, using blocks:

- Source download article.
- `ImageDownloader` download every image.
  Inside may be used image deduplicator blocks applied to the image.
- Transform article file, i.e. fix images URLs.
- Format article to the specific format (Markdown, HTML, PDF, etc.), using selected formatters.

`ArticleProcessor` class is a strategy, applies blocks, based on the parameters (from the CLI, for example).
