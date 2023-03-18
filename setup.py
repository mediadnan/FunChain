try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from fastchain import __version__


with open('./README.md') as readme_file:
    readme = readme_file.read()


if __name__ == '__main__':
    setup(
        name='fastchain',
        version=__version__,
        description="Chain functions easily and safely",
        long_description=readme,
        long_description_content_type='text/markdown',
        keywords=[
            "function",
            "functional",
            "chain",
            "chaining",
            "pipe",
            "piping",
            "pipeline",
            "compose",
            "composing",
            "composition",
            "flow",
            "data",
            "process",
            "processing",
            "safe",
            "node",
            "handle",
            "report",
        ],
        author='MARSO Adnan',
        maintainer='MARSO Adnan',
        author_email='mediadnan@gmail.com',
        license='MIT',
        license_files='LICENSE',
        classifiers=[
            "Development Status :: 3 - Alpha",

            "Intended Audience :: Developers",

            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3 :: Only",

            "Topic :: Software Development",
            "Topic :: Utilities",

            "Typing :: Typed",
        ],
        url="https://github.com/mediadnan/fastchain",
        project_urls={
            'documentation': "https://fast-chain.readthedocs.io/",
            'bug-tracker': "https://github.com/mediadnan/fastchain/issues",
        },
        packages=['fastchain'],
        python_requires='>=3.11',
        zip_safe=False,
        options={

        }
    )
