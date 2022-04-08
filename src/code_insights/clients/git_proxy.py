"""A proxy for working with the git cli."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from plumbum import local
from plumbum.machines.local import LocalCommand


class GitProxy:
    """A service for interacting with git."""

    def __init__(self, git: LocalCommand) -> None:
        """Initialize the service."""
        self.git = git

    @classmethod
    def create(cls) -> GitProxy:
        """Create evergreen CLI service instance."""
        return cls(local.cmd.git)

    def log(
        self,
        all: bool = False,
        numstat: bool = False,
        date: Optional[str] = None,
        pretty: Optional[str] = None,
        no_renames: bool = False,
        after: Optional[str] = None,
        excludes: Optional[List[str]] = None,
        directory: Optional[Path] = None,
    ) -> str:
        args = ["log"]
        if all:
            args.append("--all")
        if numstat:
            args.append("--numstat")
        if date is not None:
            args.append(f"--date={date}")
        if pretty is not None:
            args.append(f"--pretty=format:{pretty}")
        if no_renames:
            args.append("--no-renames")
        if after is not None:
            args.append(f"--after={after}")
        if excludes is not None:
            args.append("--")
            args.extend([f":(exclude){exclude}" for exclude in excludes])
        with local.cwd(self._determine_directory(directory)):
            return self.git[args]()

    @staticmethod
    def _determine_directory(directory: Optional[Path] = None) -> Path:
        """
        Determine which directory to run git command in.
        :param directory: Directory containing it repository.
        :return: Path to run git commands in.
        """
        if directory is None:
            return Path(local.cwd)
        elif not directory.is_absolute():
            return Path(local.cwd / directory)
        return directory
