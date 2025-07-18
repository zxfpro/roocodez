import json
from typing import Optional, Any, Dict, List, Tuple
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `formatResponse.toolResult` and `formatResponse.toolError`
# Re-using previous simple mocks.
def format_tool_error_mock(message: str) -> str:
    """Mocks formatResponse.toolError."""
    return f"Error: {message}"

def format_tool_result_mock(content: str, images: Optional[List[str]] = None) -> str:
    """Mocks formatResponse.toolResult."""
    if images:
        return f"Result: {content}\\n(Note: {len(images)} images were also retrieved, but not directly rendered in this text output.)"
    return f"Result: {content}"

# Mock for `formatResponse.imageBlocks`: Returns empty list as images are not directly handled by FunctionTool
def format_image_blocks_mock(images: Optional[List[str]]) -> List[Dict[str, Any]]:
    """
    STUB: Mocks formatResponse.imageBlocks.
    Since Llama-Index FunctionTool typically returns text, image blocks are not directly supported.
    """
    return []

# STUB for `TelemetryService.instance.captureTaskCompleted`:
# Telemetry is host-specific and should be stripped.
def capture_task_completed_stub(task_id: str):
    """STUB: Mocks TelemetryService.instance.captureTaskCompleted."""
    print(f"STUB: Telemetry captured task {task_id} as completed.")

# STUB for `cline.sayAndCreateMissingParamError`:
# Replaces specific error messages with generic ones.
def say_and_create_missing_param_error_stub(tool_name: str, param_name: str) -> str:
    """STUB: Mocks cline.sayAndCreateMissingParamError."""
    return f"Error: Missing required parameter '{param_name}' for tool '{tool_name}'."


# --- Pydantic BaseModel for Tool Parameters ---

class AttemptCompletionToolParams(BaseModel):
    """Parameters for the attempt_completion tool."""
    result: str = Field(
        ...,
        description=(
            "The final result or summary of the task that the agent has completed. "
            "This should be a comprehensive description of the work done, findings, "
            "or changes made. Example: `result=\\\"Successfully refactored module X. "
            "All tests pass.\\\"`"
        ),
    )
    command: Optional[str] = Field(
        None,
        description=(
            "Optional. A command string that the user is expected to execute after the completion. "
            "This is typically a suggestion for the next step outside the agent's direct control, "
            "e.g., `git push`, `npm run deploy`. If provided, the agent will suggest this to the user."
        ),
    )

# --- Python Tool Logic ---

def attempt_completion_function(result: str, command: Optional[str] = None) -> str:
    """
    Signals that the agent believes it has completed the current task and provides a final result or summary.

    This tool is used to present the outcome of the agent's work to the user.
    It can also suggest a follow-up command for the user to execute manually.

    Args:
        result (str): A detailed summary of the task's outcome, changes made,
                      or information gathered. This is the primary output of the tool.
        command (str, optional): An optional shell command that the agent suggests
                                 the user run as a next step. This command is presented
                                 to the user for manual execution, not executed by the agent.

    Returns:
        str: A formatted string indicating the completion of the task, including
             the result summary and any suggested command.
             If the `result` parameter is missing, an error message is returned.
    """
    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (`cline.consecutiveMistakeCount`, `cline.recordToolError`,
    # `cline.ask`, `cline.say`, `cline.parentTask`, `cline.providerRef`, `cline.lastMessageTs`,
    # `cline.emit`, `cline.getTokenUsage`, `cline.toolUsage`, `cline.userMessageContent`,
    # `askFinishSubTaskApproval`, `toolDescription`).
    # No `block.partial` handling.
    # No `TelemetryService` calls.

    if not result:
        # This check is technically redundant due to Pydantic Field(..., description=...)
        # but kept for explicit clarity matching original logic.
        return say_and_create_missing_param_error_stub("attempt_completion", "result")

    # Simulate task completion actions stripped from host environment
    capture_task_completed_stub("simulated_task_id") # Using a dummy task_id

    response_message = f"Task completed successfully.\\nResult: {result}"
    if command:
        response_message += f"\\nSuggested next command for user: `{command}`"

    # The original tool had complex logic for user approval and feedback loops.
    # For a Llama-Index FunctionTool, the return value is the "tool result".
    # We consolidate the final output into a single string.
    # The agent is responsible for handling the "approval" flow before calling this tool,
    # and for interpreting the final result.

    return format_tool_result_mock(response_message)

# --- FunctionTool Instantiation ---

attempt_completion_tool = FunctionTool.from_defaults(
    fn=attempt_completion_function,
    name="attempt_completion",
    description=(
        "Signals that the agent believes it has completed the current task and provides a final result or summary. "
        "This tool is used to present the outcome of the agent's work to the user. "
        "It can also suggest a follow-up command for the user to execute manually outside the agent's control. "
        "This is the final step for most tasks, indicating that the agent has finished its objective."
        "\\n\\nArgs:"
        "\\n- `result` (str): A detailed summary of the task's outcome, findings, or changes made. "
        "  This is the primary output of the tool and should comprehensively describe the completed work. "
        "  Example: `result=\\\"Successfully implemented feature X. All unit tests pass and code is committed.\\\"`."
        "\\n- `command` (str, optional): An optional shell command that the agent suggests the user run "
        "  as a next step. This command is presented to the user for manual execution "
        "  (e.g., `git push`, `npm run deploy`), not executed by the agent itself. "
        "  Example: `command=\\\"git push origin main\\\"`."
        "\\n\\nReturns:"
        "\\n  A string message indicating the successful completion of the task, including "
        "  the detailed result summary and any suggested follow-up command for the user."
        "\\n\\n**Important Note on Implementation:** This Python tool is designed to be the final reporting step. "
        "It does not handle real-time user interaction, approval flows, or background processes "
        "as the original TypeScript version might. The agent is responsible for managing "
        "these aspects externally before calling this tool. The `command` parameter is purely "
        "informational for the user; the agent does not execute it."
        "\\n\\nExample Usage:"
        '\\n`{"tool_code": "attempt_completion(result=\\"All files have been updated and validated.\\")"}`'
        '\\n`{"tool_code": "attempt_completion(result=\\"New user authentication module is deployed.\\", command=\\"npm run deploy-prod\\")"}`'
    ),
    fn_schema=AttemptCompletionToolParams,
)