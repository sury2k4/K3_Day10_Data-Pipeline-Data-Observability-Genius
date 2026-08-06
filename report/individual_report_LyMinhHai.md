# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | **Lý Minh Hải** |
| MSSV | **2A202601503** |
| Khóa/Lớp | **K3** |
| Tên nhóm | Nhóm Data Observability K3 - Group 5 |
| Vai trò chính | **Pipeline Integrator (Lead / Điều phối)** |
| Repository | `https://github.com/sury2k4/K3_Day10_Data-Pipeline-Data-Observability-Genius.git` |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Core Settings & Environment | `src/core/config.py` | Variables từ `.env` | Class `Settings`, `Paths` | Hoàn thành |
| Baseline Pipeline Orchestration | `src/pipelines/phase1.py` | Modules Ingest, Clean, Index, Eval, Observe | End-to-end Baseline Flow & Reports | Hoàn thành |
| Corruption & Repair Flow Orchestration | `src/pipelines/corruption_flow.py` | Baseline Clean Data, Raw Records Snapshot | End-to-end Corruption/Repair Comparison Flow | Hoàn thành |
| Entrypoint Scripts | `script/run_phase1.py`, `script/run_corruption_flow.py` | Execution trigger | Terminal logs & Output Artifacts | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính
- Hỗ trợ Nguyễn Công Hùng (Ingestion): Xử lý cơ chế retry/backoff và fallback payload cho Crossref API.
- Hỗ trợ Hoàng Quang Minh (RAG): Khắc phục lỗi PyTorch C++ DLL `WinError 1114` trên môi trường Windows bằng Feature Hashing 384 chiều dự phòng.

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Dựng khung thiết lập môi trường & contract đường dẫn | `src/core/config.py` | Object `Settings` & `Paths` đồng bộ | `python -c "from core.config import load_settings; print(load_settings())"` |
| Tích hợp Baseline Pipeline | `src/pipelines/phase1.py` | Baseline Dataset, Chroma Index, Metrics, Phase 1 Report | `uv run python script/run_phase1.py` |
| Tích hợp Corruption & Repair Pipeline | `src/pipelines/corruption_flow.py` | Corrupted/Repaired Dataset, Comparison Report | `uv run python script/run_corruption_flow.py` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Ghép nối các module độc lập của 4 thành viên thành một dòng chảy dữ liệu tự động, nhất quán, có khả năng xử lý lỗi môi trường (Windows UnicodeEncodeError, PyTorch DLL crash) và tái lập 100% kết quả.

### Cách triển khai
- Sử dụng `load_settings()` làm nơi tập trung duy nhất khai báo cấu hình đường dẫn và tham số (`top_k`, `freshness_threshold_days`, `max_results`).
- Trong `phase1.py`: Gọi tuần tự `fetch_source_records` ➔ `build_clean_dataframe` ➔ `LocalEmbeddingIndex.build` ➔ `build_test_set` ➔ `evaluate_pipeline` ➔ `run_data_quality_checks` ➔ `generate_phase1_report`.
- Trong `corruption_flow.py`: Đọc clean baseline ➔ `corrupt_clean_dataframe` ➔ re-evaluate ➔ `load_raw_records` ➔ rebuild clean dataset ➔ re-evaluate ➔ `generate_corruption_report`.

### Cách xác minh
```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```
- **Kết quả mong đợi:** Toàn bộ dữ liệu thô, dữ liệu sạch, vector store index, kết quả đánh giá JSON và 2 báo cáo Markdown được ghi đầy đủ vào `data/`.
- **Kết quả thực tế:** Chạy thành công 100%, không còn lỗi encoding hay lộ API key.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương án quản lý đường dẫn và cấu hình trong toàn bộ dự án.
- **Các phương án đã cân nhắc:**
  1. Mỗi module tự hard-code đường dẫn tương đối hoặc tuyệt đối.
  2. Tạo Dataclass `Settings` và `Paths` trung tâm kế thừa từ `core/config.py`.
- **Phương án đã chọn:** Phương án 2 (Centralized `Settings` Dataclass).
- **Lý do:** Đảm bảo tính nhất quán tuyệt đối giữa các module của 5 thành viên, dễ dàng thay đổi đường dẫn lưu trữ hoặc threshold mà không cần sửa code ở từng file riêng lẻ.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Khi chạy trên Windows PowerShell, script báo lỗi `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'` và lỗi nạp DLL `WinError 1114` từ PyTorch.
- **Nguyên nhân:** PowerShell Windows mặc định dùng bảng mã `cp1252` không thể in ký tự Emoji, và PyTorch `.venv` bị thiếu phụ thuộc VC++ Runtime DLL trên Windows.
- **Cách xử lý:** Thay thế ký tự Emoji bằng các thẻ nhãn ASCII như `[INFO]`, `[SUCCESS]`, bổ sung cấu hình `pytorch-cpu` trong `pyproject.toml` và viết cơ chế embedding dự phòng 384 chiều trong `embeddings.py`.
- **Bài học:** Luôn kiểm tra khả năng tương thích mã hóa Unicode/ASCII và xung đột C++ DLL trên nhiều hệ điều hành khi viết pipeline.

---

## 7. Phân tích kết quả tổng hợp

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | :---: | :---: | :---: | --- |
| `retrieval_hit_rate` | **100.00%** | **33.33%** | **100.00%** | Corruption làm mất context dẫn đến retrieval sụt giảm nghiêm trọng; Repair giúp phục hồi 100%. |
| `mean_token_f1` | **85.00%** | **28.50%** | **85.00%** | Token F1 sụt giảm theo do Agent trả lời thiếu chính xác khi nhận context hỏng. |
| `judge_accuracy` | **100.00%** | **33.33%** | **100.00%** | Khớp hoàn toàn với xu hướng của Retrieval Hit Rate. |
| Quality checks | **PASSED** | **FAILED** | **PASSED** | Quality Gate phát hiện chính xác các lỗi blank summary, duplicate IDs và stale date. |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Stale status xuất hiện khi ngày xuất bản bị cố tình lùi về quá xa (2010). |

---

## 8. Phụ trách Lớp K3 & Cam kết

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Lý Minh Hải  
**Lớp:** K3  
**Ngày xác nhận:** 2026-08-06
