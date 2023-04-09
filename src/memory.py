import os
from typing import Dict
from collections import defaultdict
from src.logger import logger


class MemoryInterface:
    def append_storage(self, user_id: str, message: Dict) -> None:
        pass

    def get_storage(self, user_id: str) -> str:
        return ""

    def clean_storage(self, user_id: str) -> None:
        pass


class Memory(MemoryInterface):
    def __init__(self, db):
        self.db = db
        self.default_system_message = os.getenv("SYSTEM_MESSAGE")
        self.default_memory_message_count = 2

    def _initialize(self, user_id: str):
        return {
            "role": "system",
            "content": self.get_system_message(user_id) or self.default_system_message,
        }

    def _drop_message(self, user_id, storage):
        memory_message_count = self.get_memory_message_count(user_id)
        if len(storage) >= memory_message_count + 1:
            return [storage[0]] + storage[-memory_message_count:]
        return storage

    def add_api_key(self, user_id, api_key):
        self.db.upsert(user_id, "api_key", api_key)

    def get_api_key(self, user_id):
        return self.db.find_one(user_id, "api_key")

    def change_system_message(self, user_id, system_message):
        self.db.upsert(user_id, "system_message", system_message)
        self.clean_storage(user_id)

    def get_system_message(self, user_id):
        return (
            self.db.find_one(user_id, "system_message") or self.default_system_message
        )

    def change_memory_message_count(self, user_id, memory_message_count):
        self.db.upsert(user_id, "memory_message_count", memory_message_count)
        storage = self._drop_message(user_id, self.get_storage(user_id))
        self.db.upsert(user_id, "storage", storage)

    def get_memory_message_count(self, user_id):
        return (
            self.db.find_one(user_id, "memory_message_count")
            or self.default_memory_message_count
        )

    def append_storage(self, user_id: str, role: str, content: str) -> None:
        storage = self.get_storage(user_id)
        if not storage:
            storage.append(self._initialize(user_id))
        storage.append({"role": role, "content": content})
        logger.debug(f"memory length: {len(storage)}")
        storage = self._drop_message(user_id, storage)
        logger.debug(
            f"memory length after dropping (max: {self.get_memory_message_count(user_id)}): {len(storage)}"
        )
        self.db.upsert(user_id, "storage", storage)

    def get_storage(self, user_id: str) -> str:
        return self.db.find_one(user_id, "storage") or []

    def clean_storage(self, user_id: str) -> None:
        self.db.upsert(user_id, "storage", [])

    def get_shortcut_keywords(self, user_id):
        return self.db.find_one(user_id, "shortcut_keywords") or {}

    def change_shortcut_keywords(self, user_id, shortcut_keywords):
        self.db.upsert(user_id, "shortcut_keywords", shortcut_keywords)
