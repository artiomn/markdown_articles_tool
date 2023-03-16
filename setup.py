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
    tests_require=['pytest==7.2.2'],
    scripts=['markdown_tool.py'],
    entry_points={
        'console_scripts': [
            'markdown_tool = markdown_tool:main',
        ],
    },
    # flake8: ignore=F821
    version=__version__,  # noqa
    zip_safe=False
)
