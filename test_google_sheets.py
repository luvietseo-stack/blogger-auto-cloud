#!/usr/bin/env python3
"""
Công cụ kiểm tra & chẩn đoán kết nối Google Sheets cho Blogger Auto-Poster
Cách dùng:
    python test_google_sheets.py
    hoặc:
    python test_google_sheets.py "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0"
"""

import os
import sys
import re
import csv
import io
import json
import requests

# Ensure utf-8 stdout on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thử nạp từ .env nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'posted_history.json')

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'history': []}

def test_sheet(sheet_url):
    print("=" * 65)
    print("🔍 CHẨN ĐOÁN ĐỒNG BỘ GOOGLE SHEETS ➔ BLOGGER AUTO-POSTER")
    print("=" * 65)
    print(f"📌 URL kiểm tra: {sheet_url}")

    if not sheet_url:
        print("\n❌ LỖI: Biến GOOGLE_SHEET_URL đang rỗng!")
        print("💡 Cách khắc phục:")
        print("   1. Nếu chạy trên GitHub Actions: Vào Settings -> Secrets and variables -> Actions")
        print("      Thêm Secret hoặc Variable mang tên: GOOGLE_SHEET_URL")
        print("   2. Nếu chạy trên máy: Tạo file .env và thêm dòng:")
        print("      GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/.../edit#gid=0")
        print("   3. Hoặc chạy lệnh: python test_google_sheets.py \"<LINK_GOOGLE_SHEETS>\"")
        return

    sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
    sheet_id = sheet_id_match.group(1) if sheet_id_match else sheet_url.strip()

    gid_match = re.search(r'[#&?]gid=([0-9]+)', sheet_url)
    gid = gid_match.group(1) if gid_match else '0'

    print(f"🔑 Trích xuất: Sheet ID = {sheet_id}")
    print(f"📑 Tab Sheet (GID) = {gid}")

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
    print(f"🌐 Link GViz CSV: {csv_url}\n")

    print("⏳ Đang gửi yêu cầu tải dữ liệu...")
    try:
        resp = requests.get(csv_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    except Exception as e:
        print(f"❌ Không thể kết nối tới Google: {e}")
        return

    print(f"📡 Trạng thái phản hồi HTTP: {resp.status_code}")

    if resp.status_code != 200:
        print(f"❌ LỖI HTTP {resp.status_code}: Không thể tải Google Sheet.")
        print("💡 Hãy kiểm tra xem Sheet ID có chính xác không!")
        return

    content = resp.content.decode('utf-8-sig', errors='replace')

    # Kiểm tra xem có bị chuyển hướng sang trang đăng nhập Google Accounts không
    if '<html' in content.lower() or 'accounts.google.com' in content or 'serviceLogin' in content:
        print("\n❌ LỖI QUYỀN TRUY CẬP (ACCESS DENIED):")
        print("   Google Sheets trả về trang HTML Đăng nhập tài khoản thay vì dữ liệu CSV.")
        print("👉 NGUYÊN NHÂN: Bảng tính của bạn đang ở chế độ Riêng tư (Chỉ mình tôi / Restricted)!")
        print("💡 CÁCH SỬA:")
        print("   1. Mở bảng tính Google Sheets của bạn.")
        print("   2. Bấm nút 'Chia sẻ' (Share) màu xanh ở góc trên bên phải.")
        print("   3. Ở mục 'Quyền truy cập chung' (General access), đổi thành:")
        print("      'Bất kỳ ai có đường liên kết' (Anyone with the link) ➔ Quyền: 'Người xem' (Viewer).")
        print("   4. Bấm 'Xong' (Done) và chạy lại kịch bản!")
        return

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    print(f"📊 Tổng số hàng đọc được từ Google Sheets: {len(rows)} hàng")

    if not rows:
        print("⚠️ Bảng tính hoàn toàn trống!")
        return

    # Quét qua 5 dòng đầu để tìm header
    header_row_idx = 0
    col_title = -1
    col_status = -1

    for r_idx in range(min(5, len(rows))):
        h_row = [str(c).strip().lower() for c in rows[r_idx]]
        c_title = -1
        for i, h in enumerate(h_row):
            if any(k in h for k in ['tiêu đề', 'tieu de', 'title', 'chủ đề', 'chu de', 'topic']):
                c_title = i
                break
        if c_title != -1:
            header_row_idx = r_idx
            col_title = c_title
            break

    headers = [str(c).strip() for c in rows[header_row_idx]]
    print(f"\n📋 Dòng Header được nhận diện (Dòng #{header_row_idx + 1}):")
    for i, h in enumerate(headers):
        hl = h.lower()
        role = "Khác"
        if any(k in hl for k in ['tiêu đề', 'tieu de', 'title', 'chủ đề', 'chu de', 'topic']):
            role = "🎯 [TIÊU ĐỀ BÀI VIẾT]"
            col_title = i
        elif any(k in hl for k in ['từ khóa', 'tu khoa', 'keyword']):
            role = "🔑 [TỪ KHÓA CHÍNH]"
        elif any(k in hl for k in ['nhãn', 'nhan', 'label', 'chuyên mục', 'category']):
            role = "🏷️ [NHÃN CHUYÊN MỤC]"
        elif any(k in hl for k in ['gợi ý', 'goi y', 'tóm tắt', 'tom tat', 'nội dung', 'summary']):
            role = "📝 [GỢI Ý NỘI DUNG]"
        elif any(k in hl for k in ['trạng thái', 'trang thai', 'status']):
            role = "⚙️ [TRẠNG THÁI]"
            col_status = i
        print(f"   - Cột {chr(65+i)} ({i+1}): '{h}' ➔ {role}")

    if col_title == -1:
        print("\n⚠️ CẢNH BÁO: Không tìm thấy cột nào chứa chữ 'Tiêu đề' hoặc 'Title'!")
        print("   Hệ thống sẽ lấy mặc định Cột B (hoặc Cột A). Hãy đặt tên cột là 'Tiêu Đề Bài Viết' để chính xác nhất.")
        col_title = 1 if len(headers) > 1 else 0

    history = load_history()
    posted_topics = set(item['topic'].lower().strip() for item in history.get('history', []))

    valid_candidates = []
    already_posted_count = 0
    in_history_count = 0

    for row_idx, r in enumerate(rows[header_row_idx + 1:], header_row_idx + 2):
        if not r or len(r) <= col_title:
            continue
        title = r[col_title].strip()
        if not title or title.startswith('#'):
            continue

        status = r[col_status].strip().lower() if col_status != -1 and len(r) > col_status else ''
        if any(s in status for s in ['đã đăng', 'da dang', 'posted', 'done', 'đã lên lịch', 'da len lich', 'scheduled', 'hoàn thành']):
            already_posted_count += 1
            continue

        if title.lower() in posted_topics:
            in_history_count += 1
            continue

        valid_candidates.append((row_idx, title))

    print(f"\n📈 KẾT QUẢ ĐÁNH GIÁ ĐỀ TÀI:")
    print(f"   ✅ Đề tài hợp lệ sẵn sàng đăng tiếp theo: {len(valid_candidates)} bài")
    print(f"   ⏩ Đã bỏ qua do có trạng thái 'Đã đăng' / 'Đã lên lịch' trên Sheet: {already_posted_count} bài")
    print(f"   ⏩ Đã bỏ qua do đã có trong posted_history.json: {in_history_count} bài")

    if valid_candidates:
        print(f"\n🎯 3 ĐỀ TÀI SẼ ĐƯỢC CHỌN ĐĂNG TIẾP THEO:")
        for idx, (r_idx, t) in enumerate(valid_candidates[:3], 1):
            print(f"   [{idx}] Dòng #{r_idx}: {t}")
    else:
        print("\n⚠️ HIỆN TẠI KHÔNG CÒN ĐỀ TÀI NÀO ĐỂ ĐĂNG TỪ GOOGLE SHEETS NÀY!")
        print("   ➔ Nếu chạy hệ thống, bot sẽ chuyển sang file dự phòng topics.txt.")

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('GOOGLE_SHEET_URL', '')
    test_sheet(url)
