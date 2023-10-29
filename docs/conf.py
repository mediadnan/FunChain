# -- Project Info
project = 'FunChain'
copyright = '2022, MARSO Adnan'
author = 'MARSO Adnan'
version = '0.1'
release = '0.1.0'


# General Config
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinxcontrib.mermaid",
    "myst_parser"
]
templates_path = ['_templates']
exclude_patterns = []
master_doc = 'index'
_py_docs = 'https://docs.python.org/3/library'
external_links = {
    'map': f'{_py_docs}/functions.html#map',
    'filter': f'{_py_docs}/functions.html#filter',
    'functools.partial': f'{_py_docs}/functools.html#functools.partial',
    'logging.Logger': f'{_py_docs}/logging.html#logging.Logger',
    'statistics.mean': f'{_py_docs}/statistics.html#statistics.mean'
}
rst_epilog = '\n'.join(f"""
.. |{name}| raw:: html

    <a href="{link}" target="_blank">{name}</a>
""" for name, link in external_links.items())

# HTML Config
html_theme = 'furo'
html_title = f"{project} {version}"
html_short_title = f"{project} docs"
html_logo = "_static/favicon/favicon.svg"
html_static_path = ['_static']
html_favicon = "_static/favicon/favicon.svg"
html_theme_options = {
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
}


# Autodoc Config
autoclass_content = "both"
autodoc_class_signature = "mixed"

# mermaid config
mermaid_params = [
    '--theme', 'dark',
    '--backgroundColor', 'transparent',
    '--width', '600'
]
