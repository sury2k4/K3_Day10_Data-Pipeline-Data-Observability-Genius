# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | **Nguyễn Tiến Dũng** |
| MSSV | **2A202601707** |
| Khóa/Lớp | **K3** |
| Tên nhóm | Nhóm Data Observability K3 - Group 5 |
| Vai trò chính | **Evaluation & Observability (Đánh giá & Giám sát)** |
| Repository | `https://github.com/sury2k4/K3_Day10_Data-Pipeline-Data-Observability-Genius.git` |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Test Set Generator | `src/evaluation/testset.py` -> `build_test_set` | Clean DataFrame | `data/eval/test_set.json` (24 test cases) | Hoàn thành |
| Metrics Evaluator | `src/evaluation/metrics.py` -> `evaluate_pipeline` | Test Set & Vector Index | `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Hoàn thành |
| Data Quality Gate | `src/observability/quality.py` -> `run_data_quality_checks` | DataFrame & Settings | `baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json` | Hoàn thành |
| Freshness Monitor | `src/observability/quality.py` -> `build_freshness_report` | DataFrame & Threshold | `freshness_report.json` | Hoàn thành |
| Markdown Report Generator | `src/observability/reporting.py` | Metrics & Quality JSON payloads | `phase1_report.md`, `corruption_report.md` | Hoàn thành |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xây dựng bộ 24 câu hỏi đánh giá cố định | `src/evaluation/testset.py` | `data/eval/test_set.json` | `cat data/eval/test_set.json` |
| Chấm điểm RAG Pipeline qua 3 trạng thái | `src/evaluation/metrics.py` | Hit Rate: Baseline 100% ➔ Corrupted 33.3% ➔ Repaired 100% | `cat data/results/baseline_metrics.json` |
| Giám sát Quality Gates & Freshness Status | `src/observability/quality.py` | Status: Baseline PASS ➔ Corrupted FAIL ➔ Repaired PASS | `cat data/quality/baseline_quality.json` |
| Báo cáo so sánh Markdown tự động | `src/observability/reporting.py` | `data/reports/phase1_report.md`, `corruption_report.md` | `cat data/reports/corruption_report.md` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. Đảm bảo tính nhất quán của quy trình đánh giá (Evaluation) bằng cách cố định 1 bộ `test_set.json` cho cả 3 trạng thái.
2. Tính toán chính xác các chỉ số: Retrieval Hit Rate (xác định xem `ground_truth_doc_ids` có nằm trong top-k kết quả tìm kiếm không), Token F1 score giữa câu trả lời và ground truth, và LLM Judge accuracy.
3. Thiết lập các quy tắc Data Quality Checks (Nulls, Duplicates, Length, Completeness) và Freshness Status.

### Cách triển khai
- **Hàm `build_test_set`:** Chọn ngẫu nhiên các bài báo đại diện từ clean dataframe và sinh các loại câu hỏi đa dạng (`summary`, `authors`, `date`, `categories`).
- **Hàm `evaluate_pipeline`:**
  - Với mỗi câu hỏi, gọi Q&A Engine lấy kết quả câu trả lời và danh sách `retrieved_doc_ids`.
  - Tính `retrieval_hit = any(doc_id in ground_truth_doc_ids for doc_id in retrieved_doc_ids)`.
  - Chấm Token F1 score bằng thuật toán tính Overlapping Precision & Recall.
  - Sử dụng LLM Judge hoặc Heuristic Judge để chấm điểm độ đúng đắn (Accuracy & Score 1-5).
- **Hàm `run_data_quality_checks`:** Kiểm tra 6 chỉ số chất lượng: `non_empty_dataset`, `no_null_paper_ids`, `unique_paper_ids`, `no_null_titles`, `no_blank_summaries`, `freshness_threshold`.

---

## 5. Phân tích số liệu và chứng minh nhân quả

| Trạng thái | Retrieval Hit Rate | Mean Token F1 | Judge Accuracy | Quality Status | Freshness Status |
| --- | :---: | :---: | :---: | :---: | :---: |
| **Baseline** | **100.00%** | **85.00%** | **100.00%** | **PASSED** | **FRESH** |
| **Corrupted** | **33.33%** | **28.50%** | **33.33%** | **FAILED** | **STALE** |
| **Repaired** | **100.00%** | **85.00%** | **100.00%** | **PASSED** | **FRESH** |

- **Kết luận 1 (Tác hại của dữ liệu xấu):** Việc giả lập lỗi làm rỗng tóm tắt và làm nhiễu tiêu đề làm giảm trực tiếp Retrieval Hit Rate từ **100% xuống 33.33%**, đồng thời kéo Token F1 giảm từ **85% xuống 28.50%**.
- **Kết luận 2 (Khả năng phục hồi của Data Repair):** Khi thực hiện Re-ingest từ nguồn raw thô chuẩn xác, các chỉ số Retrieval Hit Rate và Quality Gate được khôi phục **100% về mức Baseline ban đầu**.

---

## 6. Phụ trách Lớp K3 & Cam kết

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Nguyễn Tiến Dũng  
**Lớp:** K3  
**Ngày xác nhận:** 2026-08-06
