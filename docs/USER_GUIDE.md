# Vibecode v6 — Hướng Dẫn Sử Dụng

## Runtime source-centric update

Từ bản cập nhật này, workspace không còn nhận bản copy của các runtime Python scripts. Khi chạy trong workspace, luôn gọi orchestrator từ thư mục nguồn Vibecode:

```powershell
python "C:\Users\dohuy\Downloads\vibecode-v6-updated\python\orchestrator.py" --workspace "." <command>
```

`start` chỉ tạo `.aiwf/`, copy instruction files và tạo `goal.md`. Các file sau được lưu và cập nhật tập trung tại gốc `vibecode-v6-updated`, không phụ thuộc workspace:

- `common_failures_runbook.md`
- `AGENT_LESSONS.md`

Điều này giúp mọi workspace mới đều dùng cùng bộ nhớ học tập mới nhất và tránh rác file như `orchestrator.py`, `build_tasks_from_blueprint.py`, `cli_wrappers.py`, `prompts.py`, `brain_cli_adapter.py` trong từng workspace.
## Tổng quan hệ thống

Vibecode v6 là pipeline tự động hoá 3 Agent: **Brain → Coder → Reviewer**.  
Mỗi Agent có vai trò riêng biệt, giao tiếp qua file `.md`, và học hỏi từ các lần chạy trước.

```
Phase A: Planning (Human-in-the-loop)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Viết goal.md
2. Brain tạo plan.md
3. Claude review → feedback_1.md
4. Gemini review → feedback_2.md
5. Brain tổng hợp → blueprint.md + contract.md  ← NEW: 2 files bắt buộc
   ↓
Phase B: Execution (Tự động hoàn toàn)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. Parse blueprint → tasks.json
7. Orchestrator auto-loop:
   [Instruction] + [Lessons] → Coder → Checks → Reviewer → Decision
   Lặp cho đến khi tất cả tasks PASS hoặc BLOCKED
   ↓
Phase C: Learning (Tự động sau mỗi run)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8. Phân tích failures → cập nhật common_failures_runbook.md
9. Chắt lọc runbook → AGENT_LESSONS.md (bộ nhớ học tập)
   → Lần chạy tiếp theo: agents đọc AGENT_LESSONS.md trước khi làm việc
```

---

## Cấu trúc file

```
vibecode-v6/
├── BRAIN_AGENT_INSTRUCTION_v2.md     ← Hướng dẫn vai trò Brain
├── CODER_AGENT_INSTRUCTION_v2.md     ← Hướng dẫn vai trò Coder
├── REVIEWER_AGENT_INSTRUCTION_v2.md  ← Hướng dẫn vai trò Reviewer
├── common_failures_runbook.md        ← Log lỗi tích lũy (tự động cập nhật)
├── AGENT_LESSONS.md                  ← Bài học chắt lọc (tự động tạo sau run)
│
├── python/
│   ├── orchestrator.py               ← Engine điều phối chính
│   ├── prompts.py                    ← Tất cả prompt templates
│   ├── build_tasks_from_blueprint.py ← Parse blueprint → tasks.json
│   ├── cli_wrappers.py               ← Wrapper gọi CLI agents
│   └── brain_cli_adapter.py          ← Bridge cho nhiều loại Brain CLI
│
└── .aiwf/
    ├── input/
    │   ├── goal.md
    │   ├── plan.md
    │   ├── feedback_1.md
    │   ├── feedback_2.md
    │   ├── blueprint.md              ← Kiến trúc tổng thể
    │   ├── contract.md               ← Scope & DoD (NEW - bắt buộc)
    │   ├── common_failures_runbook.md ← Copy từ workspace root
    │   └── AGENT_LESSONS.md          ← Copy từ workspace root
    └── run/
        ├── tasks.json
        ├── state.json
        ├── coder_report.txt
        ├── review.json
        ├── test_output.txt
        ├── runbook_update.txt        ← Output phân tích failures
        ├── agent_lessons_draft.txt   ← Output draft lessons
        └── logs/
            └── orchestrator.log
```

---

## Phase A: Planning

### Bước 1 — Viết goal.md

Tạo file `.aiwf/input/goal.md`:

```markdown
# Goal: [Tên dự án]

## Objective
[Mô tả mục tiêu cuối cùng]

## Scope
### In Scope:
- [Tính năng 1]
- [Tính năng 2]

### Out of Scope:
- [Không làm gì]

## Constraints
- [Ràng buộc kỹ thuật]

## Success Criteria
- [ ] [Tiêu chí đo được 1]
- [ ] [Tiêu chí đo được 2]
```

---

### Bước 2 — Tạo Plan

**VS Code:** Command Palette → `Vibecode: Generate Plan`

**CLI:**
```bash
cd vibecode-v6/python
python -c "from cli_wrappers import generate_plan; generate_plan('.aiwf/input/goal.md', '.aiwf/input/plan.md')"
```

**Output:** `.aiwf/input/plan.md`

---

### Bước 3 & 4 — Lấy Feedback

**VS Code:**
- `Vibecode: Get Claude Feedback`
- `Vibecode: Get Gemini Feedback`

**CLI:**
```bash
# Claude review
python -c "from cli_wrappers import review_plan_claude; review_plan_claude('.aiwf/input/plan.md', '.aiwf/input/feedback_1.md')"

# Gemini review
python -c "from cli_wrappers import review_plan_gemini; review_plan_gemini('.aiwf/input/plan.md', '.aiwf/input/feedback_2.md')"
```

**Output:** `feedback_1.md`, `feedback_2.md`

---

### Bước 5 — Tổng hợp Blueprint + Contract

> ⚠️ **Bắt buộc sinh CẢ HAI file:** `blueprint.md` và `contract.md`.  
> Brain Synthesizer sẽ đảm bảo hai file này đồng bộ với nhau.

**VS Code:** `Vibecode: Synthesize Blueprint`

**CLI:**
```bash
python -c "from cli_wrappers import synthesize_blueprint; synthesize_blueprint('.aiwf/input/plan.md', '.aiwf/input/feedback_1.md', '.aiwf/input/feedback_2.md', '.aiwf/input/blueprint.md')"
```

**Output:**
- `.aiwf/input/blueprint.md` — Kiến trúc, module map, data flow, tech decisions
- `.aiwf/input/contract.md` — Scope, Out-of-Scope, Definition of Done, môi trường

**Kiểm tra đồng bộ:** Mọi module trong `blueprint.md` phải có deliverable tương ứng trong `contract.md`.

---

## Phase B: Execution

### Bước 6 — Khởi tạo Tasks

Parse blueprint thành tasks.json:

**VS Code:** `Vibecode: Init Tasks`

**CLI:**
```bash
cd vibecode-v6/python
python build_tasks_from_blueprint.py .aiwf/input/blueprint.md .aiwf/run/
```

**Output:**
- `.aiwf/run/tasks.json` — Danh sách tasks với DoD, allowed files, machine checks
- `.aiwf/run/state.json` — Trạng thái khởi tạo

---

### Bước 7 — Chạy Execution Loop

**VS Code:** `Vibecode: Start Execution Loop`

**CLI:**
```bash
cd vibecode-v6/python
python orchestrator.py loop
```

**Mỗi iteration, orchestrator thực hiện:**

```
1. Load coder instruction   (CODER_AGENT_INSTRUCTION_v2.md)
   + Load agent lessons      (AGENT_LESSONS.md — bài học từ runs trước)
   ↓
2. Gọi Coder → implement task
   ↓
3. Chạy machine checks (test/lint/build)
   ↓
4. Lấy git diff
   ↓
5. Load reviewer instruction (REVIEWER_AGENT_INSTRUCTION_v2.md)
   + Load agent lessons       (AGENT_LESSONS.md)
   ↓
6. Gọi Reviewer → đánh giá theo CONTRACT + GATE
   ↓
7. Quyết định:
   PASS   → task tiếp theo
   REVISE → retry (tối đa 2 lần)
   BLOCK  → dừng, chờ human
```

**Loop kết thúc khi:**
- ✅ Tất cả tasks PASS → `status: "completed"`
- 🚧 Gặp BLOCK → `status: "blocked"`
- ⚠️ Max retries exceeded → `status: "blocked"`

---

## Phase C: Learning Loop

Đây là điểm khác biệt chính của Vibecode v6 — **agents cải thiện theo thời gian**.

### Cơ chế học tập

```
Sau mỗi workflow (completed / blocked / max_iterations):
  │
  ├─► post_workflow_runbook_update()
  │     Thu thập REVISE/BLOCK events từ review JSONs
  │     Gọi Brain phân tích → tìm pattern lỗi MỚI
  │     Append vào common_failures_runbook.md
  │
  └─► synthesize_agent_lessons()
        Gọi Brain chắt lọc toàn bộ runbook
        Tạo AGENT_LESSONS.md — 3 phần: Brain / Coder / Reviewer
        Lần chạy tiếp theo: mỗi agent đọc file này TRƯỚC KHI làm việc
```

### AGENT_LESSONS.md trông như thế nào

```markdown
# AGENT_LESSONS.md — Bài học tích lũy

## Cho Brain (Planner & Synthesizer)
### Quy tắc PHẢI LÀM:
1. Luôn sinh cả blueprint.md VÀ contract.md đồng bộ
2. ...

### Bẫy hay gặp nhất:
- **Blueprint thiếu Contract**: module không có deliverable → coder over-engineer
- ...

## Cho Coder
### Quy tắc PHẢI LÀM:
1. Đọc đủ 4 file: JOB BRIEF, BLUEPRINT, CONTRACT, GATE trước khi code
2. ...

## Cho Reviewer
### Quy tắc PHẢI LÀM:
...

## Top 5 lỗi nghiêm trọng nhất:
1. ...
```

### Chạy thủ công

Khi muốn cập nhật AGENT_LESSONS.md ngay mà không cần chờ hết workflow:

```bash
cd vibecode-v6/python
python orchestrator.py synthesize-lessons
```

---

## Quản lý & Giám sát

### Xem trạng thái

```bash
python orchestrator.py status
```

**Output:**
```
VIBECODE v6 - ORCHESTRATOR STATUS
==================================
Status: RUNNING
Current Task: 3/10
Completed: 2
Current Retry: 1/2

Completed Tasks:
  [DONE] T001 - 2024-04-20T10:30:00
  [DONE] T002 - 2024-04-20T11:00:00

Current Task:
  ID: T003
  Title: Create profile edit form
  DoD: 5 criteria
```

### Xử lý BLOCKED

Khi workflow bị block:

**1. Đọc lý do:**
```bash
python orchestrator.py status
# → Hiển thị blocked_task.reason

# Chi tiết hơn:
cat .aiwf/run/review.json
cat .aiwf/run/coder_report.txt
cat .aiwf/run/test_output.txt
```

**2. Xem logs:**
```bash
cat .aiwf/run/logs/orchestrator.log
```

**3. Giải quyết vấn đề rồi tiếp tục:**
```bash
# Option A: Tiếp tục từ task bị block (sau khi fix)
python orchestrator.py resume

# Option B: Bỏ qua task bị block, chuyển sang task tiếp theo
python orchestrator.py unblock

# Option C: Reset toàn bộ từ đầu
python orchestrator.py reset
```

### Chuyển đổi Coder

```bash
# Dùng Gemini làm Coder
python orchestrator.py set-coder gemini

# Dùng Claude làm Coder
python orchestrator.py set-coder claude
```

### Cấu hình Brain / Reviewer

```bash
python orchestrator.py set-brain <cli_command> [reviewer_model] [brain_model]

# Ví dụ với Codex:
python orchestrator.py set-brain codex.cmd gpt-5.3-codex gpt-5.4
```

---

## Chạy workflow từ folder dự án khác

Mặc định, orchestrator dùng thư mục hiện tại làm workspace (nơi chứa `.aiwf/`).
Nếu bạn muốn chạy từ một thư mục khác (ví dụ: script nằm trong `vibecode-v6/python/`
nhưng dự án nằm ở `C:/Projects/my-app/`), dùng flag `--workspace` (hoặc `-w`).

### Cấu trúc yêu cầu tại workspace

```
<workspace>/                         ← đây là đường dẫn truyền vào --workspace
├── .aiwf/
│   ├── input/
│   │   ├── goal.md
│   │   ├── blueprint.md
│   │   ├── contract.md
│   │   └── ...
│   └── run/
│       ├── tasks.json
│       └── state.json
├── CODER_AGENT_INSTRUCTION_v2.md    ← hoặc đặt cùng chỗ với vibecode-v6/
├── REVIEWER_AGENT_INSTRUCTION_v2.md
└── [source code của dự án]
```

> **Lưu ý:** File instruction (`BRAIN_AGENT_INSTRUCTION_v2.md`, v.v.) được tìm kiếm
> từ workspace lên tối đa 3 cấp thư mục cha, nên chỉ cần đặt ở một trong các vị trí đó.

### Bước 0 — Khởi tạo workspace với lệnh `start`

Lệnh `start` tự động tạo toàn bộ cấu trúc thư mục và copy các file cơ sở cần thiết
từ thư mục cài đặt vibecode-v6 vào workspace của bạn.

```bash
cd vibecode-v6/python

python orchestrator.py --workspace "C:/Projects/my-app" start
# hoặc viết tắt:
python orchestrator.py -w "C:/Projects/my-app" start
# hoặc từ thư mục đang đứng
python "C:\Users\dohuy\Downloads\vibecode-v6-updated\python\orchestrator.py" --workspace "." start
```

**Output mẫu:**
```
Vibecode v6 — Khởi tạo workspace mới
  Workspace : C:\Projects\my-app
  Nguồn     : C:\vibecode-v6

[OK] Tạo thư mục: .aiwf/input/  .aiwf/run/logs/
[OK]  Copy          : BRAIN_AGENT_INSTRUCTION_v2.md
[OK]  Copy          : CODER_AGENT_INSTRUCTION_v2.md
[OK]  Copy          : REVIEWER_AGENT_INSTRUCTION_v2.md
[OK]  Copy          : common_failures_runbook.md → my-app/
[OK]  Copy          : common_failures_runbook.md → input/
[OK]  Copy          : AGENT_LESSONS.md → my-app/
[OK]  Copy          : AGENT_LESSONS.md → input/
[OK]  Tạo template  : .aiwf/input/goal.md

============================================================
Workspace đã sẵn sàng! Bước tiếp theo:

  1. Chỉnh sửa goal.md:
       C:\Projects\my-app\.aiwf\input\goal.md

  2. [Tuỳ chọn] Cấu hình Brain/Coder CLI:
       python orchestrator.py -w "C:\Projects\my-app" set-coder claude

  3. Sau khi có blueprint.md + contract.md:
       python orchestrator.py -w "C:\Projects\my-app" init

  4. Chạy workflow:
       python orchestrator.py -w "C:\Projects\my-app" loop
============================================================
```

**Files được copy vào workspace:**

| File | Đích | Mô tả |
|------|------|-------|
| `BRAIN_AGENT_INSTRUCTION_v2.md` | `workspace/` | Hướng dẫn vai trò Brain |
| `CODER_AGENT_INSTRUCTION_v2.md` | `workspace/` | Hướng dẫn vai trò Coder |
| `REVIEWER_AGENT_INSTRUCTION_v2.md` | `workspace/` | Hướng dẫn vai trò Reviewer |
| `common_failures_runbook.md` | `workspace/` + `.aiwf/input/` | Log lỗi tích lũy |
| `AGENT_LESSONS.md` | `workspace/` + `.aiwf/input/` | Bài học (nếu đã có) |
| `templates/goal.md` | `.aiwf/input/goal.md` | Template viết goal |

> **Lưu ý:** Nếu file đã tồn tại tại đích, lệnh `start` sẽ bỏ qua (`[SKIP]`) và không ghi đè.

---

### Cú pháp các lệnh khác

```bash
cd vibecode-v6/python

# Chạy loop cho dự án ở folder khác
python orchestrator.py --workspace /path/to/my-project loop

python "C:\Users\dohuy\Downloads\vibecode-v6-updated\python\orchestrator.py" --workspace "C:\Users\dohuy\Downloads\01. Documents\Bubble_1" loop

#Nếu đứng trong thư mục luôn
python "C:\Users\dohuy\Downloads\vibecode-v6-updated\python\orchestrator.py" --workspace "." loop

# Dùng đường dẫn tương đối
python orchestrator.py -w ../../my-project loop

# Windows
python orchestrator.py --workspace "C:\Projects\my-app" loop
python orchestrator.py -w "C:/Projects/my-app" loop
```

### Ví dụ thực tế — workflow đầy đủ cho dự án nằm ngoài vibecode

```bash
# Bước 0: Khởi tạo workspace (chỉ cần làm 1 lần)
python orchestrator.py --workspace "C:/Projects/my-app" start

python "C:\Users\dohuy\Downloads\vibecode-v6-updated\python\orchestrator.py" --workspace "." loop
# → Chỉnh sửa .aiwf/input/goal.md, sau đó dùng Brain để tạo blueprint + contract

# Bước 1: Khởi tạo tasks từ blueprint
python orchestrator.py --workspace "C:/Projects/my-app" init

# Bước 2: Chạy execution loop
python orchestrator.py --workspace "C:/Projects/my-app" loop

# Bước 3: Kiểm tra trạng thái (nếu bị block)
python orchestrator.py --workspace "C:/Projects/my-app" status

# Bước 4: Tiếp tục sau khi fix
python orchestrator.py --workspace "C:/Projects/my-app" resume

# Bước 5: Cập nhật bài học
python orchestrator.py --workspace "C:/Projects/my-app" synthesize-lessons

python "C:\Users\dohuy\Downloads\vibecode-v6-updated\python\orchestrator.py" --workspace "." synthesize-lessons
```

### Kết hợp với set-coder / set-brain

```bash
# Đổi coder cho workspace cụ thể
python orchestrator.py --workspace "C:/Projects/my-app" set-coder claude

# Cấu hình Brain CLI cho workspace cụ thể
python orchestrator.py -w "C:/Projects/my-app" set-brain codex.cmd gpt-5.3-codex gpt-5.4
```

> **Mẹo Windows:** Dùng dấu `/` hoặc `\` đều được. Nếu đường dẫn có khoảng trắng, luôn đặt trong dấu ngoặc kép.

---

## Danh sách lệnh CLI đầy đủ

Tất cả lệnh đều hỗ trợ flag `--workspace <path>` / `-w <path>` đặt trước tên lệnh.

| Lệnh | Mô tả |
|------|-------|
| `python orchestrator.py start` | Khởi tạo workspace mới (copy files cơ sở, tạo `.aiwf/`) |
| `python orchestrator.py init` | Parse blueprint → tasks.json + state.json |
| `python orchestrator.py loop` | Chạy execution loop đến khi xong hoặc blocked |
| `python orchestrator.py run` | Chạy một iteration duy nhất |
| `python orchestrator.py status` | Xem trạng thái hiện tại |
| `python orchestrator.py resume` | Clear blocked state, tiếp tục loop |
| `python orchestrator.py unblock` | Force-skip task bị block |
| `python orchestrator.py reset` | Reset toàn bộ execution state |
| `python orchestrator.py set-coder <name>` | Đổi coder: `gemini` hoặc `claude` |
| `python orchestrator.py set-brain <cli> [models]` | Cấu hình Brain CLI |
| `python orchestrator.py synthesize-lessons` | Chắt lọc runbook → AGENT_LESSONS.md |

**Flag workspace:**

| Flag | Ví dụ | Mô tả |
|------|-------|-------|
| `--workspace <path>` | `--workspace /home/user/project` | Chỉ định thư mục gốc dự án |
| `-w <path>` | `-w C:/Projects/app` | Viết tắt của `--workspace` |

---

## Nguyên tắc vàng khi dùng

### Trước khi chạy workflow

1. **Đặt instruction files đúng chỗ:**  
   `BRAIN_AGENT_INSTRUCTION_v2.md`, `CODER_AGENT_INSTRUCTION_v2.md`, `REVIEWER_AGENT_INSTRUCTION_v2.md`  
   phải nằm ở **workspace root** (cùng cấp với thư mục `python/`).

2. **Copy runbook vào input dir:**
   ```bash
   cp common_failures_runbook.md .aiwf/input/
   cp AGENT_LESSONS.md .aiwf/input/   # nếu đã có từ lần trước
   ```

3. **Kiểm tra blueprint + contract đồng bộ:**  
   Mọi module trong `blueprint.md` phải có deliverable trong `contract.md`.

### Trong khi chạy

- Không edit `tasks.json` hay `state.json` khi orchestrator đang chạy — luôn stop trước
- Nếu cần thay đổi machine checks trong `tasks.json`, restart orchestrator sau khi sửa
- Theo dõi `orchestrator.log` để debug: `cat .aiwf/run/logs/orchestrator.log`

### Sau khi workflow xong

- Orchestrator tự động cập nhật `common_failures_runbook.md` và `AGENT_LESSONS.md`
- Commit cả hai file này vào git để team chia sẻ bộ nhớ học tập
- Đọc `AGENT_LESSONS.md` để hiểu hệ thống đang học gì từ các lần chạy

---

## Best Practices

### Viết Definition of Done tốt

**Tốt:**
```
- [ ] File `src/auth/login.ts` tồn tại và export hàm `loginUser()`
- [ ] `pnpm test auth` pass với 0 failures
- [ ] Response status 401 khi sai password
```

**Xấu:**
```
- [ ] Auth hoạt động được
- [ ] Code chạy ổn
```

### Kích thước task hợp lý

- **15–45 phút** mỗi task là lý tưởng
- Nếu task > 1 giờ: tách nhỏ hơn
- Nếu task < 10 phút: có thể gộp với task liên quan

### Allowed Files phải cụ thể

**Tốt:**
```
- `src/components/UserProfile.tsx`
- `src/hooks/useProfile.ts`
- `tests/unit/profile.test.ts`
```

**Xấu:**
```
- `src/**/*`
- `*.ts`
```

---

## Troubleshooting

### REVISE loop liên tục

**Nguyên nhân:** DoD mơ hồ hoặc Coder và Reviewer hiểu khác nhau.

**Fix:**
1. Stop loop
2. Đọc `review.json` để xem reviewer yêu cầu gì cụ thể
3. Làm rõ DoD trong `tasks.json` — thêm tiêu chí định lượng
4. Restart orchestrator sau khi sửa
5. Resume loop

### Coder tạo file ngoài allowed_files

**Nguyên nhân:** allowed_files quá hẹp hoặc task scope không rõ.

**Fix:**
1. Reviewer sẽ BLOCK việc này
2. Mở rộng `allowed_files` trong `blueprint.md`
3. Rebuild tasks: `python build_tasks_from_blueprint.py .aiwf/input/blueprint.md .aiwf/run/`
4. Reset và resume

### Machine checks fail

**Nguyên nhân:** Coder làm hỏng test hiện có.

**Fix:**
1. Xem chi tiết: `cat .aiwf/run/test_output.txt`
2. Sửa code để pass tests
3. Resume: `python orchestrator.py resume`

### Reviewer JSON parse error

**Nguyên nhân:** Reviewer CLI timeout hoặc trả về output không đúng schema.

**Fix:**
1. Mở `review.json` xem nội dung thực tế
2. Nếu bị cắt: tăng timeout reviewer, chạy lại
3. Nếu sai schema: kiểm tra reviewer prompt có yêu cầu JSON format rõ không

**Xem thêm:** `common_failures_runbook.md` — entry #11 và các entries liên quan

### Blueprint/Contract không đồng bộ

**Nguyên nhân:** Brain Synthesizer chỉ tạo `blueprint.md`, thiếu `contract.md`.

**Fix:**
1. Kiểm tra xem `contract.md` có tồn tại không:  
   `ls .aiwf/input/contract.md`
2. Nếu thiếu: chạy lại bước Synthesize, đảm bảo Brain sinh cả 2 file
3. Cross-check: mọi module trong blueprint có deliverable trong contract không

**Xem thêm:** `common_failures_runbook.md` — entry #36

---

## Cách đóng góp cải tiến cho hệ thống

Khi phát hiện pattern lỗi mới chưa có trong runbook:

1. Thêm thủ công vào `common_failures_runbook.md` theo format:
   ```markdown
   ### [N]) [Tên lỗi]
   - Dấu hiệu: ...
   - Nguyên nhân gốc: ...
   - Xử trí chuẩn: ...
   - Phòng ngừa: ...
   ```

2. Chạy `python orchestrator.py synthesize-lessons` để cập nhật AGENT_LESSONS.md ngay

3. Commit cả hai file để team cùng được hưởng lợi

---

## Đọc thêm

- [ARCHITECTURE.md](./ARCHITECTURE.md) — Thiết kế hệ thống chi tiết
- [SETUP.md](./SETUP.md) — Cài đặt từ đầu
- [WINDOWS_WORKFLOW_FROM_SCRATCH.md](./WINDOWS_WORKFLOW_FROM_SCRATCH.md) — Hướng dẫn Windows
- `BRAIN_AGENT_INSTRUCTION_v2.md` — Vai trò và quy tắc của Brain
- `CODER_AGENT_INSTRUCTION_v2.md` — Vai trò và quy tắc của Coder
- `REVIEWER_AGENT_INSTRUCTION_v2.md` — Vai trò và quy tắc của Reviewer
- `common_failures_runbook.md` — Toàn bộ lỗi đã gặp và cách xử lý
- `AGENT_LESSONS.md` — Bài học chắt lọc (xem để hiểu hệ thống đang học gì)

