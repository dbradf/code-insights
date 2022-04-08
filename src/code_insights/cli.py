import json
from pathlib import Path
from typing import List, Optional

import click
import inject

from code_insights.clients.git_proxy import GitProxy
from code_insights.clients.mongo import FileChange, GitCommit, Mongo


@click.group()
@click.option("--mongo-uri", required=True)
@click.pass_context
def cli(ctx, mongo_uri: str):
    def dependencies(binder: inject.Binder) -> None:
        binder.bind(GitProxy, GitProxy.create())
        binder.bind(Mongo, Mongo.from_uri(mongo_uri))

    inject.configure(dependencies)

    ctx.ensure_object(dict)


@inject.autoparams()
def _coupling(git_proxy: GitProxy, mongo: Mongo, after_date: str, repo_dir: Optional[str]) -> None:

    output = git_proxy.log(
        all=True,
        numstat=True,
        date="short",
        # %h == abbreviated commit hash
        # %ad == author date
        # %aN == author name
        pretty="--%h--%ad--%aN",
        no_renames=True,
        after=after_date,
        excludes=["site_scons/", "debian/", "src/third_party/"],
        directory=Path(repo_dir),
    )

    changes: List[GitCommit] = []
    current_commit = None
    for line in output.splitlines():
        if not line:
            continue

        if line.startswith("--"):
            if current_commit is not None:
                changes.append(current_commit)
            parts = line.split("--")
            current_commit = GitCommit(
                commit=parts[1],
                date=parts[2],
                author=parts[3],
                files=[]
            )
        else:
            if not current_commit:
                continue
            parts = line.split()
            current_commit.files.append(
                FileChange(
                    added=int(parts[0]) if parts[0] != "-" else 0,
                    deleted=int(parts[1]) if parts[1] != "-" else 0,
                    filename=parts[2]
                )
            )

    for change in changes:
        mongo.add_commit(change)


@cli.command()
@click.option("--after-date", required=True)
@click.option("--repo-dir", type=click.Path(exists=True))
@click.pass_context
def coupling(ctx, after_date: str, repo_dir: Optional[str]) -> None:
    _coupling(after_date=after_date, repo_dir=repo_dir)


def main():
    """Entry point into commandline."""
    return cli(obj={})


if __name__ == "__main__":
    cli()
