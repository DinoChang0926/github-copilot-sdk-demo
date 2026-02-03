#!/usr/bin/env python3
import asyncio
from typing import Optional, List, Callable, Awaitable
from dataclasses import dataclass
from copilot import CopilotClient, MessageOptions, SessionEvent
from copilot.generated.session_events import SessionEventType
from src.skills.repository import RepositorySkill
from src.skills.filesystem import FileSystemSkill
from src.skills.clarification import ClarificationSkill

@dataclass
class AgentResult:
    success: bool
    code: str
    messages: List[str]  # History logs

class MultiAgentTask:
    def __init__(self, client: CopilotClient, model: str = "gpt-5 mini"):
        self.client = client
        self.model = model
        self.max_retries = 3

    def _setup_logging(self, session, agent_name: str):
        """Attaches a real-time logger to the session."""
        def on_event(event: SessionEvent):
            if event.type == SessionEventType.ASSISTANT_MESSAGE:
                # Stream the content
                print(event.data.content, end="", flush=True)
            elif event.type == SessionEventType.TOOL_EXECUTION_START:
                if getattr(event.data, 'name', None):
                    print(f"\n[{agent_name}] 🛠️  Using Tool: {event.data.name}")
            elif event.type == SessionEventType.SESSION_ERROR:
                print(f"\n[{agent_name}] ❌ Error: {event.data.message}")
            elif event.type == SessionEventType.TOOL_EXECUTION_COMPLETE:
                pass # Already logged start
        
        session.on(on_event)

    async def run(self, user_prompt: str, repo_url: Optional[str] = None, local_repo_path: Optional[str] = None, ask_user_func: Optional[Callable[[str], Awaitable[str]]] = None) -> AgentResult:
        """
        執行多代理人協作任務
        :param user_prompt: 使用者的需求
        :param repo_url: (可選) 要 Clone 的 Repo URL
        :param local_repo_path: (可選) 已存在的本地 Repo 路徑
        """
        logs = []
        final_requirements = user_prompt

        # --- Phase 0: Clarification (Event-Driven) ---
        if ask_user_func:
            logs.append("[Clarification] Starting clarification phase...")
            
            clarification_done = asyncio.Event()
            
            def on_requirements_ready(summary: str):
                nonlocal final_requirements
                final_requirements = summary
                clarification_done.set()
                
            # Initialize Skills
            repo_skill = RepositorySkill()
            fs_skill = FileSystemSkill()
            
            # Helper to handle cloning if needed
            working_dir = local_repo_path
            
            if repo_url and not working_dir:
                 # Clone first if we have a URL but no path yet
                 # NOTE: Ideally the agent does this, but to simplify the flow as requested:
                 # "System should clone first if URL provided"
                 # Let's let the Agent know it needs to deal with this URL or Path.
                 pass

            clar_skill = ClarificationSkill(ask_user_func, on_requirements_ready)
            
            # Clarifier gets FS tools to inspect repo if needed
            clarifier_tools = clar_skill.get_tools() + fs_skill.get_tools() + repo_skill.get_tools()
            
            system_msg_extras = ""
            if working_dir:
                system_msg_extras = f"**目前工作目錄 (CWD)**: `{working_dir}`\n請務必只讀取/修改此目錄下的檔案。"
            elif repo_url:
                system_msg_extras = f"**任務目標**: 請先 Clone `{repo_url}`，然後將工作目錄鎖定在 Clone 下來的資料夾。"

            clarifier_session = await self.client.create_session({
                "model": self.model,
                "system_message": (
                    "你是需求分析師。你的任務是確保使用者的需求完全明確且可執行。"
                    f"{system_msg_extras}\n"
                    "重要：如果不確定檔案內容，請使用 `list_directory` 或 `read_file` 查看。\n"
                    "如果使用者的 Prompt 太模糊，請使用 `ask_user` 工具向使用者發問。"
                    "一旦資訊充足，請使用 `finalize_requirements` 工具提交完整的需求總結。"
                ),
                "tools": clarifier_tools,
                "on_permission_request": lambda req, meta: {"kind": "allowed"}
            })
            
            # Setup logging and idle detection
            self._setup_logging(clarifier_session, "Clarifier")
            print(f"\n--- [Clarifier Analysis] ---")

            session_idle = asyncio.Event()
            def on_idle(event: SessionEvent):
                if event.type == SessionEventType.SESSION_IDLE:
                    session_idle.set()
            clarifier_session.on(on_idle)

            # Start the conversation
            try:
                # Initial message
                await clarifier_session.send(MessageOptions(prompt=f"User Request: {user_prompt}"))
                
                # Loop until requirements are finalized
                while not clarification_done.is_set():
                    # Wait for either completion or idle
                    done, pending = await asyncio.wait(
                        [
                            asyncio.create_task(clarification_done.wait()), 
                            asyncio.create_task(session_idle.wait())
                        ], 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    if clarification_done.is_set():
                        break
                    
                    if session_idle.is_set():
                        session_idle.clear()
                        # If idle but not done, it means the agent outputted text (without using the finalize tool)
                        # and is now waiting for user input.
                        # We use the provided callback to get input.
                        response = await ask_user_func(" (Please answer the agent's question above)")
                        
                        # Send user response back to agent
                        await clarifier_session.send(MessageOptions(prompt=response))

                logs.append(f"[Clarification] Requirements finalized: {final_requirements[:100]}...")
            except asyncio.TimeoutError:
                logs.append("[Clarification] Timed out waiting for clarification.")
                return AgentResult(False, "", logs + ["Clarification timed out."])
            finally:
                await clarifier_session.destroy()

        # Initialize Skills (if not already done)
        repo_skill = RepositorySkill()
        fs_skill = FileSystemSkill()
        
        worker_tools = repo_skill.get_tools() + fs_skill.get_tools()

        # Construct Prompt
        if working_dir:
            final_prompt = (
                f"Target Repository Path: {working_dir}\n"
                f"Request: {final_requirements}"
            )
        elif repo_url:
            final_prompt = (
                f"Please clone the repository at '{repo_url}' using the available tool first.\n"
                f"Once cloned, analyze the codebase and fulfill the user request:\n\n{final_requirements}"
            )

        # 1. 初始化 Sessions
        # Worker gets the tools (skills) to interact with the world
        
        worker_sys_msg = "你是 Worker Agent。你擁有操作 Git 儲存庫與檔案系統技能。"
        if working_dir:
            worker_sys_msg += f"\n**工作目標目錄**: `{working_dir}`。請直接在此目錄進行操作，不需要 Clone。"
        else:
            worker_sys_msg += "\n若使用者提供儲存庫 URL，請務必先使用工具將其 clone 下來。"

        session_config = {
            "model": self.model,
            "system_message": worker_sys_msg,
            "tools": worker_tools,
            "on_permission_request": lambda req, meta: {"kind": "allowed"}
        }
        
        # Reviewer doesn't need the tools, just needs to read the code (conceptual)
        # But in a real scenario, Reviewer might also want to search files.
        # For this demo, let's keep Reviewer focused on text analysis or give it read access if we had a FileSystem skill.
        reviewer_config = {
            "model": self.model,
            "system_message": "你是 Reviewer Agent。你的任務是驗證 Worker 產生的程式碼是否完全符合 User Prompt 的要求。如果符合，請只回答 'PASS'。如果不符合或有錯誤，請具體指出問題。",
            "on_permission_request": lambda req, meta: {"kind": "allowed"}
        }
        
        # Set permissions for tools (allow cloning)
        session_config["on_permission_request"] = lambda req, meta: {"kind": "allowed"}

        worker_session = await self.client.create_session(session_config)
        reviewer_session = await self.client.create_session(reviewer_config)
        
        # Setup logging
        self._setup_logging(worker_session, "Worker")
        self._setup_logging(reviewer_session, "Reviewer")

        current_code = ""
        feedback = ""
        
        try:
            for attempt in range(self.max_retries + 1):
                logs.append(f"--- Attempt {attempt + 1} ---")
                
                # --- Worker Phase ---
                if attempt == 0:
                    worker_prompt = f"User Request: {final_prompt}"
                else:
                    worker_prompt = f"Previous Code:\n{current_code}\n\nReviewer Feedback: {feedback}\n\nPlease fix the code."

                logs.append(f"[Workering] Generating code...")
                print(f"\n\n--- [Worker Attempt {attempt + 1}] ---")
                # 這裡為了簡化，使用 send_and_wait 並假設回傳的是訊息
                # 在實際 SDK 中，send_and_wait 回傳的是最後一個事件 (通常是 assistant message)
                worker_event = await worker_session.send_and_wait(MessageOptions(prompt=worker_prompt))
                
                if worker_event and worker_event.type == SessionEventType.ASSISTANT_MESSAGE:
                    current_code = worker_event.data.content
                    logs.append(f"[Worker Output]:\n{current_code[:200]}...") # Log 簡短版
                else:
                    logs.append("[Worker Error] No response.")
                    return AgentResult(False, "", logs)

                # --- Reviewer Phase ---
                reviewer_prompt = f"""
Original User Request: {final_requirements}
(Note: The task might involve a repository: {repo_url})

Worker Generated Code / Output:
{current_code}

Task: Check if the code/action meets the request. If yes, say 'PASS'. If no, explain why.
"""
                logs.append(f"[Reviewing] Validating code...")
                print(f"\n\n--- [Reviewer Attempt {attempt + 1}] ---")
                reviewer_event = await reviewer_session.send_and_wait(MessageOptions(prompt=reviewer_prompt))
                
                if reviewer_event and reviewer_event.type == SessionEventType.ASSISTANT_MESSAGE:
                    feedback = reviewer_event.data.content
                    logs.append(f"[Reviewer Output]: {feedback}")
                    
                    if "PASS" in feedback:
                        logs.append("[Success] Review Passed!")
                        return AgentResult(True, current_code, logs)
                else:
                    logs.append("[Reviewer Error] No response.")
            
            return AgentResult(False, current_code, logs)

        finally:
            await worker_session.destroy()
            await reviewer_session.destroy()
