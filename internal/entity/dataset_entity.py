# 默认知识库描述格式化文本
from enum import Enum

DEFAULT_DATASET_DESCRIPTION_FORMATTER = "当你需要回答管理《{name}》的时候可以引用该知识库。"


# 文档处理类型
class DocumentProcessType:
    AUTOMIC = "automic"
    CUSTOM = "custom"


DEFAULT_PROCESS_RULE = {
    "mode": "custom",
    "rule": {
        "pre_process_rule": [
            {"id": "remove_extra_space", "enabled": True},
            {"id": "remove_url_and_email", "enabled": True},

        ],
        "segment": {
            "separators": [
                    "\n\n",
                    "\n",
                    "。|！|？",
                    "\.|\!|\?\s",
                    "; |;\s",
                    "，|.\s",
                    " ",
                    ""
            ],
            "chunk_size": 500,
            "overlap": 50
        }
    }
}


class DocumentStatus(str, Enum):
    """文档处理状态"""
    WAITING = "waiting"
    PARSING = "parsing"
    SPLITTING = "splitting"
    INDEXING = "indexing"
    COMPLETED = "completed"
    ERROR = "error"


class SegmentStatus(str, Enum):
    """文档处理状态"""
    WAITING = "waiting"
    INDEXING = "indexing"
    COMPLETED = "completed"
    ERROR = "error"