import os
import re
import hashlib
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from llama_index.core.tools import FunctionTool

# --- Type Definitions (Mimicking TypeScript Enums/Types) ---
TodoStatus = Literal["pending", "in_progress", "completed"]

class TodoItem(BaseModel):
    id: str = Field(..., description="Unique identifier for the todo item.")
    content: str = Field(..., description="The content or description of the todo item.")
    status: TodoStatus = Field("pending", description="The status of the todo item: 'pending', 'in_progress', or 'completed'.")

# --- Helper Functions (Simulating original TS functions) ---

def normalize_status(status: Optional[str]) -> TodoStatus:
    """Normalizes a string status to a valid TodoStatus."""
    if status == "completed":
        return "completed"
    if status == "in_progress":
        return "in_progress"
    return "pending"

def parse_markdown_checklist(md: str) -> List[TodoItem]:
    """
    Parses a markdown checklist string into a list of TodoItem objects.
    This is a functional simulation of the original TypeScript `parseMarkdownChecklist`.
    """
    if not isinstance(md, str):
        return []

    lines = [line.strip() for line in md.splitlines() if line.strip()]
    todos: List[TodoItem] = []

    for line in lines:
        match = re.match(r"^\s*\[\s*([ xX\-\~])\s*\]\s+(.+)$", line)
        if not match:
            continue

        status: TodoStatus = "pending"
        status_char = match.group(1)
        if status_char in ("x", "X"):
            status = "completed"
        elif status_char in ("-", "~"):
            status = "in_progress"

        content = match.group(2).strip()
        # Simulate crypto.createHash("md5").update(content + status).digest("hex")
        item_id = hashlib.md5((content + status).encode('utf-8')).hexdigest()

        todos.append(TodoItem(id=item_id, content=content, status=status))
    return todos

def todo_list_to_markdown(todos: List[TodoItem]) -> str:
    """
    Converts a list of TodoItem objects into a markdown checklist string.
    This is a functional simulation of the original TypeScript `todoListToMarkdown`.
    """
    return "\n".join([
        f"[x] {t.content}" if t.status == "completed" else
        f"[-] {t.content}" if t.status == "in_progress" else
        f"[ ] {t.content}"
        for t in todos
    ])

# --- Pydantic BaseModel for the tool's input parameters ---
class UpdateTodoListParams(BaseModel):
    # The original `todosRaw` was a string that could be markdown or JSON.
    # For a FunctionTool, it's best to expect a structured input if possible.
    # However, to mimic the original behavior of parsing markdown, we keep it as a string.
    todos: str = Field(..., description=(
        "A string representing the updated todo list. This should be provided as a markdown checklist string. "
        "Each line represents a todo item, prefixed with a checkbox: "
        "`[ ]` for pending, `[-]` for in-progress, `[x]` for completed. "
        "Example: `[ ] Task 1\\n[-] Task 2 (in progress)\\n[x] Task 3 (completed)`."
    ))

# --- Python tool logic function ---
def update_todo_list_tool_py(todos: str) -> str:
    """
    Updates the current todo list for the task based on the provided markdown checklist.

    This tool allows the agent to manage its ongoing tasks and objectives.
    It can add new items, mark existing items as in-progress or completed,
    or remove items from the list.

    Args:
        todos (str): A string representing the updated todo list in markdown checklist format.
                     Each line should be a todo item, prefixed with:
                     - `[ ]` for a pending item
                     - `[-]` for an item in progress
                     - `[x]` for a completed item
                     Example: "[ ] Plan project\n[-] Write code\n[x] Test module"

    Returns:
        str: A message indicating the success or failure of the update operation.
             On success, it returns the updated todo list in markdown format.
             On failure, it returns an error message.

    Example:
        To update the todo list to include new items and mark one as completed:
        {"tool_code": "updateTodoList", "todos": "[ ] Research new features\\n[-] Implement core logic\\n[x] Fix bug #123"}
    """
    try:
        # 1. Parse the incoming markdown string into TodoItem objects
        parsed_todos: List[TodoItem] = parse_markdown_checklist(todos)

        # 2. Normalize statuses and create validated TodoItem objects
        normalized_todos: List[TodoItem] = []
        for t_item in parsed_todos:
            try:
                # Re-validate using Pydantic to ensure all fields are correct
                normalized_todos.append(TodoItem(
                    id=t_item.id,
                    content=t_item.content,
                    status=normalize_status(t_item.status) # Ensure status is valid TodoStatus
                ))
            except ValidationError as e:
                # If individual item validation fails, report it
                return f"Error: Invalid todo item format detected: {e}"

        # 3. Simulate the approval process.
        # In a real Llama-Index setup, the agent framework handles approval/confirmation
        # outside the tool's atomic execution. This tool assumes approval is granted
        # if it's called. The original `askApproval` is an external interaction.
        # The `userEdited` flag and `block.partial` logic are also part of the
        # host environment's interaction flow, not the tool's atomic function.

        # 4. Simulate updating the todo list
        # In the original TS, `cline.todoList` was updated.
        # For a FunctionTool, we return the result, implying an external system
        # will consume this result and update its internal state (like a database or memory).
        # We don't have a `cline` object here.

        # Convert the normalized list back to markdown for the output
        updated_md = todo_list_to_markdown(normalized_todos)

        # Simulate success output
        # The original had `isTodoListChanged` logic, but for a FunctionTool,
        # we always return the new state if successful.
        return f"Todo list updated successfully:\n\n{updated_md}"

    except Exception as e:
        # Simulate error handling
        return f"Error updating todo list: {str(e)}"

# --- FunctionTool instantiation ---
update_todo_list_function_tool = FunctionTool.from_defaults(
    fn=update_todo_list_tool_py,
    name="updateTodoList",
    description=(
        "Updates the current todo list for the task based on the provided markdown checklist. "
        "This tool allows the agent to manage its ongoing tasks and objectives. "
        "It can add new items, mark existing items as in-progress or completed, "
        "or remove items from the list.\\n"
        "Args:\\n"
        r"  todos (str): A string representing the updated todo list in markdown checklist format. "
        "               Each line should be a todo item, prefixed with: "
        "               `[ ]` for a pending item, "
        "               `[-]` for an item in progress, "
        "               `[x]` for a completed item. "
        "               Example: `[ ] Plan project\\n[-] Write code\\n[x] Test module`\\n"
        "Returns:\\n"
        "  str: A message indicating the success or failure of the update operation. "
        "       On success, it returns the updated todo list in markdown format. "
        "       On failure, it returns an error message.\\n"
        "Example:\\n"
        r"  To update the todo list to include new items and mark one as completed:"
        r"  ```json"
        r'  {"tool_code": "updateTodoList", "todos": "[ ] Research new features\\n[-] Implement core logic\\n[x] Fix bug #123"}'
        r"  ```"
    ),
    fn_schema=UpdateTodoListParams,
)