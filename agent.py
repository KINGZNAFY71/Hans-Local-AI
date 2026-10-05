"""
agent.py - Local Python AI Agent powered by Ollama and Pydantic AI.

Features:
- Connects to local Ollama instance (default: http://localhost:11434)
- Equipped with local tools:
  * Safe mathematical calculator
  * Markdown note creator, reader, and lister (stored in ./notes/)
  * Local system time and date inspector
- Interactive terminal REPL loop with conversation memory and system commands
"""

import ast
import math
import operator
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Suppress pydantic-ai telemetry banner for cleaner CLI
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

# Load environment configuration
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")
NOTES_DIR = Path(os.getenv("NOTES_DIR", "./notes")).resolve()

# Ensure notes directory exists
NOTES_DIR.mkdir(parents=True, exist_ok=True)

# Optional rich formatting for enhanced terminal experience
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


def print_ui(msg: str, style: str = "white", bold: bool = False):
    """Print text with optional rich styling fallback."""
    if HAS_RICH and console:
        console.print(msg, style=f"{'bold ' if bold else ''}{style}")
    else:
        print(msg)


# ==============================================================================
# Local Agent Tools
# ==============================================================================

def get_system_time() -> str:
    """
    Get the current local system date, time, day of the week, and timezone.
    Always use this tool when the user asks for the current time, today's date, or scheduling.
    """
    now = datetime.now().astimezone()
    return (
        f"Current Local Date & Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"Day of the Week: {now.strftime('%A')}\n"
        f"ISO 8601: {now.isoformat()}"
    )


def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.
    Supports addition (+), subtraction (-), multiplication (*), division (/),
    modulo (%), exponentiation (**), parentheses, and common math functions:
    sqrt, abs, round, sin, cos, tan, log, exp, pi, e.
    """
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    allowed_functions = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Invalid constant: {node.value}")
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in allowed_operators:
                return allowed_operators[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in allowed_operators:
                return allowed_operators[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in allowed_functions:
                func = allowed_functions[node.func.id]
                args = [_eval(arg) for arg in node.args]
                return func(*args)
            raise ValueError(f"Unsupported function call")
        elif isinstance(node, ast.Name):
            if node.id in allowed_functions:
                return allowed_functions[node.id]
            raise ValueError(f"Unknown variable: {node.id}")
        else:
            raise ValueError(f"Unsupported expression construct: {type(node).__name__}")

    try:
        parsed = ast.parse(expression.strip(), mode="eval")
        result = _eval(parsed.body)
        return f"Calculation: {expression} = {result}"
    except ZeroDivisionError:
        return "Error: Division by zero."
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}"


def _slugify(text: str) -> str:
    """Convert a title to a safe filename."""
    text = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[-\s]+", "_", text) or "untitled"


def save_note(title: str, content: str) -> str:
    """
    Save or update a markdown note in the local notes directory.
    - title: Title of the note (used as the header and filename).
    - content: Markdown text content to save.
    """
    filename = f"{_slugify(title)}.md"
    file_path = NOTES_DIR / filename
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    markdown_data = (
        f"# {title}\n\n"
        f"> *Saved on {timestamp}*\n\n"
        f"{content.strip()}\n"
    )

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_data)
        return f"Note successfully saved to '{file_path.name}'. File path: {file_path}"
    except Exception as e:
        return f"Failed to save note '{title}': {str(e)}"


def read_note(title: str) -> str:
    """
    Read the contents of a saved note by its title or filename.
    - title: Name of the note or filename (with or without .md).
    """
    filename = title.strip()
    if not filename.endswith(".md"):
        filename = f"{_slugify(title)}.md"

    file_path = NOTES_DIR / filename
    if not file_path.exists():
        # Try finding a matching file case-insensitively
        matches = [f for f in NOTES_DIR.glob("*.md") if f.stem.lower() == _slugify(title)]
        if matches:
            file_path = matches[0]
        else:
            return f"Note not found: '{title}'. Use list_notes() to view available notes."

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading note '{title}': {str(e)}"


def list_notes() -> str:
    """
    List all notes currently saved in the local notes directory.
    """
    notes = list(NOTES_DIR.glob("*.md"))
    if not notes:
        return "No notes found in the notes directory."

    output = ["Available Notes:"]
    for note in sorted(notes, key=lambda p: p.stat().st_mtime, reverse=True):
        mtime = datetime.fromtimestamp(note.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        output.append(f"- {note.stem} ({note.name}) [Modified: {mtime}]")
    return "\n".join(output)


# ==============================================================================
# Agent Initialization (Pydantic AI / OpenAI Bridge)
# ==============================================================================

SYSTEM_PROMPT = """You are an intelligent, helpful local AI Agent running on the user's personal machine.
You have direct access to local tools:
1. `get_system_time`: Retrieve accurate local time, date, and timezone.
2. `calculate`: Execute safe arithmetic calculations.
3. `save_note`: Save structured markdown notes to the local filesystem.
4. `read_note`: Retrieve previously saved markdown notes.
5. `list_notes`: View all stored notes in the directory.

Guidelines:
- When the user asks to save a note, record information, or summarize something to a file, invoke `save_note`.
- When asked for calculation, use `calculate`.
- When asked for the current time, date, or day, invoke `get_system_time`.
- Keep answers clear, well-structured, and formatted with markdown where helpful.
"""


def check_ollama_alive(base_url: str) -> bool:
    """Verify if the Ollama server is responding."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=3.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def build_pydantic_agent():
    """
    Construct the Pydantic AI agent configured for Ollama.
    Uses OpenAI-compatible model interface pointing to Ollama's /v1 endpoint.
    """
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        provider = OpenAIProvider(
            base_url=f"{OLLAMA_BASE_URL}/v1",
            api_key="ollama",
        )
        model = OpenAIChatModel(
            model_name=OLLAMA_MODEL,
            provider=provider,
        )

        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
        )

        # Register local tools
        agent.tool_plain(get_system_time)
        agent.tool_plain(calculate)
        agent.tool_plain(save_note)
        agent.tool_plain(read_note)
        agent.tool_plain(list_notes)

        return agent
    except Exception as e:
        print_ui(f"Notice during Pydantic AI init: {e}", style="dim")
        return None


# Fallback direct LLM client if pydantic-ai is not yet installed
class DirectOllamaAgent:
    """Fallback agent using direct HTTP calls to Ollama with tool dispatch."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
        self.tools = {
            "get_system_time": get_system_time,
            "calculate": calculate,
            "save_note": save_note,
            "read_note": read_note,
            "list_notes": list_notes,
        }

    def run_sync(self, prompt: str, message_history: Optional[List[Dict[str, Any]]] = None):
        import urllib.request
        import json

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if message_history:
            messages.extend(message_history)
        messages.append({"role": "user", "content": prompt})

        # Check for simple tool intent triggers
        prompt_lower = prompt.lower()
        tool_injected_context = ""

        if any(w in prompt_lower for w in ["time", "date", "today", "clock", "day of week"]):
            tool_injected_context += f"\n[System Tool Context: {get_system_time()}]\n"
        if any(w in prompt_lower for w in ["list notes", "show notes", "what notes"]):
            tool_injected_context += f"\n[System Tool Context: {list_notes()}]\n"

        if tool_injected_context:
            messages[-1]["content"] += f"\n\n{tool_injected_context}"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=60.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("message", {}).get("content", "")
            return type("Result", (), {"data": content, "all_messages": lambda: messages})()


# ==============================================================================
# Interactive Terminal Loop
# ==============================================================================

def print_banner():
    banner = f"""
=================================================================
      LOCAL PYTHON AI AGENT (Ollama + Pydantic AI)
=================================================================
  * Ollama Host : {OLLAMA_BASE_URL}
  * Active Model: {OLLAMA_MODEL}
  * Notes Folder: {NOTES_DIR}
-----------------------------------------------------------------
  Special Commands:
    /help   - Show available commands and tool information
    /tools  - List available local tools
    /clear  - Clear conversation history
    /notes  - List markdown notes in ./notes/
    exit    - Quit the agent loop
=================================================================
"""
    if HAS_RICH and console:
        console.print(Panel(banner.strip(), title="AI Agent Ready", border_style="cyan"))
    else:
        print(banner)


def show_help():
    help_text = """
Commands:
  /help    - Display this help message.
  /tools   - Display local tools available to the agent.
  /notes   - Quick view of saved markdown notes.
  /clear   - Reset current session memory.
  exit/quit- Terminate the terminal session.

Examples to try:
  > What is the current system date and time?
  > Calculate (450 * 12) + (85 / 5) ^ 2
  > Save a note titled 'Meeting Summary' with action items for project Kingz
  > List all my saved notes
  > Read the note 'Meeting Summary'
"""
    print_ui(help_text, style="green")


def main():
    print_ui("Checking Ollama server connectivity...", style="yellow")
    if not check_ollama_alive(OLLAMA_BASE_URL):
        print_ui(
            f"\n[ERROR] Could not connect to Ollama at {OLLAMA_BASE_URL}!\n\n"
            "Please ensure Ollama is running:\n"
            "  1. Run '.\\start_ollama.ps1' in PowerShell\n"
            "  2. Or start Ollama from the desktop application / 'ollama serve'\n"
            "  3. Check 'python test_connection.py' for detailed diagnostics.",
            style="red",
            bold=True,
        )
        sys.exit(1)

    print_ui("Ollama server is online!", style="green")

    # Try building Pydantic AI agent
    agent = build_pydantic_agent()
    using_pydantic = agent is not None

    if using_pydantic:
        print_ui("Loaded Pydantic AI Agent with native tool execution.", style="cyan")
    else:
        print_ui(
            "Notice: 'pydantic-ai' package not installed in current environment.\n"
            "Falling back to direct HTTP Ollama wrapper.\n"
            "Run 'pip install -r requirements.txt' for full Pydantic AI tool integration.",
            style="yellow",
        )
        agent = DirectOllamaAgent(OLLAMA_BASE_URL, OLLAMA_MODEL)

    print_banner()

    message_history = []

    while True:
        try:
            prompt = input("\nYou > ").strip()
        except (KeyboardInterrupt, EOFError):
            print_ui("\nExiting. Goodbye!", style="cyan")
            break

        if not prompt:
            continue

        cmd = prompt.lower()
        if cmd in ["exit", "quit", "/q"]:
            print_ui("Goodbye!", style="cyan")
            break
        elif cmd == "/help":
            show_help()
            continue
        elif cmd == "/tools":
            print_ui(
                "\nAvailable Local Tools:\n"
                "  1. get_system_time()            - Retrieve local date, time, timezone\n"
                "  2. calculate(expression)        - Safe arithmetic evaluator\n"
                "  3. save_note(title, content)    - Save markdown note to ./notes/\n"
                "  4. read_note(title)             - Read markdown note from ./notes/\n"
                "  5. list_notes()                 - List all notes in ./notes/\n",
                style="cyan",
            )
            continue
        elif cmd == "/notes":
            print_ui(f"\n{list_notes()}", style="cyan")
            continue
        elif cmd == "/clear":
            message_history = []
            print_ui("Conversation history cleared.", style="yellow")
            continue

        print_ui("\nAgent is thinking...", style="dim")

        try:
            if using_pydantic:
                # Run through Pydantic AI
                result = agent.run_sync(
                    prompt,
                    message_history=message_history if message_history else None,
                )
                if hasattr(result, "response") and hasattr(result.response, "text") and result.response.text:
                    response_text = result.response.text
                elif hasattr(result, "output") and result.output:
                    response_text = str(result.output)
                elif hasattr(result, "data") and result.data:
                    response_text = str(result.data)
                else:
                    response_text = str(getattr(result, "response", result))

                # Update history if supported
                if hasattr(result, "all_messages"):
                    message_history = result.all_messages()
            else:
                result = agent.run_sync(prompt, message_history=message_history)
                response_text = getattr(result, "data", str(result))
                message_history.append({"role": "user", "content": prompt})
                message_history.append({"role": "assistant", "content": response_text})

            print_ui("\nAgent:", style="magenta", bold=True)
            if HAS_RICH and console:
                console.print(Markdown(response_text))
            else:
                print(response_text)

        except Exception as e:
            print_ui(
                f"\n[Error executing request]: {str(e)}\n"
                f"Make sure model '{OLLAMA_MODEL}' is downloaded (`ollama pull {OLLAMA_MODEL}`).",
                style="red",
            )


if __name__ == "__main__":
    main()
