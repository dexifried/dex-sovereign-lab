import requests
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich import print as rprint

console = Console()
EXECUTE_URL = "http://localhost:8000/execute"
SANDBOX_URL = "http://localhost:8000/sandbox"
SECRET = "dex-lab-2026"

def main():
    console.clear()
    console.print(Panel.fit("[bold cyan]DEX OS TERMINAL v2.0[/bold cyan]\n[dim]Split-Brain & Autonomous Sandbox Engine Online[/dim]", border_style="cyan"))

    while True:
        try:
            user_prompt = Prompt.ask("\n[bold green]Guest@Dex[/bold green]")
            if user_prompt.lower() in ['exit', 'quit']: break
            if not user_prompt.strip(): continue
            
            # 1. Standard Routing
            with console.status("[bold yellow]Routing to Cortex...", spinner="point"):
                resp = requests.post(EXECUTE_URL, json={"prompt": user_prompt}).json()
                reply = resp.get("response", "")
                agent = resp.get("agent", "Node")
                intent = resp.get("intent", "UNK")

            p_color = "magenta" if "Coder" in agent else "green"
            console.print(Panel(Markdown(reply), title=f"[bold {p_color}]{agent}[/bold {p_color}] | Intent: {intent}", border_style=p_color))

            # 2. The Sandbox Trigger (Only triggers if DeepSeek writes code)
            if "Coder" in agent and "```python" in reply:
                if Confirm.ask("\n[bold cyan]Deploy objective to Autonomous Sandbox for execution & self-correction?[/bold cyan]"):
                    with console.status("[bold red]Sandbox Active... DeepSeek is generating, testing, and fixing...[/bold red]", spinner="bouncingBar"):
                        sand_resp = requests.post(SANDBOX_URL, json={"prompt": user_prompt, "secret_key": SECRET}, timeout=180).json()
                    
                    if sand_resp.get("status") == "success":
                        attempts = sand_resp.get("attempts")
                        console.print(f"\n[bold green]✔ Objective achieved after {attempts} attempt(s)![/bold green]")
                        if sand_resp.get("output"):
                            console.print(Panel(sand_resp["output"], title="Sandbox STDOUT", border_style="white"))
                    else:
                        console.print(f"\n[bold red]✘ Sandbox Failed[/bold red]")
                        if sand_resp.get("last_stderr"):
                            console.print(Panel(sand_resp["last_stderr"], title="Final STDERR", border_style="red"))

        except Exception as e:
            rprint(f"[bold red]System Error:[/] {e}")

if __name__ == "__main__":
    main()


