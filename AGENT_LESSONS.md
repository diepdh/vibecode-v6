```markdown
# AGENT_LESSONS.md — Bài học tích lũy từ các workflow đã chạy

> Cập nhật lần cuối: 2026-05-08
> Tổng số lỗi trong runbook: 48

---

## Cho Brain (Planner & Synthesizer)

### Quy tắc PHẢI LÀM (rút ra từ lỗi thực tế):
1. Luôn sinh đồng thời `blueprint.md` và `contract.md`, rồi cross-check 1-1 module ↔ deliverable.
2. Mỗi task phải có DoD định lượng + artifact cụ thể + machine check chạy được ở đúng `repo_root`.
3. Task sweep/solver bắt buộc có convergence policy (ngưỡng, residual, pass/fail rõ).
4. Task nhiều case bắt buộc định nghĩa manifest schema kiểm đếm đầy đủ (kể cả case fail/exception).
5. Bắt buộc thêm `Pitfalls & Mitigation` cho task rủi ro cao, ưu tiên lỗi đã có trong runbook.
6. Mỗi JOB BRIEF phải có `GATE_[NNN].md` với tiêu chí binary đo được, không dùng từ mơ hồ.
7. Sau mọi thay đổi check/task config, yêu cầu restart process orchestrator để nạp cấu hình mới.
8. Tất cả tài liệu bàn giao nội bộ (`docs/*.md`, report, handover, README) phải là tiếng Việt có dấu.
9. Mọi thay đổi `blueprint.md`/`contract.md` phải ghi `## Changelog` có timestamp + lý do.
10. Scope task phải đủ hẹp để hoàn thành trong 15-45 phút và giảm REVISE/AUTO_RESCUE loop.

### Bẫy hay gặp nhất (tránh ngay từ khi viết blueprint):
- **DoD mơ hồ**: Dùng “ổn/hợp lý” làm coder-reviewer lệch kỳ vọng; luôn chuyển thành tiêu chí đo được.
- **Thiếu contract/GATE**: Pipeline REVISE/BLOCK liên tục; chặn chạy nếu thiếu 1 trong 2 file.
- **Machine check không split-safe**: Lệnh có quote/khoảng trắng hoặc shell built-in gây fail giả; chỉ dùng executable thật và lệnh split-safe.
- **Không chỉ định working directory**: Check chạy sai root dẫn tới `no tests ran`; ghi rõ repo root cho từng check.
- **Không encode known pitfalls**: Brain bỏ qua runbook làm lặp lỗi cũ; bắt buộc map lỗi phổ biến vào từng task rủi ro.

---

## Cho Coder

### Quy tắc PHẢI LÀM:
1. Trước khi làm, xác nhận đủ 4 context: JOB BRIEF, BLUEPRINT, CONTRACT, GATE.
2. Chỉ sửa trong `allowed_files`; không để lẫn artifact/file ngoài scope review.
3. Luôn chạy machine check ở đúng working directory đã quy định.
4. Mọi output runtime phải có evidence: đường dẫn file, schema/cột/key bắt buộc, số dòng/kích thước > 0.
5. Task sweep phải chạy thật (grid nhỏ nếu cần), có CSV/log runtime + trạng thái success/failure rõ ràng.
6. Khi case lỗi/exception vẫn phải ghi manifest record `FAIL + reason`, không được “mất dấu”.
7. Khóa schema output giữa các nhánh logic (skip/run) bằng danh sách cột bắt buộc.
8. Không để test ghi đè artifact production; test integration phải dùng path tạm/sandbox.
9. Luôn chỉ định UTF-8 khi đọc/ghi/subprocess để tránh lỗi encoding Windows.
10. Report phải kết thúc bằng `STATUS: DONE` và liệt kê đầy đủ artifact đã kiểm chứng.

### Bẫy hay gặp nhất:
- **Shadow folder sai repo**: Viết vào `V*/xphd_python` thay vì repo thật; kiểm `exec_root/repo_root` trước khi chạy.
- **“Pass giả” vì chỉ pass check tối thiểu**: Nhánh skip pass nhưng nhánh run thiếu DoD; kiểm full checklist reviewer, không chỉ nhìn pytest xanh.
- **Thiếu bằng chứng runtime**: Có code nhưng không có CSV/PNG/JSON thực; luôn chạy thật và snapshot.
- **Manifest thiếu granularity**: Chỉ đếm tổng, không theo mode/case; bắt buộc ghi đủ required/missing/status theo từng mức.
- **Import/path phụ thuộc cwd**: Script/test pass cục bộ nhưng fail ở workspace root; bootstrap `PROJECT_ROOT` và dùng absolute path.

---

## Cho Reviewer

### Quy tắc PHẢI LÀM:
1. Chỉ review, không sửa code; mọi kết luận FAIL/BLOCK phải có file/line hoặc artifact/value cụ thể.
2. Kiểm theo GATE/CONTRACT trước, tách rõ REQUIRED (PASS/FAIL) và RECOMMENDED (WARNING).
3. Với task artifact, không chỉ xem “file tồn tại”; kiểm schema, số dòng, key bắt buộc, và tính đầy đủ theo case/mode.
4. Với sweep/solver, bắt buộc kiểm convergence evidence định lượng, không chấp nhận mô tả chung.
5. Nếu output reviewer là JSON, phải trả JSON strict đúng schema để tránh crash orchestrator.
6. Khi evidence ngoài scope, yêu cầu coder gửi snapshot lọc theo `allowed_files` thay vì đánh đồng toàn bộ diff.
7. Nếu machine check fail do môi trường/parser, nêu rõ “environmental blocker” vs “code blocker”.
8. Khi REVISE lặp, chỉ ra pattern root-cause (DoD mơ hồ, scope sai, check sai) và yêu cầu sửa đúng điểm gốc.

### Bẫy hay gặp nhất:
- **REVISE loop do tiêu chí không khả thi**: Reviewer đòi ngoài scope task; bám CONTRACT/GATE và đề xuất tách task mới.
- **Đánh giá theo triệu chứng**: Chỉ nhìn pass/fail check mà bỏ qua logic DoD; luôn map yêu cầu ↔ bằng chứng.
- **JSON review lỗi format**: Nội dung đúng nhưng parse fail làm pipeline block; trả “only valid JSON”.
- **Nhầm lỗi môi trường thành lỗi code**: Ví dụ `tmp_path` permission/CLI quota; phải phân loại rõ để xử trí đúng.
- **Bỏ sót artifact completeness**: Có manifest nhưng thiếu mode/case; kiểm độ phủ, không chỉ kiểm existence.

---

## Top 5 lỗi nghiêm trọng nhất (mọi vai trò phải biết):
1. **DoD/GATE mơ hồ gây REVISE loop** — Làm pipeline lặp vô hạn và tốn vòng rescue; luôn viết tiêu chí binary, định lượng, đo được.
2. **Sai repo root hoặc ghi vào shadow folder** — Coder báo DONE nhưng repo thật không đổi; preflight xác nhận `repo_root` là git repo đúng.
3. **Thiếu runtime artifact evidence** — Code đúng vẫn BLOCK vì không chứng minh đã chạy thật; bắt buộc snapshot artifact + schema + số liệu chính.
4. **Manifest/convergence không đầy đủ cho sweep** — Không chứng minh đủ case hoặc hội tụ làm reviewer từ chối; ghi full record kể cả fail + ngưỡng hội tụ rõ.
5. **Cấu hình/đầu ra orchestrator không ổn định (JSON parse, auto-rescue che lỗi, quota/auth)** — Pipeline dừng sai nguyên nhân; ưu tiên xử lý lỗi hạ tầng theo thứ tự root-cause và restart process sau khi sửa config.
```