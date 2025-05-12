# 🚀 Awesome OpenAI CLI

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A sleek terminal app for chatting with OpenAI models—complete with confidence-based color coding, customizable models, history, streaming answers, and more. Perfect for impressing recruiters and powering serious demos.

## Features

- **Secure API key entry** via prompt or `.env` file  
- **Configurable model & parameters** (`--model`, `--max-tokens`, `--stream`)  
- **Real-time streaming** of token-by-token responses  
- **Confidence coloring** (red/yellow/green) using log-probs  
- **Command history** with `readline` support  
- **Loading spinner** during generation  
- **Export** conversation logs to JSON  
- **Error handling & retries** on network/API errors  
- Ready for extension (plugin hooks, custom prompts)

## Quickstart

1. **Clone & install**  
   ```bash
   git clone https://github.com/jitendra2603/interpretability-cli.git
   cd interpretability-cli
   pip install -r requirements.txt
   ```

2. **Configure API key**

   * Copy and fill in your key in `.env`

     ```bash
     echo OPENAI_API_KEY="sk-..." > .env
     ```
   * Or just let the script prompt you.

3. **Run the CLI**

   ```bash
   python cli_tool.py --model gpt-4 \
                     --max-tokens 200 \
                     --stream \
                     --export logs.json
   ```

4. **Ask away:**
   Type your question and watch answers appear color-coded by confidence.
   Exit with `Ctrl+D` or type `quit`.

## 🛠️ Usage & Flags

| Flag             | Description                       | Default            |
| ---------------- | --------------------------------- | ------------------ |
| `--model`        | OpenAI model to use               | `gpt-3.5-turbo`    |
| `--max-tokens`   | Max tokens in response            | `150`              |
| `--logprobs`     | Request log probabilities for confidence scoring and alternative tokens | `False`            |
| `--top-logprobs` | Show N alternative tokens (0-5) if main token confidence < 80% (requires `--logprobs`) | `0`                |
| `--stream`       | Stream tokens as they arrive      | `False`            |
| `--export`       | Path to save full chat log (JSON) | *none*             |

## 💡 Extending

1. Add new flags or subcommands via [Click](https://click.palletsprojects.com/)
2. Hook into the `on_response` callback to add analytics or custom logic
3. Swap out the output library (Rich) for your own renderer

## License

MIT © [Jitendra](https://github.com/jitendra2603) 