import json
from pathlib import Path
from time import perf_counter
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

    start = perf_counter()
    output = git_proxy.log(
        all=True,
        numstat=True,
        date="short",
        # %h == abbreviated commit hash
        # %ad == author date
        # %aN == author name
        pretty="--%h--%cd--%aN--%s",
        no_renames=True,
        after=after_date,
        excludes=["site_scons/", "debian/", "src/third_party/"],
        directory=Path(repo_dir),
    )
    print(f"Reading from git in: {perf_counter() - start}s")

    start = perf_counter()
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
                summary=parts[4],
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
    print(f"Creating commits in: {perf_counter() - start}s")

    start = perf_counter()
    mongo.bulk_add_commit(changes)
    print(f"Loading to mongo in: {perf_counter() - start}s")


@cli.command()
@click.option("--after-date", required=True)
@click.option("--repo-dir", type=click.Path(exists=True))
@click.pass_context
def coupling(ctx, after_date: str, repo_dir: Optional[str]) -> None:
    _coupling(after_date=after_date, repo_dir=repo_dir)


@inject.autoparams()
def _files_per_commit(mongo: Mongo) -> None:
    items = mongo.get_files_per_commit()
    for item in items:
        print(f"{item.id}: {item.avg_files}")


@cli.command()
@click.pass_context
def files_per_commit(ctx) -> None:
    _files_per_commit()


def main():
    """Entry point into commandline."""
    return cli(obj={})


if __name__ == "__main__":
    cli()
