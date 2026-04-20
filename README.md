# Vibecode v6 🧠⚙️

**AI-Orchestrated Coding Workflow với Multi-Agent Planning và Automated Execution**

---

## 🎯 Tổng Quan

Vibecode v6 là một workflow tự động hóa AI coding gồm 2 giai đoạn:

### **Phase A: Planning (Human-in-the-loop)**
- Brain tạo plan từ goal
- Claude và Gemini review độc lập
- Brain tổng hợp feedback → Blueprint cuối cùng

### **Phase B: Execution (Automated Loop)**
- Orchestrator tự động điều phối Coder ↔ Reviewer
- Gemini code → Machine checks → Brain review → Decision
- Loop cho đến khi tất cả tasks PASS hoặc BLOCKED

---

## ✨ Tính Năng

- ✅ **Multi-agent planning** với feedback từ Claude + Gemini
- ✅ **Automated execution loop** không cần manual handoff
- ✅ **Quality gates** với Definition of Done + Machine checks
- ✅ **Safety guardrails** (allowed files, retry limits, escalation)
- ✅ **VS Code Extension** với UI buttons
- ✅ **File-based artifacts** dễ debug và inspect
- ✅ **CLI support** cho automation workflows

---

## 📦 Cài Đặt

### Prerequisites

1. **Claude Code CLI** (với subscription account)
```bash
npm install -g @anthropic-ai/claude-code
claude login
```

2. **Gemini CLI** (với subscription account)
```bash
npm install -g @google/generative-ai-cli
gemini login
```

3. **Python 3.8+**
```bash
python --version
```

4. **VS Code** (optional, cho UI extension)

### Install Vibecode v6

```bash
# Clone repository
git clone https://github.com/your-org/vibecode-v6.git
cd vibecode-v6

# Install VS Code Extension
cd extension
npm install
npm run compile

# Mở VS Code, press F5 để launch Extension Development Host
```

---

## 🚀 Quick Start

### 1. Initialize Project

```bash
mkdir my-project
cd my-project
mkdir -p .aiwf/input
```

### 2. Write Goal

Create `.aiwf/input/goal.md`:

```markdown
# Goal: Add User Profile Feature

## Objective
Create a user profile page with edit capabilities.

## Scope
### In Scope:
- View profile
- Edit profile form
- Avatar upload

### Out of Scope:
- Password change

## Constraints
- Must use existing auth system
- Mobile-first responsive

## Success Criteria
- [ ] Users can view profile
- [ ] Users can edit and save changes
- [ ] Avatar upload works
```

### 3. Run Phase A (Planning)

**Via VS Code:**
1. Open Command Palette (`Cmd+Shift+P`)
2. Run "Vibecode: Show Control Panel"
3. Click buttons in Phase A section

**Via CLI:**
```bash
cd /path/to/vibecode-v6/python

# Generate plan
python -c "from cli_wrappers import generate_plan; generate_plan('.aiwf/input/goal.md', '.aiwf/input/plan.md')"

# Get feedback
python -c "from cli_wrappers import review_plan_claude; review_plan_claude('.aiwf/input/plan.md', '.aiwf/input/feedback_1.md')"
python -c "from cli_wrappers import review_plan_gemini; review_plan_gemini('.aiwf/input/plan.md', '.aiwf/input/feedback_2.md')"

# Synthesize blueprint
python -c "from cli_wrappers import synthesize_blueprint; synthesize_blueprint('.aiwf/input/plan.md', '.aiwf/input/feedback_1.md', '.aiwf/input/feedback_2.md', '.aiwf/input/blueprint.md')"
```

### 4. Run Phase B (Execution)

```bash
# Init tasks
python build_tasks_from_blueprint.py .aiwf/input/blueprint.md .aiwf/run/

# Start automated loop
python orchestrator.py loop

# Monitor status
python orchestrator.py status
```

---

## 📁 Project Structure

```
vibecode-v6/
├── python/                  # Backend logic
│   ├── prompts.py              # Prompt templates cho 6 roles
│   ├── cli_wrappers.py         # Claude/Gemini CLI integration
│   ├── build_tasks_from_blueprint.py
│   └── orchestrator.py         # Main execution engine
├── extension/               # VS Code Extension
│   ├── src/
│   │   ├── extension.ts
│   │   ├── python_bridge.ts
│   │   └── webview.ts
│   └── package.json
├── templates/               # File templates
│   ├── goal.md
│   ├── plan_template.md
│   ├── tasks_template.json
│   └── state_template.json
└── docs/                    # Documentation
    ├── SETUP.md
    ├── USER_GUIDE.md
    └── ARCHITECTURE.md
```

---

## 📖 Documentation

- **[Setup Guide](./docs/SETUP.md)** - Hướng dẫn cài đặt chi tiết
- **[User Guide](./docs/USER_GUIDE.md)** - Cách sử dụng từng bước
- **[Architecture](./docs/ARCHITECTURE.md)** - Kiến trúc hệ thống

---

## 🔄 Workflow Chi Tiết

```
Phase A: Planning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User writes goal.md
    ↓
Brain generates plan.md
    ↓
Claude reviews → feedback_1.md
Gemini reviews → feedback_2.md
    ↓
Brain synthesizes → blueprint.md (FINAL)

Phase B: Execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Parse blueprint → tasks.json
    ↓
Orchestrator Loop:
  ┌────────────────────────────────┐
  │ 1. Gemini Coder implements     │
  │ 2. Run machine checks          │
  │ 3. Get git diff                │
  │ 4. Brain Reviewer evaluates    │
  │ 5. Decision:                   │
  │    - PASS → next task          │
  │    - REVISE → retry (max 2x)   │
  │    - BLOCK → stop, escalate    │
  └────────────────────────────────┘
    ↓
All tasks PASS → Completed! 🎉
```

---

## 🛠️ Commands Reference

### Phase A Commands

```bash
# Generate plan
vibecode.generatePlan

# Get reviews
vibecode.getClaudeFeedback
vibecode.getGeminiFeedback

# Synthesize
vibecode.synthesizeBlueprint
```

### Phase B Commands

```bash
# Orchestrator
python orchestrator.py init    # Initialize tasks
python orchestrator.py run     # Run one iteration
python orchestrator.py loop    # Auto-loop until done
python orchestrator.py status  # Show current status
python orchestrator.py reset   # Reset execution state
```

---

## 🐛 Troubleshooting

### CLI Login Issues

```bash
# Re-login
claude logout && claude login
gemini logout && gemini login
```

### Extension Not Loading

```bash
cd extension
npm run compile
# Restart VS Code
```

### Python Import Errors

```bash
cd vibecode-v6/python
export PYTHONPATH="."
```

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.

---

## 📜 License

MIT License - see [LICENSE](./LICENSE) file.

---

## 🙏 Credits

Built with:
- Claude Code CLI (Anthropic)
- Gemini CLI (Google)
- VS Code Extension API

---

**Vibecode v6** - "Orchestrated AI Coding, Evolved" 🚀
