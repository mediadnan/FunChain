from setuptools import setup, find_packages


if __name__ == '__main__':

    with open("README.md", 'r', encoding='utf-8') as readme_file:
        readme = readme_file.read()

    setup(
        name='funchain',
        version='0.0.0',
        description="simple python3 library for chaining functions sequentially and simultaneously",
        long_description=readme,
        long_description_content_type="text/markdown",
        url="https://github.com/mediadnan/funchain",
        author="mediadnan",
        author_email="mediadnan@gmail.com",
        license="MIT",
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Build Tools',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.10',
            'Topic :: Software Development',
            'Topic :: Utilities',
            'Typing :: Typed',
        ],
        keywords='',
        packages=find_packages(where='funchain'),
        python_requires='>=3.10',
    )
