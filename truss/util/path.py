import fnmatch
import os
import random
import string
import tempfile
from contextlib import contextmanager
from distutils.dir_util import copy_tree, remove_tree
from distutils.file_util import copy_file
from pathlib import Path
from typing import List, Optional, Tuple, Union

from truss.patch.hash import str_hash_str

PYTHON_GITIGNORE_PATH = Path(__file__).parent / "python.gitignore"


def copy_tree_path(src: Path, dest: Path) -> List[str]:
    return copy_tree(str(src), str(dest), verbose=0)


def copy_file_path(src: Path, dest: Path) -> Tuple[str, str]:
    return copy_file(str(src), str(dest), verbose=False)


def copy_tree_or_file(src: Path, dest: Path) -> Union[List[str], Tuple[str, str]]:
    if src.is_file():
        return copy_file_path(src, dest)

    return copy_tree_path(src, dest)


def remove_tree_path(target: Path) -> None:
    return remove_tree(str(target), verbose=0)


def get_max_modified_time_of_dir(path: Path) -> float:
    max_modified_time = os.path.getmtime(path)
    for root, dirs, files in os.walk(path):
        if os.path.islink(root):
            raise ValueError(f"Symlinks not allowed in Truss: {root}")
        files = [f for f in files if not f.startswith(".")]
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        max_modified_time = max(max_modified_time, os.path.getmtime(root))
        for file in files:
            max_modified_time = max(
                max_modified_time, os.path.getmtime(os.path.join(root, file))
            )
    return max_modified_time


@contextmanager
def given_or_temporary_dir(given_dir: Optional[Path] = None):
    if given_dir is not None:
        yield given_dir
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)


def build_truss_target_directory(stub: str) -> Path:
    """Builds a directory under ~/.truss/models for the purpose of creating a Truss at."""
    rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    target_directory_path = Path(
        Path.home(), ".truss", "models", f"{stub}-{rand_suffix}"
    )
    target_directory_path.mkdir(parents=True)
    return target_directory_path


def calc_shadow_truss_dirname(truss_path: Path) -> str:
    resolved_path_str = str(truss_path.resolve())
    return str_hash_str(resolved_path_str)


def build_truss_shadow_target_directory(stub: str, truss_path: Path) -> Path:
    """Builds a directory under ~/.truss/models."""
    suffix = calc_shadow_truss_dirname(truss_path)
    target_directory_path = Path(Path.home(), ".truss", "models", f"{stub}-{suffix}")
    target_directory_path.mkdir(parents=True, exist_ok=True)
    return target_directory_path


def load_gitignore_patterns(gitignore_file: Path):
    """Load patterns from a .gitignore file"""
    patterns = []
    with open(gitignore_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def is_ignored(path: Path, patterns: List[str]) -> bool:
    """Check if a given path or any of its parts matches any pattern in .gitignore"""
    for pattern in patterns:
        if path.is_dir() and pattern.endswith("/"):
            pattern = pattern.rstrip("/")
            if fnmatch.fnmatch(path.name, pattern):
                return True
        elif fnmatch.fnmatch(str(path), pattern):
            return True
    return False


def remove_ignored_files(
    directory: Path, gitignore_file: Path = PYTHON_GITIGNORE_PATH
) -> None:
    """Traverse a directory and remove any files that match patterns"""
    patterns = load_gitignore_patterns(gitignore_file)
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            file_path = Path(root) / name
            if is_ignored(file_path, patterns):
                file_path.unlink()
        for name in dirs:
            dir_path = Path(root) / name
            if is_ignored(dir_path, patterns):
                print(f"Removing {dir_path}")
                remove_tree_path(dir_path)
