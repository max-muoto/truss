import shutil

import pydantic
import sys

import inspect

import pathlib
from pathlib import Path
from sphinx import application

import truss_chains as chains


DUMMY_INDEX_RST = """
.. Dummy

Welcome to Truss Chains's documentation!
========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
"""


def _list_imported_symbols(module: object) -> list[tuple[str, str]]:
    imported_symbols = [
        (
            f"truss_chains.{name}",
            "autoclass"
            if inspect.isclass(obj)
            else "autofunction"
            if inspect.isfunction(obj)
            else "autodata",
        )
        for name, obj in inspect.getmembers(module)
        if not name.startswith("_") and not inspect.ismodule(obj)
    ]
    # Extra classes that are not really exported as public API, but are still relevant.
    imported_symbols.extend(
        [
            ("truss_chains.definitions.ABCChainlet", "autoclass"),
            ("truss_chains.definitions.AssetSpec", "autoclass"),
            ("truss_chains.definitions.ComputeSpec", "autoclass"),
            ("truss_chains.deploy.ChainService", "autoclass"),
            ("truss_chains.definitions.ServiceDescriptor", "autoclass"),
        ]
    )
    # print(imported_symbols)
    return sorted(imported_symbols, key=lambda x: x[0].split(".")[-1].lower())


def generate_sphinx_docs(
    src_dir: pathlib.Path,
    package_name: str,
    output_dir: pathlib.Path,
    snippets_dir: pathlib.Path,
) -> None:
    sys.path.insert(0, str(Path("{src_dir}")))
    config_file = pathlib.Path(__file__).parent / "sphinx_config.py"
    docs_dir = output_dir / "docs"
    conf_dir = docs_dir
    doctree_dir = docs_dir / "doctrees"
    builder = "markdown"

    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "conf.py").write_text(config_file.read_text())
    (docs_dir / "index.rst").write_text(DUMMY_INDEX_RST)

    exported_symbols = _list_imported_symbols(chains)
    rst_parts = ["API Reference\n============="]
    for symbol, kind in exported_symbols:
        rst_parts.append(
            f"""
.. {kind}:: {symbol}

"""
        )

    (docs_dir / "modules.rst").write_text("\n".join(rst_parts))

    app = application.Sphinx(
        srcdir=str(docs_dir),
        confdir=str(conf_dir),
        outdir=str(Path(output_dir).resolve()),
        doctreedir=str(doctree_dir),
        buildername=builder,
    )
    app.build()

    if builder == "markdown":
        shutil.copy(
            output_dir / "modules.md", snippets_dir / "chains/API-reference.mdx"
        )


if __name__ == "__main__":
    snippets_dir = pathlib.Path(__file__).parent.parent.parent / "snippets"
    generate_sphinx_docs(
        src_dir=pathlib.Path(chains.__file__).parent,
        package_name="Truss-Chains",
        output_dir=pathlib.Path("/tmp/doc_gen"),
        snippets_dir=snippets_dir,
    )
