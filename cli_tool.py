#!/usr/bin/env python3
"""
awesome-openai-cli: Interactive terminal for OpenAI with confidence coloring,
streaming, history, spinners, and exportable logs.
"""

import os
import sys
import json
import math
import click
import openai
import readline
from time import sleep
from rich.console import Console
from rich.text import Text
from rich.spinner import Spinner
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────────────────────
console = Console()
load_dotenv()  # loads OPENAI_API_KEY from .env if present

def get_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    return click.prompt("OpenAI API key", hide_input=True)

def compute_confidence(logprobs):
    """Average e^(logprob) across tokens → [0,1] confidence."""
    probs = [math.exp(lp) for lp in logprobs if lp is not None]
    return sum(probs) / len(probs) if probs else 0.0

def color_text(text, conf):
    """Return Rich Text colored by confidence thresholds."""
    style = "green" if conf>=0.9 else "yellow" if conf>=0.7 else "red"
    return Text(text, style=style)

@click.command()
@click.option("--model", default="text-davinci-003", help="OpenAI model")
@click.option("--max-tokens", default=150, help="Max tokens per response")
@click.option("--top-logprobs", default=5, help="Number of top logprobs")
@click.option("--stream/--no-stream", default=False, help="Enable streaming")
@click.option("--export", type=click.Path(), help="Save full chat log (JSON)")
def main(model, max_tokens, top_logprobs, stream, export):
    api_key = get_api_key()
    openai.api_key = api_key
    chat_log = []

    console.print("[bold blue]Start chatting—Ctrl+D or 'quit' to exit[/]\n")
    while True:
        try:
            prompt = console.input("[bold cyan]You:[/] ")
        except (EOFError, KeyboardInterrupt):
            break
        if prompt.strip().lower() in {"quit", "exit"}:
            break

        # Spinner context
        with console.status("⏳ Thinking...", spinner="dots"):
            resp = openai.Completion.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                logprobs=True,
                top_logprobs=top_logprobs,
                stream=stream
            )

        # Handle both streaming & non-streaming
        if stream:
            full_text, lp_accum = "", []
            for chunk in resp:
                t = chunk.choices[0].text
                console.print(t, end="")
                full_text += t
                if chunk.choices[0].logprobs:
                    lp_accum.extend(chunk.choices[0].logprobs.token_logprobs)
            console.print()  # newline
            conf = compute_confidence(lp_accum)
            console.print(f"[i]Confidence:[/] {conf:.2%}")
            # Store the full text for the log when streaming
            text = full_text 
        else:
            choice = resp.choices[0]
            text = choice.text.strip()
            # Handle cases where logprobs might be None or empty
            lp = choice.logprobs.token_logprobs if choice.logprobs and choice.logprobs.token_logprobs else []
            conf = compute_confidence(lp)
            console.print(color_text(text, conf))

        chat_log.append({"prompt": prompt, "response": text, "confidence": conf})

    # Export if requested
    if export:
        with open(export, "w") as f:
            json.dump(chat_log, f, indent=2)
        console.print(f"[green]Chat log saved to {export}[/]")

if __name__ == "__main__":
    main() 