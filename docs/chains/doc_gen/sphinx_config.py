from typing import Any

import pydantic
import sphinx_rtd_theme
from sphinx.ext.autodoc import ClassDocumenter, FunctionDocumenter
import inspect
from sphinx.util.inspect import getdoc

project = "Dummy"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "myst_parser",
    "sphinx_markdown_builder",
    # "sphinx-pydantic",
]
myst_enable_extensions = [
    "colon_fence",  # This allows the use of ::: for fenced code blocks
]
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "special-members": False,
    "exclude-members": "__*",
    "inherited-members": False,
    "show-inheritance": True,
}

autodoc_typehints = "description"
always_document_param_types = True
napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_rtype = False

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]


def skip_member(app, what, name, obj, skip, options):
    if name == "Config" and isinstance(obj, type):
        print(options.parent)
        return True
    # Exclude Pydantic's Config class and internal attributes
    pydantic_internal_attributes = {
        "model_computed_fields",
        "model_fields",
        "model_json_schema",
        "model_config",
    }
    if name in pydantic_internal_attributes:
        # This shadows user defined usage of those names...
        return True
    return skip


def update_pydantic_model_signature(
    app, what, name, obj, options, signature, return_annotation
):
    if isinstance(obj, type) and issubclass(obj, pydantic.BaseModel):
        fields = obj.__fields__
        parameters = [
            inspect.Parameter(
                name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=field.default
                if field.default != inspect.Parameter.empty
                else inspect.Parameter.empty,
                annotation=field.annotation
                if field.annotation != inspect.Parameter.empty
                else Any,
            )
            for name, field in fields.items()
        ]
        sig = inspect.Signature(parameters)
        obj.__signature__ = sig
        # print(name, sig, return_annotation)
        return str(sig), return_annotation
    return signature, return_annotation


def setup(app):
    app.connect("autodoc-skip-member", skip_member)
    # This doesn't really work... try to diff HTML files.
    # app.connect("autodoc-process-signature", update_pydantic_model_signature)

    # from sphinx_markdown_builder.builder import MarkdownBuilder
    #
    # original_write_doc = MarkdownBuilder.write_doc
    #
    # def write_doc(self, docname, doctree):
    #     # Convert the document tree to string and replace '<' with '&lt;'
    #     doctree_str = doctree.astext().replace("<", "&lt;").replace(">", "&gt;")
    #     # Update the doctree with the modified string
    #     from docutils.io import StringInput
    #     from docutils.core import Publisher
    #
    #     publisher = Publisher(source_class=StringInput, destination_class=StringInput)
    #     publisher.set_components("standalone", "restructuredtext", None)
    #     publisher.set_source(doctree_str, source_path=docname)
    #     doctree = publisher.reader.read(
    #         publisher.source, publisher.parser, publisher.settings
    #     )
    #     original_write_doc(self, docname, doctree)
    #
    # MarkdownBuilder.write_doc = write_doc
