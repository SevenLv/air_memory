"""系统配置模块，所有性能阈值均可通过环境变量配置。"""

import os


class Settings:
    """系统配置，支持通过环境变量覆盖默认值。"""

    # 存储/查询响应时间上限（毫秒）
    STORE_RESPONSE_LIMIT_MS: int = int(os.getenv("STORE_RESPONSE_LIMIT_MS", "100"))
    QUERY_RESPONSE_LIMIT_MS: int = int(os.getenv("QUERY_RESPONSE_LIMIT_MS", "100"))

    # 热层内存预算（MB），默认 6GB
    HOT_MEMORY_BUDGET_MB: int = int(os.getenv("HOT_MEMORY_BUDGET_MB", "6144"))

    # 磁盘水位配置（GB）
    DISK_TRIGGER_GB: float = float(os.getenv("DISK_TRIGGER_GB", "38"))
    DISK_SAFE_GB: float = float(os.getenv("DISK_SAFE_GB", "35"))
    DISK_MAX_GB: float = float(os.getenv("DISK_MAX_GB", "40"))

    # 新记忆保护时长（小时），默认 168 小时（7×24h）
    MEMORY_PROTECT_HOURS: int = int(os.getenv("MEMORY_PROTECT_HOURS", "168"))

    # 关联评分变化步长（每次正向反馈增加、负向反馈减少的量）
    ASSOCIATION_SCORE_STEP: float = float(os.getenv("ASSOCIATION_SCORE_STEP", "1.0"))

    # ChromaDB 冷层数据目录
    CHROMA_COLD_PATH: str = os.getenv("CHROMA_COLD_PATH", "./data/chroma_cold")

    # SQLite 数据库路径
    DB_PATH: str = os.getenv("DB_PATH", "./data/logs.db")

    # Embedding 模型名称
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # 磁盘检查间隔（秒），默认 3600s = 1 小时
    DISK_CHECK_INTERVAL_S: int = int(os.getenv("DISK_CHECK_INTERVAL_S", "3600"))

    # ChromaDB 集合名称
    HOT_COLLECTION: str = os.getenv("HOT_COLLECTION", "hot_memories")
    COLD_COLLECTION: str = os.getenv("COLD_COLLECTION", "cold_memories")


settings = Settings()
