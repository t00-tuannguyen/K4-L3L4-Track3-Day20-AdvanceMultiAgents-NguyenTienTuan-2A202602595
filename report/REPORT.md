# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Tiến Tuân | 2A202602595 | Toàn bộ |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `gpt-6-luna` qua cổng tương thích OpenAI (`AZURE_OPENAI_DEPLOYMENT_MODEL`; `make_model()` trả về `ChatOpenAI`); `LAB_TEMPERATURE=1` (mô hình chỉ chấp nhận giá trị mặc định 1, nên đầu ra có tính ngẫu nhiên giữa các lần chạy); `recursion_limit=60` (mặc định). Ghi chú: thử `gpt-5.6-luna` trước đó thất bại vì cổng không cho gọi công cụ qua `/v1/chat/completions` khi bật suy luận (lỗi 400, lỗi hạ tầng, đã xóa kết quả, không tính vào số liệu).
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: deepagents 0.7.21 (langchain 1.4.3, langchain-core 1.6.6), macOS 26.6.2, Python 3.12.14, chạy trực tiếp (venv), không dùng Docker.
- Số lần chạy tác vụ đã dùng / ngân sách:
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

> Dự đoán điều kiện nào đạt điểm cao nhất trên **tác vụ đánh giá** và vì sao. Nêu căn cứ từ phân loại lỗi (mục 4) và từ tài liệu tham khảo. Điền cả ba dòng; `verify_freeze.py` kiểm tra điều này.

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

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
