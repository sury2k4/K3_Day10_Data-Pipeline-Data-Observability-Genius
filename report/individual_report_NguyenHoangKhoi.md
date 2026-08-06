# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | **Nguyễn Hoàng Khôi** |
| MSSV | **2A202601383** |
| Khóa/Lớp | **K3** |
| Tên nhóm | Nhóm Data Observability K3 - Group 5 |
| Vai trò chính | **Cleaning & Corruption Owner (Làm sạch & Giả lập lỗi)** |
| Repository | `https://github.com/sury2k4/K3_Day10_Data-Pipeline-Data-Observability-Genius.git` |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Cleaning & Data Modeling | `src/ingestion/cleaning.py` -> `build_clean_dataframe` | List `PaperRecord` | Clean DataFrame, `papers_clean.csv`, `papers_clean.json` | Hoàn thành |
| Data Corruption Simulator | `src/ingestion/corruption.py` -> `corrupt_clean_dataframe` | Clean DataFrame | Corrupted DataFrame, `corruption_log.json`, `papers_clean_corrupted.csv` | Hoàn thành |
| Automated Data Repair | `src/ingestion/cleaning.py` | Raw Records Snapshot | Repaired DataFrame, `papers_clean_repaired.csv` | Hoàn thành |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Chuẩn hóa dữ liệu & Tạo `text_for_embedding` | `src/ingestion/cleaning.py` | `data/clean/papers_clean.csv` (99.7 KB, 24 rows) | `ls -la data/clean/papers_clean.csv` |
| Giả lập 5 dạng lỗi dữ liệu | `src/ingestion/corruption.py` | `data/results/corruption_log.json`, `papers_clean_corrupted.csv` | `cat data/results/corruption_log.json` |
| Khôi phục dữ liệu sạch từ Raw Source | `src/pipelines/corruption_flow.py` | `data/clean/papers_clean_repaired.csv` | `ls -la data/clean/papers_clean_repaired.csv` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. Xử lý làm sạch dữ liệu thô: Khử trùng lặp `paper_id`, chuẩn hóa khoảng trắng, tính số ngày từ khi xuất bản (`age_days`) và gộp các trường thành chuỗi `text_for_embedding` phục vụ cho Vector Search.
2. Giả lập kịch bản làm hỏng dữ liệu (Corruption) có kiểm soát để kiểm thử sức chịu đựng của RAG Agent.
3. Thực hiện quy trình khôi phục (Repair) dữ liệu chuẩn xác từ nguồn thô gốc.

### Cách triển khai
- **Hàm `build_clean_dataframe`:**
  - Chuẩn hóa tác giả (`authors_joined`) và danh mục (`categories_joined`).
  - Parse ngày xuất bản, tính `age_days = max(0, (run_date - pub_date).days)`.
  - Tạo cột `text_for_embedding` có định dạng: `Title: ... \nSummary: ... \nAuthors: ... \nCategories: ...`.
  - Loại bỏ các dòng trùng lặp `paper_id` bằng `.drop_duplicates(subset=['paper_id'])`.
- **Hàm `corrupt_clean_dataframe`:**
  - Xóa 2 bản ghi mới nhất (simulating dropped records).
  - Làm rỗng summary của bản ghi đầu tiên (blank summary).
  - Cắt ngắn tiêu đề và chèn nhiễu text `"NOISE RANDOM BAD DATA"` (noise injection & title truncation).
  - Đẩy ngày xuất bản về năm 2010 (`age_days = 5000`) để làm dữ liệu bị Stale.
  - Nhân bản dòng dữ liệu để tạo ô nhiễm Duplicate IDs.
  - Ghi nhật ký chi tiết vào `corruption_log.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Định dạng thông tin cho cột `text_for_embedding`.
- **Các phương án đã cân nhắc:**
  1. Chỉ sử dụng tóm tắt (`summary`).
  2. Gộp Tiêu đề + Tóm tắt + Tác giả + Danh mục chủ đề.
- **Phương án đã chọn:** Phương án 2.
- **Lý do:** Giúp RAG Vector Index vừa có thể tìm kiếm theo ngữ nghĩa tóm tắt, vừa hỗ trợ tìm kiếm/đối chiếu chính xác theo tiêu đề, tên tác giả hoặc chủ đề học thuật.

---

## 6. Phụ trách Lớp K3 & Cam kết

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Nguyễn Hoàng Khôi  
**Lớp:** K3  
**Ngày xác nhận:** 2026-08-06
