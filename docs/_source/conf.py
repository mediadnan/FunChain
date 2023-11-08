# -- Project Info
project = 'FunChain'
copyright = '2023, MARSO Adnan'
author = 'MARSO Adnan'
version = '0.1'
release = '0.1.0'


# General Config
extensions = [
    "sphinx.ext.autodoc",
    "sphinxcontrib.mermaid",
    "myst_parser"
]
templates_path = ['_templates']
exclude_patterns = []
master_doc = 'index'
_py_docs = 'https://docs.python.org/3/library'

# HTML Config
html_theme = 'furo'
html_title = f"{project} Documentation"
html_short_title = f"{project} docs"
html_logo = "../_static/logo/logo.png"
html_static_path = ['../_static']
html_css_files = ['../_static/custom.css']
html_js_files = ['../_static/theme_script.js']
html_favicon = "../_static/favicon/favicon.svg"
html_theme_options = {
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
}


# Autodoc Config
autoclass_content = "both"
autodoc_class_signature = "mixed"

# myst config
myst_enable_extensions = ["attrs_block"]

# mermaid config
mermaid_params = [
    '--backgroundColor', 'transparent',
    '--width', '600'
]
