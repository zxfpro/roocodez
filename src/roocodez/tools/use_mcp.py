import json
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `formatResponse.toolError` and `formatResponse.invalidMcpToolArgumentError`
# Re-using previous simple mocks.
def format_tool_error_mock(message: str) -> str:
    """Mocks formatResponse.toolError."""
    return f"Error: {message}"

def format_invalid_mcp_tool_argument_error_mock(server_name: str, tool_name: str) -> str:
    """Mocks formatResponse.invalidMcpToolArgumentError."""
    return f"Invalid JSON arguments for tool '{tool_name}' on server '{server_name}'."

# Mock for `processToolContent`: Simulates extracting text from MCP tool results.
# The original `toolResult` structure is complex (e.g., `content` array with `text` and `resource` types).
# This mock simplifies it to just extract 'text' content.
def process_tool_content_mock(tool_result: Optional[Dict[str, Any]]) -> str:
    """
    STUB: Mocks processToolContent.
    Simplifies the processing of MCP tool results to extract text content.
    """
    if not tool_result or 'content' not in tool_result or not isinstance(tool_result['content'], list):
        return ""
    
    extracted_texts = []
    for item in tool_result['content']:
        if isinstance(item, dict) and item.get('type') == 'text' and 'text' in item:
            extracted_texts.append(item['text'])
        elif isinstance(item, dict) and item.get('type') == 'resource' and 'resource' in item:
            # For resource types, just stringify the non-blob parts.
            # This is a simplification; a real agent might need to handle resources differently.
            resource_copy = {k: v for k, v in item['resource'].items() if k != 'blob'}
            extracted_texts.append(json.dumps(resource_copy, indent=2))
    
    return "\n\n".join(filter(None, extracted_texts))

# STUB for `cline.providerRef.deref()?.getMcpHub()?.callTool`
# This is a **CRITICAL STUB** because `McpHub` is an internal component
# of the original TypeScript application, likely managing communication
# with external "micro-credentialing providers" (MCPs).
#
# A Llama-Index `FunctionTool` cannot directly interact with such external
# or proprietary systems without a dedicated Python client/SDK for that system.
#
# This stub will simulate a successful or failed MCP tool call based on
# some simple logic (e.g., if tool_name is "error_tool", simulate an error).
#
# TODO: For a real-world scenario, this would need to be replaced with actual
# Python client code for the MCP system, or an API call that interacts with it.
def call_mcp_tool_stub(
    server_name: str,
    tool_name: str,
    arguments: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    STUB: Mocks the call to an external MCP tool.
    This is a placeholder for actual integration with an MCP system.
    Simulates a response based on `tool_name`.\n
    """
    print(f"STUB: Simulating MCP tool call: server='{server_name}', tool='{tool_name}', args={arguments}")

    if tool_name == "error_tool":
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Simulated error when calling {tool_name}."}]
        }
    elif tool_name == "get_user_info":
        user_id = arguments.get("user_id", "default_user") if arguments else "default_user"
        return {
            "isError": False,
            "content": [
                {"type": "text", "text": f"User info for {user_id}:"},
                {"type": "resource", "resource": {"name": "user_data.json", "data": {"id": user_id, "name": "John Doe", "email": f"{user_id}@example.com"}, "blob": "..."}}
            ]
        }
    elif tool_name == "list_available_tools":
        return {
            "isError": False,
            "content": [
                {"type": "text", "text": "Available tools on this server:"},
                {"type": "resource", "resource": {"name": "tools.json", "data": [{"name": "get_user_info", "description": "Retrieve user details"}, {"name": "update_status", "description": "Update user status"}], "blob": "..."}}
            ]
        }
    else:
        # Default successful response
        return {
            "isError": False,
            "content": [{"type": "text", "text": f"Successfully called MCP tool '{tool_name}' on server '{server_name}' with arguments: {arguments}"}]
        }


# --- Pydantic BaseModel for Tool Parameters ---

class UseMcpToolToolParams(BaseModel):
    """Parameters for the use_mcp_tool."""
    server_name: str = Field(
        ...,
        description=(
            "The name of the MCP (Micro-Credentialing Provider) server to interact with. "
            "This identifies the specific external service or platform."
        ),
    )
    tool_name: str = Field(
        ...,
        description=(
            "The name of the specific tool or API endpoint provided by the MCP server "
            "that should be invoked (e.g., `get_user_profile`, `create_resource`)."
        ),
    )
    arguments: Optional[str] = Field(
        None,
        description=(
            "Optional. A JSON string representing a dictionary of arguments to pass to the MCP tool. "
            "This must be a valid JSON string (e.g., '{\"user_id\": \"123\", \"status\": \"active\"}'). " # Corrected line
            "Ensure all double quotes within the JSON string are properly escaped if used inside another string."
        ),
    )

# --- Python Tool Logic ---

def use_mcp_tool_function(server_name: str, tool_name: str, arguments: Optional[str] = None) -> str:
    """
    Invokes a specific tool or API endpoint on a designated MCP (Micro-Credentialing Provider) server.

    This tool acts as a bridge to external services, allowing the agent to perform operations
    beyond its local environment, such as managing user profiles, interacting with external APIs,
    or retrieving specialized data from connected platforms.

    Args:
        server_name (str): The name of the MCP server to connect to (e.g., "GitHub_MCP", "Jira_MCP").
        tool_name (str): The specific tool or function to call on that server (e.g., "get_issue_details", "create_pull_request").
        arguments (str, optional): A JSON string containing key-value pairs of arguments
                                   required by the `tool_name`. For example:
                                   `'{"issue_id": "BUG-123", "status": "resolved"}'`.
                                   Must be a valid JSON string.

    Returns:
        str: A formatted string containing the result of the MCP tool execution,
             or an error message if the call failed (e.g., invalid arguments,
             server error, or tool not found). The output may include text and
             JSON representations of resources.
    """
    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (`cline.consecutiveMistakeCount`, `cline.recordToolError`,
    # `cline.ask`, `cline.say`, `cline.providerRef`, `cline.lastMessageTs`, `t`).
    # No `block.partial` handling.

    parsed_arguments: Optional[Dict[str, Any]] = None
    if arguments:
        try:
            parsed_arguments = json.loads(arguments)
            if not isinstance(parsed_arguments, dict):
                return format_tool_error_mock(
                    f"Arguments for tool '{tool_name}' on server '{server_name}' must be a valid JSON object (dictionary)."
                )
        except json.JSONDecodeError as e:
            # Corrected error message formatting for JSON example
            return format_tool_error_mock(
                f"Invalid JSON string provided for 'arguments': {e}. "
                f"Ensure the string is valid JSON, e.g., '{{\"key\": \"value\"}}'." # Corrected line
            )
    
    # Simulate the MCP tool call using the stub
    # In a real scenario, this would be replaced by actual client calls to the MCP system.
    tool_result = call_mcp_tool_stub(server_name, tool_name, parsed_arguments)

    if not tool_result:
        return format_tool_error_mock("No response from MCP server or tool execution failed internally.")
    
    output_text = process_tool_content_mock(tool_result)

    if tool_result.get("isError", False):
        return f"Error: MCP Tool '{tool_name}' on server '{server_name}' failed.\\nDetails:\\n{output_text or 'No specific error details provided.'}"
    else:
        return f"MCP Tool '{tool_name}' on server '{server_name}' executed successfully.\\nResult:\\n{output_text or '(No specific output)'}"

# --- FunctionTool Instantiation ---

use_mcp_tool = FunctionTool.from_defaults(
    fn=use_mcp_tool_function,
    name="use_mcp_tool",
    description=(
        "Invokes a specific tool or API endpoint on a designated MCP (Micro-Credentialing Provider) server. "
        "This tool acts as a bridge to external services, allowing the agent to perform operations "
        "beyond its local environment, such as managing user profiles, interacting with external APIs, "
        "or retrieving specialized data from connected platforms. "
        "Use this tool when you need to interact with a specific external system or use a functionality "
        "that is not directly available via other file system or shell tools."
        "\\n\\nArgs:"
        "\\n- `server_name` (str): The name of the MCP server to interact with (e.g., `GitHub_MCP`, `Jira_MCP`). "
        "  This identifies the specific external service or platform."
        "\\n- `tool_name` (str): The name of the specific tool or API endpoint provided by the MCP server "
        "  that should be invoked (e.g., `get_user_profile`, `create_resource`, `list_issues`)."
        "\\n- `arguments` (str, optional): A JSON string representing a dictionary of arguments to pass to the MCP tool. "
        "  This must be a valid JSON string (e.g., `{\\\"user_id\\\": \\\"123\\\", \\\"status\\\": \\\"active\\\"}`). " # Corrected example in description
        "  Ensure all double quotes within the JSON string are properly escaped if used inside another string. "
        "  If the tool requires no arguments, omit this parameter or pass `null`."
        "\\n\\nReturns:"
        "\\n  A formatted string containing the result of the MCP tool execution, "
        "  or an error message if the call failed (e.g., invalid arguments, "
        "  server error, or tool not found). The output may include text and "
        "  JSON representations of resources."
        "\\n\\n**Important Note on Implementation:** This Python tool provides a **stubbed implementation** "
        "for the `call_mcp_tool` function. In a real-world scenario, this stub would need to be replaced "
        "with actual Python client code that interacts with the specific MCP system via its API. "
        "The current stub simulates responses based on the `tool_name` and does not connect to any live external service."
        "\\n\\nExample Usage:"
        '\\n`{"tool_code": "use_mcp_tool(server_name=\\"GitHub_MCP\\", tool_name=\\"list_issues\\", arguments=\\"{\\\\\\"repo\\\\\\": \\\\\\\"my-project\\\\\\", \\\\\\\"state\\\\\\": \\\\\\\"open\\\\\\\"}\\\\")"`'
        '\\n`{"tool_code": "use_mcp_tool(server_name=\\"Jira_MCP\\", tool_name=\\"get_issue_details\\", arguments=\\"{\\\\\\"issue_id\\\\\\": \\\\\\\"PROJ-456\\\\\\\"}\\\\")"`'
        '\\n`{"tool_code": "use_mcp_tool(server_name=\\"Internal_API\\", tool_name=\\"get_service_status\\")"`'
    ),
    fn_schema=UseMcpToolToolParams,
)