#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from copilot import CopilotClient, SessionConfig, MessageOptions

# Load environment variables from .env file (override existing ones)
load_dotenv(override=True)

print("Initializing GitHub Copilot Client...")
print("Note: Ensure the standalone 'copilot' CLI is installed and in your PATH.")
print("If you just installed it, please RESTART your terminal/VS Code.")
print("Tip: If the program hangs at 'thinking', run 'copilot' in your terminal once to confirm 'Folder Trust'.\n")

async def main():
    try:
        # Initialize Client
        # Hint: If copilot is not in PATH, you can set cli_path parameter
        # Note: Use GH_TOKEN or GITHUB_TOKEN environment variable for authentication
        client = CopilotClient()
        
        # Create Session
        # Get model from COPILOT_MODEL env var, default to "claude-3.5-sonnet"
        model = os.getenv('COPILOT_MODEL', 'claude-3.5-sonnet')
        session_config = {"model": model}
        print(f"Creating session with model '{model}'...")
        
        
        session = await client.create_session(session_config)
        print("Session created! Enter your prompt below:")
        
        try:
            user_input = input("\nUser: ")
            
            if user_input.strip():
                print("Copilot (thinking...): ", end="", flush=True)
                
                msg_options = MessageOptions(prompt=user_input)
                
                # Send and Wait for response
                # Using a 60 second timeout
                try:
                    result = await asyncio.wait_for(
                        session.send_and_wait(msg_options),
                        timeout=60.0
                    )
                    
                    # Print only the content (not the entire object)
                    print(result.data.content)
                    
                except asyncio.TimeoutError:
                    print("\nRequest Timeout: The Copilot CLI did not respond in time.")
                    print("Possible cause: You may need to run 'copilot' manually in this folder to confirm 'Folder Trust'.")
                except Exception as request_ex:
                    print(f"\nRequest Error: {request_ex}")
        finally:
            print("\nClosing session...")
            
    except Exception as ex:
        print(f"\nProgram Error: {ex}")

if __name__ == "__main__":
    asyncio.run(main())
