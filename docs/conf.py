# -- Project information -----------------------------------------------------

project = 'FastChain'

copyright = '2022, MARSO Adnan'

author = 'MARSO Adnan'

version = '0.1'

release = '0.1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinxcontrib.mermaid",
]

templates_path = ['_templates']

exclude_patterns = []

master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'

html_title = f"{project} {version}"

html_short_title = f"{project} docs"

html_logo = "_static/logo/logo.svg"

html_static_path = ['_static']

html_favicon = "_static/favicon/favicon.svg"

html_theme_options = {
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
}

# Autodoc config

autoclass_content = "both"

autodoc_class_signature = "mixed"
