"""
自定义异常类
用于更好的错误处理和分类
"""

from typing import Optional, Dict, Any


class AIAnalyzeException(Exception):
    """AI-Analyze 基础异常类"""

    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码
            context: 错误上下文信息
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """返回错误字符串表示"""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"[{self.error_code}] {self.message} ({context_str})"
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"error_code": self.error_code, "message": self.message, "context": self.context}


# 分析相关异常
class AnalysisException(AIAnalyzeException):
    """分析异常基类"""

    pass


class SerenaAnalysisException(AnalysisException):
    """Serena 分析异常"""

    pass


class ASTAnalysisException(AnalysisException):
    """AST 分析异常"""

    pass


class AIAnalysisException(AnalysisException):
    """AI 分析异常"""

    pass


class UnifiedAnalysisException(AnalysisException):
    """统一分析异常"""

    pass


# 文件相关异常
class FileException(AIAnalyzeException):
    """文件异常基类"""

    pass


class InputFileNotFoundException(FileException):
    """输入文件不存在异常"""

    pass


class FileReadException(FileException):
    """文件读取异常"""

    pass


class FileWriteException(FileException):
    """文件写入异常"""

    pass


class InvalidFileFormatException(FileException):
    """无效文件格式异常"""

    pass


# 配置相关异常
class ConfigException(AIAnalyzeException):
    """配置异常基类"""

    pass


class ConfigNotFoundError(ConfigException):
    """配置文件不存在异常"""

    pass


class InvalidConfigException(ConfigException):
    """无效配置异常"""

    pass


class MissingConfigKeyException(ConfigException):
    """缺少配置键异常"""

    pass


# API 相关异常
class APIException(AIAnalyzeException):
    """API 异常基类"""

    pass


class APIConnectionException(APIException):
    """API 连接异常"""

    pass


class APITimeoutException(APIException):
    """API 超时异常"""

    pass


class APIRateLimitException(APIException):
    """API 速率限制异常"""

    pass


class APIAuthenticationException(APIException):
    """API 认证异常"""

    pass


class APIResponseException(APIException):
    """API 响应异常"""

    pass


# Docker 相关异常
class DockerException(AIAnalyzeException):
    """Docker 异常基类"""

    pass


class DockerGenerationException(DockerException):
    """Docker 生成异常"""

    pass


class DockerBuildException(DockerException):
    """Docker 构建异常"""

    pass


class DockerRunException(DockerException):
    """Docker 运行异常"""

    pass


# 缓存相关异常
class CacheException(AIAnalyzeException):
    """缓存异常基类"""

    pass


class CacheReadException(CacheException):
    """缓存读取异常"""

    pass


class CacheWriteException(CacheException):
    """缓存写入异常"""

    pass


class CacheInvalidException(CacheException):
    """缓存无效异常"""

    pass


# 验证相关异常
class ValidationException(AIAnalyzeException):
    """验证异常基类"""

    pass


class InvalidProjectException(ValidationException):
    """无效项目异常"""

    pass


class InvalidParameterException(ValidationException):
    """无效参数异常"""

    pass


class MissingRequiredParameterException(ValidationException):
    """缺少必需参数异常"""

    pass


# 超时相关异常
class TimeoutException(AIAnalyzeException):
    """超时异常基类"""

    pass


class AnalysisTimeoutException(TimeoutException):
    """分析超时异常"""

    pass


# 资源相关异常
class ResourceException(AIAnalyzeException):
    """资源异常基类"""

    pass


class InsufficientMemoryException(ResourceException):
    """内存不足异常"""

    pass


class InsufficientDiskSpaceException(ResourceException):
    """磁盘空间不足异常"""

    pass


class ResourceLimitExceededException(ResourceException):
    """资源限制超出异常"""

    pass


def create_exception(
    exception_type: type,
    message: str,
    error_code: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> AIAnalyzeException:
    """创建异常实例

    Args:
        exception_type: 异常类型
        message: 错误消息
        error_code: 错误代码
        context: 错误上下文
        **kwargs: 其他参数

    Returns:
        AIAnalyzeException: 异常实例
    """
    return exception_type(message, error_code, context)


def handle_exception(exc: Exception, logger=None, reraise: bool = False) -> Optional[Dict[str, Any]]:
    """处理异常

    Args:
        exc: 异常实例
        logger: 日志记录器
        reraise: 是否重新抛出异常

    Returns:
        异常信息字典或 None
    """
    if isinstance(exc, AIAnalyzeException):
        error_dict = exc.to_dict()
        if logger:
            logger.error(str(exc))
        if reraise:
            raise exc
        return error_dict
    else:
        error_dict = {"error_code": "UnknownError", "message": str(exc), "context": {}}
        if logger:
            logger.error(f"Unknown error: {exc}")
        if reraise:
            raise exc
        return error_dict


if __name__ == "__main__":
    # 测试异常
    try:
        raise SerenaAnalysisException(
            "Serena 分析失败", error_code="SERENA_001", context={"project": "test", "reason": "invalid format"}
        )
    except AIAnalyzeException as e:
        print(f"异常: {e}")
        print(f"字典: {e.to_dict()}")
