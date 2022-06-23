from setuptools import setup, find_packages
import pathlib
from funchain import __version__


current = pathlib.Path(__file__).parent.resolve()
long_description = (current / "README.md").read_text(encoding="utf-8")


if __name__ == '__main__':
    setup(
        name="funchain",
        version=__version__,
        license="MIT",

        description="tool for chain functions easily and safely",
        long_description=long_description,
        long_description_content_type="text/markdown",

        url="https://github.com/mediadnan/funchain",
        project_urls={
            "bug-report": "https://github.com/mediadnan/funchain/issues"
        },

        author="mediadnan",
        author_email="mediadnan@gmail.com",

    )
