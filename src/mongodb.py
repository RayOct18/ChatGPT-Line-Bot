import os
import datetime

from pymongo import MongoClient


class MongoDB:
    """
    Environment Variables:
        MONGODB_PATH
        MONGODB_DBNAME
    """

    client: None
    db: None

    def connect_to_database(self, mongo_path=None, db_name=None):
        mongo_path = mongo_path or os.getenv("MONGODB_PATH")
        db_name = db_name or os.getenv("MONGODB_DBNAME")
        self.client = MongoClient(mongo_path)
        assert self.client.config.command("ping")["ok"] == 1.0
        self.db = self.client[db_name]

    def upsert(self, id, key, value):
        self.db["users"].update_one(
            {"id": id},
            {
                "$set": {
                    key: value,
                    "updated_at": datetime.datetime.utcnow(),
                }
            },
            upsert=True,
        )

    def find_one(self, id, key):
        res = self.db["users"].find_one({"id": id})
        return res.get(key) if res else None


mongodb = MongoDB()
