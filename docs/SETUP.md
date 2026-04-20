# Vibecode v6 - Setup Guide

## Prerequisites

### 1. Install CLI Tools

Bạn cần cài đặt CLI tools sau và đăng nhập:

#### Brain CLI (Choose One)

**Option A: Claude Code CLI (Recommended)**
```bash
# Install
npm install -g @anthropic-ai/claude-code

# Login với subscription account
claude login

# Verify
claude --version
```

**Option B: OpenAI Codex** (Alternative)
```bash
pip install openai-cli
export OPENAI_API_KEY="your-api-key"
```

**Option C: Custom CLI** - See [CONFIGURATION.md](../CONFIGURATION.md)

#### Coder CLI (Choose One)

**Option A: Gemini CLI (Recommended - Fast & Cheap)**
```bash
# Install
npm install -g @google/generative-ai-cli

# Login với subscription account
gemini login

# Verify
gemini --version
```

**Option B: Claude Code CLI** (Higher quality, higher cost)
```bash
# Dùng luôn Claude nếu đã cài ở trên
# Set environment
export VIBECODE_CODER_CLI="claude"
```

**📖 Xem thêm:** [CONFIGURATION.md](../CONFIGURATION.md) để biết cách configure Brain và Coder CLI.

### 2. Install Python Dependencies

```bash
cd vibecode-v6/python
pip install -r requirements.txt  # Nếu có
```

### 3. Install VS Code Extension

```bash
cd vibecode-v6/extension
npm install
npm run compile
```

Sau đó trong VS Code:
- Press `F5` để launch Extension Development Host
- Hoặc package và install: `vsce package` → Install `.vsix` file

---

## Verify Installation

```bash
# Test Claude CLI
claude --version

# Test Gemini CLI  
gemini --version

# Test Python scripts
cd vibecode-v6/python
python orchestrator.py status
```

---

## Project Setup

### 1. Initialize .aiwf/ Directory

Trong project của bạn, tạo cấu trúc:

```bash
mkdir -p .aiwf/input
mkdir -p .aiwf/run/logs
```

### 2. Copy Templates

```bash
cp vibecode-v6/templates/goal.md .aiwf/input/
```

### 3. Configure VS Code

Copy `vibecode-v6/.vscode/tasks.json` vào project của bạn (optional).

---

## Quick Start

### Option A: Sử dụng VS Code Extension

1. Mở project trong VS Code
2. Mở Command Palette (`Cmd+Shift+P`)
3. Chọn "Vibecode v6: Start Planning Phase"
4. Follow UI prompts

### Option B: Sử dụng CLI Directly

```bash
# Step 1: Viết goal.md
vim .aiwf/input/goal.md

# Step 2: Generate plan
cd vibecode-v6/python
python -c "from cli_wrappers import generate_plan; generate_plan('../.aiwf/input/goal.md', '../.aiwf/input/plan.md')"

# Step 3: Get feedback từ Claude
python -c "from cli_wrappers import review_plan_claude; review_plan_claude('../.aiwf/input/plan.md', '../.aiwf/input/feedback_1.md')"

# Step 4: Get feedback từ Gemini
python -c "from cli_wrappers import review_plan_gemini; review_plan_gemini('../.aiwf/input/plan.md', '../.aiwf/input/feedback_2.md')"

# Step 5: Synthesize blueprint
python -c "from cli_wrappers import synthesize_blueprint; synthesize_blueprint('../.aiwf/input/plan.md', '../.aiwf/input/feedback_1.md', '../.aiwf/input/feedback_2.md', '../.aiwf/input/blueprint.md')"

# Step 6: Init tasks
python build_tasks_from_blueprint.py ../.aiwf/input/blueprint.md ../.aiwf/run/

# Step 7: Run execution loop
python orchestrator.py loop
```

---

## Troubleshooting

### CLI Login Issues

```bash
# Claude
claude logout
claude login

# Gemini
gemini logout
gemini login
```

### Python Import Errors

Make sure you're in `vibecode-v6/python/` directory:
```bash
cd vibecode-v6/python
export PYTHONPATH="."
```

### VS Code Extension Not Loading

```bash
cd vibecode-v6/extension
npm run compile
# Restart VS Code
```

---

## Next Steps

Read [USER_GUIDE.md](./USER_GUIDE.md) để biết cách sử dụng chi tiết.
