import os
import re
from typing import Optional, List
from pathlib import Path

from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- 模拟 regexSearchFiles 函数 ---
# 这是一个存根，你在实际应用中可能需要更高效的实现（如调用外部ripgrep）
def _perform_regex_search_files(
    start_dir: str,
    search_regex: str,
    file_pattern: Optional[str] = None,
    # roo_ignore_controller: Any = None # 忽略这里的cline特定控制器
) -> str:
    """
    Simulates searching files using regex.
    Returns results in a format similar to ripgrep or original TS.
    Example output: "file_path:line_number:matched_text"
    """
    results: List[str] = []
    
    # Compile regex for content search
    try:
        content_re = re.compile(search_regex)
    except re.error as e:
        return f"Error: Invalid regex pattern '{search_regex}': {e}"

    # Compile regex for file pattern (if provided)
    file_pattern_re = None
    if file_pattern:
        try:
            # For file patterns, often they are glob-like or simple regex
            # Convert glob to regex if necessary, or assume direct regex
            file_pattern_re = re.compile(file_pattern)
        except re.error as e:
            return f"Error: Invalid file pattern regex '{file_pattern}': {e}"

    abs_start_dir = Path(start_dir).resolve()

    for root, _, files in os.walk(abs_start_dir):
        for file in files:
            file_path = Path(root) / file
            
            # Skip if it's a "binary" file or matches common ignore patterns
            # (Simplistic check, a real one would use .gitignore or .rooignore logic)
            if file_path.suffix.lower() in ['.pyc', '.git', '.DS_Store', '.log', '.bin', '.exe', '.dll']:
                continue

            # Check file pattern if provided
            if file_pattern_re and not file_pattern_re.search(file):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f):
                        if content_re.search(line):
                            relative_path = str(file_path.relative_to(abs_start_dir))
                            results.append(f"{relative_path}:{i + 1}:{line.strip()}")
            except Exception as e:
                # print(f"Warning: Could not read file {file_path}: {e}")
                pass # Silently ignore unreadable files or log
                
    if not results:
        return "No matches found."

    # Join results with newlines
    return "\n".join(results)

# --- 1. 定义工具输入模式 (Schema) ---
class SearchFilesParams(BaseModel):
    """Parameters for the search_files tool."""
    path: str = Field(
        ...,
        description=(
            "The directory path (relative or absolute) where the search should start. "
            "Use '.' for the current directory or a specific subdirectory name."
        )
    )
    regex: str = Field(
        ...,
        description=(
            "The regular expression to search for within the file contents. "
            "Example: 'myFunction\\(.*?\\)' to find calls to 'myFunction'."
        )
    )
    file_pattern: Optional[str] = Field(
        None,
        description=(
            "An optional regular expression to filter which file names to search. "
            "Only files whose names match this pattern will be searched. "
            "Example: '.*\\.py$' to search only Python files."
        )
    )

# --- 2. 实现工具的实际逻辑 ---
def search_files_tool_func(path: str, regex: str, file_pattern: Optional[str] = None) -> str:
    """
    Searches for files matching a regular expression within their content,
    optionally filtering by file name pattern, starting from a specified directory.

    Args:
        path (str): The starting directory path for the search.
        regex (str): The regular expression to search for within file contents.
        file_pattern (Optional[str]): An optional regular expression to filter file names.

    Returns:
        str: A string containing matching lines, formatted as 'file_path:line_number:matched_text',
             or a message indicating no matches found or an error.
    """
    try:
        # In the original TS, this would be `regexSearchFiles(cline.cwd, absolutePath, regex, filePattern, cline.rooIgnoreController)`
        # Here we use our simplified mock function.
        # Note: cline.cwd (current working directory) is usually the base for search.
        # For a simple tool, we'll assume the 'path' parameter is the actual start_dir.
        # If your agent has a global 'cwd' context, pass that instead.
        search_results = _perform_regex_search_files(path, regex, file_pattern)
        
        return search_results

    except Exception as e:
        # Simulate handleError
        return f"Error performing file search: {e}"

# --- 3. 包装成 Llama-Index FunctionTool ---
search_files_tool = FunctionTool.from_defaults(
    fn=search_files_tool_func,
    name="search_files",
    description=(
        "Searches for files within a specified directory whose content matches a given regular expression. "
        "Optionally, you can filter the files by their names using another regular expression. "
        "Results are returned as a list of 'file_path:line_number:matched_text' entries."
        "Parameters: 'path' (str, required, directory to start search), "
        "'regex' (str, required, content regular expression), "
        "'file_pattern' (str, optional, file name regular expression)."
        "Example: search for 'TODO' in all '.py' files within 'src' directory:"
        "search_files(path='src', regex='TODO', file_pattern='.*\\.py$')"
    ),
    fn_schema=SearchFilesParams,
)

# 你现在可以将 `search_files_tool` 添加到你的 Agent 中，例如：
# from llama_index.core.agent import ReActAgent
# agent = ReActAgent.from_tools(tools=[search_files_tool, ...], llm=...)


# # 示例使用 (仅供测试，通常由 Agent 内部调用)
# if __name__ == "__main__":
#     # 假设你已经配置了 Llama-Index LLM
#     from llama_index.core import Settings
#     from llama_index.llms.openai import OpenAI
#     Settings.llm = OpenAI(model="gpt-4-turbo-preview")

#     from llama_index.core.agent import ReActAgent
#     agent = ReActAgent.from_tools(tools=[search_files_tool], llm=Settings.llm, verbose=True)

#     # 创建一些测试文件
#     os.makedirs("test_search_dir/subdir", exist_ok=True)
#     with open("test_search_dir/file1.py", "w") as f:
#         f.write("import os\ndef hello_world():\n    print('Hello world from Python!')\n# TODO: Implement feature X")
#     with open("test_search_dir/file2.js", "w") as f:
#         f.write("console.log('Hello from JS');\n// TODO: Fix bug Y")
#     with open("test_search_dir/subdir/file3.txt", "w") as f:
#         f.write("This is a test file.\nAnother line.\nTODO: Check this.")
#     with open("test_search_dir/binary.bin", "wb") as f:
#         f.write(b"\x00\x01\x02\x03")

#     print("--- Query 1: Search for 'Hello' in Python files in test_search_dir ---")
#     response = agent.chat("Search for 'Hello' in Python files within the 'test_search_dir' directory.")
#     print(f"Agent response: {response}")

#     print("\n--- Query 2: Search for 'TODO' in all files in test_search_dir ---")
#     response = agent.chat("Find all 'TODO' comments in 'test_search_dir'.")
#     print(f"Agent response: {response}")

#     print("\n--- Query 3: Search for 'print' in text files in subdir ---")
#     response = agent.chat("Search for 'print' in '.txt' files inside 'test_search_dir/subdir'.")
#     print(f"Agent response: {response}")

#     print("\n--- Query 4: Search for something that doesn't exist ---")
#     response = agent.chat("Search for 'NONEXISTENT_KEYWORD' in 'test_search_dir'.")
#     print(f"Agent response: {response}")

#     # 清理测试文件
#     import shutil
#     shutil.rmtree("test_search_dir")