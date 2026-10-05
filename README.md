# ☁️ Blogger Gemini AI Auto-Poster Cloud (GitHub Actions 24/7)

Hệ thống tự động hóa viết bài chuẩn SEO và đăng lên **Blogger (Blogger.com)** hoàn toàn tự động trên nền tảng đám mây **GitHub Actions**. 

> ⚡ **Ưu điểm vượt trội**:
> - **100% MIỄN PHÍ trọn đời** (Sử dụng 2.000 phút/tháng miễn phí từ GitHub).
> - **Không cần mở máy tính**: Máy tính tắt hoàn toàn, bạn đi ngủ hay đi du lịch thì đúng giờ hẹn hệ thống trên mây vẫn tự động thức dậy, viết bài và đăng lên Blogger.
> - **Chuẩn SEO & CRO LuViet**: Bài viết có Heading `<h2>`, `<h3>`, Bảng so sánh trực quan, FAQ Schema và nút kêu gọi hành động Zalo OA & Fanpage LuViet.
> - **Tự động lưu lịch sử**: Tránh trùng lặp đề tài, tự động chuyển sang bài tiếp theo mỗi ngày.

---

## 📁 Cấu trúc thư mục

```text
blogger-auto-cloud/
├── .github/workflows/
│   └── auto_post.yml         # File cấu hình lịch chạy tự động trên GitHub
├── main.py                   # Script chính: Gọi Gemini AI & Đăng lên Blogger API
├── get_refresh_token.py      # Script hỗ trợ lấy Refresh Token trong 30 giây
├── topics.txt                # Danh sách các đề tài cần đăng (mỗi dòng 1 bài)
├── posted_history.json       # Lịch sử lưu các bài đã đăng thành công
├── requirements.txt          # Thư viện Python cần thiết
└── README.md                 # Hướng dẫn chi tiết này
```

---

## 🛠️ Hướng dẫn cài đặt trọn gói (Chỉ mất 5 - 10 phút)

### Bước 1: Tạo kho lưu trữ (Repository) trên GitHub
1. Truy cập: [GitHub.com](https://github.com) và đăng nhập tài khoản của bạn.
2. Bấm nút **New** (Tạo repository mới):
   - Đặt tên: `blogger-auto-cloud`
   - Chọn chế độ: **Private** (Riêng tư - để bảo mật danh sách bài và cấu hình).
3. Tải toàn bộ các file trong thư mục này lên repository của bạn:
   ```bash
   git init
   git add .
   git commit -m "Khởi tạo hệ thống Blogger Cloud Bot"
   git branch -M main
   git remote add origin https://github.com/<tai-khoan-cua-ban>/blogger-auto-cloud.git
   git push -u origin main
   ```
   *(Hoặc bạn có thể bấm **Add file ➔ Upload files** trực tiếp trên giao diện web của GitHub).*

---

### Bước 2: Chuẩn bị 5 thông số kết nối (Secrets)

| Tên Secret | Ý nghĩa | Cách lấy |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Khóa Google Gemini AI | Lấy miễn phí tại: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `BLOGGER_BLOG_ID` | ID blog trên Blogger | Vào `blogger.com` ➔ Dãy số trên URL: `blogger.com/blog/posts/`**`123456789...`** |
| `GOOGLE_CLIENT_ID` | Mã Client ID OAuth2 | Tạo tại [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |
| `GOOGLE_CLIENT_SECRET` | Mã Bí mật OAuth2 | Tạo cùng lúc với Client ID ở trên |
| `GOOGLE_REFRESH_TOKEN` | Token đăng bài vĩnh viễn | Chạy file `get_refresh_token.py` (hoặc qua OAuth Playground) |

#### 🔑 Cách lấy `GOOGLE_REFRESH_TOKEN` cực nhanh (Chỉ 30 giây):
1. Chạy script có sẵn trên máy tính của bạn:
   ```bash
   python get_refresh_token.py
   ```
2. Nhập `Client ID` và `Client Secret`.
3. Trình duyệt tự mở cửa sổ đăng nhập Google ➔ Bạn bấm Cho phép (Allow).
4. Màn hình console sẽ in ra chuỗi mã `GOOGLE_REFRESH_TOKEN` vĩnh viễn!

---

### Bước 3: Cài đặt Secrets vào GitHub Repository
1. Trên trang Repository GitHub của bạn, vào mục: **Settings** ➔ Cột bên trái chọn **Secrets and variables** ➔ Bấm **Actions**.
2. Bấm nút **New repository secret** màu xanh và lần lượt thêm 5 mục:
   - `GEMINI_API_KEY`: *(Dán mã AIzaSy...)*
   - `BLOGGER_BLOG_ID`: *(Dán số ID blog của bạn)*
   - `GOOGLE_CLIENT_ID`: *(Dán Client ID)*
   - `GOOGLE_CLIENT_SECRET`: *(Dán Client Secret)*
   - `GOOGLE_REFRESH_TOKEN`: *(Dán Refresh Token)*

---

### Bước 4: Cấp quyền ghi lịch sử cho GitHub Actions
1. Vẫn trong mục **Settings** của Repository ➔ Cột bên trái chọn **Actions** ➔ **General**.
2. Cuộn xuống phần **Workflow permissions**:
   - Chọn: **Read and write permissions** (Cho phép bot tự động lưu file `posted_history.json`).
3. Bấm **Save**.

---

## 🚀 Kiểm tra và Khởi chạy hệ thống

### 1. Chạy thử nghiệm ngay lập tức (Manual Trigger):
1. Vào tab **Actions** trên GitHub.
2. Ở cột bên trái, chọn workflow: **🚀 Blogger Gemini AI Auto-Poster Cloud**.
3. Bấm nút **Run workflow** ➔ Bấm nút xanh **Run workflow**.
4. Bạn sẽ thấy máy ảo đám mây của GitHub khởi động, gọi Gemini AI viết bài và đăng thẳng lên Blogger chỉ trong khoảng 10 - 20 giây!

### 2. Lịch chạy tự động hàng ngày:
Mặc định hệ thống được cài đặt:
- **08:00 sáng mỗi ngày** (giờ Việt Nam): Tự động thức dậy ➔ lấy đề tài tiếp theo trong `topics.txt` ➔ Viết bài chuẩn SEO ➔ Đăng lên Blogger ➔ Tự động lưu lịch sử ➔ Nghỉ.

---

## 📝 Cách bổ sung đề tài mới

Mở file `topics.txt` trên GitHub hoặc máy tính, thêm các dòng đề tài theo cú pháp:
```text
Tiêu đề hoặc từ khóa mục tiêu | Nhãn 1, Nhãn 2
```
Ví dụ:
```text
Dịch vụ thiết kế website doanh nghiệp chuẩn SEO chuyên nghiệp 2026 | Thiết Kế Web, SEO
Bí quyết chạy quảng cáo Facebook tối ưu chi phí ra đơn khủng | Facebook Ads, Marketing
Chiến lược SEO tổng thể đưa từ khóa lên Top 1 Google bền vững | Dịch Vụ SEO, Google
```
Mỗi ngày hệ thống sẽ tự động duyệt từ trên xuống dưới, bài nào đã đăng sẽ được lưu vào `posted_history.json` và không bao giờ bị đăng trùng lặp!
