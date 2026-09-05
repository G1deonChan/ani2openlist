from json import loads, dumps
from typing import Literal, Optional
from types import FunctionType

from pydantic import BaseModel, ConfigDict, model_validator, field_validator

from ani2openlist.core.logger import logger


class OpenlistStorage(BaseModel):
    """
    Openlist 存储器模型
    """

    model_config = ConfigDict(
        ignored_types=(FunctionType, type(lambda: None))  # 覆盖 Cython 类型
    )

    id: int = 0  # 存储器 ID
    status: Literal["work", "disabled"] = "work"  # 存储器状态
    remark: str = ""  # 备注
    modified: Optional[str] = None  # 修改时间（可为空）
    disabled: bool = False  # 是否禁用
    mount_path: str = ""  # 挂载路径
    order: int = 0  # 排序
    driver: str = "Local"  # 驱动器
    cache_expiration: int = 30  # 缓存过期时间
    addition: str = "{}"  # 附加信息
    enable_sign: bool = False  # 是否启用签名
    order_by: str = "name"  # 排序字段
    order_direction: str = "asc"  # 排序方向
    extract_folder: str = "front"  # 提取文件夹
    web_proxy: bool = False  # 是否启用 Web 代理
    webdav_policy: str = "native_proxy"  # WebDAV 策略
    down_proxy_url: str = ""  # 下载代理 URL

    def set_addition_by_dict(self, additon: dict) -> None:
        """
        使用 Python 字典设置 Storage 附加信息
        """
        self.addition = dumps(additon)

    @property
    def addition2dict(self) -> dict:
        """
        获取 Storage 附加信息，返回Python 字典
        """
        return loads(self.addition)

    @field_validator("modified", mode="before")
    @classmethod
    def validate_modified(cls, v):
        """验证 modified 字段，将空字符串转换为 None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        """验证 status 字段，将无效值转换为默认值"""
        if v not in ("work", "disabled"):
            logger.warning(f"收到无效的存储器状态值: '{v}'，将使用默认值 'disabled'")
            return "disabled"
        return v

    @model_validator(mode="after")
    def normalize_status(self):
        status_set = "status" in self.model_fields_set
        disabled_set = "disabled" in self.model_fields_set

        if status_set and not disabled_set:
            self.disabled = self.status == "disabled"
        elif disabled_set and not status_set:
            self.status = "disabled" if self.disabled else "work"
        elif status_set and disabled_set:
            expected_status = "disabled" if self.disabled else "work"
            if self.status != expected_status:
                logger.warning(
                    "收到不一致的存储器状态，已自动修正: "
                    f"status='{self.status}', disabled={self.disabled}"
                )
                self.status = expected_status
        return self
