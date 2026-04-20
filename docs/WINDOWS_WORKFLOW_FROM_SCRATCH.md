# Vibecode Workflow Trên Windows (From Scratch)

Tài liệu này là checklist chạy lại toàn bộ workflow khi bắt đầu từ một workspace mới.

## 1) Chuẩn bị môi trường (làm 1 lần)

### 1.1 Cài Python, Node.js
- Python 3.10+ (`python --version`)
- Node.js + npm (`node -v`, `npm -v`)

### 1.2 Cài Codex CLI (Brain/Reviewer)
```powershell
npm i -g @openai/codex
codex --version
```

Đăng nhập:
```powershell
codex
```

### 1.3 Cài Gemini CLI (Coder)
```powershell
npm i -g @google/generative-ai-cli
gemini --version
gemini login
```

### 1.4 Xác nhận repo workflow
Giả sử repo workflow đang ở:
`C:\Users\dohuy\Downloads\vibecode-v6-updated`

Python scripts nằm ở:
`C:\Users\dohuy\Downloads\vibecode-v6-updated\python`

---

## 2) Tạo workspace mới cho dự án

Ví dụ tạo workspace mới:
```powershell
mkdir C:\work\my-new-project
cd C:\work\my-new-project
mkdir .aiwf
mkdir .aiwf\input
mkdir .aiwf\run
mkdir .aiwf\run\logs
```

Copy template goal:
```powershell
Copy-Item "C:\Users\dohuy\Downloads\vibecode-v6-updated\templates\goal.md" ".aiwf\input\goal.md"
```

---

## 3) Set biến môi trường cho phiên terminal hiện tại

Chạy trong PowerShell trước khi chạy workflow:

```powershell
# Python bridge/scripts
$env:VIBECODE_PYTHON_PATH = "python"
$env:VIBECODE_SCRIPTS_DIR = "C:\Users\dohuy\Downloads\vibecode-v6-updated\python"

# Brain/Reviewer dùng Codex CLI
$env:VIBECODE_BRAIN_CLI = "codex"

# Phase A Brain model (plan + synthesize)
$env:VIBECODE_BRAIN_PHASE_A_MODEL = "gpt-5.4"

# Phase B Reviewer model
$env:VIBECODE_REVIEWER_MODEL = "gpt-5.3-codex"

# Coder dùng Gemini CLI
$env:VIBECODE_CODER_CLI = "gemini"

# Để trống để Gemini CLI tự chọn model theo ngữ cảnh/cost
$env:VIBECODE_CODER_MODEL = ""

# Brain adapter mode (thường dùng stdin ổn nhất với codex)
$env:VIBECODE_BRAIN_ADAPTER_MODE = "stdin"
```

Kiểm tra nhanh:
```powershell
python -c "import os; print('BRAIN_CLI=', os.getenv('VIBECODE_BRAIN_CLI')); print('PHASE_A_MODEL=', os.getenv('VIBECODE_BRAIN_PHASE_A_MODEL')); print('REVIEWER_MODEL=', os.getenv('VIBECODE_REVIEWER_MODEL')); print('CODER_CLI=', os.getenv('VIBECODE_CODER_CLI')); print('CODER_MODEL=', repr(os.getenv('VIBECODE_CODER_MODEL')))"
```

---

## 4) Phase A (anh làm thủ công bằng chat)

## Mục tiêu đầu ra của Phase A
Cần có đủ 4 file:
- `.aiwf/input/plan.md`
- `.aiwf/input/feedback_1.md`
- `.aiwf/input/feedback_2.md`
- `.aiwf/input/blueprint.md`

### Bước A1: Brain tạo plan
1. Mở `.aiwf/input/goal.md` và điền yêu cầu dự án.
2. Dùng Brain (GPT-5.4) tạo `plan.md`.
3. Lưu vào `.aiwf/input/plan.md`.

### Bước A2: Claude góp ý
1. Copy nội dung `plan.md` sang Claude web chat.
2. Yêu cầu review kế hoạch.
3. Lưu phản hồi vào `.aiwf/input/feedback_1.md`.

### Bước A3: Gemini góp ý
1. Copy `plan.md` sang Gemini web chat.
2. Yêu cầu review độc lập.
3. Lưu vào `.aiwf/input/feedback_2.md`.

### Bước A4: Brain tổng hợp blueprint
1. Đưa `plan.md + feedback_1.md + feedback_2.md` cho Brain (GPT-5.4).
2. Yêu cầu synthesize thành blueprint.
3. Lưu vào `.aiwf/input/blueprint.md`.

---

## 5) Khởi tạo tasks/state từ blueprint

```powershell
cd C:\Users\dohuy\Downloads\vibecode-v6-updated\python
python build_tasks_from_blueprint.py C:\work\my-new-project\.aiwf\input\blueprint.md C:\work\my-new-project\.aiwf\run\
```

Kết quả cần có:
- `C:\work\my-new-project\.aiwf\run\tasks.json`
- `C:\work\my-new-project\.aiwf\run\state.json`

---

## 6) Phase B chạy loop tự động

```powershell
cd C:\Users\dohuy\Downloads\vibecode-v6-updated\python
python orchestrator.py loop
```

Xem trạng thái:
```powershell
python orchestrator.py status
```

---

## 7) Luồng quyết định trong Phase B

- `PASS`: task hoàn thành, qua task tiếp theo.
- `REVISE`: coder sửa theo feedback reviewer, retry cùng task.
- `BLOCK`: dừng loop để anh xử lý thủ công.

Reviewer là GPT-5.3 Codex theo biến:
`VIBECODE_REVIEWER_MODEL=gpt-5.3-codex`.

Coder là Gemini CLI; nếu `VIBECODE_CODER_MODEL=""` thì CLI tự chọn model.

---

## 8) Khi bị BLOCKED thì làm gì

Đọc file:
- `.aiwf/run/review.json`
- `.aiwf/run/test_output.txt`
- `.aiwf/run/logs/orchestrator.log`

Sau khi xử lý:
- Sửa code/blueprint/task nếu cần.
- Chạy lại:
```powershell
python orchestrator.py loop
```

Nếu muốn reset toàn bộ tiến trình:
```powershell
python orchestrator.py reset
```

---

## 9) Checklist ngắn gọn mỗi lần bắt đầu dự án mới

1. Tạo workspace + `.aiwf/input`, `.aiwf/run/logs`.
2. Set env variables (Section 3).
3. Viết `goal.md`.
4. Làm đủ 4 file đầu ra Phase A.
5. Build `tasks.json/state.json`.
6. Chạy `orchestrator.py loop`.
7. Theo dõi `status` đến khi `completed`.

---

## 10) Lỗi hay gặp

### `codex` hoặc `gemini` không nhận lệnh
- Kiểm tra cài global npm.
- Mở terminal mới sau khi cài.
- Chạy lại `codex --version`, `gemini --version`.

### `tasks.json not found`
- Chưa chạy bước build từ blueprint hoặc path sai.

### Reviewer trả JSON lỗi
- Mở `review.json` kiểm tra output.
- Chạy lại iteration hoặc giảm prompt nhiễu.

### Quên set biến môi trường
- Quay lại Section 3 và set lại trong terminal hiện tại.

---

## 11) Chạy hoàn toàn bằng giao diện VS Code (bản nâng cấp)

Extension đã có các lệnh mới:
- `Vibecode: Init Workspace`
- `Vibecode: Prepare Manual Phase A`
- Dashboard trạng thái ngay trong `Vibecode: Show Control Panel`
- `Vibecode` settings trong VS Code (không cần nhớ env mỗi lần)

### 11.1 Cài extension local từ source
```powershell
cd C:\Users\dohuy\Downloads\vibecode-v6-updated\extension
npm install
npm run compile
npx vsce package
```

Trong VS Code:
1. Mở Extensions
2. `...` -> `Install from VSIX...`
3. Chọn file `.vsix` vừa tạo

### 11.2 Cấu hình trong VS Code Settings
Mở Settings và tìm `Vibecode`, điền:
- `vibecode.scriptsDir`: `C:\Users\dohuy\Downloads\vibecode-v6-updated\python`
- `vibecode.brainCli`: `codex`
- `vibecode.brainPhaseAModel`: `gpt-5.4`
- `vibecode.reviewerModel`: `gpt-5.3-codex`
- `vibecode.coderCli`: `gemini`
- `vibecode.coderModel`: để trống (Gemini tự chọn)
- `vibecode.brainAdapterMode`: `stdin`

### 11.3 Luồng thao tác từ UI
1. Mở folder dự án mới.
2. Mở command `Vibecode: Show Control Panel`.
3. Bấm `Init Workspace`.
4. Bấm `Prepare Manual Phase A`.
5. Làm Phase A theo checklist trong `.aiwf/input/PHASE_A_MANUAL_CHECKLIST.md`.
6. Bấm `Init Tasks`.
7. Bấm `Start Loop`.
8. Theo dõi dashboard và `Show Status`.
