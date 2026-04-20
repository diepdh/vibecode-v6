# Vibecode v6 - Configuration Guide

## 🔧 CLI Configuration

Vibecode v6 cho phép anh cấu hình Brain và Coder CLI theo ý muốn.

---

## 🧠 Brain CLI Options

Brain được dùng cho:
- **Brain Planner** (Phase A.1) - Tạo plan từ goal
- **Brain Synthesizer** (Phase A.5) - Tổng hợp feedback thành blueprint
- **Brain Reviewer** (Phase B) - Review code của Coder

### **Option 1: Claude Code CLI (Recommended - Default)**

```bash
# Install
npm install -g @anthropic-ai/claude-code

# Login
claude login

# Verify
claude --version

# Set environment (optional - đây là default)
export VIBECODE_BRAIN_CLI="claude"
export VIBECODE_BRAIN_MODEL="claude-sonnet-4-20250514"
```

**Ưu điểm:**
- ✅ Chất lượng cao
- ✅ Hỗ trợ tốt structured outputs
- ✅ Subscription-based (anh đã có)

### **Option 2: OpenAI Codex (Alternative)**

```bash
# Install OpenAI CLI
pip install openai-cli

# Login
export OPENAI_API_KEY="your-api-key"

# Configure Vibecode
export VIBECODE_BRAIN_CLI="openai"
export VIBECODE_BRAIN_MODEL="gpt-4"
```

### **Option 3: Custom CLI Command**

Nếu anh có custom wrapper, config như sau:

```bash
# Ví dụ: custom script gọi API
export VIBECODE_BRAIN_CLI="/path/to/your-brain-cli.sh"
export VIBECODE_BRAIN_MODEL="your-model-name"
```

**Yêu cầu:** CLI command phải support:
```bash
your-cli --model <model> --file <context-file> --prompt-file <prompt-file>
```

---

## 🤖 Coder CLI Options

Coder được dùng cho:
- **Gemini Coder** (Phase B) - Implement tasks

### **Option 1: Gemini CLI (Default)**

```bash
# Install
npm install -g @google/generative-ai-cli

# Login
gemini login

# Verify
gemini --version

# Set environment (optional - đây là default)
export VIBECODE_CODER_CLI="gemini"
export VIBECODE_CODER_MODEL="gemini-2.0-flash-exp"
```

### **Option 2: Claude Code CLI**

Nếu muốn dùng Claude cho cả Brain và Coder:

```bash
export VIBECODE_CODER_CLI="claude"
export VIBECODE_CODER_MODEL="claude-sonnet-4-20250514"
```

**Note:** Sẽ tốn nhiều API credits hơn.

### **Option 3: OpenAI**

```bash
export VIBECODE_CODER_CLI="openai"
export VIBECODE_CODER_MODEL="gpt-4"
```

---

## 📝 Configuration File (Optional)

Tạo file `.vibecode.env` trong project root:

```bash
# Brain Configuration
VIBECODE_BRAIN_CLI=claude
VIBECODE_BRAIN_MODEL=claude-sonnet-4-20250514

# Coder Configuration
VIBECODE_CODER_CLI=gemini
VIBECODE_CODER_MODEL=gemini-2.0-flash-exp

# Timeout (optional)
VIBECODE_CLI_TIMEOUT=300
```

Load trước khi chạy:

```bash
source .vibecode.env
python orchestrator.py loop
```

---

## 🎯 Recommended Configurations

### **Config 1: Best Quality (High Cost)**

```bash
# Brain: Claude Sonnet 4
export VIBECODE_BRAIN_CLI="claude"
export VIBECODE_BRAIN_MODEL="claude-sonnet-4-20250514"

# Coder: Claude Sonnet 4
export VIBECODE_CODER_CLI="claude"
export VIBECODE_CODER_MODEL="claude-sonnet-4-20250514"
```

**Use case:** Production code, critical projects

### **Config 2: Balanced (Recommended)**

```bash
# Brain: Claude Sonnet 4
export VIBECODE_BRAIN_CLI="claude"
export VIBECODE_BRAIN_MODEL="claude-sonnet-4-20250514"

# Coder: Gemini Flash
export VIBECODE_CODER_CLI="gemini"
export VIBECODE_CODER_MODEL="gemini-2.0-flash-exp"
```

**Use case:** Most projects (good quality, reasonable cost)

### **Config 3: Fast & Cheap**

```bash
# Brain: Gemini Flash
export VIBECODE_BRAIN_CLI="gemini"
export VIBECODE_BRAIN_MODEL="gemini-2.0-flash-exp"

# Coder: Gemini Flash
export VIBECODE_CODER_CLI="gemini"
export VIBECODE_CODER_MODEL="gemini-2.0-flash-exp"
```

**Use case:** Prototyping, experiments

---

## 🔍 Verify Configuration

```bash
# Check environment variables
echo $VIBECODE_BRAIN_CLI
echo $VIBECODE_CODER_CLI

# Test Brain CLI
claude --version  # hoặc command của anh

# Test Coder CLI
gemini --version  # hoặc command của anh

# Run dry test
cd vibecode-v6/python
python3 -c "from cli_wrappers import BRAIN_CLI_COMMAND, CODER_CLI_COMMAND; print(f'Brain: {BRAIN_CLI_COMMAND}, Coder: {CODER_CLI_COMMAND}')"
```

---

## 🐛 Troubleshooting

### **Lỗi: "BRAIN_CLI_COMMAND not found"**

```bash
# Check PATH
which claude
which gemini

# Add to PATH if needed
export PATH="$PATH:/usr/local/bin"

# Or set full path
export VIBECODE_BRAIN_CLI="/usr/local/bin/claude"
```

### **Lỗi: "Model not supported"**

```bash
# List available models
claude models list
gemini models list

# Pick one và set
export VIBECODE_BRAIN_MODEL="model-name-here"
```

### **Lỗi: "Authentication failed"**

```bash
# Re-login
claude logout && claude login
gemini logout && gemini login
```

---

## 📊 Performance Comparison

| Configuration | Quality | Speed | Cost | Recommended |
|---------------|---------|-------|------|-------------|
| Claude + Claude | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Production |
| Claude + Gemini | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Default |
| Gemini + Gemini | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Prototyping |

---

## 🚀 Quick Start with Custom Config

```bash
# 1. Set environment
export VIBECODE_BRAIN_CLI="claude"
export VIBECODE_CODER_CLI="gemini"

# 2. Verify
python -c "import os; print('Brain:', os.getenv('VIBECODE_BRAIN_CLI'), 'Coder:', os.getenv('VIBECODE_CODER_CLI'))"

# 3. Run workflow
cd vibecode-v6/python
python orchestrator.py loop
```

---

## 💡 Best Practices

1. **Brain = Claude** cho planning và review (chất lượng cao)
2. **Coder = Gemini** cho execution (nhanh và rẻ)
3. **Timeout = 300s** (5 minutes) cho complex tasks
4. **Save configs** trong `.vibecode.env` để reuse

---

Anh config theo nhu cầu project nhé! 🎯

---

## Windows / Cross-platform notes (new)

### 1) Python temp files

`cli_wrappers.py` now uses Python `tempfile` (no hardcoded `/tmp`), so it works on Windows/Linux/macOS.

### 2) VS Code extension path resolution

`python_bridge.ts` now auto-detects:
- Python executable: `VIBECODE_PYTHON_PATH` (optional), fallback `python` on Windows, `python3` on Unix.
- Scripts directory: `VIBECODE_SCRIPTS_DIR` (optional), otherwise tries common folders and verifies `orchestrator.py`.

Recommended on Windows:

```powershell
$env:VIBECODE_PYTHON_PATH = "python"
$env:VIBECODE_SCRIPTS_DIR = "C:\Users\dohuy\Downloads\vibecode-v6-updated\python"
```

### 3) Brain CLI adapter (for non-Claude CLI formats)

`call_brain_cli()` now invokes `python/brain_cli_adapter.py`.

Useful env vars:

```powershell
# Which brain command to run
$env:VIBECODE_BRAIN_CLI = "codex"   # or "claude", etc.

# Adapter mode:
# - claude_file:  CLI --model ... --file ... --prompt-file ...
# - stdin:        pass prompt via stdin
# - prompt_arg:   CLI ... --prompt "<text>"
$env:VIBECODE_BRAIN_ADAPTER_MODE = "stdin"

# Optional flags
$env:VIBECODE_BRAIN_MODEL_FLAG = "--model"
$env:VIBECODE_BRAIN_CONTEXT_FLAG = "--file"
$env:VIBECODE_BRAIN_PROMPT_FILE_FLAG = "--prompt-file"
$env:VIBECODE_BRAIN_PROMPT_FLAG = "--prompt"
$env:VIBECODE_BRAIN_EXTRA_ARGS = ""
```

If reviewer uses GPT-5.3 Codex CLI with a different command syntax, keep `VIBECODE_BRAIN_CLI=codex` and tune adapter mode/flags above.
