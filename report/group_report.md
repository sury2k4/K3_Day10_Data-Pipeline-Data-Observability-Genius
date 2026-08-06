# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | **K3** |
| Tên nhóm | Nhóm Data Observability K3 - Group 5 |
| Repository | `https://github.com/sury2k4/K3_Day10_Data-Pipeline-Data-Observability-Genius.git` |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | **Lý Minh Hải** | 2A202601503 | Pipeline Integrator (Lead / Điều phối) | `src/core/`, `src/pipelines/` (`phase1.py`, `corruption_flow.py`), `script/` |
| 2 | **Nguyễn Công Hùng** | 2A202601071 | Ingestion Owner (Nguồn dữ liệu thô) | `src/ingestion/crossref.py`, `data/raw/` (`crossref_response.json`, `crossref_records.json`) |
| 3 | **Nguyễn Hoàng Khôi** | 2A202601383 | Cleaning & Corruption Owner (Làm sạch & Giả lập lỗi) | `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, `data/clean/` (`papers_clean.csv`, `papers_clean_corrupted.csv`) |
| 4 | **Hoàng Quang Minh** | 2A202601301 | RAG & Agent Owner (Vector Index & RAG Agent) | `src/retrieval/` (`embeddings.py`, `index.py`, `agent.py`, `llm.py`, `qa.py`), `data/embeddings/` |
| 5 | **Nguyễn Tiến Dũng** | 2A202601707 | Evaluation & Observability (Đánh giá & Giám sát) | `src/evaluation/` (`testset.py`, `metrics.py`), `src/observability/` (`quality.py`, `reporting.py`), `data/eval/`, `data/quality/`, `data/reports/` |

---

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**
Nhóm K3 đã xây dựng hoàn chỉnh hệ thống Data Pipeline end-to-end tích hợp Data Observability và RAG Evaluation. 
1. **Baseline Pipeline:** Đã thu thập 24 bản ghi học thuật từ Crossref API, làm sạch dữ liệu và tạo cột `text_for_embedding`, xây dựng Vector Collection trên ChromaDB với embedding 384 chiều, sinh bộ test set gồm 24 câu hỏi kiểm thử và thu được điểm Baseline ấn tượng: Retrieval Hit Rate 100.00%, Token F1 85.00%, Judge Accuracy 100.00%.
2. **Corruption Simulation:** Nhóm đã giả lập thành công kịch bản làm hỏng dữ liệu có kiểm soát (xóa bản ghi mới nhất, blank summary, chèn nhiễu, làm stale ngày xuất bản và nhân bản ID). Kết quả cho thấy hiệu năng RAG bị giảm sút nghiêm trọng: Retrieval Hit Rate giảm từ 100.00% xuống 33.33%, Token F1 giảm xuống 28.50%.
3. **Automated Repair:** Hệ thống tự động re-ingest từ nguồn raw gốc đáng tin cậy và khôi phục hoàn toàn chỉ số Retrieval Hit Rate về 100.00% và Data Quality status đạt PASS.

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (Works Endpoint)
    └─► Raw API Response & Raw Records JSON (data/raw/)
         └─► Cleaning & Data Modeling (text_for_embedding, age_days, dedupe) (data/clean/)
              ├─► Vector Store & Embeddings Index (ChromaDB) (data/embeddings/)
              ├─► Test Set Generation (test_set.json) (data/eval/)
              ├─► Baseline Evaluation & Metrics Scoring (data/results/)
              └─► Data Quality & Freshness Monitoring (data/quality/)
                   └─► Phase 1 Baseline Report (data/reports/phase1_report.md)
                        └─► Controlled Data Corruption Simulation (corruption_log.json)
                             └─► Corrupted Re-indexing & Re-evaluation
                                  └─► Automated Data Repair from Raw Source Snapshot
                                       └─► Comparison Report (data/reports/corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| **Ingestion** | Crossref API (`https://api.crossref.org/works`) | Fetch REST API, retry 429/503, parse JSON payload thành `PaperRecord` | `data/raw/crossref_response.json`, `crossref_records.json` | Nguyễn Công Hùng |
| **Cleaning** | Raw `PaperRecord` list | Chuẩn hóa text, gộp authors/categories, tính `age_days`, tạo `text_for_embedding`, dedupe | `data/clean/papers_clean.csv`, `papers_clean.json` | Nguyễn Hoàng Khôi |
| **Embedding/Index** | Cleaned DataFrame | MiniLM 384-dim Embeddings & ChromaDB collection persistent index | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Hoàng Quang Minh |
| **Evaluation** | Cleaned DataFrame | Xây dựng bộ 24 test cases (summary, authors, date, categories), chấm Hit Rate, Token F1, LLM Judge | `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `baseline_answers.json` | Nguyễn Tiến Dũng |
| **Observability** | Cleaned DataFrame | Kiểm tra null, unique `paper_id`, độ dài summary, freshness `age_days <= 180` | `data/quality/baseline_quality.json`, `freshness_report.json` | Nguyễn Tiến Dũng |
| **Corruption/Repair** | Baseline Clean DataFrame | Corrupt data (drop latest, blank summary, noise, stale date, duplicate rows) & Re-ingest Repair | `data/results/corruption_log.json`, `papers_clean_corrupted.csv`, `papers_clean_repaired.csv` | Nguyễn Hoàng Khôi |
| **Orchestration** | Settings & Config | Điều phối toàn bộ luồng Phase 1 và Corruption/Repair Flow | `src/pipelines/phase1.py`, `corruption_flow.py`, `script/` | Lý Minh Hải |

---

## 4. Cách tái hiện kết quả

### Cấu hình môi trường

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384 dim) |
| Số lượng Crossref records | `24` |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180 days` |

### Lệnh cài đặt
```bash
uv sync
```
Hoặc dùng pip:
```bash
python -m pip install -e .
```

### Lệnh chạy
1. **Chạy Baseline Pipeline:**
   ```bash
   uv run python script/run_phase1.py
   ```
2. **Chạy Corruption & Repair Flow:**
   ```bash
   uv run python script/run_corruption_flow.py
   ```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | **Thành công 100%** | 2026-08-06 12:30 UTC | `data/reports/phase1_report.md`, `data/results/baseline_metrics.json` |
| Corruption flow | **Thành công 100%** | 2026-08-06 12:35 UTC | `data/reports/corruption_report.md`, `data/results/corrupted_metrics.json` |

---

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu
- **Source:** Crossref REST API Works Endpoint (`https://api.crossref.org/works`)
- **Query / Filter:** `query=agentic retrieval augmented generation large language model`, `filter=from-pub-date:2024-02-07,has-abstract:true`
- **Số record nhận được:** 24 bản ghi
- **Cơ chế retry:** HTTP backoff retry cho 429/503 với timeout 3s và fallback dataset an toàn.

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | String | Có | Mã định danh duy nhất từ DOI | Khử ký tự đặc biệt, lowercase, nếu rỗng gán `paper_unknown` |
| `title` | String | Có | Tiêu đề bài báo | Loại bỏ thẻ XML/JATS HTML, normalize whitespace |
| `summary` | String | Có | Tóm tắt (Abstract) | Loại bỏ HTML tags, normalize whitespace, giữ rỗng nếu không có |
| `authors_joined` | String | Có | Danh sách tác giả gộp | Gộp tên `given family`, nếu trống gán `Unknown Author` |
| `categories_joined` | String | Có | Danh sách chủ đề/danh mục | Gộp subject list, nếu trống gán `General` |
| `published` | String (YYYY-MM-DD) | Có | Ngày xuất bản | Parse format ISO, nếu sai gán mặc định `2024-01-01` |
| `age_days` | Integer | Có | Tuổi của bài báo tính theo ngày | `max(0, (run_date - pub_date).days)` |
| `text_for_embedding` | String | Có | Chuỗi gộp chuẩn bị cho Vector Embedding | Định dạng: `Title: ... \nSummary: ... \nAuthors: ... \nCategories: ...` |

---

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 24 câu hỏi |
| Các `question_type` | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID | Khai thác trực tiếp từ `paper_id` của bản ghi clean |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store / collection | ChromaDB Persistent Collections (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k` | 4 documents |
| LLM Judge | Gemini 2.5 Flash / Heuristic F1 Evaluator |
| Test set dùng chung | `data/eval/test_set.json` (cố định cho cả 3 trạng thái) |

---

## 7. Kết quả baseline, corrupted và repaired

### Baseline vs Corrupted vs Repaired Metrics

| Metric / Signal | Baseline | Corrupted | Repaired | Thay đổi do Corruption | Mức phục hồi sau Repair | Nhận xét |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `retrieval_hit_rate` | **100.00%** | **33.33%** | **100.00%** | **-66.67%** | **+66.67%** | Corruption làm mất thông tin tiêu đề/tóm tắt khiến Vector Search không tìm thấy context. Repair giúp phục hồi 100%. |
| `mean_token_f1` | **85.00%** | **28.50%** | **85.00%** | **-56.50%** | **+56.50%** | Dữ liệu bị rác làm giảm độ chính xác từ ngữ trong câu trả lời của Agent. |
| `judge_accuracy` | **100.00%** | **33.33%** | **100.00%** | **-66.67%** | **+66.67%** | LLM Judge đánh giá câu trả lời bị sai khi context bị hỏng. |
| `mean_judge_score` (1-5) | **4.50** | **2.10** | **4.50** | **-2.40** | **+2.40** | Điểm chất lượng câu trả lời bị giảm nghiêm trọng khi dữ liệu bị lỗi. |
| Quality Checks Pass/Fail | **PASSED** | **FAILED** | **PASSED** | **Fail 3 checks** | **Phục hồi PASS** | Lỗi blank summary, duplicate IDs và stale date làm trượt Quality Gate. |
| Freshness Status | **FRESH** | **STALE** | **FRESH** | **Trở thành Stale** | **Khôi phục Fresh** | Do đẩy ngày xuất bản về quá xa (2010). |

---

## 8. Data quality và freshness

### Quality checks breakdown (Baseline)

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| Non-empty dataset | Completeness | Total rows > 0 | **PASS (24 rows)** | `data/quality/baseline_quality.json` |
| No null paper_ids | Integrity | Null count == 0 | **PASS (0 null)** | `data/quality/baseline_quality.json` |
| Unique paper_ids | Uniqueness | Duplicate count == 0 | **PASS (0 duplicates)** | `data/quality/baseline_quality.json` |
| No null titles | Completeness | Null titles == 0 | **PASS (0 null)** | `data/quality/baseline_quality.json` |
| No blank summaries | Completeness | Summary chars > 0 | **PASS (0 blank)** | `data/quality/baseline_quality.json` |
| Freshness threshold | Timeliness | Stale rows (`age_days > 180`) == 0 | **PASS (0 stale)** | `data/quality/freshness_report.json` |

---

## 9. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi chạy trên môi trường Windows PowerShell, lệnh `python script/run_phase1.py` bị lỗi `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'` và lỗi nạp DLL `WinError 1114` từ PyTorch.
- **Nguyên nhân:** Môi trường Windows sử dụng bảng mã mặc định `cp1252` không hỗ trợ hiển thị ký tự Emoji trong hàm `print()`, đồng thời thư viện `torch` gặp xung đột DLL C++ khi load `c10.dll`.
- **Cách xử lý:** 
  1. Loại bỏ các ký tự Emoji ngoài dải ASCII trong chuỗi `print()` của `phase1.py` và `corruption_flow.py`, thay bằng các nhãn ASCII tiêu chuẩn như `[INFO]`, `[SUCCESS]`.
  2. Bổ sung nguồn PyTorch CPU vào `pyproject.toml` và tối ưu hóa module `embeddings.py` với cơ chế Feature Hashing 384 chiều dự phòng an toàn.
- **Cách xác minh:** Chạy lại `uv run python script/run_phase1.py` thành công 100% không còn lỗi mã hóa hay lỗi DLL.

---

## 10. Bảng cam kết nộp bài

- [x] Thông tin nhóm K3 và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
