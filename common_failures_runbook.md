# Sổ Tay Lỗi Thường Gặp Cho Automation (Vibecode)

## Mục đích
Tài liệu này tổng hợp lỗi đã gặp trong các vòng chạy thực tế và cách xử trí chuẩn.
Khi Brain viết `blueprint.md`, bắt buộc đọc tài liệu này để phòng lỗi từ sớm.
Khi coder thực thi task, phải kiểm tra các mục liên quan trước khi báo `STATUS: DONE`.

## Quy tắc bắt buộc khi viết Blueprint
- Mỗi task phải có **bằng chứng đầu ra (artifact evidence)** rõ ràng, không chỉ mô tả chung chung.
- Mỗi task kỹ thuật phải có **machine check có thể chạy được** trong đúng working directory.
- Nếu task liên quan sweep/solver, DoD phải có **convergence policy định lượng**.
- Nếu task sinh nhiều file logs/metadata, DoD phải có **manifest kiểm đếm đầy đủ**.
- Mỗi task nên có mục "Pitfalls & Mitigation" để coder tránh lỗi ngay từ đầu.
- Tất cả tài liệu báo cáo/handover/readme cho các version tiếp theo phải viết bằng **tiếng Việt có dấu**.

## Chính sách ngôn ngữ tài liệu (bắt buộc)
- Phạm vi áp dụng: `docs/*.md`, `README.md`, báo cáo kỹ thuật, handover, validation notes.
- Chuẩn bắt buộc: tiếng Việt có dấu, câu từ rõ ràng, giữ nguyên thuật ngữ kỹ thuật cần thiết.
- Không chấp nhận bản tiếng Anh làm bản chính thức để bàn giao nội bộ.
- Nếu nhận đầu vào tiếng Anh, coder phải chuyển sang tiếng Việt có dấu trước khi báo DONE.

## Template chèn vào mỗi task trong Blueprint
```markdown
**Pitfalls & Mitigation:**
- Pitfall 1: [mô tả lỗi dễ gặp]
  - Mitigation: [cách phòng ngay từ đầu]
- Pitfall 2: [mô tả]
  - Mitigation: [cách phòng]
```

## Nhóm lỗi thường gặp và cách xử trí

### 1) Coder CLI chưa đăng nhập / sai phiên đăng nhập
- Dấu hiệu:
  - `Coder not authenticated`
  - `Please run /login`
- Nguyên nhân gốc:
  - CLI đổi phiên hoặc token hết hạn.
- Xử trí chuẩn:
  1. Đăng nhập đúng CLI đang dùng (`gemini` hoặc `claude`).
  2. Kiểm tra lại bằng lệnh version/ping ở cùng terminal.
  3. Chạy lại orchestrator.
- Phòng ngừa:
  - Preflight phải kiểm tra auth trước Step 1.

### 2) Chạy test sai thư mục dẫn tới `no tests ran`
- Dấu hiệu:
  - `python -m pytest -q` trả `no tests ran in 0.00s`.
- Nguyên nhân gốc:
  - Machine check chạy ở root sai (không phải `xphd_python`).
- Xử trí chuẩn:
  1. Đặt `repo_root` đúng vào `xphd_python`.
  2. Chạy lại `python -m pytest -q` từ đúng thư mục.
- Phòng ngừa:
  - Blueprint ghi rõ "check chạy từ repo root nào".

### 3) Encoding Windows (cp1252) làm crash subprocess
- Dấu hiệu:
  - `UnicodeEncodeError` hoặc `UnicodeDecodeError` với `charmap`.
- Nguyên nhân gốc:
  - Output chứa tiếng Việt có dấu, console/pipe dùng cp1252.
- Xử trí chuẩn:
  1. Dùng UTF-8 khi đọc/ghi file và subprocess (`encoding='utf-8', errors='replace'`).
  2. Tránh phụ thuộc vào default encoding của terminal.
- Phòng ngừa:
  - Không giả định encoding hệ thống; luôn chỉ định rõ.

### 4) Reviewer BLOCK vì evidence lẫn ngoài scope task
- Dấu hiệu:
  - `git status` có nhiều thay đổi ngoài `allowed_files`.
- Nguyên nhân gốc:
  - Không tách evidence theo scope task.
- Xử trí chuẩn:
  1. Chỉ gửi diff/status đã lọc theo `allowed_files`.
  2. Bổ sung `ARTIFACT_SNAPSHOTS_FOR_REVIEW` cho file chính.
- Phòng ngừa:
  - Blueprint yêu cầu task có phạm vi file cụ thể, không mơ hồ.

### 5) Reviewer REVISE vì thiếu bằng chứng convergence
- Dấu hiệu:
  - Task sweep hoàn thành nhưng reviewer nói thiếu chứng minh hội tụ.
- Nguyên nhân gốc:
  - Chỉ kiểm NaN/Inf, không có metric residual/tolerance.
- Xử trí chuẩn:
  1. Xuất bảng convergence theo từng case (`converged`, `residual`, `tol`).
  2. Fail run nếu case không đạt ngưỡng.
- Phòng ngừa:
  - DoD phải ghi rõ ngưỡng hội tụ định lượng.

### 6) Reviewer REVISE vì thiếu metadata đầy đủ toàn bộ case
- Dấu hiệu:
  - Có metadata rời rạc, không chứng minh đủ N case.
- Nguyên nhân gốc:
  - Không có manifest kiểm đếm tổng thể.
- Xử trí chuẩn:
  1. Tạo `metadata_manifest_*.csv` với trạng thái từng case.
  2. Đảm bảo số dòng manifest khớp số case sweep.
- Phòng ngừa:
  - Blueprint yêu cầu rõ artifact kiểm đếm metadata.

### 7) Timeout do coder chạy lâu
- Dấu hiệu:
  - `Coder CLI timeout after ...`.
- Nguyên nhân gốc:
  - Timeout mặc định thấp so với task.
- Xử trí chuẩn:
  1. Tăng timeout môi trường cho coder.
  2. Chia nhỏ task nếu cần.
- Phòng ngừa:
  - Task thiết kế trong khoảng 15-45 phút, scope rõ.

### 8) Coder viết file vào shadow folder (V3/xphd_python thay vì xphd_python)
- Dấu hiệu:
  - Reviewer báo "không tìm thấy bằng chứng thay đổi" hoặc "ngoài scope".
  - `git diff` tại repo thật không có gì, nhưng coder báo DONE.
  - File xuất hiện trong `V3/xphd_python/...` thay vì `xphd_python/...`.
- Nguyên nhân gốc:
  - `exec_root` hoặc working directory của orchestrator trỏ sai vào V3 subfolder.
- Xử trí chuẩn:
  1. Kiểm tra `exec_root` và `repo_root` trong orchestrator config.
  2. Dọn sạch thư mục shadow `V3/xphd_python` nếu có.
  3. Chạy lại task với path đúng.
- Phòng ngừa:
  - Preflight kiểm tra `repo_root` tồn tại và là git repo thật trước khi gọi coder.

### 9) Machine check fail giả với task docs-only
- Dấu hiệu:
  - `pytest` trả `no tests ran in 0.00s` với task chỉ viết tài liệu.
  - Reviewer coi đây là fail và BLOCK/REVISE.
- Nguyên nhân gốc:
  - Task docs-only không có code thay đổi, pytest không có gì để chạy.
- Xử trí chuẩn:
  1. Xác nhận task là docs-only (không sửa `.py`).
  2. Áp dụng waiver: `pytest no tests ran` không tính là fail cho docs-only.
  3. Nếu orchestrator hỗ trợ AUTO_RESCUE: để tự xử lý.
- Phòng ngừa:
  - Blueprint đánh dấu rõ loại task (`type: docs` / `type: code`) để orchestrator chọn check phù hợp.
  - Machine check cho docs-only nên dùng kiểm tra file tồn tại thay vì pytest.

### 10) AUTO_RESCUE hết lượt, pipeline dừng
- Dấu hiệu:
  - Log ghi `auto_rescue_attempts` đạt giới hạn tối đa.
  - Task không tiến thêm dù lỗi có vẻ nhỏ.
- Nguyên nhân gốc:
  - Lỗi lặp lại không được giải quyết gốc rễ, AUTO_RESCUE kích hoạt nhiều lần liên tiếp.
- Xử trí chuẩn:
  1. Đọc `review.json` → `test_output.txt` → `coder_report.txt` → `orchestrator.log` theo thứ tự.
  2. Xác định nguyên nhân gốc thật sự (không phải triệu chứng).
  3. Sửa thủ công, reset `auto_rescue_attempts` về 0 trong `state.json`, chạy lại.
- Phòng ngừa:
  - Không để task có scope quá rộng dẫn tới coder gặp nhiều lỗi một lúc.

### 11) Reviewer output không parse được (JSON lỗi)
- Dấu hiệu:
  - Orchestrator crash với `JSONDecodeError` khi đọc `review.json`.
  - Reviewer CLI trả về text tự do hoặc output cắt ngang.
- Nguyên nhân gốc:
  - Reviewer CLI timeout giữa chừng hoặc trả về nội dung không đúng schema.
- Xử trí chuẩn:
  1. Mở `review.json` kiểm tra nội dung thực tế.
  2. Nếu output bị cắt: tăng timeout reviewer, chạy lại.
  3. Nếu output sai schema: kiểm tra prompt reviewer có yêu cầu JSON format rõ không.
- Phòng ngừa:
  - Prompt reviewer phải yêu cầu output JSON strict, có ví dụ schema cụ thể.
  - Orchestrator nên có try/except JSONDecodeError với fallback REVISE thay vì crash.

### 12) Coder không báo STATUS: DONE — pipeline treo chờ
- Dấu hiệu:
  - `coder_report.txt` rỗng hoặc không chứa `STATUS: DONE`.
  - Orchestrator không chuyển sang bước machine check.
- Nguyên nhân gốc:
  - Coder CLI bị lỗi giữa chừng, hoặc prompt không đủ rõ yêu cầu format báo cáo.
- Xử trí chuẩn:
  1. Xem `coder_report.txt` để biết coder dừng ở đâu.
  2. Nếu coder thực ra đã làm xong: viết thủ công `STATUS: DONE` vào report.
  3. Nếu coder chưa xong: chạy lại với timeout cao hơn.
- Phòng ngừa:
  - Prompt coder phải có template báo cáo bắt buộc, bao gồm dòng `STATUS: DONE` cuối cùng.

### 13) REVISE loop — task bị REVISE liên tục không thoát được
- Dấu hiệu:
  - Task bị REVISE nhiều lần, coder sửa đi sửa lại nhưng reviewer vẫn REVISE.
  - Số lần REVISE vượt ngưỡng nhưng orchestrator chưa escalate.
- Nguyên nhân gốc:
  - DoD trong blueprint quá mơ hồ, reviewer và coder hiểu khác nhau.
  - Reviewer prompt có tiêu chí không thể đạt được với scope task hiện tại.
- Xử trí chuẩn:
  1. Đọc `review.json` các vòng REVISE để tìm pattern reviewer yêu cầu gì.
  2. Nếu DoD mơ hồ: sửa blueprint, làm rõ tiêu chí định lượng, reset task.
  3. Nếu reviewer yêu cầu ngoài scope: điều chỉnh prompt reviewer hoặc tách thành task mới.
- Phòng ngừa:
  - DoD phải có tiêu chí cụ thể, đo được — không dùng "hợp lý", "đủ", "ổn".
  - Orchestrator nên có giới hạn REVISE tối đa, sau đó escalate sang BLOCK thủ công.

### 14) state.json desync — trạng thái không khớp thực tế
- Dấu hiệu:
  - Orchestrator bỏ qua task đã làm hoặc chạy lại task đã PASS.
  - `state.json` ghi task ở trạng thái cũ không phản ánh thực tế.
- Nguyên nhân gốc:
  - Crash giữa chừng khiến `state.json` không được cập nhật đúng.
  - Reset thủ công không cẩn thận làm mất thông tin task đã hoàn thành.
- Xử trí chuẩn:
  1. Đối chiếu `state.json` với `tasks.json` để xác định task nào thực sự đã xong.
  2. Chỉnh sửa tối thiểu `state.json` — chỉ sửa field cần thiết, không reset toàn bộ.
  3. Kiểm tra artifact và git log để xác nhận task thật sự đã done trước khi đánh dấu.
- Phòng ngừa:
  - Orchestrator nên ghi `state.json` nguyên tử (write temp file rồi rename).
  - Không dùng reset toàn cục `state.json` trừ khi bắt đầu lại từ đầu hoàn toàn.

### 15) Gemini CLI EPERM `realpath` ở thư mục Home
- Dấu hiệu:
  - Coder BLOCK ngay Step 1 với lỗi:
    - `EPERM: operation not permitted, realpath 'C:\\Users\\<user>'`
    - stack trace có `loadServerHierarchicalMemory`.
- Nguyên nhân gốc:
  - Gemini CLI cố quét hierarchical memory từ Home và gặp hạn chế quyền/sandbox.
  - Dùng `coder_approval_mode: yolo` có thể kích hoạt sandbox mặc định, tăng khả năng gặp EPERM.
- Xử trí chuẩn:
  1. Đổi `coder_approval_mode` trong `.aiwf/workflow_config.json` từ `yolo` sang `auto_edit`.
  2. Chạy lại orchestrator ở terminal local (không sandbox trung gian) để xác nhận.
  3. Nếu vẫn lỗi: kiểm tra quyền truy cập thư mục Home và phiên đăng nhập Gemini.
- Phòng ngừa:
  - Mặc định dùng `auto_edit` cho task thường; chỉ dùng `yolo` khi thật sự cần.
  - Khi gặp EPERM kiểu `realpath Home`, ưu tiên xử lý cấu hình approval/sandbox trước khi debug task code.

### 16) Machine check có dấu cách bị fail do parser `split()`
- Dấu hiệu:
  - Check `findstr` với pattern có khoảng trắng fail dù file có nội dung đúng.
  - Ví dụ stderr: `FINDSTR: Cannot open V5\"`.
- Nguyên nhân gốc:
  - Runner machine-check tách lệnh bằng `check_cmd.split()`, làm vỡ cặp quote.
- Xử trí chuẩn:
  1. Tránh pattern có khoảng trắng trong `checks` khi có thể.
  2. Với `findstr`, dùng regex không dấu cách, ví dụ:
     - `findstr /I /R /C:checklist.*V5 docs\\HANDOVER_REPORT_V4.md`
  3. Rerun machine checks và xác nhận toàn bộ `Success: True`.
- Phòng ngừa:
  - Khi viết Blueprint, thiết kế check command theo “split-safe”.
  - Nâng cấp runner sau này: dùng `shlex.split`/tokenizer phù hợp thay cho `.split()`.

### 17) Sửa `tasks.json` trong lúc workflow RUNNING nhưng không có hiệu lực ngay
- Dấu hiệu:
  - Đã sửa check trong `tasks.json` nhưng `test_output.txt` vẫn chạy command cũ.
  - Task tiếp tục REVISE với lỗi cũ.
- Nguyên nhân gốc:
  - Process orchestrator đang chạy đã nạp task vào memory từ trước.
- Xử trí chuẩn:
  1. Dừng vòng chạy hiện tại (hoặc chờ block), sau đó khởi chạy process mới.
  2. Ưu tiên dùng `python orchestrator.py loop` để nạp lại `tasks.json` từ đầu process.
  3. Kiểm tra `status` và `test_output.txt` để chắc chắn command mới đã được dùng.
- Phòng ngừa:
  - Sau khi chỉnh machine checks, luôn restart orchestrator process thay vì chỉ `resume` ngay.
  - Ghi chú trong handover: “task/check thay đổi cần reload process”.

### 18) Dùng lệnh built-in của shell (`dir`) trong machine check làm fail giả
- Dấu hiệu:
  - `Success: False` với lệnh `dir ...` dù file thực tế có tồn tại.
  - Thường gặp ở check kiểu:
    - `dir docs\TECH_REPORT_V5.md`
    - `dir results\v5\...`
- Nguyên nhân gốc:
  - Runner dùng `subprocess.run(check_cmd.split())` (không chạy qua shell).
  - `dir` là built-in của `cmd`, không phải executable độc lập.
- Xử trí chuẩn:
  1. Thay check `dir ...` bằng lệnh có executable thật:
     - `python -c "import os,sys; sys.exit(0 if os.path.exists('path') else 1)"` (nếu parser hỗ trợ quote tốt)
     - Hoặc ưu tiên check gián tiếp qua script đã tạo artifact (ví dụ chạy script export rồi verify bằng `findstr`/bước khác split-safe).
  2. Cập nhật cả `blueprint.md` và `tasks.json`, sau đó restart orchestrator process.
- Phòng ngừa:
  - Không dùng built-in shell (`dir`, `copy`, `type`, ...) trong machine checks.
  - Chuẩn hóa machine checks theo nguyên tắc “executable-only, split-safe”.

### 19) Sweep fail do nhầm đơn vị `h1_mm` làm foam over-compressed
- Dấu hiệu:
  - `Pressure solver failed: Foam over-compressed: CR=... < 0.2`
  - Convergence rate tụt thấp hoặc 0/6 ở benchmark.
- Nguyên nhân gốc:
  - Case matrix dùng `h1_mm` quá nhỏ so với `h0`/`CR_min` hiện tại.
  - Imported geometry có vùng lệch âm, làm local gap giảm thêm và vi phạm `CR_min`.
- Xử trí chuẩn:
  1. Kiểm tra nhanh điều kiện vật lý trước khi solve:
     - `CR = h1 / h0 >= CR_min`.
  2. Với imported mode, kiểm tra thêm local minimum gap sau offset profile.
  3. Thêm guard trong script sweep để auto-raise `h1` tối thiểu (và ghi note rõ trong CSV).
- Phòng ngừa:
  - Trong protocol/blueprint, thêm mục “Physical feasibility pre-check” trước solver.
  - Không khóa case matrix mà thiếu kiểm tra tương thích với `h0`, `CR_min` của config đang chạy.

### 20) Cú pháp Python “hợp lệ trên máy này” nhưng fail ở môi trường khác
- Dấu hiệu:
  - Script fail ngay khi parse, ví dụ `SyntaxError` quanh `:=`.
- Nguyên nhân gốc:
  - Dùng cú pháp mới/khó đọc (walrus, pattern nâng cao) trong file cần chạy ổn định đa môi trường.
  - Hoặc dùng sai ngữ cảnh cú pháp (ví dụ assignment expression trong biểu thức phức tạp).
- Xử trí chuẩn:
  1. Ưu tiên cú pháp rõ ràng, tương thích rộng (gán biến tách dòng).
  2. Chạy thử script trực tiếp bằng đúng interpreter của workflow trước khi báo DONE.
- Phòng ngừa:
- Với script automation, ưu tiên readability và compatibility hơn “code golf”.
- Tránh walrus/operator nâng cao nếu không thật sự cần.

### 21) Coder Gemini hết quota giữa vòng chạy
- Dấu hiệu:
  - `quota exceeded`, `quota_exhausted`, `429`, `rate limit`, `exhausted your capacity`.
  - Task bị BLOCK ngay tại bước gọi coder.
- Nguyên nhân gốc:
  - Hạn mức Gemini theo giờ/ngày của tài khoản đã chạm trần.
- Xử trí chuẩn:
  1. Workflow tự động chuyển coder từ Gemini sang Claude và chạy lại iteration.
  2. Nếu Claude cũng báo hết quota, dừng loop ngay để tránh REVISE/BLOCK lặp vô ích.
  3. Chờ quota reset hoặc đổi account/API key rồi mới `resume`.
- Phòng ngừa:
  - Theo dõi quota trước khi chạy batch dài.
  - Ưu tiên tách task lớn thành batch ngắn để giảm rủi ro cạn quota giữa chừng.

### 22) Claude cũng hết quota sau khi đã fallback từ Gemini
- Dấu hiệu:
  - Sau khi đã auto-switch sang Claude, coder tiếp tục trả lỗi `quota`/`429`.
- Nguyên nhân gốc:
  - Cả hai coder đều không còn khả năng phục vụ tại thời điểm hiện tại.
- Xử trí chuẩn:
  1. Orchestrator dừng loop và giữ trạng thái BLOCKED có chủ đích.
  2. Không auto-switch vòng lại Gemini để tránh loop vô hạn.
  3. Sau khi nạp lại quota hoặc đổi credential, chạy `resume`.
- Phòng ngừa:
  - Không chạy phiên dài khi quota của cả Gemini/Claude đều ở mức thấp.

### 23) Quota Gemini bị “nuốt” bởi rescue EPERM nên không switch sang Claude
- Dấu hiệu:
  - Log có cả `EPERM ... pytest-cache-files-*` và `QUOTA_EXHAUSTED`, nhưng iteration sau vẫn gọi Gemini.
- Nguyên nhân gốc:
  - Nhánh AUTO_RESCUE xử lý `permissionerror` chạy trước nhánh quota và `return` sớm.
- Xử trí chuẩn:
  1. Ưu tiên nhánh quota cho `stage == coder_block`.
  2. Chỉ áp dụng rescue `pytest-cache-files-*` cho stage machine-check/review, không áp cho coder-block.
  3. Rerun process mới để nạp code orchestrator đã sửa.
- Phòng ngừa:
  - Khi thêm rescue rule mới, luôn kiểm tra thứ tự `if/return` để tránh che khuất lỗi nghiêm trọng hơn.

### 24) AUTO_RESCUE đã chạm trần nên failover quota không còn chạy
- Dấu hiệu:
  - `state.json` có `auto_rescue_attempts` đạt max, task tiếp tục BLOCK dù reason chứa `quota`.
- Nguyên nhân gốc:
  - Guard `AUTO_RESCUE limit reached` chặn toàn bộ rescue trước khi kiểm tra quota.
- Xử trí chuẩn:
  1. Cho phép quota-failover là ngoại lệ ngay cả khi đã đạt trần rescue.
  2. Nếu không sửa code ngay, tạm reset riêng `metadata.auto_rescue_attempts[task_id]` rồi resume.
- Phòng ngừa:
  - Thiết kế rescue theo mức ưu tiên: quota/auth/service-availability nên nằm nhóm “always-evaluate”.

### 25) Reviewer rơi về CLI mặc định `claude` do mất cấu hình Brain
- Dấu hiệu:
  - Log reviewer báo command dạng `brain_cli_adapter.py --cli claude ...` và fail `rc=1` không rõ.
  - `workflow_config.json` chỉ còn key coder, thiếu `brain_cli`, `reviewer_model`, `brain_extra_args`.
- Nguyên nhân gốc:
  - Cấu hình Brain/Reviewer bị ghi đè hoặc chưa set lại cho workspace version hiện tại.
- Xử trí chuẩn:
  1. Chạy lại:
     - `python orchestrator.py set-brain codex.cmd gpt-5.3-codex gpt-5.4`
  2. Kiểm tra `.aiwf/workflow_config.json` có đủ key Brain.
  3. Resume bằng process mới.
- Phòng ngừa:
  - Sau `set-coder`, kiểm tra lại config Brain trước khi chạy loop dài.

### 26) Claude API `529 Overloaded` làm coder BLOCK tạm thời
- Dấu hiệu:
  - `API Error: 529 Overloaded ... status.claude.com`.
- Nguyên nhân gốc:
  - Sự cố tải hệ thống phía nhà cung cấp, không phải lỗi task/code.
- Xử trí chuẩn:
  1. Dừng loop, chờ vài phút, rồi `resume`.
  2. Nếu lặp lại nhiều lần: chuyển coder tạm sang Gemini (nếu còn quota).
- Phòng ngừa:
  - Với phiên dài, chuẩn bị sẵn phương án fallback coder và checkpoint rõ ở từng task.

### 27) Gemini CLI báo “not running in a trusted directory”
- Dấu hiệu:
  - `Gemini CLI is not running in a trusted directory ... use --skip-trust ...`.
- Nguyên nhân gốc:
  - Chạy lệnh headless ngoài thư mục dự án trusted (ví dụ `C:\Windows\System32`).
- Xử trí chuẩn:
  1. `cd` vào workspace project trước khi gọi Gemini.
  2. Dùng `--skip-trust` cho lệnh kiểm tra nhanh headless nếu cần.
  3. Hoặc set biến môi trường `GEMINI_CLI_TRUST_WORKSPACE=true` cho phiên hiện tại.
- Phòng ngừa:
  - Chuẩn hóa terminal workflow: luôn khởi chạy từ thư mục version (`V6`, `V7`, ...).

### 28) T009 bị REVISE do cờ `FIGURES_V7_READY` không được verify đúng cách
- Dấu hiệu:
  - `python -m pytest -q tests/v7/test_figures_v7.py` pass nhưng reviewer vẫn FAIL tiêu chí cờ/report.
  - Reviewer báo artifact ngoài scope (`results/v7/logs/figures_v7_status.txt`).
- Nguyên nhân gốc:
  - Test chỉ `print` cờ nên phụ thuộc pytest capture.
  - Script sinh thêm file log ngoài `allowed_files`.
- Xử trí chuẩn:
  1. Test phải assert cờ từ output thật (subprocess stdout/stderr), không chỉ print.
  2. Dùng `capsys.disabled()` nếu cần hiển thị marker trong test report.
  3. Không sinh artifact ngoài scope task; xóa file dư đã tạo trước đó.
  4. Bổ sung legend/annotation nhất quán cho figures nếu DoD yêu cầu.
- Phòng ngừa:
  - Với DoD kiểu “flag trong report”, phải có assert deterministic + command check tương ứng từ đầu.

### 29) T005 REVISE loop vì nhánh skip pass nhưng nhánh run chưa đủ DoD
- Dấu hiệu:
  - Machine check pass ở nhánh skip (`PERMEABILITY_REFINEMENT_SKIPPED`) nhưng reviewer vẫn REVISE nhiều vòng.
  - `review_T005_retry*.json` yêu cầu các điều kiện “nếu run” chưa được đáp ứng.
- Nguyên nhân gốc:
  - Script chỉ hoàn thiện nhánh skip, còn nhánh run chưa có đầy đủ logic/artifact theo DoD.
- Xử trí chuẩn:
  1. Đọc toàn bộ checklist DoD trong review, không chỉ nhìn machine check pass/fail.
  2. Bổ sung đầy đủ nhánh run (3 run A/B/C, KPI schema, manifest, decision gate).
  3. Thêm test unit cho các helper logic của nhánh run để tránh regression.
- Phòng ngừa:
  - Với task có điều kiện run/skip, DoD phải được kiểm cho cả hai nhánh ngay từ vòng implement đầu tiên.

### 30) Script chạy trực tiếp bị `ModuleNotFoundError: No module named 'src'`
- Dấu hiệu:
  - `python scripts/...py` fail ngay ở import `from src...`.
- Nguyên nhân gốc:
  - Working directory/PYTHONPATH không bảo đảm repo root được nạp khi chạy entrypoint script.
- Xử trí chuẩn:
  1. Trong script, bootstrap `REPO_ROOT` vào `sys.path` trước khi import module nội bộ.
  2. Giữ machine check chạy từ đúng repo root.
- Phòng ngừa:
  - Mọi script dưới `scripts/` cần tự chạy độc lập bằng `python scripts/...py` trong môi trường clean.

### 31) Manifest không audit đủ 18 case/run khi có exception
- Dấu hiệu:
  - Reviewer báo “không chứng minh đủ 18 case hoặc fail-log rõ ràng”.
  - Manifest chỉ có các case pass, case lỗi bị `print` rồi mất dấu.
- Nguyên nhân gốc:
  - Nhánh exception không append record vào manifest source.
- Xử trí chuẩn:
  1. Khi case fail, vẫn append record `status=FAIL` + `reason`.
  2. Bảo đảm mỗi run luôn có đủ 18 record (hoặc pad `MISSING_*` có lý do).
- Phòng ngừa:
  - Tách helper `build_manifest_rows()` và test riêng điều kiện đủ số dòng.

### 32) CSV schema lệch giữa nhánh skip và nhánh run
- Dấu hiệu:
  - Nhánh skip có cột `decision`, nhánh run thiếu cột này.
  - Reviewer REVISE dù script vẫn tạo file.
- Nguyên nhân gốc:
  - Output schema không được khóa bằng một danh sách cột bắt buộc dùng chung.
- Xử trí chuẩn:
  1. Định nghĩa `REQUIRED_COLUMNS` trong script.
  2. Trước khi ghi CSV, ép DataFrame về đúng schema, bổ sung cột thiếu với giá trị mặc định.
- Phòng ngừa:
  - Mọi artifact CSV dùng cho review phải có contract schema bất biến giữa các nhánh logic.

### 33) Winner gate thiếu điều kiện vật lý nên reviewer không chấp nhận
- Dấu hiệu:
  - Logic chọn winner chỉ check SMAPE/spread, reviewer yêu cầu thêm monotonicity/consistency.
- Nguyên nhân gốc:
  - DoD yêu cầu 3 điều kiện đồng thời nhưng code mới enforce một phần.
- Xử trí chuẩn:
  1. Tách hàm gate rõ ràng (ví dụ `_is_eligible_winner`).
  2. Enforce đồng thời:
     - cải thiện >= 5pp SMAPE so với Run A,
     - spread giảm,
     - monotonicity = 1.0 và consistency = 1.0.
- Phòng ngừa:
  - Viết unit test riêng cho decision gate theo đúng contract DoD.

### 34) Test integration ghi đè artifact thật của workflow
- Dấu hiệu:
  - Sau khi chạy test, artifact sản xuất bị đổi nội dung (ví dụ từ `SKIPPED` thành `DONE`).
- Nguyên nhân gốc:
  - Test gọi run thật (`--force`) dùng chung path output production.
- Xử trí chuẩn:
  1. Tránh test ghi trực tiếp vào artifact production.
  2. Ưu tiên test unit helper function (trigger, decision, manifest builder) thay vì full run ghi file thật.
  3. Nếu buộc integration test, dùng path tạm (`tmp_path`) hoặc monkeypatch path output.
- Phòng ngừa:
  - Tách rõ “artifact để nghiệm thu task” và “artifact test sandbox”, không dùng chung file đích.

### 35) Trigger threshold dùng giá trị placeholder gây REVISE
- Dấu hiệu:
  - Reviewer ghi nhận ngưỡng `Peak_Ratio_mean_v8b` “tạm” hoặc không phản ánh spec.
- Nguyên nhân gốc:
  - Hardcode ngưỡng quá rộng/hẹp không bám blueprint hoặc protocol.
- Xử trí chuẩn:
  1. Đưa threshold thành hằng số có tên rõ và comment ngắn.
  2. Viết test cho trigger (`should_run_refinement`) để khóa hành vi.
- Phòng ngừa:
  - Mọi threshold dùng cho gating phải có nguồn tham chiếu (protocol/blueprint) và test bảo vệ.

### 36) Blueprint và Contract không đồng bộ — module thiếu deliverable
- Dấu hiệu:
  - Reviewer báo FAIL vì coder làm đúng blueprint nhưng vi phạm contract (hoặc ngược lại).
  - `contract.md` không tồn tại hoặc không được sinh cùng lúc với `blueprint.md`.
  - Task scope trong blueprint rộng hơn contract, gây coder over-engineer.
- Nguyên nhân gốc:
  - Brain Synthesizer chỉ sinh `blueprint.md`, bỏ qua `contract.md`.
  - Hai file được viết độc lập, không cross-check module map với deliverable list.
- Xử trí chuẩn:
  1. Dừng execution loop ngay khi phát hiện thiếu `contract.md`.
  2. Brain Synthesizer phải tạo lại cả hai file đồng bộ.
  3. Kiểm tra: mọi module trong blueprint có deliverable tương ứng trong contract không.
- Phòng ngừa:
  - Prompt Brain Synthesizer phải yêu cầu CẢ HAI file — blueprint.md VÀ contract.md.
  - Thêm validation bước `init`: nếu thiếu `contract.md` → cảnh báo trước khi build tasks.

### 37) Coder hoặc Reviewer bỏ qua instruction file — sai vai trò hệ thống
- Dấu hiệu:
  - Coder tự ý thay đổi kiến trúc hoặc làm thêm feature ngoài JOB BRIEF.
  - Reviewer viết/sửa code thay vì chỉ đánh giá và báo cáo.
  - Coder báo DONE khi chưa có đủ 4 file context (JOB BRIEF, BLUEPRINT, CONTRACT, GATE).
- Nguyên nhân gốc:
  - Agent không đọc instruction file trước khi bắt đầu — bỏ qua quy tắc bất di bất dịch.
  - Instruction không được inject vào đầu context prompt.
- Xử trí chuẩn:
  1. Đảm bảo `BRAIN_AGENT_INSTRUCTION_v2.md`, `CODER_AGENT_INSTRUCTION_v2.md`,
     `REVIEWER_AGENT_INSTRUCTION_v2.md` tồn tại ở workspace root.
  2. Orchestrator inject nội dung instruction vào đầu mỗi prompt với header `⚠️ BẮT BUỘC ĐỌC TRƯỚC`.
  3. Nếu agent vẫn vi phạm → BLOCK task, ghi rõ violation type trong review report.
- Phòng ngừa:
  - Instruction file phải ở workspace root, không trong `.aiwf/`.
  - Orchestrator luôn gọi `_load_agent_instruction(role)` và truyền vào context builder.

### 38) GATE thiếu hoặc tiêu chí GATE không đo được
- Dấu hiệu:
  - Reviewer không thể kết luận PASS/FAIL vì GATE_[NNN].md thiếu hoặc tiêu chí mơ hồ.
  - REVISE loop liên tục vì Brain và Reviewer hiểu tiêu chí khác nhau.
  - Reviewer đánh dấu tiêu chí là `⬜ BLOCKED` nhiều lần liên tiếp.
- Nguyên nhân gốc:
  - JOB BRIEF được viết nhưng không có GATE file tương ứng.
  - Tiêu chí GATE dùng từ ngữ mơ hồ: "hợp lý", "đủ tốt", "hoạt động được".
- Xử trí chuẩn:
  1. Brain phải tạo `GATE_[NNN].md` ngay sau mỗi JOB BRIEF — không để PENDING.
  2. Sửa tiêu chí thành dạng binary: "file X tồn tại", "output Y chứa Z", "metric >= N".
  3. Reset retry counter về 0 sau khi sửa GATE.
- Phòng ngừa:
  - JOB BRIEF template phải có mục TIÊU CHÍ GATE với ít nhất 2 tiêu chí REQUIRED định lượng.
  - Brain Synthesizer kiểm tra: mọi task trong blueprint phải có `checks` tương ứng.

### 39) Contract.md bị silent-update mà không thông báo
- Dấu hiệu:
  - Coder nhận JOB BRIEF mới nhưng phát hiện contract.md đã thay đổi so với lần trước.
  - Reviewer FAIL vì code đúng với contract cũ nhưng sai contract mới.
  - `BLUEPRINT.md` và `CONTRACT.md` có version timestamp khác nhau không rõ lý do.
- Nguyên nhân gốc:
  - Brain silent-update contract khi phát hiện vấn đề kỹ thuật, không thông báo Chủ dự án.
  - Không có version control cho artifact files.
- Xử trí chuẩn:
  1. Bất kỳ thay đổi nào với `blueprint.md` hoặc `contract.md` phải được ghi vào
     một section `## Changelog` với timestamp và lý do thay đổi.
  2. Coder phải đọc lại `contract.md` mỗi lần bắt đầu JOB mới, không cache từ lần trước.
  3. Nếu contract thay đổi giữa chừng → escalate lên Chủ dự án trước khi tiếp tục.
- Phòng ngừa:
  - Template contract.md phải có section `## Changelog` bắt buộc.
  - Không silent-update bất kỳ artifact nào — nguyên tắc bất di bất dịch của Brain.

### 40) Brain Planner không đọc COMMON FAILURES RUNBOOK khi viết blueprint
- Dấu hiệu:
  - Blueprint thiếu mục "Pitfalls & Mitigation" cho task rủi ro cao.
  - Coder gặp lỗi đã được ghi trong runbook nhưng không có mitigation sẵn.
  - DoD của task không có tiêu chí phòng lỗi đã biết (ví dụ: không có convergence policy).
- Nguyên nhân gốc:
  - Brain Planner không được cung cấp runbook trong context, hoặc có nhưng bỏ qua.
  - Prompt Brain Synthesizer không enforce "bắt buộc áp dụng runbook vào Pitfalls & DoD".
- Xử trí chuẩn:
  1. Đảm bảo `common_failures_runbook.md` được copy vào `.aiwf/input/` trước khi plan.
  2. Brain Synthesizer prompt phải có dòng bắt buộc: "Nếu có COMMON FAILURES RUNBOOK,
     PHẢI áp dụng vào Pitfalls & Mitigation và DoD của TỪNG task".
  3. Review blueprint: mỗi task rủi ro cao phải có ít nhất 1 pitfall từ runbook.
- Phòng ngừa:
  - Orchestrator copy runbook vào input dir trước bước planning (như đã làm cho execution).
  - Sau mỗi workflow, `post_workflow_runbook_update()` tự động cập nhật runbook.

### 41) `start` workspace không copy đủ runtime scripts
- Dấu hiệu:
  - Chạy trong workspace mới gặp lỗi:
    - `can't open file '<workspace>\\orchestrator.py': [Errno 2] No such file or directory`
    - `can't open file '<workspace>\\build_tasks_from_blueprint.py': [Errno 2] No such file or directory`
- Nguyên nhân gốc:
  - `orchestrator.py start` chỉ tạo `.aiwf/` và copy instruction/runbook, nhưng không copy đủ script runtime.
  - Tài liệu hướng dẫn lệnh chạy tại workspace root nhưng file script vẫn nằm ở Vibecode source root.
- Xử trí chuẩn:
  1. Sửa `orchestrator.start_workspace()` để copy đủ các file runtime tối thiểu:
     `orchestrator.py`, `build_tasks_from_blueprint.py`, `cli_wrappers.py`, `prompts.py`,
     `brain_cli_adapter.py`, instruction files, runbook.
  2. `init` phải resolve build script bằng `_source_file(...)`, không giả định file nằm ở cwd.
  3. Sau khi sửa, chạy `python orchestrator.py --workspace <workspace> status/init` trong workspace mới.
- Phòng ngừa:
  - USER_GUIDE phải nói rõ 2 mode chạy: chạy script tại source root với `--workspace`, hoặc chạy bản đã copy trong workspace.
  - `start` phải kiểm tra post-copy: nếu thiếu file runtime thì fail sớm với danh sách file thiếu.

### 42) Reviewer trả PASS nhưng JSON không parse được
- Dấu hiệu:
  - Orchestrator block với `Reviewer response not valid JSON`.
  - `.aiwf/run/review.json` có nội dung semantically `PASS`, nhưng JSON lỗi cú pháp:
    thiếu quote, markdown fence lỗi, trailing text, hoặc dùng backtick làm string delimiter.
- Nguyên nhân gốc:
  - Reviewer LLM trả JSON gần đúng nhưng không hợp lệ tuyệt đối.
  - `parse_json_from_response()` chỉ parse JSON chuẩn, không repair.
- Xử trí chuẩn:
  1. Đọc raw `.aiwf/run/review.json`.
  2. Nếu nội dung là PASS rõ ràng và toàn bộ DoD/machine check đã xác minh độc lập, tạo
     `review_<TASK>_manual_fixed.json` hợp lệ.
  3. Tạo `GATE_<TASK>.md` ghi rõ lỗi là formatter/parser, không phải lỗi code.
  4. Chỉ mark task complete sau khi chạy lại machine checks và kiểm artifact.
- Phòng ngừa:
  - Reviewer prompt phải yêu cầu "return ONLY valid JSON, no markdown fence".
  - Orchestrator nên validate JSON bằng `json.loads()` và nếu fail thì lưu thêm raw response + vị trí lỗi parse.
  - Với task quan trọng, DoD phải có đường dẫn artifact để Brain có thể manual gate an toàn.

### 43) Reviewer REVISE/BLOCK vì thiếu runtime artifact evidence dù code đã đúng
- Dấu hiệu:
  - Coder report nói artifact đã sinh nhưng reviewer không thấy snapshot.
  - Machine checks pass nhưng reviewer vẫn BLOCK vì thiếu CSV/PNG/JSON thực tế.
  - Hay gặp ở task script/plot/sweep như Plan 1, Plan 2, Plan 3.
- Nguyên nhân gốc:
  - Artifact nằm trong `results/` nhưng không nằm trong diff hoặc `allowed_files`.
  - Coder chỉ báo "đã tạo" mà không liệt kê đường dẫn, schema, số dòng, metric chính.
- Xử trí chuẩn:
  1. Chạy script thật để sinh artifact production/test.
  2. Kiểm tra bằng lệnh máy: file tồn tại, size > 0, CSV có đúng cột, JSON có key bắt buộc.
  3. Ghi `.aiwf/input/GATE_<TASK>.md` hoặc `BUILD_LOG.md` với danh sách artifact và kết quả kiểm.
  4. Nếu reviewer thiếu context do không có git repo, thêm artifact snapshots vào review package.
- Phòng ngừa:
  - DoD của task artifact phải liệt kê tên file cụ thể, schema/cột CSV, key JSON, và folder output.
  - Coder report phải có mục `Runtime artifacts checked`.

### 44) Test import script sai khi pytest chạy từ workspace root
- Dấu hiệu:
  - `ModuleNotFoundError: No module named 'scripts.<name>'`
  - Test pass khi chạy trong project root nhưng fail khi orchestrator chạy từ workspace root.
- Nguyên nhân gốc:
  - Test import `from scripts.foo import bar` nhưng `bubble_dynamics_project/` không có trên `sys.path`.
  - Config path dùng relative path như `configs/...` không đúng khi cwd khác project root.
- Xử trí chuẩn:
  1. Trong test, tự định vị project root bằng `Path(__file__).resolve().parents[1]`.
  2. `sys.path.insert(0, str(PROJECT_ROOT))` trước khi import `scripts...`.
  3. Dùng absolute path cho config/artifact input: `PROJECT_ROOT / "configs" / ...`.
- Phòng ngừa:
  - Machine check phải chạy đúng theo orchestrator command từ workspace root, không chỉ chạy thủ công trong subproject.
  - Nếu script cần tái sử dụng nhiều, cân nhắc chuyển logic core vào package `src/` và để script chỉ là CLI wrapper.

### 45) Pytest `tmp_path` fail do Windows temp permission
- Dấu hiệu:
  - `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\...\\AppData\\Local\\Temp\\pytest-of-...'`
  - Test lỗi ở setup fixture `tmp_path`, trước khi vào code test.
  - Có thể pass ngoài sandbox nhưng fail trong sandbox/terminal khác.
- Nguyên nhân gốc:
  - Thư mục temp pytest bị khóa/quyền truy cập lỗi trên Windows.
  - Sandbox hoặc process trước để lại folder temp không scan/mkdir được.
- Xử trí chuẩn:
  1. Xác định đây là lỗi môi trường nếu stack trace dừng ở `_pytest/tmpdir.py` trước khi chạy code dự án.
  2. Với smoke/integration artifact test, dùng output deterministic trong `results/.../pytest_<case>` thay vì `tmp_path` nếu phù hợp.
  3. Khi cần xác minh cuối cùng, chạy lại ngoài sandbox hoặc với temp directory đã được cấp quyền.
- Phòng ngừa:
  - Các test integration nặng về artifact nên dùng output folder rõ ràng và cleanup/overwrite an toàn.
  - Không dùng `tmp_path` cho artifact cần reviewer audit sau run.
  - Nếu vẫn cần `tmp_path`, thêm runbook note rằng lỗi fixture setup là environmental blocker, không phải code blocker.

### 46) Trend test dùng tiêu chí quá yếu kiểu `diff > 0`
- Dấu hiệu:
  - Reviewer REVISE vì "tiêu chí mơ hồ", "quá yếu", "dễ pass do nhiễu số".
  - Test chỉ assert `diff > 0`, `x_diff > 0`, hoặc "khác nhau" không có ngưỡng.
- Nguyên nhân gốc:
  - DoD yêu cầu trend định lượng nhưng test chỉ kiểm khác biệt không-zero.
  - Không có absolute/relative tolerance hoặc không log metric difference.
- Xử trí chuẩn:
  1. Đặt threshold rõ: absolute threshold, relative threshold, hoặc cả hai.
  2. In/log giá trị metric thực tế: `abs_diff`, `rel_diff`, baseline.
  3. Assertion message phải chứa giá trị đo được và ngưỡng.
- Phòng ngừa:
  - Blueprint phải ghi ngưỡng trend ngay trong DoD hoặc yêu cầu coder giải thích ngưỡng chọn.
  - Với physics trend yếu, yêu cầu test ghi metric difference thay vì dùng tiêu chí mơ hồ.

### 47) Manifest chỉ kiểm case-level, thiếu plan/case/mode granularity
- Dấu hiệu:
  - Reviewer FAIL dù `manifest.json` có status success.
  - Task yêu cầu manifest theo mode nhưng JSON chỉ có `plans.<plan>.cases.<case>.status`.
  - Plan 3 có 4 mode nhưng manifest chỉ kiểm `present/wcm` hoặc chỉ đếm tổng số file.
- Nguyên nhân gốc:
  - Manifest schema quá tổng quát, không encode mode-level required artifacts.
  - `artifact_count` không đủ để chứng minh từng mode success/failure.
- Xử trí chuẩn:
  1. Manifest case record phải có `required_artifacts`, `artifacts`, `missing_artifacts`.
  2. Với Plan 3 mode comparison, thêm `modes.present`, `modes.wcm`, `modes.wpt`, `modes.wcmpt`.
  3. Mỗi mode record phải có `status`, `required_artifacts`, `missing_artifacts`, và metric success nếu có.
  4. Thêm regression test: thiếu một mode CSV thì manifest không được báo success cho mode đó.
- Phòng ngừa:
  - Blueprint task sweep/final validation phải mô tả manifest schema tối thiểu, không chỉ nói "có manifest".
  - Reviewer phải kiểm JSON structure, không chỉ xem file `manifest.json` tồn tại.

### 48) Sweep task thiếu bằng chứng đã chạy thật
- Dấu hiệu:
  - Reviewer nói script sweep tồn tại nhưng "chưa có bằng chứng runtime".
  - Test chỉ kiểm import/callable của `run_sweep`, không kiểm CSV thật.
- Nguyên nhân gốc:
  - Coder viết script nhưng không chạy script production/test để sinh artifact.
  - DoD không yêu cầu snapshot CSV/log chạy sweep.
- Xử trí chuẩn:
  1. Chạy sweep thật với grid nhỏ, bounded runtime.
  2. Lưu `sweep_results.csv` và config/base metadata.
  3. Kiểm CSV có đủ cột metric bắt buộc như `R2max_star`, `Tosc2_star`, `present_minus_wcm`.
  4. Thêm test đọc artifact sweep thật hoặc tạo integration smoke chạy grid rất nhỏ.
- Phòng ngừa:
  - Sweep task DoD phải có cả script, output CSV, schema, số dòng tối thiểu, và status success/failure.
  - BUILD_LOG phải ghi command chạy sweep, grid, output path, số dòng CSV.

## Checklist trước khi báo DONE (cho coder)
- Đã đọc `CODER_AGENT_INSTRUCTION_v2.md` (hoặc thấy trong phần BẮT BUỘC ĐỌC TRƯỚC của prompt).
- Đã có đủ 4 file context: JOB BRIEF, BLUEPRINT.md, CONTRACT.md, GATE_[NNN].md.
- Đã sửa đúng trong `allowed_files`.
- Machine checks pass ở đúng working directory.
- Có artifact evidence cho từng DoD.
- Nếu là task sweep: có convergence summary + metadata manifest.
- Coder report có đường dẫn file cụ thể, không chỉ mô tả chung.

## Checklist cho Brain khi viết/sửa Blueprint
- Đã đọc `BRAIN_AGENT_INSTRUCTION_v2.md` trước khi bắt đầu.
- Đã đọc `common_failures_runbook.md` và áp dụng vào Pitfalls & DoD.
- Sinh cả `blueprint.md` VÀ `contract.md` — không thiếu một trong hai.
- Blueprint và Contract đồng bộ: mọi module có deliverable tương ứng.
- Mỗi task có mục tiêu đo được và artifact bắt buộc.
- Mỗi DoD có cách verify tương ứng.
- Có section Pitfalls & Mitigation cho task rủi ro cao.
- Không dùng tiêu chí mơ hồ kiểu "ổn", "hợp lý" nếu không có số đo.
- Mỗi JOB BRIEF có GATE file tương ứng với ít nhất 2 tiêu chí REQUIRED định lượng.

## Checklist cho Reviewer trước khi review
- Đã đọc `REVIEWER_AGENT_INSTRUCTION_v2.md` (hoặc thấy trong phần BẮT BUỘC ĐỌC TRƯỚC).
- Đã có đủ 4 input: code/output từ Coder, BUILD_LOG.md, GATE_[NNN].md, CONTRACT.md.
- Không viết hay sửa bất kỳ dòng code nào — chỉ đánh giá và báo cáo.
- Mọi FAIL phải kèm vị trí cụ thể (file, dòng) và giá trị thực tế vs mong đợi.
- Phân biệt rõ REQUIRED (binary PASS/FAIL) và RECOMMENDED (WARNING).
