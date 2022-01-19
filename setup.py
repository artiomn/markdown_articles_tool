from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()

requirements = [r for r in (here / 'requirements.txt').read_text(encoding='utf-8').split()
                if r and not r.lstrip().startswith('#')]
version = here / 'markdown_toolset' / '__version__.py'
v = compile(version.read_text(encoding='utf-8'), '', 'exec')
exec(v)

setup(
    install_requires=requirements,
    scripts=['markdown_tool.py'],
    # flake8: ignore=F821
    version=__version__,  # noqa
    zip_safe=False
)
