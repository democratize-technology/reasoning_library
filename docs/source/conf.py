import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# Project information
project = "reasoning-library"
copyright = "2024, reasoning-library contributors"
author = "reasoning-library contributors"

# Version information
version = "0.1.0"
release = "0.1.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

autosummary_generate = False
autodoc_typehints = "description"

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Theme
html_theme = "alabaster"  # Use alabaster as it's included by default
html_theme_options = {
    "description": "A Python library for formal reasoning methods",
    "github_user": "democratize-technology",
    "github_repo": "reasoning_library",
}

# Static files
html_static_path = ["_static"]

# Source suffix
source_suffix = ".rst"

# Master doc
master_doc = "index"

# Intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}
