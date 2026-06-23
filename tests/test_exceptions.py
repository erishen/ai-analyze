"""Tests for exceptions module - custom exception hierarchy"""

import pytest

from src.infrastructure.exceptions import (
    AIAnalyzeException,
    AnalysisException,
    SerenaAnalysisException,
    ASTAnalysisException,
    AIAnalysisException,
    UnifiedAnalysisException,
    FileException,
    InputFileNotFoundException,
    FileReadException,
    FileWriteException,
    InvalidFileFormatException,
    ConfigException,
    ConfigNotFoundError,
    InvalidConfigException,
    MissingConfigKeyException,
    APIException,
    APIConnectionException,
    APITimeoutException,
    APIRateLimitException,
    APIAuthenticationException,
    APIResponseException,
    DockerException,
    DockerGenerationException,
    DockerBuildException,
    DockerRunException,
    CacheException,
    CacheReadException,
    CacheWriteException,
    CacheInvalidException,
    ValidationException,
    InvalidProjectException,
    InvalidParameterException,
    MissingRequiredParameterException,
    TimeoutException,
    AnalysisTimeoutException,
    ResourceException,
    InsufficientMemoryException,
)


class TestAIAnalyzeException:
    """Base exception class tests"""

    def test_basic_message(self):
        e = AIAnalyzeException("test error")
        assert e.message == "test error"
        assert e.error_code == "AIAnalyzeException"
        assert e.context == {}

    def test_custom_error_code(self):
        e = AIAnalyzeException("test error", error_code="E001")
        assert e.error_code == "E001"

    def test_custom_context(self):
        e = AIAnalyzeException("test error", context={"file": "main.py", "line": 42})
        assert e.context == {"file": "main.py", "line": 42}

    def test_str_no_context(self):
        e = AIAnalyzeException("test error", error_code="E001")
        assert str(e) == "[E001] test error"

    def test_str_with_context(self):
        e = AIAnalyzeException("test error", error_code="E001", context={"key": "val"})
        assert "[E001]" in str(e)
        assert "test error" in str(e)
        assert "key=val" in str(e)

    def test_to_dict(self):
        e = AIAnalyzeException("test error", error_code="E001", context={"k": "v"})
        d = e.to_dict()
        assert d["error_code"] == "E001"
        assert d["message"] == "test error"
        assert d["context"] == {"k": "v"}

    def test_is_exception(self):
        e = AIAnalyzeException("test")
        assert isinstance(e, Exception)


class TestExceptionHierarchy:
    """Verify inheritance chain"""

    @pytest.mark.parametrize(
        "cls,parent",
        [
            (SerenaAnalysisException, AnalysisException),
            (ASTAnalysisException, AnalysisException),
            (AIAnalysisException, AnalysisException),
            (UnifiedAnalysisException, AnalysisException),
            (AnalysisException, AIAnalyzeException),
            (InputFileNotFoundException, FileException),
            (FileReadException, FileException),
            (FileWriteException, FileException),
            (InvalidFileFormatException, FileException),
            (FileException, AIAnalyzeException),
            (ConfigNotFoundError, ConfigException),
            (InvalidConfigException, ConfigException),
            (MissingConfigKeyException, ConfigException),
            (ConfigException, AIAnalyzeException),
            (APIConnectionException, APIException),
            (APITimeoutException, APIException),
            (APIRateLimitException, APIException),
            (APIAuthenticationException, APIException),
            (APIResponseException, APIException),
            (APIException, AIAnalyzeException),
            (DockerGenerationException, DockerException),
            (DockerBuildException, DockerException),
            (DockerRunException, DockerException),
            (DockerException, AIAnalyzeException),
            (CacheReadException, CacheException),
            (CacheWriteException, CacheException),
            (CacheInvalidException, CacheException),
            (CacheException, AIAnalyzeException),
            (InvalidProjectException, ValidationException),
            (InvalidParameterException, ValidationException),
            (MissingRequiredParameterException, ValidationException),
            (ValidationException, AIAnalyzeException),
            (AnalysisTimeoutException, TimeoutException),
            (TimeoutException, AIAnalyzeException),
            (InsufficientMemoryException, ResourceException),
            (ResourceException, AIAnalyzeException),
        ],
    )
    def test_inheritance(self, cls, parent):
        assert issubclass(cls, parent)

    def test_all_inherit_from_base(self):
        subclasses = [
            AnalysisException,
            FileException,
            ConfigException,
            APIException,
            DockerException,
            CacheException,
            ValidationException,
            TimeoutException,
            ResourceException,
        ]
        for cls in subclasses:
            assert issubclass(cls, AIAnalyzeException)

    def test_subclass_catchable_by_parent(self):
        with pytest.raises(APIException):
            raise APITimeoutException("timeout")

        with pytest.raises(AIAnalyzeException):
            raise CacheReadException("cache read error")

    def test_subclass_preserves_context(self):
        e = APITimeoutException("timeout", error_code="T001", context={"url": "http://x"})
        assert e.error_code == "T001"
        assert e.context == {"url": "http://x"}
        assert "[T001]" in str(e)
