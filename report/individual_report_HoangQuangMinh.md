# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | **Hoàng Quang Minh** |
| MSSV | **2A202601301** |
| Khóa/Lớp | **K3** |
| Tên nhóm | Nhóm Data Observability K3 - Group 5 |
| Vai trò chính | **RAG & Agent Owner (Vector Index & RAG Agent)** |
| Repository | `https://github.com/sury2k4/K3_Day10_Data-Pipeline-Data-Observability-Genius.git` |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| MiniLM Embedding Provider | `src/retrieval/embeddings.py` | List text strings | Embeddings matrix (dim=384) | Hoàn thành |
| Local ChromaDB Index | `src/retrieval/index.py` -> `LocalEmbeddingIndex` | Clean DataFrame | Chroma Collections (`papers-baseline`, `papers-corrupted`, `papers-repaired`), Embeddings JSON Manifest | Hoàn thành |
| Multi-provider LLM Factory | `src/retrieval/llm.py` -> `build_llm` | `Settings` | LangChain ChatModel object | Hoàn thành |
| RAG Agent & Tools | `src/retrieval/agent.py` -> `build_agent` | Index & LLM Model | LangChain Agent với `semantic_search_papers` và `lookup_paper` tools | Hoàn thành |
| Question Answering Engine | `src/retrieval/qa.py` -> `answer_question` | Question string & Index | `AnswerResult` với retrieved doc IDs và context | Hoàn thành |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Quản lý 3 Vector Collections riêng biệt | `src/retrieval/index.py` | Collections: `papers-baseline`, `papers-corrupted`, `papers-repaired` | `ls -la data/chroma/` |
| Tích hợp RAG Agent & Q&A Engine | `src/retrieval/agent.py`, `qa.py` | Trả lời câu hỏi và trích xuất đúng context | `python -c "from retrieval.qa import answer_question; print(answer_question)..."` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. Xây dựng không gian Vector Embeddings 384 chiều cho dữ liệu bài báo học thuật.
2. Thiết lập cơ sở dữ liệu Vector (ChromaDB) để thực hiện tìm kiếm ngữ nghĩa (Semantic Search) theo khoảng cách Cosine Similarity.
3. Cung cấp API Exact Lookup theo `paper_id` hoặc tiêu đề bài báo.
4. Tích hợp RAG Agent sử dụng LangChain Tools để trả lời câu hỏi thực tế dựa trên Corpus.

### Cách triển khai
- **Class `LocalEmbeddingIndex`:**
  - Định nghĩa metadata chuẩn cho mỗi document gồm: `paper_id`, `title`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`.
  - Khởi tạo `chromadb.PersistentClient(path=data/chroma)` và tạo collection với khoảng cách Cosine: `metadata={"hnsw:space": "cosine"}`.
  - Cung cấp phương thức `search(query, top_k)` thực hiện query embedding và trả về danh sách `SearchResult` kèm độ tương đồng.
  - Cung cấp phương thức `lookup(paper_id_or_title)` thực hiện tra cứu O(1) từ HashMap.
- **RAG Agent (`agent.py`):**
  - Đăng ký 2 công cụ chính: `@tool semantic_search_papers` và `@tool lookup_paper`.
  - Thiết lập System Prompt yêu cầu Agent ưu tiên dùng công cụ truy vấn dữ liệu trước khi trả lời.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn chiến lược quản lý Vector Collections giữa 3 trạng thái Baseline, Corrupted và Repaired.
- **Các phương án đã cân nhắc:**
  1. Dùng chung 1 collection duy nhất và ghi đè dữ liệu ở mỗi bước.
  2. Tạo 3 collection hoàn toàn độc lập (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
- **Phương án đã chọn:** Phương án 2 (Tách biệt 3 collection).
- **Lý do:** Tránh nguy cơ nhiễm bẩn dữ liệu (data contamination), đảm bảo tính minh bạch khi đối chiếu kết quả Retrieval Hit Rate giữa 3 trạng thái.

---

## 6. Phụ trách Lớp K3 & Cam kết

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Hoàng Quang Minh  
**Lớp:** K3  
**Ngày xác nhận:** 2026-08-06
