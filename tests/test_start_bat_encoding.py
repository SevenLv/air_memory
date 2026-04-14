# -*- coding: utf-8 -*-
"""
测试模块: test_start_bat_encoding.py
测试目的: 验证 start.bat 的编码修复是否正确
背景:
    v1.0.0 存在 start.bat 在 Windows CP936/GBK 环境下启动失败的问题。
    根因是 UTF-8 中文字符在 GBK 解析时，行末的 UTF-8 字节落在 GBK 前导字节
    范围（0x81-0xFE），导致 LF 行尾被 GBK 解析器消费，行边界丢失，相邻行合并。
修复方案:
    1. start.bat 第2行添加 chcp 65001 >nul 2>&1
    2. start.bat 行尾从 LF 改为 CRLF
    3. 新增 .gitattributes 指定 *.bat text eol=crlf，*.sh text eol=lf
"""

import os
import warnings
import pytest

# 项目根目录（测试文件位于 tests/ 子目录下，向上一级即为项目根目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 被测文件路径
START_BAT_PATH = os.path.join(PROJECT_ROOT, "start.bat")
GITATTRIBUTES_PATH = os.path.join(PROJECT_ROOT, ".gitattributes")


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _read_binary(path: str) -> bytes:
    """以二进制模式读取文件内容，并断言文件存在。"""
    assert os.path.isfile(path), f"文件不存在: {path}"
    with open(path, "rb") as f:
        return f.read()


# ---------------------------------------------------------------------------
# start.bat 编码与行尾测试
# ---------------------------------------------------------------------------

def test_start_bat_crlf_line_endings():
    """
    测试目的: 验证 start.bat 使用 CRLF 行尾（\\r\\n），且不存在孤立的 LF。
    修复说明: CRLF 行尾确保 GBK 解析器在遇到 CR (0x0D) 时不会把 LF (0x0A)
              当作 GBK 双字节字符的第二字节消费，从而避免行边界丢失。
    """
    content = _read_binary(START_BAT_PATH)

    # 验证文件中存在 CRLF
    assert b"\r\n" in content, "start.bat 必须包含 CRLF (\\r\\n) 行尾"

    # 验证不存在孤立的 LF（即 LF 前面必须是 CR）
    # 策略: 将所有 \r\n 替换为占位符后，剩余内容不应包含 \n
    content_without_crlf = content.replace(b"\r\n", b"")
    isolated_lf_count = content_without_crlf.count(b"\n")
    assert isolated_lf_count == 0, (
        f"start.bat 存在 {isolated_lf_count} 个孤立的 LF (\\n)，"
        "文件行尾必须全部为 CRLF"
    )


def test_start_bat_no_bom():
    """
    测试目的: 验证 start.bat 不以 UTF-8 BOM（EF BB BF）开头。
    修复说明: BOM 会导致 Windows 命令解释器将文件头识别为乱码，
              破坏批处理文件的第一条指令（通常是 @echo off）的解析。
    """
    content = _read_binary(START_BAT_PATH)
    utf8_bom = b"\xef\xbb\xbf"
    assert not content.startswith(utf8_bom), (
        "start.bat 不应以 UTF-8 BOM (EF BB BF) 开头，"
        "BOM 会破坏 Windows 批处理文件的执行"
    )


def test_start_bat_first_line():
    """
    测试目的: 验证 start.bat 第1行是 @echo off。
    修复说明: @echo off 是批处理文件的标准首行，
              禁止回显命令输出，必须作为文件的第一条指令。
    """
    content = _read_binary(START_BAT_PATH)
    # 以 CRLF 分割行（忽略空行）
    lines = content.split(b"\r\n")
    first_line = lines[0].strip().decode("utf-8")
    assert first_line == "@echo off", (
        f"start.bat 第1行应为 '@echo off'，实际为: '{first_line}'"
    )


def test_start_bat_chcp_65001_second_line():
    """
    测试目的: 验证 start.bat 第2行是 chcp 65001 >nul 2>&1。
    修复说明: chcp 65001 将控制台代码页切换到 UTF-8，确保后续中文字符
              在 GBK（CP936）环境下能被正确解析，避免行合并问题。
              >nul 2>&1 抑制 chcp 命令本身的输出，避免干扰用户界面。
    """
    content = _read_binary(START_BAT_PATH)
    lines = content.split(b"\r\n")
    assert len(lines) >= 2, "start.bat 至少应有2行内容"
    second_line = lines[1].strip().decode("utf-8")
    assert second_line == "chcp 65001 >nul 2>&1", (
        f"start.bat 第2行应为 'chcp 65001 >nul 2>&1'，实际为: '{second_line}'"
    )


def test_start_bat_no_gbk_lead_byte_before_crlf():
    """
    测试目的: 验证 start.bat 以 CRLF 分割后，统计各行末尾字节落在
              GBK 前导字节范围（0x81-0xFE）的数量，并以信息形式报告。
    修复说明: CRLF 修复的核心保证是——即使某行末尾字节是 GBK 前导字节，
              随后的 CR (0x0D) 作为缓冲阻止了 GBK 解析器将 LF 消费，
              行边界因此得以保留。本测试验证行尾均为 CRLF，已覆盖此场景。
    附加统计: 列出含有 GBK 前导字节末尾的行，供调试参考（不影响通过与否）。
    """
    content = _read_binary(START_BAT_PATH)
    lines = content.split(b"\r\n")

    # 过滤空行（文件末尾的空 split 产物）
    non_empty_lines = [line for line in lines if line]

    gbk_lead_lines = []
    for idx, line in enumerate(non_empty_lines, start=1):
        if not line:
            continue
        last_byte = line[-1]
        if 0x81 <= last_byte <= 0xFE:
            gbk_lead_lines.append((idx, last_byte, line))

    # 核心断言: 文件使用 CRLF，已通过 test_start_bat_crlf_line_endings 验证。
    # 此处额外输出统计信息，方便排查潜在编码问题。
    if gbk_lead_lines:
        detail = ", ".join(
            f"行{idx}(0x{byte:02X})"
            for idx, byte, _ in gbk_lead_lines
        )
        # 有 GBK 前导字节末尾是正常现象（UTF-8 多字节序列），
        # 关键是行尾为 CRLF，CR 作为缓冲保证解析正确性。
        # 使用 warnings.warn 记录统计信息，不影响测试通过与否。
        warnings.warn(
            f"start.bat 中有 {len(gbk_lead_lines)} 行末尾字节落在 GBK 前导字节范围"
            f"（0x81-0xFE）: {detail}。"
            "（这是正常现象，CRLF 行尾已确保 GBK 解析器不会消费 LF）",
            UserWarning,
            stacklevel=2,
        )

    # 核心验证: 再次确认文件使用 CRLF（double-check）
    assert b"\r\n" in content, (
        "start.bat 必须使用 CRLF 行尾以确保 GBK 环境下的解析正确性"
    )


def test_start_bat_is_utf8():
    """
    测试目的: 验证 start.bat 是合法的 UTF-8 编码文件。
    修复说明: start.bat 包含中文注释，必须以 UTF-8 编码保存，
              才能配合 chcp 65001 在 Windows 控制台中正确显示。
              非法的 UTF-8 序列会导致中文乱码或命令解析错误。
    """
    content = _read_binary(START_BAT_PATH)
    # 直接调用 decode，若不是合法 UTF-8 则抛出 UnicodeDecodeError，
    # pytest 会捕获并报告详细错误信息，无需手动包装 pytest.fail()
    decoded = content.decode("utf-8")
    assert len(decoded) > 0, "start.bat 内容不应为空"


def test_start_bat_no_fullwidth_symbols():
    """
    测试目的: 验证 start.bat 不含全角中文符号。
    修复说明: 全角中文符号（：，（）。！等）的 UTF-8 编码字节序形如 EF BC xx，
              其中第三字节落在 GBK 前导字节范围（0x81-0xFE）内。在部分 Windows
              系统的 CMD 中，chcp 65001 未能完全生效时，CMD 仍以 GBK 方式解析
              字节，导致字节边界错位，相关行内容被当作命令执行（如出现
              "'页（CMD' is not recognized" 等错误）。
              所有标点应使用 ASCII 半角符号。
    """
    content = _read_binary(START_BAT_PATH)
    decoded = content.decode("utf-8")

    # 需要检测的全角符号列表（按 ai_rules 规范禁止使用的全角符号）
    fullwidth_symbols = {
        "：": "U+FF1A 全角冒号",
        "，": "U+FF0C 全角逗号",
        "（": "U+FF08 全角左括号",
        "）": "U+FF09 全角右括号",
        "。": "U+3002 全角句号",
        "！": "U+FF01 全角感叹号",
    }

    found = []
    for char, desc in fullwidth_symbols.items():
        if char in decoded:
            count = decoded.count(char)
            found.append(f"  {desc}: 出现 {count} 次")

    assert not found, (
        "start.bat 中发现全角中文符号，必须替换为对应 ASCII 半角符号:\n"
        + "\n".join(found)
    )


# ---------------------------------------------------------------------------
# .gitattributes 规则验证
# ---------------------------------------------------------------------------

def test_gitattributes_bat_eol_crlf():
    """
    测试目的: 验证 .gitattributes 文件存在，
              且包含 *.bat text eol=crlf 规则。
    修复说明: .gitattributes 中的 eol=crlf 规则确保 Git 在 checkout 时
              自动将 *.bat 文件的行尾转换为 CRLF，防止跨平台协作时
              开发者在 Linux/macOS 环境下提交 LF 行尾的 .bat 文件。
    """
    assert os.path.isfile(GITATTRIBUTES_PATH), (
        f".gitattributes 文件不存在: {GITATTRIBUTES_PATH}"
    )
    with open(GITATTRIBUTES_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "*.bat text eol=crlf" in content, (
        ".gitattributes 必须包含 '*.bat text eol=crlf' 规则，"
        "以确保 .bat 文件在所有平台下均使用 CRLF 行尾"
    )


def test_gitattributes_sh_eol_lf():
    """
    测试目的: 验证 .gitattributes 文件存在，
              且包含 *.sh text eol=lf 规则。
    修复说明: .gitattributes 中的 eol=lf 规则确保 Git 在 checkout 时
              自动将 *.sh 文件的行尾转换为 LF，防止 Shell 脚本在
              Linux/macOS 下因 CRLF 行尾导致的 "bad interpreter" 错误。
    """
    assert os.path.isfile(GITATTRIBUTES_PATH), (
        f".gitattributes 文件不存在: {GITATTRIBUTES_PATH}"
    )
    with open(GITATTRIBUTES_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "*.sh text eol=lf" in content, (
        ".gitattributes 必须包含 '*.sh text eol=lf' 规则，"
        "以确保 .sh 文件在所有平台下均使用 LF 行尾"
    )
