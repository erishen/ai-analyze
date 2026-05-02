"""
代码相似性检测
用于识别重复代码和相似代码片段
"""

import hashlib
from typing import Any, Dict, List
from dataclasses import dataclass
from difflib import SequenceMatcher
import logging


@dataclass
class CodeBlock:
    """代码块"""

    file_path: str
    start_line: int
    end_line: int
    content: str
    language: str = "unknown"

    @property
    def line_count(self) -> int:
        """代码行数"""
        return self.end_line - self.start_line + 1

    @property
    def hash(self) -> str:
        """代码块哈希"""
        return hashlib.md5(self.content.encode()).hexdigest()

    def normalize(self) -> str:
        """规范化代码（用于比较）"""
        # 移除注释和空行
        lines = []
        for line in self.content.split("\n"):
            # 移除注释
            if "#" in line:
                line = line[: line.index("#")]
            # 移除空行
            line = line.strip()
            if line:
                lines.append(line)

        return "\n".join(lines)


@dataclass
class SimilarityResult:
    """相似性结果"""

    block1: CodeBlock
    block2: CodeBlock
    similarity: float  # 0-1

    @property
    def is_duplicate(self) -> bool:
        """是否为完全重复"""
        return self.similarity >= 0.95

    @property
    def is_similar(self) -> bool:
        """是否为相似"""
        return self.similarity >= 0.7


class SimilarityDetector:
    """相似性检测器"""

    def __init__(self, min_block_size: int = 5):
        """初始化相似性检测器

        Args:
            min_block_size: 最小代码块大小（行数）
        """
        self.min_block_size = min_block_size
        self.logger = logging.getLogger("ai-analyze.similarity")
        self.code_blocks: List[CodeBlock] = []
        self.results: List[SimilarityResult] = []

    def add_code_block(self, block: CodeBlock):
        """添加代码块

        Args:
            block: 代码块
        """
        if block.line_count >= self.min_block_size:
            self.code_blocks.append(block)

    def add_code_blocks(self, blocks: List[CodeBlock]):
        """添加多个代码块

        Args:
            blocks: 代码块列表
        """
        for block in blocks:
            self.add_code_block(block)

    def detect_duplicates(self) -> List[SimilarityResult]:
        """检测完全重复的代码

        Returns:
            重复代码列表
        """
        duplicates = []

        # 按哈希分组
        hash_groups: Dict[str, List[CodeBlock]] = {}
        for block in self.code_blocks:
            block_hash = block.hash
            if block_hash not in hash_groups:
                hash_groups[block_hash] = []
            hash_groups[block_hash].append(block)

        # 找出重复的代码块
        for block_hash, blocks in hash_groups.items():
            if len(blocks) > 1:
                for i in range(len(blocks)):
                    for j in range(i + 1, len(blocks)):
                        result = SimilarityResult(block1=blocks[i], block2=blocks[j], similarity=1.0)
                        duplicates.append(result)

        return duplicates

    def detect_similar(self, threshold: float = 0.7) -> List[SimilarityResult]:
        """检测相似的代码

        Args:
            threshold: 相似度阈值

        Returns:
            相似代码列表
        """
        similar = []

        for i in range(len(self.code_blocks)):
            for j in range(i + 1, len(self.code_blocks)):
                block1 = self.code_blocks[i]
                block2 = self.code_blocks[j]

                # 计算相似度
                similarity = self._calculate_similarity(block1, block2)

                if similarity >= threshold:
                    result = SimilarityResult(block1=block1, block2=block2, similarity=similarity)
                    similar.append(result)

        # 按相似度排序
        similar.sort(key=lambda x: x.similarity, reverse=True)

        return similar

    def _calculate_similarity(self, block1: CodeBlock, block2: CodeBlock) -> float:
        """计算两个代码块的相似度

        Args:
            block1: 代码块 1
            block2: 代码块 2

        Returns:
            相似度（0-1）
        """
        # 规范化代码
        norm1 = block1.normalize()
        norm2 = block2.normalize()

        # 使用 SequenceMatcher 计算相似度
        matcher = SequenceMatcher(None, norm1, norm2)
        return matcher.ratio()

    def detect_all(self, threshold: float = 0.7) -> Dict[str, List[SimilarityResult]]:
        """检测所有相似性

        Args:
            threshold: 相似度阈值

        Returns:
            包含重复和相似代码的字典
        """
        return {"duplicates": self.detect_duplicates(), "similar": self.detect_similar(threshold)}

    def print_results(self, results: List[SimilarityResult]):
        """打印结果

        Args:
            results: 相似性结果列表
        """
        if not results:
            print("没有发现相似代码")
            return

        print("\n" + "=" * 80)
        print("代码相似性检测结果")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            print(f"\n相似代码对 {i}:")
            print(f"  文件 1: {result.block1.file_path} (行 {result.block1.start_line}-{result.block1.end_line})")
            print(f"  文件 2: {result.block2.file_path} (行 {result.block2.start_line}-{result.block2.end_line})")
            print(f"  相似度: {result.similarity:.1%}")
            print(f"  类型: {'完全重复' if result.is_duplicate else '相似代码'}")

        print("\n" + "=" * 80 + "\n")


class CodeCloneDetector:
    """代码克隆检测器"""

    def __init__(self):
        """初始化代码克隆检测器"""
        self.logger = logging.getLogger("ai-analyze.clone")
        self.detector = SimilarityDetector()

    def analyze_files(self, files: Dict[str, str]) -> Dict[str, Any]:
        """分析文件中的代码克隆

        Args:
            files: 文件路径和内容的字典

        Returns:
            分析结果
        """
        # 提取代码块
        for file_path, content in files.items():
            lines = content.split("\n")

            # 简单的代码块提取（按函数/类分割）
            current_block = []
            start_line = 0

            for i, line in enumerate(lines):
                current_block.append(line)

                # 检测代码块结束（简化版本）
                if len(current_block) >= 5 and (
                    line.strip().startswith("def ") or line.strip().startswith("class ") or i == len(lines) - 1
                ):
                    if len(current_block) > 5:
                        block = CodeBlock(
                            file_path=file_path, start_line=start_line, end_line=i, content="\n".join(current_block)
                        )
                        self.detector.add_code_block(block)

                    current_block = []
                    start_line = i + 1

        # 检测相似性
        results = self.detector.detect_all()

        return {
            "total_blocks": len(self.detector.code_blocks),
            "duplicates": len(results["duplicates"]),
            "similar": len(results["similar"]),
            "results": results,
        }

    def print_report(self, analysis: Dict[str, Any]):
        """打印分析报告

        Args:
            analysis: 分析结果
        """
        print("\n" + "=" * 80)
        print("代码克隆检测报告")
        print("=" * 80)
        print(f"\n总代码块数: {analysis['total_blocks']}")
        print(f"完全重复: {analysis['duplicates']} 对")
        print(f"相似代码: {analysis['similar']} 对")

        if analysis["results"]["duplicates"]:
            print("\n完全重复的代码:")
            self.detector.print_results(analysis["results"]["duplicates"])

        if analysis["results"]["similar"]:
            print("\n相似的代码:")
            self.detector.print_results(analysis["results"]["similar"])

        print("=" * 80 + "\n")


def calculate_code_similarity(code1: str, code2: str) -> float:
    """计算两段代码的相似度

    Args:
        code1: 代码 1
        code2: 代码 2

    Returns:
        相似度（0-1）
    """
    matcher = SequenceMatcher(None, code1, code2)
    return matcher.ratio()


if __name__ == "__main__":
    # 测试代码相似性检测
    print("测试代码相似性检测:")

    # 创建测试代码块
    code1 = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
"""

    code2 = """
def calculate_sum(items):
    result = 0
    for item in items:
        result += item
    return result
"""

    code3 = """
def calculate_product(numbers):
    total = 1
    for num in numbers:
        total *= num
    return total
"""

    # 创建代码块
    block1 = CodeBlock("file1.py", 1, 5, code1)
    block2 = CodeBlock("file2.py", 1, 5, code2)
    block3 = CodeBlock("file3.py", 1, 5, code3)

    # 创建检测器
    detector = SimilarityDetector()
    detector.add_code_blocks([block1, block2, block3])

    # 检测相似性
    similar = detector.detect_similar(threshold=0.5)

    # 打印结果
    detector.print_results(similar)
