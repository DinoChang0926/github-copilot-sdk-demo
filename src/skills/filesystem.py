import os
import glob
from typing import List, Optional
from pydantic import BaseModel, Field
from copilot.tools import define_tool

# --- Parameter Models ---

class ListDirParams(BaseModel):
    path: str = Field(..., description="Absolute path or relative path to the workspace root to list.")

class ReadFileParams(BaseModel):
    path: str = Field(..., description="Absolute path to the file to read.")

class WriteFileParams(BaseModel):
    path: str = Field(..., description="Absolute path to the file to write.")
    content: str = Field(..., description="The content to write to the file.")

class FileSystemSkill:
    """
    Provides standard file system operations.
    """
    def __init__(self, workspace_root: str = "workspaces"):
        # We can enforce a jail here if we want, but for this demo let's stay flexible
        self.workspace_root = os.path.abspath(workspace_root)

    @define_tool(description="List files and directories in a given path.")
    def list_directory(self, params: ListDirParams) -> str:
        try:
            target_path = os.path.abspath(params.path)
            if not os.path.exists(target_path):
                return f"Error: Path '{target_path}' does not exist."
            
            items = os.listdir(target_path)
            # Add type info (File/Dir)
            result = []
            for item in items:
                full_path = os.path.join(target_path, item)
                type_str = "DIR" if os.path.isdir(full_path) else "FILE"
                result.append(f"[{type_str}] {item}")
            
            return "\n".join(result)
        except Exception as e:
            return f"Error listing directory: {e}"

    @define_tool(description="Read the text content of a file.")
    def read_file(self, params: ReadFileParams) -> str:
        try:
            target_path = os.path.abspath(params.path)
            if not os.path.exists(target_path):
                return f"Error: File '{target_path}' does not exist."
            
            with open(target_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return "Error: File is binary or not UTF-8 encoded."
        except Exception as e:
            return f"Error reading file: {e}"

    @define_tool(description="Write text content to a file (overwrites existing).")
    def write_file(self, params: WriteFileParams) -> str:
        try:
            target_path = os.path.abspath(params.path)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(params.content)
            return f"Successfully wrote to {target_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def get_tools(self):
        return [self.list_directory, self.read_file, self.write_file]
