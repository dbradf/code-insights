from __future__ import annotations
from typing import List

from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database

DB_NAME = "code_insights"
COLL_NAME = "commits"


class FileChange(BaseModel):

    added: int
    deleted: int
    filename: str


class GitCommit(BaseModel):

    commit: str
    date: str
    author: str
    files: List[FileChange]


class Mongo:

    def __init__(self, database: Database) -> None:
        self.database = database
        self.collection = database.get_collection(COLL_NAME)

    @classmethod
    def from_uri(cls, mongo_uri: str) -> Mongo:
        client = MongoClient(mongo_uri)
        return cls(client.get_database(DB_NAME))

    def add_commit(self, git_commit: GitCommit) -> None:
        self.collection.insert_one(git_commit.dict())
