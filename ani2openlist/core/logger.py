import logging
from pathlib import Path


# 创建默认 logger
logger = logging.getLogger("ani2openlist")
logger.setLevel(logging.INFO)

# 默认控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def setup_logger(
    level: int = logging.INFO,
    log_file: str | Path | None = None,
    format_string: str | None = None
) -> None:
    """
    配置 logger

    :param level: 日志级别，默认 INFO
    :param log_file: 日志文件路径，如果提供则同时输出到文件
    :param format_string: 自定义日志格式
    """
    global logger
    
    logger.setLevel(level)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 设置格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"日志将输出到文件: {log_path}")
