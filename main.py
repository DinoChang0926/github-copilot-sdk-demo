#!/usr/bin/env python3
import asyncio
import os
import sys
from dotenv import load_dotenv
from copilot import CopilotClient
from src.multi_agent import MultiAgentTask
from src.skills.repository import RepositorySkill, CloneRepoParams

# Load environment variables
load_dotenv(override=True)

async def async_input(prompt: str) -> str:
    """Async wrapper for input() to avoid blocking the event loop excessively."""
    return await asyncio.to_thread(input, f"\n❓ [Clarifier] {prompt}\n> ")

async def main():
    try:
        print("Initializing GitHub Copilot Client (Multi-Agent Mode)...")
        print("Note: Ensure the standalone 'copilot' CLI is installed and in your PATH.")
        
        client = CopilotClient()
        try:
            # Start the client explicitly
            await client.start()
            
            task_runner = MultiAgentTask(client)
            
            print("\n✅ Multi-Agent System Ready! (Worker + Reviewer + Clarifier)")
            print("Enter your request below (or type 'exit' to quit).")
            
            print("\n🔍 Checking 'workspaces' directory for existing repositories...")
            os.makedirs("workspaces", exist_ok=True)
            existing_repos = [d for d in os.listdir("workspaces") if os.path.isdir(os.path.join("workspaces", d))]
            
            repo_url = None
            local_path = None
            
            print(f"Found {len(existing_repos)} existing repositories.")
            
            choices = []
            for i, repo in enumerate(existing_repos):
                choices.append(f"[{i+1}] {repo}")
            
            print("\nSelect a repository to work on:")
            for c in choices:
                print(c)
            print(f"[{len(choices)+1}] Clone a new repository URL")
            
            choice = input(f"\nEnter choice (1-{len(choices)+1}): ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(existing_repos):
                    selected_repo = existing_repos[idx]
                    local_path = os.path.abspath(os.path.join("workspaces", selected_repo))
                    print(f"\n📂 Selected: {local_path}")
                elif idx == len(existing_repos):
                    # Clone new
                    repo_input = input("📂 GitHub Repo URL: ").strip()
                    if repo_input:
                        repo_url = repo_input
                        print(f"⬇️ Cloning {repo_url}...")
                        try:
                            # Use RepositorySkill directly to clone
                            repo_skill = RepositorySkill()
                            result_msg = repo_skill.clone_repository(CloneRepoParams(repo_url=repo_url))
                            
                            # Parse content to find path (or modify skill to return path cleanly, but for now assuming standard structure)
                            # The skill returns a message string. Let's re-derive path or parse it.
                            # Skill logic: repo_name = params.repo_url.split("/")[-1].replace(".git", "")
                            repo_name = repo_url.split("/")[-1].replace(".git", "")
                            local_path = os.path.abspath(os.path.join("workspaces", repo_name))
                            
                            print(f"✅ Cloned to: {local_path}")
                            repo_url = None # Clear URL since we now have a local path
                        except Exception as e:
                            print(f"❌ Clone failed: {e}")
                            return
                else:
                    print("Invalid choice, defaulting to new URL.")
                    repo_input = input("📂 GitHub Repo URL: ").strip()
                    if repo_input:
                        repo_url = repo_input
            
            if not repo_url and not local_path:
                 print("No repository selected. Exiting.")
                 return

            print("\n✅ Target Locked. Ready for instructions.")

            # Get User Request Once
            while True:
                user_input = input("\n📝 User Request: ").strip()
                if user_input:
                    break
            
            print("\n[System] Starting Multi-Agent Task... (This may take a moment)")
            
            # Run the task
            result = await task_runner.run(user_input, repo_url=repo_url, local_repo_path=local_path, ask_user_func=async_input)
            
            print("\n" + "="*50)
            print("� FINAL RESULT")
            print("="*50)
            
            if result.success:
                print("\n✅ [SUCCESS] Task completed and passed review.")
                # Optional: Print the final code if it's not too long, or just say it's updated.
                # Since agents modify files directly now, we might not need to print code unless it's a snippet.
                if len(result.code) < 2000:
                   print(result.code)
                else:
                   print("(Code updated in files)")
            else:
                print("\n❌ [FAILED] Task failed to pass review after retries.")
                print(f"Last candidate code:\n{result.code[:500]}...")
        finally:
            # Ensure client is stopped
            await client.stop()

    except Exception as ex:
        print(f"\nProgram Error: {ex}")

if __name__ == "__main__":
    asyncio.run(main())
