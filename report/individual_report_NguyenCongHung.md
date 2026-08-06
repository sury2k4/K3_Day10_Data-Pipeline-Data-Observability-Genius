# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | **Nguyễn Công Hùng** |
| MSSV | **2A202601071** |
| Khóa/Lớp | **K3** |
| Tên nhóm | Nhóm Data Observability K3 - Group 5 |
| Vai trò chính | **Ingestion Owner (Nguồn dữ liệu thô)** |
| Repository | `https://github.com/sury2k4/K3_Day10_Data-Pipeline-Data-Observability-Genius.git` |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Crossref Payload Parser | `src/ingestion/crossref.py` -> `parse_crossref_payload` | JSON payload từ API | List `PaperRecord` dataclasses | Hoàn thành |
| Source Record Fetcher | `src/ingestion/crossref.py` -> `fetch_source_records` | API query, filter, max_results | `raw_api_response.json`, `raw_records.json` | Hoàn thành |
| Raw Record Loader | `src/ingestion/crossref.py` -> `load_raw_records` | Path tới file `raw_records.json` | List `PaperRecord` | Hoàn thành |
| Raw Artifact Storage | `data/raw/` | Direct API response & records | Raw JSON snapshots | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính
- Hỗ trợ Nguyễn Hoàng Khôi (Cleaning): Cung cấp schema `PaperRecord` chuẩn hóa và truy vết các trường dữ liệu bị thiếu từ nguồn thô.

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Thu thập 24 bản ghi từ Crossref API | `src/ingestion/crossref.py` | `data/raw/crossref_response.json` (245 KB) | `ls -la data/raw/crossref_response.json` |
| Parse và lưu trữ `PaperRecord` | `src/ingestion/crossref.py` | `data/raw/crossref_records.json` (59.7 KB) | `ls -la data/raw/crossref_records.json` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Kết nối tới Crossref REST API public endpoint (`https://api.crossref.org/works`), xử lý việc trích xuất thông tin bài báo (DOI, tiêu đề, abstract, tác giả, ngày tháng, danh mục), xử lý lỗi mạng/rate limit và đảm bảo định danh `paper_id` ổn định.

### Cách triển khai
- Viết hàm `parse_crossref_payload`: Duyệt qua mảng `items`, bóc tách DOI làm `paper_id` duy nhất (loại bỏ ký tự đặc biệt, chuyển về chữ thường).
- Loại bỏ các thẻ HTML/JATS XML (như `<jats:p>`) trong tóm tắt bằng Regex `re.sub(r"<[^>]+>", "", summary)`.
- Xử lý mảng `author` để tạo danh sách tác giả `given family` đầy đủ.
- Viết cơ chế retry với HTTP backoff và bổ sung hàm `_fallback_crossref_payload` phòng trường hợp API bị chập chờn.

### Cách xác minh
```bash
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); recs=fetch_source_records(s); print(len(recs))"
```
- **Kết quả mong đợi:** Lấy đủ 24 bản ghi `PaperRecord`, file JSON được ghi vào `data/raw/`.
- **Kết quả thực tế:** Trích xuất 100% chính xác 24 bản ghi thô.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương án sinh `paper_id` cho từng bản ghi học thuật.
- **Các phương án đã cân nhắc:**
  1. Dùng số thứ tự tăng dần (`paper_1`, `paper_2`).
  2. Khai thác trực tiếp mã DOI của bài báo và làm sạch (`10.1145/3639476.3639735` ➔ `10_1145_3639476_3639735`).
- **Phương án đã chọn:** Phương án 2 (Dựa trên DOI).
- **Lý do:** DOI là mã định danh học thuật duy nhất trên toàn cầu, giúp duy trì tính ổn định (idempotency) của dữ liệu xuyên suốt qua các giai đoạn clean, index và repair.

---

## 6. Phụ trách Lớp K3 & Cam kết

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Nguyễn Công Hùng  
**Lớp:** K3  
**Ngày xác nhận:** 2026-08-06
