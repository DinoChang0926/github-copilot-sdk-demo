from typing import Callable, Awaitable, Optional
from pydantic import BaseModel, Field
from copilot.tools import define_tool

# Pydantic Models
class AskUserParams(BaseModel):
    question: str = Field(..., description="The question to ask the user for clarification.")

class FinalizeReqParams(BaseModel):
    summary: str = Field(..., description="The finalized, detailed requirements summary.")

class ClarificationSkill:
    """
    Skill for clarifying user requirements via enabling the agent to ask questions 
    and signal completion.
    """
    def __init__(self, ask_user_callback: Callable[[str], Awaitable[str]], on_ready_callback: Callable[[str], None]):
        """
        Args:
            ask_user_callback: Async function to get input from user.
            on_ready_callback: Function to call when requirements are finalized.
        """
        self._ask_user = ask_user_callback
        self._on_ready = on_ready_callback

    @define_tool(description="Ask the user a specific question to clarify requirements.")
    async def ask_user(self, params: AskUserParams) -> str:
        """
        Asks the user a question and waits for their response.
        """
        print(f"[System] Agent asks: {params.question}")
        response = await self._ask_user(params.question)
        return response

    @define_tool(description="Call this when the user's requirements are fully clarified and clear.")
    def finalize_requirements(self, params: FinalizeReqParams) -> str:
        """
        Signals that the clarification phase is complete.
        """
        print("[System] Requirements finalized.")
        self._on_ready(params.summary)
        return "Requirements finalized. Proceeding to execution phase."

    def get_tools(self):
        return [self.ask_user, self.finalize_requirements]
