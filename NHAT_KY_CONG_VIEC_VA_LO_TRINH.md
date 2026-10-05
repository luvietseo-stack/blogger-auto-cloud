# 📋 NHẬT KÝ CÔNG VIỆC & LỘ TRÌNH DỰ ÁN BLOGGER AUTO CLOUD
**Thời gian ghi nhận:** Ngày 28 - 29/09/2026  
**Chủ dự án:** Auto Content LuVietcom  
**Hệ thống:** AILADI Platform & Blogger LuViet (`https://www.luviet.com`)  
**Kho mã nguồn GitHub:** `https://github.com/thuantranblog/blogger-auto-cloud.git`

---

## 🚀 I. TOÀN BỘ CÔNG VIỆC ĐÃ HOÀN THÀNH HÔM NAY

### 1. Khắc phục lỗi GitHub Actions & Tối ưu luồng tự động
- **Xử lý lỗi HTTP 503 UNAVAILABLE:** Bổ sung cơ chế thử lại luỹ tiến (Exponential Backoff: 3s, 7s, 15s) kết hợp chuỗi model dự phòng `['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.5-flash-lite', 'gemini-flash-latest']`.
- **Ưu tiên đề tài Google Sheets:** Hoàn thiện bộ quét bảng tính tự động nhận diện tiêu đề, tóm tắt, nhãn, ảnh tùy chỉnh và gửi Webhook phản hồi trạng thái sang Google Apps Script.
- **Dọn dẹp kho lưu trữ:** Đồng bộ mã nguồn sạch lên branch `main`, loại bỏ các file thừa, bảo mật các khóa OAuth và cấu hình tự động đẩy lịch sử đăng (`posted_history.json`, `thumbnails/`).

### 2. Tích hợp Hồ chứa API Key xoay vòng (Key Pool)
- **Hỗ trợ nạp nhiều key:** Cho phép dán nhiều Gemini API Key vào ô `GEMINI_API_KEY` (hoặc biến `GEMINI_API_KEYS`), phân tách bằng dấu xuống dòng hoặc dấu phẩy.
- **Tự động chuyển key:** Khi key chính gặp lỗi quá tải hoặc hết hạn mức (`HTTP 429 Quota Exceeded`), hệ thống lập tức luân chuyển sang key phụ cho cả việc viết bài lẫn tạo ảnh nền mà không ngắt quãng quy trình.

### 3. Tự động thiết kế Thumbnail Doanh Nhân 3D Typography
- **Module độc quyền:** Xây dựng [`generate_executive_thumbnail.py`](file:///C:/Users/Admin/.gemini/antigravity-ide/scratch/blogger-auto-cloud/generate_executive_thumbnail.py) tạo ảnh 16:9 sắc nét.
- **Phong cách chuẩn BNI Executive:** Chữ vàng kim 3D khối nổi (`#FFD700`), dải băng đỏ vát chéo Dynamic Ribbon (`#B91C1C`), chữ trắng viền đen chrome, 4 icon vector HUD công nghệ cao và watermark thương hiệu `AILADI™ PLATFORM DIGITAL TRANSFORMATION`.
- **Đóng gói font chữ:** Đưa tệp `Roboto-Bold.ttf` vào thư mục gốc để đảm bảo chữ tiếng Việt hiển thị to, rõ, không bị lỗi font trên hệ điều hành Linux Ubuntu của GitHub Actions.

### 4. Xử lý triệt để lỗi Thumbnail máy ảnh xám ngoài trang chuyên mục
- **Nguyên nhân cốt lõi:** Blogger feed không tự sinh `media$thumbnail` cho các ảnh lưu trữ ngoài CDN Google, dẫn đến theme hiển thị ảnh mặc định `nth.png` (icon máy ảnh xám).
- **Đã cập nhật file giao diện XML:** Chỉnh sửa hoàn tất toàn bộ 10 khối hiển thị ảnh trong tệp:  
  📁 `D:\blogger-auto-cloud\theme-1444221897689962852 (3).xml`
- **File sao lưu an toàn:** Đã tạo bản lưu dự phòng tại:  
  📁 `D:\blogger-auto-cloud\theme-1444221897689962852 (3)_backup_original.xml`
- **Hàm xử lý mới `_getBloggerThumbnail`:** Tự động trích xuất thẻ `<img>` đầu tiên trong bài viết để làm thumbnail nếu Google feed thiếu dữ liệu.

### 5. Khắc phục triệt để lỗi không nhận được thông báo Telegram & Gmail
- **Nguyên nhân Telegram:**
  1. Kịch bản `main.py` trước đây chưa có hàm gửi Telegram trực tiếp mà phụ thuộc hoàn toàn vào Webhook Google Apps Script.
  2. Trên GitHub repo và Apps Script, biến `TELEGRAM_BOT_TOKEN` bị đặt là `YOUR_TELEGRAM_BOT_TOKEN` (placeholder), hoặc chưa tạo New Deployment Version.
  3. Webhook Apps Script đôi khi bị quá tải / timeout sau 15 giây (như bài #3 sáng nay) khiến tiến trình bị ngắt.
- **Giải pháp Telegram đã triển khai:**
  1. Tích hợp trực tiếp module gửi Telegram siêu tốc (< 0.2s) ngay trong `main.py` trên GitHub Actions.
  2. Đã test bắn trực tiếp thông báo bài viết mẫu vào nhóm **Content Luviet** (`-5074952407`) thành công 100%.
  3. Đã đưa cấu hình Token Bot và Chat ID vào `.github/workflows/auto_post.yml` và đồng bộ lên GitHub `main`.
- **Nguyên nhân Gmail:**
  1. Biến `NOTIFICATION_EMAIL` trong `google_sheets_webhook.js` để trống `""`. Khi Webhook nhận lệnh ẩn danh từ GitHub, `Session.getEffectiveUser().getEmail()` trả về chuỗi rỗng nên hàm gửi email tự bỏ qua.
  2. Dịch vụ `MailApp` của Google yêu cầu phải mở trình soạn thảo Apps Script, bấm chọn hàm `testNotification` rồi nhấn **Chạy (Run)** một lần duy nhất để Google hiện thông báo cấp quyền gửi email (`Review Permissions` ➔ `Allow`).
- **Giải pháp Gmail đã cập nhật:**
  1. Cập nhật `NOTIFICATION_EMAIL = "thuantranblo@gmail.com"` trong file [`google_sheets_webhook.js`](file:///D:/blogger-auto-cloud/google_sheets_webhook.js).
  2. Tăng thời gian chờ Webhook từ 15s lên 30s để Apps Script có đủ thời gian gửi mail và cập nhật Sheet.

### 6. Nâng cấp Bộ tạo Thumbnail chuẩn YouTube (High CTR)
- **Ảnh nền bám sát tóm tắt (summary):** Tự động phân tích ngữ cảnh bài viết để sinh prompt ảnh nền điện ảnh (Cinematic 16:9, Photorealistic 8k) phù hợp theo từng ngành nghề (Bất động sản, Bán lẻ POS, Quảng cáo Ads, Logistics/Bom hàng, Thiết kế web doanh nghiệp, v.v.). Bố cục tạo khoảng tối bên trái (Left negative space) để chữ nổi bật.
- **Tối giản hóa chữ và icon:** Loại bỏ toàn bộ 4 hộp thẻ HUD rườm rà và các icon vụn vặt; chỉ giữ 1 nhãn badge tinh tế phía trên và logo nhỏ góc phải.
- **Quy chuẩn chữ giật tít:**
  - Đúng **2 hàng**, mỗi hàng tối đa **3 chữ** (`len <= 3 words`), không rườm rà.
  - Chữ **TO** (135px - 145px) cực nét, dễ đọc trên cả điện thoại di động.
  - **Viền sáng phát quang (Glowing Aura / Neon Glow):** Hàng 1 chữ vàng ánh kim viền phát quang vàng rực; Hàng 2 chữ trắng tuyết viền phát quang Cyan/Neon rực rỡ kết hợp đổ bóng khối 3D dày tách nền.
- **Đã kiểm nghiệm:** Xuất ảnh mẫu tại [`test_yt_thumb.jpg`](file:///C:/Users/Admin/.gemini/antigravity-ide/scratch/blogger-auto-cloud/test_yt_thumb.jpg) sắc nét, bắt mắt.
- **Đồng bộ hóa:** Đã cập nhật lên GitHub branch `main`.

### 7. Sửa lỗi `Uncaught ReferenceError: _getBloggerThumbnail is not defined`
- **Nguyên nhân cốt lõi:** Trước đó hàm `_getBloggerThumbnail` được đặt bên trong khối điều kiện `<b:if cond='data:view.isLabelSearch'>`. Khi người dùng xem trang chi tiết bài viết (như `05-ly-do-chu-shop...html`), điều kiện `isLabelSearch` là `False`, nên Blogger không nạp hàm này vào trình duyệt. Khi các widget AJAX dưới chân bài viết (`blogsrights` - xem nhiều nhất, `relatedblogpost` - bài liên quan) chạy và gọi `_getBloggerThumbnail` thì bị crash.
- **Giải pháp triệt để:** Đã chuyển hàm `_getBloggerThumbnail` ra phạm vi toàn cục (Global Scope), đặt ngay trước thẻ đóng `</head>` trong tệp:  
  📁 `D:\blogger-auto-cloud\theme-1444221897689962852 (3).xml`.  
  Đồng thời gán `window._getBloggerThumbnail = _getBloggerThumbnail` để mọi trang (Trang chủ, Trang chuyên mục, Trang bài viết, Trang tĩnh) đều gọi được trơn tru mà không bao giờ gặp lỗi.

---

## 📌 II. LỘ TRÌNH CÔNG VIỆC TIẾP THEO (KẾ HOẠCH CHO NGÀY MAI)

### 1. Nạp giao diện XML vào Blogger (15 giây)
- Vào **Blogger -> Chủ đề (Theme)** ➔ Bấm mũi tên cạnh nút **Tùy chỉnh** ➔ Chọn **Khôi phục (Restore)** ➔ Tải lên file:  
  `D:\blogger-auto-cloud\theme-1444221897689962852 (3).xml`.
- Tải lại trang `luviet.com/search/label/dich-vu` để nghiệm thu giao diện thumbnail mới.

### 2. Nâng cấp Extension thành "Blogger SEO Doctor & Keyword Optimizer"
- **Thư mục Extension:** `C:\Users\Admin\.gemini\antigravity-ide\scratch\blogger-gemini-ai`
- **Các tính năng sẽ tích hợp:**
  1. **Tab SEO On-Page Realtime:** Nhập Focus Keyword và đo điểm SEO (0 - 100 điểm) trực tiếp khi đang mở Bài viết (Posts) hoặc Trang tĩnh (Pages).
  2. **Checklist 8 tiêu chuẩn Google:** Quét Tiêu đề, Thẻ mô tả tìm kiếm, Mật độ từ khóa (1.2% - 2.5%), Thẻ Heading H2/H3, Thẻ Alt hình ảnh, Liên kết nội bộ LuViet, Độ dài từ khóa.
  3. **Bộ công cụ AI 1-Click tự động sửa trên Blogger:**
     - AI tự viết và điền Thẻ mô tả tìm kiếm (Search Description) vào thanh cài đặt Blogger.
     - AI tự rà soát và bổ sung thẻ `alt` cho toàn bộ ảnh trong bài viết.
     - AI gợi ý từ khóa LSI và các câu hỏi thường gặp (FAQ Schema) bổ trợ.
     - AI mở rộng / tối ưu lại các bài viết cũ đang bị tụt top.
8. **Chuyển đổi toàn diện Extension thành Blogger SEO Doctor Pro & AI Optimizer (v3.0.0 & v3.1.0 Deep Editor Engine):**
   - **Mục tiêu:** Chuyển đổi toàn bộ extension từ công cụ viết bài sang hệ thống hỗ trợ SEO On-Page Realtime (0 - 100 điểm) trực tiếp trong trình soạn thảo Blogger.com (tương tự Yoast SEO / Rank Math trên WordPress).
   - **Khắc phục triệt để lỗi nhận diện Editor (v3.1.0):**
     * Tích hợp **Deep Editor Engine** 4 tầng: Thâm nhập sâu vào iframe Compose của Blogger (kể cả khi `doc.designMode = 'on'` hoặc chưa focus), trích xuất HTML CodeMirror từ DOM, div `contenteditable` và textarea.
     * Gắn bộ lắng nghe sự kiện (`input`, `keyup`, `paste`, `change`) và `MutationObserver` **trực tiếp vào bên trong `iframe.contentDocument`**, giải quyết tận gốc vấn đề sự kiện không nổi bọt ra trang cha.
     * Tích hợp **Smart Polling**: Tự động thăm dò chu kỳ 600ms khi trang vừa mở để nạp bài ngay khi AJAX nạp xong nội dung từ máy chủ Blogger.
     * Bổ sung thanh trạng thái **Editor Connection Banner** & nút **"👁️ Xem đoạn trích nội dung đã nhận diện"** giúp người dùng kiểm chứng ngay tức thì.
   - **Hệ thống tính điểm & Audit Realtime:**
     * Vòng tròn SVG Radial Gauge tính điểm On-Page tức thì theo thời gian thực (0 - 100đ).
     * Checklist 10 tiêu chuẩn Google khắt khe: Từ khóa trong Tiêu đề (vị trí & độ dài 40-65 ký tự), Search Description (120-155 ký tự & chứa từ khóa), Mật độ từ khóa On-Page (1.0% - 2.5%), Từ khóa trong 100 từ đầu & kết bài, Cấu trúc Heading H2/H3, Thẻ Alt hình ảnh, Độ dài nội dung (Word count >= 1200 từ), Liên kết nội bộ/ngoài, Khối Rich Content/FAQ.
9. **Kích hoạt tự động viết bài từ Google Sheets 20 phút / lần (29/09/2026):**
   - **Cấu hình Workflow GitHub Actions:**
     * Cập nhật `.github/workflows/auto_post.yml` sang lịch cron: `*/20 * * * *` (mỗi 20 phút chạy 1 lần).
     * Thiết lập mỗi lần chạy viết 1 bài (`POSTS_COUNT = 1`).
     * Cơ chế tự động lấy đề tài tiếp theo chưa đăng từ Google Sheets (311 đề tài sẵn có).
     * Thuật toán `get_next_schedule_slots()` tự động nối tiếp lấp đầy 3 khung giờ vàng (06:30, 11:30, 14:30) của các ngày tiếp theo mà không bị trùng slot.
     * Cập nhật ngược lại Google Sheets qua Webhook (Đổi trạng thái "Đã lên lịch", điền ngày giờ hẹn, link bài viết và thumbnail).
     * Báo cáo Telegram & Gmail tự động tức thì.
   - **Kết quả kiểm thử thực tế:**
     * Run ID `36572394368` hoàn thành **Success** trong 45 giây.
     * Tự động lấy đề tài STT 10 từ Google Sheet và lên lịch hẹn chuẩn xác lúc **01/10/2026 14:30 (Giờ VN)**.
     * Cột G Google Sheet tự động đổi sang "Đã lên lịch" và Cột H ghi nhận ngày giờ thành công 100%.


| Thành phần | Đường dẫn tệp | Trạng thái |
| :--- | :--- | :--- |
| **Mã nguồn Auto-Post Cloud** | `C:\Users\Admin\.gemini\antigravity-ide\scratch\blogger-auto-cloud` | Đã đồng bộ GitHub |
| **Engine tạo Thumbnail 3D** | `.../blogger-auto-cloud/generate_executive_thumbnail.py` | Hoàn thiện 100% |
| **File Giao diện XML đã sửa** | `D:\blogger-auto-cloud\theme-1444221897689962852 (3).xml` | Đã sửa `_getBloggerThumbnail` |
| **File Giao diện sao lưu gốc** | `D:\blogger-auto-cloud\theme-1444221897689962852 (3)_backup_original.xml` | Đã sao lưu an toàn |
| **Blogger SEO Doctor Pro v3.0.0** | `C:\Users\Admin\.gemini\antigravity-ide\scratch\blogger-gemini-ai` | Hoàn thành chuyển đổi 100% |

