import os
import json
import glob

class KnowledgeBaseManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.topics_index = {}  # topic_id -> topic_data
        self._load_all_topics()

    def _load_all_topics(self):
        """加载 base_path 下所有 JSON 文件中的 topics"""
        json_files = glob.glob(os.path.join(self.base_path, "*.json"))
        for file_path in json_files:
            # 跳过测试用的 memory.json（可选，不跳也不会影响，因为它的 topics ID 不会冲突）
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 处理两种格式：{"topics": [...]} 或 直接是列表
                if "topics" in data:
                    topics = data["topics"]
                elif isinstance(data, list):
                    topics = data
                else:
                    continue
                for topic in topics:
                    topic_id = topic.get("id")
                    if topic_id:
                        self.topics_index[topic_id] = topic

    def get_topic_by_id(self, topic_id):
        return self.topics_index.get(topic_id)