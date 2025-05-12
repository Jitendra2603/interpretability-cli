#!/usr/bin/env python3
"""
awesome-openai-cli: Interactive terminal for OpenAI with confidence coloring,
streaming, history, spinners, and exportable logs, using the modern OpenAI v1+ SDK.
"""

import os
import sys
import json
import math
import click
try:
    import gnureadline as readline
except ImportError:
    import readline # Fallback if gnureadline not installed

from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
from time import sleep
from rich.console import Console
from rich.text import Text
from rich.spinner import Spinner
from dotenv import load_dotenv
from rich.live import Live
from rich.panel import Panel

# ──────────────────────────────────────────────────────────────────────────────
console = Console()
load_dotenv()  # loads OPENAI_API_KEY from .env if present

# Instantiate the client. Attempt to use environment variable first.
try:
    client = OpenAI()
    if not client.api_key:
        raise APIError("API key environment variable found but empty.")
except APIError as e:
    console.print(f"[yellow]Could not find OPENAI_API_KEY environment variable ({e}).[/]")
    api_key_from_prompt = click.prompt("Please enter your OpenAI API key", hide_input=True)
    if not api_key_from_prompt:
        console.print("[bold red]API key cannot be empty.[/]")
        sys.exit(1)
    try:
        client = OpenAI(api_key=api_key_from_prompt)
        client.models.list() # Test the key
    except (APIError, RateLimitError, APITimeoutError) as e:
        console.print(f"[bold red]API Error: Failed to initialize OpenAI client with provided key. Details: {e}[/]")
        sys.exit(1)
except Exception as e:
    console.print(f"[bold red]An unexpected error occurred during client initialization: {e}[/]")
    sys.exit(1)

def get_token_confidence(logprob_value):
    """Calculate individual token confidence (probability)."""
    if logprob_value is None:
        return 0.0
    return math.exp(logprob_value)

def color_token(token_text, token_conf):
    """Return Rich Text for a single token colored by its confidence."""
    style = "green" if token_conf >= 0.9 else "yellow" if token_conf >= 0.5 else "red"
    return Text(token_text, style=style)

@click.command()
@click.option("--model", default="gpt-3.5-turbo", help="OpenAI model (e.g., gpt-4, gpt-3.5-turbo)")
@click.option("--max-tokens", default=150, help="Max tokens per response")
@click.option("--logprobs/--no-logprobs", default=False, help="Request log probabilities for confidence scoring")
@click.option("--top-logprobs", type=click.IntRange(0, 5), default=0, help="Include N top alternative tokens (requires --logprobs, max 5)")
@click.option("--stream/--no-stream", default=False, help="Enable streaming display (token by token)")
@click.option("--export", type=click.Path(), default=None, help="Save full chat log (JSON)")
def main(model, max_tokens, logprobs, top_logprobs, stream, export):
    # Ensure top_logprobs requires logprobs
    if top_logprobs > 0 and not logprobs:
        console.print("[bold yellow]Warning: --top-logprobs requires --logprobs to be enabled. Ignoring --top-logprobs.[/]")
        top_logprobs = 0

    chat_log = []
    messages = [
        # {"role": "system", "content": "You are a helpful assistant."}
    ]
    console.print("[bold blue]Start chatting—Ctrl+D or 'quit' to exit[/]\\n")

    SHOW_ALT_CONFIDENCE_THRESHOLD = 0.80 # Only show alternatives if main token confidence is BELOW this

    while True:
        try:
            prompt = console.input("[bold cyan]You:[/] ")
        except (EOFError, KeyboardInterrupt):
            break
        if prompt.strip().lower() in {"quit", "exit"}:
            break

        messages.append({"role": "user", "content": prompt})
        full_response_text_for_history = ""
        overall_logprobs_for_avg_conf = []
        
        api_call_should_stream = True if logprobs else stream
        status_context = console.status("⏳ Thinking...", spinner="dots") if not api_call_should_stream else open('/dev/null', 'w')

        try:
            with status_context:
                response_data = client.chat.completions.create(
                    model=model, messages=messages, max_tokens=max_tokens,
                    logprobs=logprobs, top_logprobs=top_logprobs if logprobs else None,
                    stream=api_call_should_stream
                )

            if stream: # User wants token-by-token display
                console.print("[bold green]AI:[/] ", end="") # Print AI prefix once before Live
                live_renderable_content = Text("", no_wrap=True)
                with Live(live_renderable_content, console=console, refresh_per_second=15, transient=True, vertical_overflow="visible") as live:
                    for chunk in response_data:
                        choice = chunk.choices[0]
                        current_chunk_segment = Text("")
                        if logprobs and choice.logprobs and choice.logprobs.content:
                            for lp_item in choice.logprobs.content:
                                token_text = lp_item.token
                                if not token_text: continue
                                full_response_text_for_history += token_text
                                token_conf = get_token_confidence(lp_item.logprob)
                                if lp_item.logprob is not None: overall_logprobs_for_avg_conf.append(lp_item.logprob)
                                current_chunk_segment.append(color_token(token_text, token_conf))
                                # SELECTIVE ALTERNATIVES DISPLAY
                                if top_logprobs > 0 and lp_item.top_logprobs and token_conf < SHOW_ALT_CONFIDENCE_THRESHOLD:
                                    alts = [alt.token for alt in lp_item.top_logprobs[:top_logprobs]]
                                    current_chunk_segment.append(Text.from_markup(f" [dim](alt: {', '.join(alts)})[/dim]"))
                        elif choice.delta and choice.delta.content:
                            token_text = choice.delta.content
                            full_response_text_for_history += token_text
                            current_chunk_segment.append(token_text)
                        if current_chunk_segment:
                            live_renderable_content.append(current_chunk_segment)
                            live.update(live_renderable_content)
                if stream and full_response_text_for_history: console.print(live_renderable_content)
                elif stream: console.print()
            
            else: # User wants non-streaming display
                console.print("[bold green]AI:[/] ", end="")
                final_display_text = Text("", no_wrap=True)
                if api_call_should_stream: # API streamed (e.g., for logprobs)
                    for chunk in response_data:
                        choice = chunk.choices[0]
                        if logprobs and choice.logprobs and choice.logprobs.content:
                            for lp_item in choice.logprobs.content:
                                token_text = lp_item.token
                                if not token_text: continue
                                full_response_text_for_history += token_text
                                token_conf = get_token_confidence(lp_item.logprob)
                                if lp_item.logprob is not None: overall_logprobs_for_avg_conf.append(lp_item.logprob)
                                final_display_text.append(color_token(token_text, token_conf))
                                # SELECTIVE ALTERNATIVES DISPLAY
                                if top_logprobs > 0 and lp_item.top_logprobs and token_conf < SHOW_ALT_CONFIDENCE_THRESHOLD:
                                    alts = [alt.token for alt in lp_item.top_logprobs[:top_logprobs]]
                                    final_display_text.append(Text.from_markup(f" [dim](alt: {', '.join(alts)})[/dim]"))
                        elif choice.delta and choice.delta.content:
                            token_text = choice.delta.content
                            full_response_text_for_history += token_text
                            final_display_text.append(token_text)
                    console.print(final_display_text)
                else: # API was not streaming
                    full_response_text_for_history = response_data.choices[0].message.content.strip()
                    console.print(full_response_text_for_history)
                console.print() # Newline for non-streaming case too

            # Common post-response logic (history, overall confidence)
            if full_response_text_for_history:
                messages.append({"role": "assistant", "content": full_response_text_for_history})
            if logprobs and overall_logprobs_for_avg_conf:
                valid_lps = [lp for lp in overall_logprobs_for_avg_conf if lp is not None]
                if valid_lps:
                    avg_prob = sum(math.exp(lp) for lp in valid_lps) / len(valid_lps)
                    console.print(f"[i](Overall Confidence: {avg_prob:.1%})[/i]")

        except (APIError, APIConnectionError, RateLimitError, APITimeoutError) as e:
            console.print() # Ensure newline after error too
            err_msg = str(e).lower()
            is_logprobs_unsupported = ("logprobs is not supported" in err_msg or 
                                     "top_logprobs is not supported" in err_msg or
                                     ("params" in err_msg and ("logprobs" in err_msg or "top_logprobs" in err_msg)) or 
                                     ("context_length_exceeded" in err_msg and logprobs))
            current_logprobs_setting = logprobs 
            current_top_logprobs_setting = top_logprobs

            if is_logprobs_unsupported and logprobs:
                console.print(f"[bold yellow]\nWarning: Logprobs/Top_logprobs not supported or incompatible with model '{model}'. Retrying without them.[/]")
                current_logprobs_setting = False 
                current_top_logprobs_setting = 0 
                try:
                    console.print("[bold green]AI:[/] ", end="")
                    plain_resp_data = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, stream=stream)
                    if stream:
                        temp_full_text = ""
                        for chunk_retry in plain_resp_data:
                            content = chunk_retry.choices[0].delta.content
                            if content is not None: console.print(content, end=""); temp_full_text += content
                        console.print()
                        full_response_text_for_history = temp_full_text
                    else:
                        full_response_text_for_history = plain_resp_data.choices[0].message.content.strip()
                        console.print(full_response_text_for_history)
                    if full_response_text_for_history: messages.append({"role": "assistant", "content": full_response_text_for_history})
                except Exception as plain_e:
                    console.print(f"[bold red]\nOpenAI API Error (retry attempt): {plain_e}[/]")
                    full_response_text_for_history = "<error retrieving response>"
                    if messages and messages[-1]["role"] == "user": messages.pop()
            else:
                console.print(f"[bold red]\nOpenAI API Error: {e}[/]")
                full_response_text_for_history = "<error retrieving response>"
                if messages and messages[-1]["role"] == "user": messages.pop()
        except Exception as e:
                console.print(f"[bold red]\nAn unexpected error occurred: {e}[/]")
                full_response_text_for_history = "<error retrieving response>"
                if messages and messages[-1]["role"] == "user": messages.pop()
                current_logprobs_setting = logprobs 
                current_top_logprobs_setting = top_logprobs
        else: 
            current_logprobs_setting = logprobs
            current_top_logprobs_setting = top_logprobs
        
        chat_log.append({"prompt": prompt, "response": full_response_text_for_history, "logprobs_enabled": current_logprobs_setting, "top_logprobs_enabled": current_top_logprobs_setting > 0})

    # Export log
    if export:
        try:
            with open(export, "w") as f:
                json.dump(chat_log, f, indent=2)
            console.print(f"[green]Chat log saved to {export}[/]")
        except IOError as e:
            console.print(f"[bold red]Error saving chat log to {export}: {e}[/]")

if __name__ == "__main__":
    main() 