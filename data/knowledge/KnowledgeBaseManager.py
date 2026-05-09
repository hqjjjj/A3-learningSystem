import os
import json

class KnowledgeBaseManager:

    def __init__(self, base_path):

        self.base_path = base_path

        file_path = os.path.join(base_path, "memory.json")

        with open(file_path, "r", encoding="utf-8") as f:
            self.index = json.load(f)

    def get_topic_by_id(self, topic_id):

        for t in self.index["topics"]:

            if t["id"] == topic_id:
                return t

        return None