# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'FastChain'
copyright = '2022, MARSO Adnan'
author = 'MARSO Adnan'
version = '1.0.1'
release = '1.0.1'


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
]

templates_path = ['_templates']

exclude_patterns = []

master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_static_path = ['_static', '_examples']
# html_logo = "_static/logo/logo-color.svg"
html_favicon = "_static/favicon/favicon-black.svg"
html_theme_options = {
    "sidebar_hide_name": True,
    "light_logo": "logo/logo-black-no-bg.svg",
    "dark_logo": "logo/logo-white-no-bg.svg",
}
