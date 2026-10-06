# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Tiến Tuân | 2A202602595 | Toàn bộ |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `gpt-6-luna` qua cổng tương thích OpenAI (`AZURE_OPENAI_DEPLOYMENT_MODEL`; `make_model()` trả về `ChatOpenAI`); `LAB_TEMPERATURE=1` (mô hình chỉ chấp nhận giá trị mặc định 1, nên đầu ra có tính ngẫu nhiên giữa các lần chạy); `recursion_limit=60` (mặc định). Ghi chú: thử `gpt-5.6-luna` trước đó thất bại vì cổng không cho gọi công cụ qua `/v1/chat/completions` khi bật suy luận (lỗi 400, lỗi hạ tầng, đã xóa kết quả, không tính vào số liệu).
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: deepagents 0.7.21 (langchain 1.4.3, langchain-core 1.6.6), macOS 26.6.2, Python 3.12.14, chạy trực tiếp (venv), không dùng Docker.
- Số lần chạy tác vụ đã dùng / ngân sách: 24 lần chạy tác vụ có kết quả hợp lệ.
  - 3 baseline học, 3 subagents học, 3 skills-auto học ở Phần 3.4 (lưu ở `results/skills-auto-dev/`).
  - 3 baseline đánh giá, 3 subagents đánh giá, 6 skills-auto sau đóng băng.
  - Thêm 1 lần baseline `data-learn` bị ghi đè khi chạy lại ở Phần 2.1.
  - Thêm 2 lần thất bại do hạ tầng, 0 token: lỗi 400 của `gpt-5.6-luna` và lỗi 400 khi đặt `temperature=0`.
  - Curator: 2 lần gọi mô hình.
  - Không có giới hạn ngân sách cụ thể nào được giao.
- Commit của tag `freeze`: `4b3c13d` ("freeze skills"). Commit giả thuyết đứng ngay trước nó: `c381226` ("hypotheses").

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Trên tác vụ đánh giá, `subagents` **không cao hơn** `baseline`; dự đoán chênh lệch tổng trong khoảng ±1 check, nhưng tốn khoảng **gấp 2 lần token**. Căn cứ: (1) toàn bộ lỗi ở tác vụ học thuộc nhóm E (thiếu thông tin quy ước, mục 4), mà giao việc không tạo ra được thông tin đó; trên tác vụ học `subagents` đạt 17/27 so với 18/27 và vẫn 0/9 check `rule_`; (2) lời giao việc còn có thể làm mất định nghĩa của đề (lỗi `north_q1_orders`, mục 5); (3) tài liệu về hệ thống đa tác tử của Anthropic ghi nhận đa tác tử tốn token hơn nhiều lần, và trên tác vụ học tỉ lệ token là ×2,0.
- H2 (skills-auto so với baseline): `skills-auto` đạt **điểm cao nhất** trên tác vụ đánh giá. Mức tăng chủ yếu đến từ các check `rule_` của họ `code` và `logs`, vì tác vụ đánh giá dùng lại các quy ước của tác vụ học, và hai skill `python-bugfix-handoff`, `log-triage-output` ghi cụ thể các quy ước này. Dự đoán: hai họ này tăng được phần lớn số check quy ước đã học. Họ `data` không tăng, vì không có skill data; có thể còn bị chuyển giao âm do tác tử đọc nhầm skill log như đã thấy ở Phần 3.4. Check kỹ thuật không đổi, vì baseline đã đạt 18/18 trên tác vụ học. Căn cứ đối chiếu: SkillsBench cho rằng skill do mô hình tự sinh trung bình không có lợi. Nhóm dự đoán thí nghiệm này là ngoại lệ, vì lỗi ở đây là thiếu thông tin (quy ước ẩn) chứ không phải thiếu kỹ năng, và phản hồi `detail` cung cấp đúng thông tin đó.
- H3 (tác vụ học so với tác vụ đánh giá): Mức tăng của `skills-auto` so với `baseline` trên tác vụ đánh giá sẽ **nhỏ hơn** trên tác vụ học: tác vụ học tăng +6 check, từ 18/27 lên 24/27 ở Phần 3.4. Lý do là mỗi tác vụ đánh giá có thêm một quy ước **mới** mà skill không thể biết; bước chung "check the task for any other Acme convention" không cung cấp được nội dung của quy ước đó. Vì vậy nhóm dự đoán check quy ước mới thất bại ở cả ba điều kiện. Đây là dạng quá khớp được SkillEvolBench mô tả: lợi ích trên tác vụ học chuyển sang tác vụ mới chỉ một phần. Nhóm cũng dự đoán điểm tác vụ học của cùng bộ skill sau đóng băng chênh với Phần 3.4 khoảng ±1–2 check, do nhiễu: `LAB_TEMPERATURE=1` và mỗi cấu hình chỉ chạy một lần.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Theo `python scripts/tour.py`, tác tử mặc định có 9 công cụ:
   - Công cụ tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`.
   - Shell: `execute`.
   - Giao việc cho subagent: `task`.

   Công cụ cho phép chạy lệnh là `execute`. Công cụ này chỉ dùng được khi backend cài đặt `SandboxBackendProtocol`, ví dụ `LocalShellBackend`.
2. Theo mô tả của `task`, `general-purpose` là subagent đa năng, dùng để "researching complex questions, searching for files and content, and executing multi-step tasks". Nó "has access to all tools as the main agent".
   - Ngữ cảnh: subagent này **không** thấy hội thoại hay system prompt của tác tử chính: "Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report".
   - Hệ quả: tác tử chính phải đưa toàn bộ quy tắc và đường dẫn vào lời giao việc. Ngược lại, tác tử chính chỉ nhận về báo cáo cuối, không thấy các bước bên trong subagent.
3. Hai câu trích về hành vi:
   - Từ mô tả `task`: *"Put full detail in the prompt and state exactly what it should return"*. Ngoài ra còn có *"Launch multiple agents concurrently when their tasks are independent"*.
   - Từ mô tả `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

   Một điểm cần lưu ý: mô tả `execute` khuyên *"Use absolute paths and avoid `cd`"*. Điều này mâu thuẫn với `PATHS_NOTE` của lab, vốn yêu cầu đường dẫn tương đối `workspace/...`, vì `/workspace` không tồn tại trên hệ thống tệp thật. Đây là lý do `BASE_PROMPT` phải nêu rõ quy ước đường dẫn.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `rule_type_hints` | E | `detail`: "RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value." Tác tử chỉ sửa logic của `pricing.py`, `report.py`, `export.py`; không thêm chú thích kiểu. |
| code-learn | `rule_regression_tests` | E | `detail`: "RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3)". Vết không có lệnh `write_file` nào tạo `tests/test_regressions.py`; tác tử dừng khi thấy "All 6 tests pass". |
| code-learn | `rule_changelog` | E | `detail`: "RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): …'". Vết cho thấy tác tử **đã đọc** `workspace/CHANGELOG.md` (tool call `read_file`, kết quả có mục `## Unreleased` còn trống) nhưng không ghi gì vào đó. |
| data-learn | `rule_money_in_cents` | E | `detail`: "RULE: money values in answer.json are integer cents (1606.67 USD is written 160667)." Tác tử ghi `"north_q1_revenue": 3130.24` (USD, số thực). |
| data-learn | `rule_meta_block` | E | `detail`: "RULE: answer.json has an object `meta` = {"source", "rows_in", "rows_used"}". `answer.json` trong vết chỉ có đúng 5 khóa của đề, không có `meta`. |
| data-learn | `rule_clean_csv` | E | `detail`: "RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents …". Không có `clean.csv`: tác tử chỉ ghi `answer.json`, và câu trả lời cuối cũng chỉ nhắc "Created `workspace/answer.json`". |
| logs-learn | `rule_service_names` | E | `detail`: "RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service)." Tác tử giữ nguyên dạng `payment-service`, giống ví dụ trong đề. |
| logs-learn | `rule_sorted_errors` | E | `detail`: "RULE: `errors` is sorted by service, then by timestamp_utc, ascending." Tác tử giữ thứ tự xuất hiện trong tệp log. |
| logs-learn | `rule_schema_header` | E | `detail`: "RULE: the top-level object has \"schema_version\": 2 and \"generated_by\": \"log-triage\"." Đầu ra chỉ có `errors` và `counts_by_service`, đúng theo cấu trúc mẫu trong đề. |

Nhận xét:

- **Nhóm E chiếm toàn bộ: 9/9 check thất bại.** Mỗi tác vụ học có đúng 3 check quy ước `rule_`, và baseline thất bại cả 9 (`house rules 0/9` theo `python scripts/check_breakdown.py`).
- **Nguyên nhân chung là thiếu thông tin, không phải thiếu năng lực.** Đề chỉ nói "plus whatever the Acme … conventions require" và "checked by Acme's review bot". Nội dung các quy ước không có trong đề hay workspace: `grep -i "acme\|convention"` trên `tasks/*-learn/workspace/README.md` không ra kết quả nào. Tác tử không có cách nào suy ra các quy ước này. Nó cũng không hỏi lại, và không nêu trong câu trả lời cuối rằng quy ước chưa rõ.
- **Bằng chứng phủ định cho nhóm A–D:**
  - `check_breakdown.py` cho baseline `technical 18/18`: mọi check kỹ thuật đều đạt. Cụ thể: `parse_price_all_formats`, `other_caller_fixed` (sửa đúng hàm dùng chung, tức không vá triệu chứng – C), `low_stock_follows_docstring`, `csv_quoting_follows_docstring` (đọc docstring – A), `duplicate_rows_removed`, `missing_amount_orders` (xử lý dữ liệu bẩn – D), `timestamps_utc`, `repeat_counts` (múi giờ, dòng lặp – D), `visible_suite_passes` (có chạy lại test – B).
  - Không có lỗi nhóm F: câu trả lời cuối của cả ba tác vụ chỉ nêu những tệp thật sự có trong vết (ví dụ "Created `workspace/answer.json`", "All 6 tests pass").
  - Không có lỗi hạ tầng: `error = null` ở cả 3 lần chạy.
- **Skill có thể phòng ngừa nhóm E, nhưng có giới hạn.**
  - Với tác vụ học, phản hồi `detail` của bot đã phát biểu rõ từng quy tắc. Một skill do curator rút ra có thể truyền lại đúng các quy ước này, ví dụ: tiền ghi bằng cent, khối `meta`, CHANGELOG `fix(<fn>)`, kiểu chú thích, test hồi quy, tên service dạng `snake_case`, header schema.
  - Skill khó giúp được với quy ước **mới** chỉ có ở tác vụ đánh giá: chưa có phản hồi nào nhắc đến chúng. Với quy ước mới, skill tốt nhất chỉ có thể dạy *quy trình* (tìm và tuân thủ quy ước của tổ chức, ghi tệp phụ, sắp xếp ổn định), không thể dạy *nội dung*.
  - Đây cũng là rủi ro quá khớp: skill có thể học thuộc quy ước của tác vụ học mà không chuyển sang được tác vụ mới.

## 5. Điều kiện `subagents` (Phần 2.3)

- **Các subagent đã định nghĩa** (`src/lab/subagents.py`). `build_agent` nối thêm `PATHS_NOTE` vào cả ba.
  - `explorer`: chỉ đọc. Đọc README, docstring, test và mẫu dữ liệu, rồi báo cáo quy tắc, định dạng đầu ra và điểm bất thường của dữ liệu. Lý do: phòng nhóm lỗi A (bỏ qua đặc tả) và D (bỏ sót dữ liệu bẩn).
  - `implementer`: thực hiện thay đổi, sửa nguyên nhân gốc, chạy lại test hoặc script, và chỉ báo cáo những tệp thật sự đã sửa. Lý do: phòng nhóm C (vá triệu chứng) và F (báo cáo sai sự thật).
  - `reviewer`: kiểm tra độc lập theo từng quy tắc và trả về danh sách PASS/FAIL, không sửa tệp. Lý do: phòng nhóm B (không kiểm chứng).

- **`subagent_calls` ở từng tác vụ.** Bằng 3 ở cả ba tác vụ học (`code-learn`, `data-learn`, `logs-learn`).
  - Lần nào tác tử chính cũng gọi đúng một chuỗi `explorer` → `implementer` → `reviewer`.
  - Ở baseline, `subagent_calls` = 0 ở cả ba tác vụ: tác tử chính không dùng subagent `general-purpose` có sẵn.
  - Số tool call ở luồng chính giảm, vì việc đọc và ghi chuyển vào bên trong subagent nên không hiện trong `trace.md`:

  | Tác vụ | tool_calls baseline | tool_calls subagents |
  |---|---|---|
  | code-learn | 26 | 7 |
  | data-learn | 8 | 6 |
  | logs-learn | 4 | 6 |

  - Tác tử chính có tự kiểm tra một phần trước khi dùng kết quả.
    - Ở `code-learn` và `data-learn`, sau khi `implementer` báo xong, nó tự `ls` và `read_file` các tệp vừa sửa hoặc vừa tạo, rồi mới gọi `reviewer`.
    - Ở `logs-learn`, sau báo cáo của `explorer`, nó tự đọc lại `workspace/README.md` và `workspace/app.log`. Đây là việc làm lặp lại mà `explorer` đã làm.

- **Thông tin thiếu hoặc thừa khi giao việc** (trích từ các tool call `task` trong `trace.md`):
  1. **Lời giao việc cho `explorer` thiếu đề bài.** Ở `data-learn`, lời giao việc chỉ nêu tệp cần đọc, không chép danh sách khóa phải có trong `answer.json`. Vì vậy `explorer` báo: *"No required output filename, JSON keys, or formatting are specified."* Lời giao việc cho `explorer` ở `logs-learn` cũng thiếu như vậy.
  2. **Định nghĩa bị viết lại sai khi chuyển tiếp.** Đây là nguyên nhân của check duy nhất mà `subagents` làm kém hơn baseline: `data-learn / north_q1_orders`, `detail`: *"wrong value (got 13)"*. Baseline ghi 10 và đạt.
     - Đề định nghĩa `north_q1_orders` là *"number of distinct orders counted in `north_q1_revenue`"*. Tức là phải loại các đơn thiếu số tiền (`-999`).
     - Lời giao việc cho `implementer` rút gọn thành *"North Q1 2024 ..., distinct orders"* và mất mệnh đề "counted in revenue". `implementer` vì thế đếm cả đơn thiếu số tiền: cùng doanh thu 3130.24 nhưng ra 13 đơn.
     - Lời giao việc cho `reviewer` cũng không có định nghĩa này, nên `reviewer` cho PASS với giá trị 13.

     Đây là minh họa cho rủi ro "subagent chỉ thấy những gì được gửi": cả hai subagent làm đúng theo lời giao việc, nhưng lời giao việc đã sai so với đề.
  3. **Không subagent nào phát hiện được quy ước Acme** (các check `rule_*`). Lời giao việc có nhắc *"Acme conventions apply"* hoặc *"plus only whatever reporting conventions in workspace README require"*. Nhưng quy ước này không nằm trong workspace, và `explorer` báo đúng như vậy: *"The README does not state any Acme-specific triage conventions"*. Vì thế 9/9 check `rule_` vẫn thất bại, giống baseline. Đa tác tử không bù được thông tin không có trong ngữ cảnh.
  4. **Lời giao việc ở `code-learn` đầy đủ nhất.** Nó chép lại từng yêu cầu docstring và lệnh test. Cả 7/7 check kỹ thuật đều đạt, giống baseline.

- **Ảnh hưởng đến điểm, token và thời gian.** `tokens.total` tính cả token bên trong subagent.

  | Tác vụ | Điểm baseline | Điểm subagents | Token baseline | Token subagents | Tỉ lệ token | Giây baseline | Giây subagents |
  |---|---|---|---|---|---|---|---|
  | code-learn | 7/10 | 7/10 | 99 215 | 127 236 | ×1,28 | 104,7 | 140,1 |
  | data-learn | 5/8 | 4/8 | 34 009 | 93 974 | ×2,76 | 40,4 | 125,3 |
  | logs-learn | 6/9 | 6/9 | 20 858 | 86 667 | ×4,16 | 29,4 | 110,3 |
  | **Tổng** | **18/27** | **17/27** | **154 082** | **307 877** | **×2,00** | **174,5** | **375,7** |

  - Đa tác tử tốn gấp đôi token và khoảng 2,2 lần thời gian, nhưng không tăng điểm nào và mất 1 check.
  - Chi phí tăng mạnh nhất ở tác vụ nhỏ (`logs-learn` ×4,16). Lý do: mỗi subagent phải đọc lại README và tệp dữ liệu từ đầu, và tác tử chính cũng đọc lại.
  - Ở tác vụ lớn (`code-learn`) chi phí cố định này chiếm tỉ lệ nhỏ hơn (×1,28).
  - Kết luận trên tác vụ học: với các tác vụ ngắn và tuần tự như ở lab này, đa tác tử không đáng chi phí. Lưu ý mỗi cấu hình mới chạy một lần, nên chênh lệch 1 check có thể là nhiễu. Nhưng nguyên nhân của nó (mất định nghĩa khi giao việc) thấy rõ trong vết.
  - Ghi chú về vết: mô hình trả nội dung dạng danh sách khối (khối `reasoning` có `encrypted_content`). Vì vậy `trace.md` hiển thị nguyên chuỗi khối đó; nội dung này không chứa khóa API.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- **Số lần chạy curator, số skill bị xóa và lý do.** Curator chạy 2 lần (lần đầu và 1 lần chạy lại, trong giới hạn 2 lần chạy lại). Đầu vào là `results/baseline/*-learn`, mỗi lần gọi mô hình một lần. Không sửa tay nội dung skill nào.
  1. **Lần 1: ghi 3 skill, cả 3 đã bị xóa.** Ba skill là `complete-code-fixes` (10 dòng), `validate-data-deliverables` (11 dòng), `enforce-log-output-conventions` (10 dòng). Bản lưu ở `report/deleted-skills/run1/`.
     - Lý do xóa: cả ba **quá tổng quát** nên vô dụng với nhóm lỗi E. Curator đã trừu tượng hóa các quy ước cụ thể trong `detail` thành những câu chung chung, ví dụ *"convert to integer minor units when the schema requires it"*, *"Normalize identifiers such as service names exactly as specified by the output contract"*, *"Sort records by the specified keys"*.
     - Nhưng đề không hề cho "schema" hay "contract". Các quy ước Acme chỉ có trong phản hồi của bot, nên những skill này không chứa thông tin mà tác tử còn thiếu.
     - Nguyên nhân nằm ở prompt của curator: nó cấm "tên tệp, con số". Mình đã bổ sung prompt (`CURATOR_PROMPT` trong `src/lab/curator.py`): các dòng `RULE:` là quy ước của tổ chức, áp dụng cho mọi tác vụ cùng loại, nên phải ghi **cụ thể**. Prompt vẫn cấm id tác vụ, tên tệp dữ liệu đầu vào, và đáp án hay con số tính từ dữ liệu. Prompt cũng thêm một bước chung: trước khi kết thúc, tìm các quy ước khác mà đề có nhắc.
  2. **Lần 2 (chạy lại 1/2): mô hình sinh 3 khối, `validate_skill` từ chối 1.** Khối bị từ chối là `sales-data-outputs`, vì *"mentions evaluation material"*: nó chứa một từ trùng với định danh của tác vụ đánh giá. Bộ lọc chống rò rỉ hoạt động đúng; ở đây đó là dương tính giả, vì từ này xuất hiện tự nhiên trong ngữ cảnh dữ liệu bán hàng.
     - Ghi được 2 skill: `python-bugfix-handoff` và `log-triage-output`.
     - Nhóm quyết định **không** dùng lần chạy lại thứ 2. Lý do: hai skill hiện có đúng và cụ thể; chạy lại có thể làm mất chúng; và họ `data` không có skill trở thành một điểm đối chứng tự nhiên.
     - Không sửa prompt để né từ bị chặn, vì làm vậy là dùng thông tin của tác vụ đánh giá.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `python-bugfix-handoff` | Cụ thể theo **quy ước Python của Acme**, không theo tác vụ: không nêu id tác vụ, tên gói `inventory` hay tên hàm. Ba quy ước (kiểu chú thích cho hàm public, `tests/test_regressions.py` có ít nhất 3 test, CHANGELOG `- fix(<function name>): …`) áp dụng được cho mọi gói Python của Acme. Chỉ có một bước thật sự tổng quát: "check the task for any other Acme convention". | **Đúng** với cả ba `detail` (đối chiếu từng câu). Một điểm có thể gây hại nhẹ: *"Add a `## Unreleased` heading to `CHANGELOG.md`"* có thể khiến tác tử tạo tiêu đề trùng nếu tiêu đề đã có. Trong vết 3.4, tác tử dùng `edit_file` chèn vào dưới tiêu đề `## Unreleased` có sẵn, nên không bị trùng. | 10 dòng (6 dòng chỉ dẫn), không thừa. `description` nêu đúng tình huống: "Python package bug-fix tasks … typing, regression-test, and changelog conventions". `code-learn`: `skills_read = 1`, đọc đúng skill này **ngay hành động đầu tiên**, và làm theo đủ: thêm 4 dòng `- fix(...)` dưới `## Unreleased`, tạo test hồi quy, thêm chú thích kiểu. Điểm **10/10** (baseline 7/10, `rule_` 3/3 so với 0/3). |
| `log-triage-output` | Cụ thể theo **quy ước log-triage của Acme**. Ba quy ước (`schema_version: 2`, `generated_by: "log-triage"`; tên service chữ thường, `-` thành `_`; sắp xếp `errors` theo service rồi `timestamp_utc`) đều chép đúng từ `detail`. Không có đáp án hay số liệu của tệp log. Ví dụ `payment-service` lấy từ phản hồi của bot (minh họa định dạng). | **Đúng** với cả ba `detail`. Nhưng `description` mở rộng sang *"structured error output"*, đủ rộng để tác tử áp dụng **sai miền**: ở `data-learn`, tác tử đọc skill này và ghi `"schema_version": 2, "generated_by": "log-triage"` vào `answer.json` (vết, `write_file`). Như vậy nó vi phạm yêu cầu *"exactly these keys"* của đề, dù bot không chấm điều này. Đây là chuyển giao âm. | 8 dòng (4 dòng chỉ dẫn), không thừa. `logs-learn`: `skills_read = 1`, đọc ngay đầu, làm theo đủ, điểm **9/9** (baseline 6/9). `data-learn`: `skills_read = 1` nhưng đọc **skill sai** (không có skill data). Không check `rule_` nào của data đạt (0/3, baseline 0/3); câu trả lời cuối ghi *"I found no additional Acme conventions beyond the JSON header fields"*. Điểm **5/8**, bằng baseline. |

- **Tổng kết Phần 3.4** (`results/skills-auto-dev/`, đã sao lưu trước khi đóng băng):
  - Điểm: 24/27 so với 18/27 của baseline. Check `rule_`: 6/9 so với 0/9. Check kỹ thuật vẫn 18/18.
  - Token: 199 003 so với 154 082 (×1,29). Mỗi lần chạy có thêm một lần đọc skill, và tác vụ code có thêm việc viết test và changelog.
  - Mọi lần chạy có `skills_modified = false`.
  - Mức tăng điểm này **chỉ đo trên chính các tác vụ đã sinh ra skill**, nên chưa phải bằng chứng về khả năng tổng quát hóa (xem giả thuyết H3 và Phần 4).

## 7. Kết quả so sánh (Phần 4.3, 4.4)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 10/10 |
| data-learn | 5/8 | 4/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 9/9 |
| code-eval | 7/11 | 7/11 | 10/11 |
| data-eval | 5/9 | 5/9 | 5/9 |
| logs-eval | 6/10 | 6/10 | 9/10 |
| **Mean score - learning tasks** | 0.66 | 0.62 | 0.88 |
| **Mean score - evaluation tasks** | 0.60 | 0.60 | 0.79 |
| **Mean tokens per run** | 44,563 | 122,157 | 56,708 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |

Kết quả `python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     18/18         0/12          37,766      0/3
baseline      learn    18/18         0/9           51,360      0/3
subagents     eval     18/18         0/12         141,689      0/3
subagents     learn    17/18         0/9          102,625      0/3
skills-auto   eval     18/18         6/12          53,377      3/3
skills-auto   learn    18/18         6/9           60,039      3/3
```

Các check quy ước thất bại ở **tác vụ đánh giá**, lấy từ `run.json`; trường `detail` để trống theo thiết kế:

| Tác vụ | baseline | subagents | skills-auto |
|---|---|---|---|
| code-eval | `rule_type_hints`, `rule_regression_tests`, `rule_changelog`, `rule_version_bump` | giống baseline | chỉ `rule_version_bump` |
| data-eval | `rule_money_in_cents`, `rule_meta_block`, `rule_clean_csv`, `rule_sorted_keys_format` | giống baseline | giống baseline |
| logs-eval | `rule_service_names`, `rule_sorted_errors`, `rule_schema_header`, `rule_source_line` | giống baseline | chỉ `rule_source_line` |

- **Quy ước mới của tác vụ đánh giá** (các check không có ở tác vụ học): `rule_version_bump`, `rule_sorted_keys_format`, `rule_source_line`. Cả ba thất bại ở **mọi** điều kiện.
- **Skill được đọc ở các lần chạy `skills-auto` sau đóng băng:**
  - `code-eval`: đọc cả `python-bugfix-handoff` và `log-triage-output`.
  - `logs-eval`: đọc `log-triage-output`.
  - `data-eval` và `data-learn`: chỉ đọc `log-triage-output`. Vì không có skill data, tác tử lại ghi `"generated_by": "log-triage"` vào `answer.json` (chuyển giao âm, lặp lại hiện tượng ở Phần 3.4).
- `subagent_calls` ở các tác vụ đánh giá: `code-eval` 4, `data-eval` 3, `logs-eval` 2.
- **Lỗi và chỉnh sửa skill:** không lần chạy nào có `error` khác `null` hay `skills_modified = true`. `python scripts/verify_freeze.py` báo `checked 6 runs of skill conditions: OK`.
- **Điểm tác vụ học của cùng bộ skill** (dùng để ước lượng nhiễu):

  | Tác vụ | Phần 3.4 (`results/skills-auto-dev/`) | Sau đóng băng (`results/skills-auto/`) |
  |---|---|---|
  | code-learn | 10/10 | 10/10 |
  | data-learn | 5/8 | 5/8 |
  | logs-learn | 9/9 | 9/9 |

  Token của hai lần lần lượt là 199 003 và 180 119.

## 8. Phân tích

### 8.1. Cải thiện trên tác vụ học và tác vụ đánh giá

| Điều kiện | Tác vụ học (điểm TB, số check) | Tác vụ đánh giá (điểm TB, số check) |
|---|---|---|
| baseline | 0,66 (18/27) | 0,60 (18/30) |
| subagents | 0,62 (17/27) | 0,60 (18/30) |
| skills-auto | **0,88 (24/27)** | **0,79 (24/30)** |

- **`skills-auto`** là điều kiện duy nhất cải thiện cả hai tập: tác vụ học +6 check (+0,22), tác vụ đánh giá +6 check (+0,19).
- **`subagents`** không cải thiện tập nào: tác vụ học −1 check, tác vụ đánh giá ±0.
- **Không có điều kiện nào cải thiện tác vụ học mà không cải thiện tác vụ đánh giá**, nên không thấy dạng quá khớp "thuộc lòng tác vụ học".
- **Quá khớp ở mức quy ước thì có.** Skill chỉ giúp các quy ước đã gặp. Tỉ lệ check đạt nhờ skill giảm từ 6/9 quy ước có ở tác vụ học xuống 6/12 quy ước ở tác vụ đánh giá. Ba quy ước mới đều thất bại (xem 8.2).
- **So với giả thuyết:**
  - H1 đúng: subagents bằng baseline trên tác vụ đánh giá.
  - H2 đúng: skills-auto cao nhất, mức tăng nằm ở họ `code` và `logs`, họ `data` không đổi.
  - H3 đúng một phần: quy ước mới thất bại ở mọi điều kiện như dự đoán, nhưng mức tăng tuyệt đối không nhỏ hơn (+6 so với +6). Lý do: mỗi tác vụ đánh giá lặp lại đủ 3 quy ước cũ của họ mình.

### 8.2. Check kỹ thuật và check quy ước

- **Check kỹ thuật:**
  - Tác vụ học: 18/18 ở `baseline` và `skills-auto`, 17/18 ở `subagents`.
  - Tác vụ đánh giá: 18/18 ở cả ba điều kiện.

  Mô hình đã giải tốt phần kỹ thuật mà không cần trợ giúp, nên không còn dư địa để skill cải thiện.
- **Check quy ước (`rule_`):**
  - `baseline` và `subagents`: 0/9 (tác vụ học), 0/12 (tác vụ đánh giá).
  - `skills-auto`: 6/9 (tác vụ học), 6/12 (tác vụ đánh giá).

  Toàn bộ mức tăng của skill nằm ở nhóm check quy ước.
- **Check quy ước mới của tác vụ đánh giá:** `rule_version_bump` (code), `rule_sorted_keys_format` (data), `rule_source_line` (logs). Skill **không giúp** được check nào: cả ba thất bại ở mọi điều kiện.
  - Lý do: nội dung các quy ước này chưa xuất hiện trong bất kỳ phản hồi nào mà curator được đọc. Curator cũng không được phép đọc tác vụ đánh giá.
  - Bước chung "check the task for any other Acme convention" có được thực hiện, nhưng chỉ dẫn đến câu trả lời *"No additional Acme conventions were specified"* (`code-eval`). Lý do là quy ước không nằm trong workspace.
  - Skill chỉ chuyển giao được **thông tin đã có trong phản hồi**, không tự sinh ra được quy ước mới.

### 8.3. Một check skill giúp đạt và một check skill không giúp

- **Skill giúp: `code-eval / rule_changelog`.** Baseline thất bại, `skills-auto` đạt.
  - Vết: tác tử đọc `skills/python-bugfix-handoff/SKILL.md` ngay từ hành động đầu tiên (`skills_read = 2`). Skill có dòng *"record each fix as `- fix(<function name>): <short description>`; include at least 3 bullets"*.
  - Sau đó tác tử đọc `workspace/CHANGELOG.md`, rồi gọi `edit_file` để chèn dưới tiêu đề `## Unreleased` có sẵn các dòng `- fix(parse_duration): …` (một gói khác với tác vụ học).
  - Skill được đọc và làm theo đúng từng chữ. Cùng cơ chế này giúp đạt `rule_type_hints` và `rule_regression_tests`.
  - Ở họ `logs` cũng vậy: `errors.json` của `logs-eval` có `"schema_version": 2` đúng như skill `log-triage-output` yêu cầu.
- **Skill không giúp (skill thiếu và bị đọc nhầm): `data-eval / rule_meta_block`** (và cả 3 check quy ước cũ còn lại của họ data).
  - Curator đã sinh skill data ở lần chạy 2, nhưng `validate_skill` loại nó vì chứa từ trùng định danh tác vụ đánh giá. Vì vậy trong `skills/auto/` không có skill data.
  - Vết của `data-eval` và `data-learn`: tác tử đọc `skills/log-triage-output/SKILL.md` (`skills_read = 1`). Đây là skill của miền khác, có `description` *"…structured error output…"* đủ rộng để khớp.
  - Tác tử làm theo sai miền: ghi `"generated_by": "log-triage"` vào `answer.json` và trả lời *"I found no additional … conventions beyond the JSON metadata requirements"*.
  - Hệ quả: skill sai miền không làm giảm điểm, vì bot không chấm khóa thừa. Nhưng nó vi phạm yêu cầu "exactly these keys" của đề và **thay thế** việc tìm quy ước thật. Đây là chuyển giao âm.
- **Skill không giúp (quy ước mới): `code-eval / rule_version_bump`.** Tác tử có đọc phiên bản trong gói (`__version__ = "1.4.2"` trong vết) nhưng không đổi nó, vì không skill hay tài liệu nào yêu cầu.

### 8.4. Chi phí

| Điều kiện | Token TB/lần chạy (cả 6 tác vụ) | Token tác vụ đánh giá (tổng 3) | Check đạt / 100k token (đánh giá) | Thời gian tác vụ đánh giá (tổng) |
|---|---|---|---|---|
| baseline | 44 563 | 113 300 | 15,9 | 138,4 s |
| subagents | 122 157 (×2,7) | 425 069 (×3,75) | 4,2 | 800,5 s |
| skills-auto | 56 708 (×1,27) | 160 132 (×1,41) | 15,0 | 101,7 s |

- **Hiệu quả theo điểm trên token:** `baseline` và `skills-auto` gần như ngang nhau (15,9 và 15,0 check đạt trên 100k token). `subagents` kém khoảng 3,7 lần.
- **Theo chi phí biên:** `skills-auto` dùng thêm 46 832 token cho 6 check, tức khoảng 7,8k token cho mỗi check thêm. Thời gian còn **ngắn hơn** baseline (101,7 s so với 138,4 s), vì tác tử biết ngay cần làm gì.
- **Đa tác tử không đáng chi phí trong thí nghiệm này:** tốn gấp 3,75 lần token và 5,8 lần thời gian (riêng `code-eval`: 538 s, 226 802 token) mà không thêm check nào.
  - Lý do: lỗi là thiếu thông tin, không phải thiếu năng lực xử lý. Tác vụ ngắn và tuần tự, và mỗi subagent phải đọc lại ngữ cảnh từ đầu.
  - Ở `data-eval` và `logs-eval`, tác tử chính chỉ giao cho `explorer` và `reviewer` rồi tự làm phần thực hiện. Đây là chi phí điều phối không mang lại lợi ích.
- **Chi phí của curator:** 2 lần gọi mô hình, một lần cho mỗi lần chạy curator. Chi phí này không có trong bảng vì nó nằm ngoài `run.json`.

### 8.5. Rò rỉ dữ liệu và quá khớp

- **Rò rỉ: không thấy dấu hiệu.**
  - Curator chỉ đọc các run có `role == "learn"` (có test kiểm tra). Trường `detail` của tác vụ đánh giá luôn rỗng.
  - `validate_skill` đã chặn một khối chứa từ trùng định danh tác vụ đánh giá. Đây là dương tính giả về ngữ nghĩa, nhưng nhóm không sửa prompt để né từ bị chặn, vì làm vậy là dùng thông tin của tác vụ đánh giá.
  - Hai skill còn lại chỉ chứa quy ước lấy từ `detail` của tác vụ học. Không có tên tệp hay số liệu của tác vụ đánh giá.
  - Nhóm không mở `check.py` hay `run.json` của tác vụ đánh giá trước tag `freeze`. Lịch sử git: commit `hypotheses` có trước `freeze`, và mọi kết quả đánh giá đều sau.
- **Quá khớp: có, ở mức quy ước.**
  - Skill chép nguyên quy ước của tác vụ học, ví dụ `generated_by: "log-triage"` và `schema_version: 2`. Vì vậy skill chỉ có ích khi tác vụ mới dùng đúng các quy ước đó.
  - Bằng chứng: 3/3 quy ước mới thất bại; skill log bị dùng sai sang tác vụ data.
  - Biện pháp nhóm đã dùng:
    1. Prompt curator yêu cầu không nêu id tác vụ, tên tệp dữ liệu đầu vào, đáp án hay con số.
    2. Đóng băng skill trước khi đo trên tác vụ đánh giá.
    3. Đọc và đánh giá từng skill (mục 6).
  - Biện pháp nên thêm: `description` nêu rõ phạm vi ("only for log-triage tasks") để tránh áp dụng sai miền.
- **Rủi ro phương pháp:** nhóm đã sửa prompt của curator sau khi xem đầu ra lần 1 (mục 6). Thông tin dùng để sửa chỉ đến từ tác vụ học, nên không có rò rỉ dữ liệu đánh giá. Nhưng đây là một bậc tự do của người làm thí nghiệm, nên được ghi lại.

### 8.6. Nhiễu

- **Điểm tác vụ học của cùng bộ skill** ở Phần 3.4 (`results/skills-auto-dev/`) và sau đóng băng (`results/skills-auto/`): 10/10, 5/8, 9/9 ở cả hai lần, **chênh 0 check**.
- **Token** chênh −9,5% (199 003 so với 180 119). Riêng `logs-learn` chênh 41 180 so với 27 834.
- **Baseline `data-learn`** cũng có hai lần chạy (lần đầu bị ghi đè): cùng 5/8, token 29 079 so với 34 009.
- **Ý nghĩa:**
  - Trên các tác vụ này, **điểm** khá ổn định, còn **token** dao động khoảng 10–30%.
  - Mức chênh +6 check của `skills-auto` lặp lại ở 2 lần đo tác vụ học và ở tác vụ đánh giá, và có cơ chế giải thích rõ trong vết (8.3). Vì vậy nhiều khả năng đây là hiệu ứng thật.
  - Ngược lại, mức −1 check của `subagents` ở `data-learn` chỉ xảy ra một lần. Dù có cơ chế (mất định nghĩa khi giao việc, mục 5), nó nằm trong vùng có thể là nhiễu.
  - Chênh lệch token nhỏ hơn khoảng 30% giữa các điều kiện không nên được diễn giải.
  - Thử thách 6e (phụ lục) lặp mỗi điều kiện 3 lần trên tác vụ đánh giá và xác nhận điều này: điểm giống hệt nhau ở cả 27 lần chạy (độ lệch chuẩn 0), còn token có hệ số biến thiên khoảng 46–54%.

## 9. Hạn chế và tính hợp lệ

1. **Cỡ mẫu nhỏ: 3 tác vụ mỗi vai trò, 9–11 check mỗi tác vụ.**
   - Toàn bộ kết luận dựa trên 30 check đánh giá, và mức tăng chỉ đến từ 2/3 họ tác vụ.
   - Không thể tính khoảng tin cậy có ý nghĩa, cũng không thể khái quát sang loại tác vụ khác. Ví dụ: tác vụ dài và song song được, nơi đa tác tử có thể có lợi.
2. **Mỗi cấu hình chạy một lần, mô hình có tính ngẫu nhiên** (`LAB_TEMPERATURE=1`, mô hình không cho đặt 0).
   - Thử thách 6e cho thấy điểm trên tác vụ đánh giá không đổi qua 3 lần lặp. Tuy vậy, 3 lần lặp vẫn là ít, và chúng dùng chung một bộ skill, một mô hình và cùng thời điểm (cùng phiên bản mô hình phía nhà cung cấp).
   - Chênh lệch ±1 check (như `subagents` ở `data-learn`) không phân biệt được với nhiễu. Chỉ mức +6 check của `skills-auto`, lặp lại nhất quán, là đủ tin cậy.
3. **Tác vụ do giảng viên thiết kế, với quy ước ẩn chỉ lộ qua phản hồi của bot.**
   - Thiết kế này làm lợi thế của skill tự sinh rất lớn: skill đơn giản là truyền lại thông tin bị giấu.
   - Kết quả "skill tự sinh có ích" vì vậy trái với SkillsBench (skill tự sinh trung bình không có lợi). Nó không nên được hiểu là skill tự sinh cải thiện *năng lực* của tác tử: check kỹ thuật đã đạt 18/18 ở baseline.
4. **Chỉ một mô hình** (`gpt-6-luna`), lại là mô hình mạnh.
   - Với mô hình yếu hơn, các check kỹ thuật (nhóm A–D) có thể thất bại. Khi đó skill quy trình và subagent `reviewer` có thể có giá trị khác.
   - Kết luận về đa tác tử chỉ đúng cho mô hình này và cho thiết kế 3 subagent của nhóm.
5. **Curator có bậc tự do của người làm thí nghiệm.**
   - Prompt bị sửa sau lần chạy 1, chỉ 2 skill được giữ, và họ data không có skill do bộ lọc chống rò rỉ.
   - Một nhóm khác với cùng quy trình có thể có bộ skill khác hẳn. Hiệu ứng đo được là của *bộ skill này*, không phải của "curator" nói chung.
6. **Đo đạc:** `tool_calls`, `skills_read` và vết chỉ phản ánh luồng chính. Việc subagent làm bên trong không hiện ra, nên phân tích cơ chế ở điều kiện `subagents` chỉ dựa vào lời giao việc và báo cáo cuối của subagent.

## 10. Kết luận

- Trên 6 tác vụ, skill do curator tự sinh từ phản hồi của tác vụ học (`skills-auto`) nâng điểm trung bình tác vụ đánh giá từ 0,60 lên 0,79, với chi phí thêm khoảng 41% token.
- Toàn bộ mức tăng đến từ các quy ước Acme đã thấy ở tác vụ học (6/12 check quy ước so với 0/12). Check kỹ thuật vẫn 18/18 ở mọi điều kiện.
- Skill không giúp được quy ước mới (0/3) và còn gây chuyển giao âm khi bị đọc sai miền (skill log được áp vào tác vụ data).
- Đa tác tử (`subagents`) không cải thiện điểm (0,60 bằng 0,60) nhưng tốn khoảng 3,75 lần token, vì lỗi ở đây là thiếu thông tin chứ không phải thiếu năng lực.
- Đề xuất tiếp theo: buộc curator viết `description` có phạm vi hẹp, và thêm một skill quy trình "hỏi hoặc tìm quy ước của tổ chức khi đề nhắc đến chúng". Ngoài ra nên thử lại với một mô hình yếu hơn, nơi các check kỹ thuật chưa đạt trần, để tách tác dụng của skill quy trình khỏi tác dụng truyền quy ước.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `python3 -m venv .venv && source .venv/bin/activate && pip install -e .`; `cp REPORT_TEMPLATE.md report/REPORT.md`; `pytest tests/test_01_provided.py` (12 passed); kiểm tra mô hình bằng `make_model().invoke('Reply with OK')`; `python scripts/tour.py`.
  2. Cài đặt `subagents.py`, `agent.py`, `runner.py`; `pytest tests/test_02_agent.py tests/test_03_runner.py` (đạt).
  3. `python -m lab.runner --condition baseline --tasks data-learn` (lần đầu lỗi 400 với `gpt-5.6-luna`, rồi lỗi 400 với `temperature=0`; cả hai đã xóa. Sau khi đổi sang `gpt-6-luna`, `LAB_TEMPERATURE=1` thì chạy thành công).
  4. `python -m lab.runner --condition baseline --tasks code-learn logs-learn` (kèm chạy lại `data-learn`); `python -m lab.runner --condition subagents --tasks learn`.
  5. Cài đặt `curator.py`; `pytest tests/test_04_curator.py` (đạt); `python -m lab.curator` lần 1 (3 skill, đã xóa, lưu ở `report/deleted-skills/run1/`); sửa prompt; `python -m lab.curator` lần 2 (2 skill hợp lệ, 1 bị `validate_skill` từ chối).
  6. `python -m lab.runner --condition skills-auto --tasks learn`; `mv results/skills-auto results/skills-auto-dev`.
  7. `git commit -m "hypotheses"` (`c381226`); `git commit --allow-empty -m "freeze skills" && git tag freeze` (`4b3c13d`).
  8. `python -m lab.runner --condition baseline --tasks eval`; `python -m lab.runner --condition subagents --tasks eval`; `python -m lab.runner --condition skills-auto --tasks all`.
  9. `python scripts/verify_freeze.py` (OK); `python -m lab.compare > report/table.md`; `python scripts/check_breakdown.py`.
- Thử thách mở rộng: hướng **6e – lặp để đo nhiễu**. Chi tiết ở mục *Phụ lục A* bên dưới.
- Ghi chú khác:
  - Toàn bộ test (`pytest tests`) đạt 29/29.
  - `runner.py` dùng `agent.stream(..., stream_mode="values")` thay cho `invoke`, để vẫn giữ được vết và số đếm khi tác tử lỗi giữa chừng. Đây là mở rộng tùy chọn được gợi ý ở `03_runner.md`.
  - Mô hình trả nội dung dạng danh sách khối (gồm khối `reasoning` đã mã hóa), nên `trace.md` hiển thị nguyên các khối này. Không có khóa API trong vết.

## Phụ lục A. Thử thách mở rộng 6e: lặp để đo nhiễu

### A.1. Thiết kế

- **Câu hỏi:** các chênh lệch trong bảng ở mục 7 có vượt nhiễu giữa các lần chạy không?
- **Cách làm:** chạy lại mỗi điều kiện trên cả 3 tác vụ đánh giá thêm **2 lần**, sau khi đã đóng băng, với cùng bộ skill (`skills/auto/` tại tag `freeze`) và cùng mô hình (`gpt-6-luna`, `LAB_TEMPERATURE=1`, `recursion_limit=60`). Tổng cộng thêm 18 lần chạy.
  - Lần 1 là kết quả chính thức trong `results/`.
  - Lần 2 và 3 nằm ở thư mục riêng `results_6e/rep2/` và `results_6e/rep3/`, tách khỏi kết quả chính nên không ảnh hưởng `lab.compare` hay `verify_freeze.py`.
- **Lệnh chạy:**

  ```bash
  for rep in rep2 rep3; do for c in baseline subagents skills-auto; do
    python -m lab.runner --condition $c --tasks eval --results results_6e/$rep; done; done
  python extension/aggregate_6e.py > report/extension_6e.md
  ```

- **Script tổng hợp:** `extension/aggregate_6e.py`, viết mới, không sửa tệp có sẵn. Nó tính trung bình, độ lệch chuẩn và khoảng min–max của điểm và token, tách check `rule_` khỏi check kỹ thuật, và đếm số lần mỗi check thất bại.

### A.2. Số liệu

#### Điểm từng lần chạy (passed/total)

| Điều kiện | Tác vụ | rep1 | rep2 | rep3 | TB ± độ lệch chuẩn [min–max] |
|---|---|---|---|---|---|
| baseline | code-eval | 7/11 | 7/11 | 7/11 | 0.64 ± 0.00 [0.64–0.64] |
| baseline | data-eval | 5/9 | 5/9 | 5/9 | 0.56 ± 0.00 [0.56–0.56] |
| baseline | logs-eval | 6/10 | 6/10 | 6/10 | 0.60 ± 0.00 [0.60–0.60] |
| subagents | code-eval | 7/11 | 7/11 | 7/11 | 0.64 ± 0.00 [0.64–0.64] |
| subagents | data-eval | 5/9 | 5/9 | 5/9 | 0.56 ± 0.00 [0.56–0.56] |
| subagents | logs-eval | 6/10 | 6/10 | 6/10 | 0.60 ± 0.00 [0.60–0.60] |
| skills-auto | code-eval | 10/11 | 10/11 | 10/11 | 0.91 ± 0.00 [0.91–0.91] |
| skills-auto | data-eval | 5/9 | 5/9 | 5/9 | 0.56 ± 0.00 [0.56–0.56] |
| skills-auto | logs-eval | 9/10 | 9/10 | 9/10 | 0.90 ± 0.00 [0.90–0.90] |

#### Tổng hợp theo điều kiện (mỗi lần lặp = trung bình 3 tác vụ đánh giá)

| Điều kiện | Điểm TB mỗi lần lặp | Điểm TB ± SD [min–max] | Check `rule_` đạt mỗi lần lặp | Check kỹ thuật đạt mỗi lần lặp | Token TB/lần chạy ± SD [min–max] | Lần chạy đọc skill |
|---|---|---|---|---|---|---|
| baseline | 0.60, 0.60, 0.60 | 0.60 ± 0.00 [0.60–0.60] | 0/12, 0/12, 0/12 | 18/18, 18/18, 18/18 | 41,935 ± 19,373 [18,220–75,768] | 0/9 |
| subagents | 0.60, 0.60, 0.60 | 0.60 ± 0.00 [0.60–0.60] | 0/12, 0/12, 0/12 | 18/18, 18/18, 18/18 | 167,937 ± 90,593 [85,454–357,668] | 0/9 |
| skills-auto | 0.79, 0.79, 0.79 | 0.79 ± 0.00 [0.79–0.79] | 6/12, 6/12, 6/12 | 18/18, 18/18, 18/18 | 58,748 ± 31,855 [25,194–104,727] | 9/9 |

#### Check thất bại theo số lần (trên tổng số lần lặp)

| Điều kiện | Tác vụ | Check thất bại (số lần) |
|---|---|---|
| baseline | code-eval | `rule_changelog` (3), `rule_regression_tests` (3), `rule_type_hints` (3), `rule_version_bump` (3) |
| baseline | data-eval | `rule_clean_csv` (3), `rule_meta_block` (3), `rule_money_in_cents` (3), `rule_sorted_keys_format` (3) |
| baseline | logs-eval | `rule_schema_header` (3), `rule_service_names` (3), `rule_sorted_errors` (3), `rule_source_line` (3) |
| subagents | code-eval | `rule_changelog` (3), `rule_regression_tests` (3), `rule_type_hints` (3), `rule_version_bump` (3) |
| subagents | data-eval | `rule_clean_csv` (3), `rule_meta_block` (3), `rule_money_in_cents` (3), `rule_sorted_keys_format` (3) |
| subagents | logs-eval | `rule_schema_header` (3), `rule_service_names` (3), `rule_sorted_errors` (3), `rule_source_line` (3) |
| skills-auto | code-eval | `rule_version_bump` (3) |
| skills-auto | data-eval | `rule_clean_csv` (3), `rule_meta_block` (3), `rule_money_in_cents` (3), `rule_sorted_keys_format` (3) |
| skills-auto | logs-eval | `rule_source_line` (3) |

Lần chạy có `error`: không có.

Hệ số biến thiên của token (SD/TB) trên 9 lần chạy mỗi điều kiện: baseline khoảng 46%, subagents khoảng 54%, skills-auto khoảng 54%. Tỉ lệ token trung bình so với baseline:
- `subagents`: ×4,0 (167 937 so với 41 935);
- `skills-auto`: ×1,40 (58 748 so với 41 935).

Mọi lần chạy có `error = null` và `skills_modified = false`.

### A.3. So sánh với kết quả chính và phân tích cơ chế

- **Điểm hoàn toàn ổn định.** 27/27 cặp (điều kiện, tác vụ, lần lặp) cho đúng cùng điểm và cùng tập check thất bại. Điểm trung bình tác vụ đánh giá: baseline 0,60, subagents 0,60, skills-auto 0,79 ở cả 3 lần, độ lệch chuẩn 0.
  - Vì vậy mức chênh +0,19 của `skills-auto` (+6 check `rule_`) **vượt xa nhiễu**.
  - Mức chênh 0 giữa `subagents` và `baseline` là một kết quả "không khác biệt" thật, không phải do nhiễu che mất.
  - Lý do điểm ổn định đến vậy: mô hình đã đạt trần ở check kỹ thuật (18/18 mọi lần). Còn mỗi check quy ước gần như là biến nhị phân xác định: có thông tin (đọc skill) thì đạt, không có thì thất bại. Không có check nào nằm ở vùng "lúc đạt lúc không".
- **Token dao động mạnh.** Ví dụ:
  - baseline `data-eval`: 18 220 đến 35 239 token;
  - subagents `code-eval`: 226 802 đến 357 668 token, tùy số lần giao việc (4–5 lần gọi `task`) và số vòng sửa.

  Chênh lệch token giữa các điều kiện chỉ nên diễn giải khi lớn hơn nhiều so với khoảng dao động này. Mức ×4,0 của `subagents` thỏa điều kiện đó. Mức ×1,40 của `skills-auto` cũng thỏa, nhưng biên độ hẹp hơn.
- **Hành vi đọc skill lặp lại nhất quán** (từ `trace.md`):
  - `code-eval` luôn đọc `python-bugfix-handoff` và luôn đạt 3 quy ước code cũ.
  - `logs-eval` luôn đọc `log-triage-output` và luôn đạt 3 quy ước log cũ.
  - `data-eval` luôn đọc nhầm `log-triage-output`; ở lần 3 còn đọc thêm `python-bugfix-handoff`. Ở cả 3 lần, chuỗi `generated_by: "log-triage"` xuất hiện trong vết khi ghi `answer.json`; ở lần 1 và 2 thấy trực tiếp trong `write_file`.

  Như vậy chuyển giao âm ở họ data không phải sự cố ngẫu nhiên mà là hành vi có hệ thống, do `description` của skill log quá rộng.
- **Quy ước mới** (`rule_version_bump`, `rule_sorted_keys_format`, `rule_source_line`) thất bại 9/9 lần ở mọi điều kiện. Điều này xác nhận giới hạn chuyển giao của skill tự sinh (H3).
- **Ở điều kiện `subagents`**, `subagent_calls` thay đổi giữa các lần (code-eval 4/5/5, data-eval 3/3/4, logs-eval 2/2/3) nhưng điểm không đổi. Số lần giao việc chỉ ảnh hưởng đến chi phí, không ảnh hưởng kết quả.

### A.4. Hạn chế và bước tiếp theo

- **Hạn chế:**
  - Chỉ 3 lần lặp, chạy liền nhau trong cùng một ngày với cùng một phiên bản mô hình phía nhà cung cấp. Biến thiên giữa các ngày hoặc phiên bản mô hình chưa được đo.
  - Chỉ lặp phần *chạy tác vụ* với một bộ skill cố định, không lặp *curator*. Nhiễu lớn nhất có lẽ nằm ở curator: lần 1 và lần 2 cho bộ skill khác hẳn (mục 6), nên độ ổn định ở đây không có nghĩa là quy trình tự tiến hóa ổn định.
  - Độ lệch chuẩn bằng 0 có một phần do thiết kế tác vụ (check nhị phân, đạt trần kỹ thuật). Kết quả này không tổng quát cho tác vụ khó hơn.
- **Bước tiếp theo:**
  - Lặp cả curator (ví dụ 5 lần, mỗi lần một bộ skill, rồi đo trên tác vụ đánh giá) để ước lượng phương sai của toàn bộ quy trình tự tiến hóa.
  - Thử một mô hình yếu hơn, nơi check kỹ thuật không đạt trần, để thấy nhiễu ở mức điểm.
- **Chi phí của 6e:** 18 lần chạy, tổng 1 719 076 token, trong đó 1 086 365 token (63%) là của `subagents`.

