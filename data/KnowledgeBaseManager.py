import os
import json
class KnowledgeBaseManager:
    def __init__(self, base_path):
        self.base_path = base_path
        with open(os.path.join(base_path, "index.json"), "r", encoding="utf-8") as f:
            self.index = json.load(f)

    def get_module(self, module_name):
        """按模块名加载知识"""
        for m in self.index["modules"]:
            if m["name"] == module_name:
                file_path = os.path.join(self.base_path, "os", m["file"])
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        return None

    def get_topic_by_id(self, module_data, topic_id):
        for t in module_data["topics"]:
            if t["id"] == topic_id:
                return t
        return None