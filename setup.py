from setuptools import setup


setup(
    name='markdown_tool',
    version='0.0.9',
    packages=['markdown_tool'],
    url='https://github.com/artiomn/markdown_articles_tool',
    license='MIT',
    author='artiom_n',
    author_email='',
    install_requires=open('requirements.txt').read().split(),
    description='Parse markdown article, download images and replace images URL\'s with local paths'
)
