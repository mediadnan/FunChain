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

from pygments.styles.dracula import DraculaStyle


# -- Project information -----------------------------------------------------

project = 'FastChain'
copyright = '2022, MARSO Adnan'
author = 'MARSO Adnan'
version = '2.0'
release = '2.0.0'


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_design",
]

templates_path = ['_templates']

exclude_patterns = []

master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_title = f"{project} (v{version}) docs"
html_short_title = f"{project} docs"
html_logo = "_static/logo/logo.svg"
html_static_path = ['_static']
html_favicon = "_static/favicon/favicon.svg"
html_theme_options = {
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
    # "announcement": "<em>Important</em> announcement!",
}

# Autodoc config

autoclass_content = "both"
autodoc_class_signature = "mixed"
