# 🚀 Awesome OpenAI CLI

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A sleek terminal app for chatting with OpenAI models—complete with confidence-based color coding, customizable models, history, streaming answers, and more. Perfect for impressing recruiters and powering serious demos.

## 🔥 Features

- **Secure API key entry** via prompt or `.env` file  
- **Configurable model & parameters** (`--model`, `--max-tokens`, `--stream`)  
- **Real-time streaming** of token-by-token responses  
- **Confidence coloring** (red/yellow/green) using log-probs  
- **Command history** with `readline` support  
- **Loading spinner** during generation  
- **Export** conversation logs to JSON  
- **Error handling & retries** on network/API errors  
- Ready for extension (plugin hooks, custom prompts)

## 🖼️ Demo

![Awesome OpenAI CLI Demo](assets/cli_demo.png)

## 🚀 Quickstart

1. **Clone & install**  
   ```