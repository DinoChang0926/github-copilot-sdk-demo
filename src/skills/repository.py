import os
import shutil
import subprocess
from typing import Optional
from pydantic import BaseModel, Field
from copilot.tools import define_tool

# Define Parameter Models (Pydantic) for Schema Generation
class CloneRepoParams(BaseModel):
    repo_url: str = Field(..., description="The HTTPS URL of the GitHub repository to clone")
    target_name: Optional[str] = Field(None, description="Optional custom folder name for the cloned repo")

class RepositorySkill:
    """
    A skill set for managing Git repositories.
    """
    
    def __init__(self, workspace_root: str = "workspaces"):
        self.workspace_root = os.path.join(os.getcwd(), workspace_root)
        os.makedirs(self.workspace_root, exist_ok=True)

    @define_tool(description="Clones a GitHub repository to the workspace.")
    def clone_repository(self, params: CloneRepoParams) -> str:
        """
        Clones the specified repository. Returns the absolute path to the cloned directory.
        """
        repo_name = params.target_name or params.repo_url.split("/")[-1].replace(".git", "")
        target_dir = os.path.join(self.workspace_root, repo_name)
        
        # Simple cleanup for demo purposes
        if os.path.exists(target_dir):
            try:
                # Handle readonly files on Windows
                def on_rm_error(func, path, exc_info):
                    os.chmod(path, 0o777)
                    os.unlink(path)
                shutil.rmtree(target_dir, onerror=on_rm_error)
            except Exception as e:
                return f"Error cleaning up existing directory: {e}"

        try:
            print(f"[Skill:Repository] Cloning {params.repo_url}...")
            subprocess.check_call(
                ["git", "clone", params.repo_url, target_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return f"Successfully cloned environment to: {target_dir}\nYou can now read/write files in this directory."
        except subprocess.CalledProcessError as e:
            return f"Failed to clone repository: {e}"
        except Exception as e:
            return f"Unexpected error during clone: {e}"

    def get_tools(self):
        """Returns the list of tools provided by this skill."""
        return [self.clone_repository]
