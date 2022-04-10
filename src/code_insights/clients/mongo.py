from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field
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
    summary: str
    files: List[FileChange]


class FilesPerCommit(BaseModel):

    id: str = Field(alias="_id")
    avg_files: float


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

    def bulk_add_commit(self, commits: List[GitCommit]) -> None:
        self.collection.insert_many([commit.dict() for commit in commits])

    def get_files_per_commit(self) -> List[FilesPerCommit]:
        aggregation = [
            {"$addFields": {"file_count": {"$size": "$files"}}},
            {"$group": {"_id": "$author", "avg_files": {"$avg": "$file_count"}}},
            {"$sort": {"avg_files": -1}},
        ]

        results = self.collection.aggregate(aggregation)
        return [FilesPerCommit(**item) for item in results]
