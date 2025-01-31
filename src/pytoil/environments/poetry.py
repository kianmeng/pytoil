"""
Module responsible for handling poetry environments.

Here we take advantage of poetry's new `local` config setting
to enforce the virtual environment being in the project without
altering the user's base config.


Author: Tom Fleet
Created: 24/12/2021
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import TYPE_CHECKING

from pytoil.exceptions import PoetryNotInstalledError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

POETRY = shutil.which("poetry")


class Poetry:
    def __init__(self, root: Path, poetry: str | None = POETRY) -> None:
        self.root = root
        self.poetry = poetry

    def __repr__(self) -> str:
        return (
            self.__class__.__qualname__
            + f"(root={self.root!r}, poetry={self.poetry!r})"
        )

    __slots__ = ("root", "poetry")

    @property
    def project_path(self) -> Path:
        return self.root.resolve()

    @property
    def executable(self) -> Path:
        return self.project_path.joinpath(".venv/bin/python")

    @property
    def name(self) -> str:
        return "poetry"

    def enforce_local_config(self) -> None:
        """
        Ensures any changes to poetry's config such as storing the
        virtual environment in the project directory as we do here, do not
        propegate to the user's global poetry config.
        """
        if not self.poetry:
            raise PoetryNotInstalledError

        subprocess.run(
            [self.poetry, "config", "virtualenvs.in-project", "true", "--local"],
            cwd=self.project_path,
        )

    def exists(self) -> bool:
        """
        Checks whether the virtual environment exists by a proxy
        check if the `executable` exists.

        If this executable exists then both the project and the virtual environment
        must also exist and must therefore be valid.
        """
        return self.executable.exists()  # pragma: no cover

    def create(
        self, packages: Sequence[str] | None = None, silent: bool = False
    ) -> None:
        """
        This method is not implemented for poetry environments.

        Use `install` instead as with poetry, creation and installation
        are handled together.
        """
        raise NotImplementedError

    def install(self, packages: Sequence[str], silent: bool = False) -> None:
        """
        Calls `poetry add` to install packages into the environment.

        Args:
            packages (List[str]): List of packages to install.
            silent (bool, optional): Whether to discard or display output.
        """
        if not self.poetry:
            raise PoetryNotInstalledError

        self.enforce_local_config()

        subprocess.run(
            [self.poetry, "add", *packages],
            cwd=self.project_path,
            stdout=subprocess.DEVNULL if silent else sys.stdout,
            stderr=subprocess.DEVNULL if silent else sys.stderr,
        )

    def install_self(self, silent: bool = False) -> None:
        """
        Calls `poetry install` under the hood to install the current package
        and all it's dependencies.

        Args:
            silent (bool, optional): Whether to discard or display output.
                Defaults to False.
        """
        if not self.poetry:
            raise PoetryNotInstalledError

        self.enforce_local_config()

        subprocess.run(
            [self.poetry, "install"],
            cwd=self.project_path,
            stdout=subprocess.DEVNULL if silent else sys.stdout,
            stderr=subprocess.DEVNULL if silent else sys.stderr,
        )
