# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Agregar raíz del proyecto al path para autodoc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# ── Proyecto ──────────────────────────────────────────────
project = "Mesa de Ayuda — Comunicarlos"
author = "Equipo PP5"
release = "0.1.0"

# ── Extensiones ───────────────────────────────────────────
extensions = [
    "sphinx.ext.autodoc",      # Genera docs desde docstrings
    "sphinx.ext.viewcode",     # Links al código fuente
    "sphinx.ext.napoleon",     # Docstrings Google/NumPy style
    "myst_parser",             # Soporte Markdown
]

# ── Formatos soportados ──────────────────────────────────
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# ── Tema ──────────────────────────────────────────────────
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
}

# ── Autodoc ───────────────────────────────────────────────
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

# ── Idioma ────────────────────────────────────────────────
language = "es"
