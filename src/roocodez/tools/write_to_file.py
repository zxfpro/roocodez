import os
from typing import Optional
from pathlib import Path

from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- 1. 定义工具输入模式 (Schema) ---
# 对应 TypeScript 的 WriteToFileToolUse.params
class WriteToFileParams(BaseModel):
    """Parameters for the write_to_file tool."""
    path: str = Field(..., description="The relative or absolute path to the file to write.")
    content: str = Field(..., description="The content to write to the file.")
    # line_count 在这里作为信息性字段，实际写入时不会强制检查
    line_count: Optional[int] = Field(None, description="Predicted number of lines in the content. For information only.")

# --- 2. 实现工具的实际逻辑 ---
def write_to_file_tool_func(
    path: str,
    content: str,
    line_count: Optional[int] = None,
) -> str:
    """
    Writes content to a specified file.

    Args:
        path (str): The path to the file (relative or absolute).
        content (str): The content to write to the file.
        line_count (Optional[int]): Predicted number of lines (for information).
    Returns:
        str: A message indicating the success or failure of the write operation.
    """
    try:
        # 简化版：模拟 content 预处理（移除常见代码块标记）
        stripped_content = content.strip()
        if stripped_content.startswith("```") and stripped_content.endswith("```"):
            lines = stripped_content.split('\n')
            if len(lines) > 2: # 至少有 ```, content, ```
                # 假设第一行是语言标识或空，移除首行和末行
                content = '\n'.join(lines[1:-1])

        absolute_path = Path(path).resolve() # 获取绝对路径

        # 确保目标目录存在
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(content)

        actual_line_count = len(content.split('\n'))
        return (
            f"Successfully wrote content to {absolute_path}. "
            f"Actual lines: {actual_line_count}. "
            f"Predicted lines (from LLM): {line_count if line_count is not None else 'N/A'}."
        )

    except Exception as e:
        return f"Error writing to file {path}: {e}"

# --- 3. 包装成 Llama-Index FunctionTool ---
write_to_file_tool = FunctionTool.from_defaults(
    fn=write_to_file_tool_func,
    name="write_to_file",
    description=(
        "Writes content to a specified file. "
        "Useful for creating new files or overwriting existing ones. "
        "Always provide both 'path' and 'content' parameters. "
        "The 'path' can be relative or absolute. "
        "The 'line_count' parameter is optional and provides the predicted number of lines."
    ),
    fn_schema=WriteToFileParams,
)

# 现在你可以将 `write_to_file_tool` 添加到你的 Agent 中，例如：
# from llama_index.core.agent import ReActAgent
# agent = ReActAgent.from_tools(tools=[write_to_file_tool, ...], llm=...)