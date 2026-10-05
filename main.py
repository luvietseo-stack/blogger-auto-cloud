#!/usr/bin/env python3
"""
Blogger Gemini AI Cloud Auto-Poster
Tự động viết bài chuẩn SEO và đăng lên Blogger.com trên đám mây (GitHub Actions)
Hỗ trợ: Google Gemini API + Blogger API v3 + CTA LuViet
"""

import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
import requests

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    Credentials = None
    build = None

# Load local .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import bộ máy tạo ảnh Thumbnail Doanh Nhân
try:
    from generate_executive_thumbnail import create_post_thumbnail
except ImportError:
    create_post_thumbnail = None

# ==============================================================================
# CẤU HÌNH HỆ THỐNG
# ==============================================================================
def clean_credential(val):
    if not val:
        return ''
    v = str(val).strip().strip('"').strip("'")
    if '=' in v and not v.startswith('1//'):
        v = v.split('=', 1)[1].strip().strip('"').strip("'")
    # Loại bỏ hoàn toàn ký tự xuống dòng và khoảng trắng do copy-paste từ PowerShell
    v = v.replace('\n', '').replace('\r', '').replace(' ', '')
    return v

def get_api_key_pool():
    import re
    # Hỗ trợ lấy key từ nhiều nguồn biến môi trường: GEMINI_API_KEY, GEMINI_API_KEYS, GEMINI_BACKUP_API_KEY
    # Người dùng có thể nhập 1 key hoặc nhiều key cách nhau bởi dấu phẩy, chấm phẩy hoặc xuống dòng
    raw = os.environ.get('GEMINI_API_KEY', '')
    backups = os.environ.get('GEMINI_API_KEYS', '') + ',' + os.environ.get('GEMINI_BACKUP_API_KEY', '')
    combined = raw + ',' + backups
    tokens = re.split(r'[,;\n\r]+', combined)
    pool = []
    for t in tokens:
        clean_k = clean_credential(t)
        if clean_k and clean_k not in pool:
            pool.append(clean_k)
    return pool

BLOGGER_BLOG_ID = clean_credential(os.environ.get('BLOGGER_BLOG_ID'))
GOOGLE_CLIENT_ID = clean_credential(os.environ.get('GOOGLE_CLIENT_ID'))
GOOGLE_CLIENT_SECRET = clean_credential(os.environ.get('GOOGLE_CLIENT_SECRET'))
GOOGLE_REFRESH_TOKEN = clean_credential(os.environ.get('GOOGLE_REFRESH_TOKEN'))

# Cấu hình Google Sheets đồng bộ đề tài & Webhook cập nhật trạng thái
GOOGLE_SHEET_URL = os.environ.get('GOOGLE_SHEET_URL', '').strip()
GOOGLE_SHEET_WEBHOOK_URL = os.environ.get('GOOGLE_SHEET_WEBHOOK_URL', '').strip()

# Cấu hình thông báo Telegram báo cáo trực tiếp
TELEGRAM_BOT_TOKEN = clean_credential(os.environ.get('TELEGRAM_BOT_TOKEN', '8480459173:AAHhSTEGSCG5zwq1jp6Dtycw97NQ2dqA8QM'))
TELEGRAM_CHAT_ID = clean_credential(os.environ.get('TELEGRAM_CHAT_ID', '-5074952407'))

# Chế độ phát hành: 'schedule' (Lên lịch theo giờ vàng), 'publish' (Đăng ngay), 'draft' (Lưu nháp)
POST_MODE = os.environ.get('POST_MODE', 'schedule').lower().strip()
SCHEDULE_HOURS_AHEAD = int(os.environ.get('SCHEDULE_HOURS_AHEAD', '24'))

def determine_label(title, summary='', raw_tags=''):
    """
    Phân loại nhãn chuẩn theo quy ước hiển thị của LuViet:
    - dich-vu: Bài về dịch vụ thiết kế web, landing page doanh nghiệp, báo giá, Đồng Nai/Biên Hòa
    - tin-tuc: Tin tức thị trường, chiến lược bán hàng, thương mại điện tử
    - kien-thuc: Hướng dẫn kỹ thuật, tool AI, thủ thuật
    """
    combined = (str(title) + ' ' + str(summary) + ' ' + str(raw_tags)).lower()
    service_keywords = [
        'dịch vụ', 'dich vu', 'thiết kế web', 'thiet ke web', 'báo giá', 'bảng giá',
        'thuê đơn vị làm website', 'thiết kế landing page', 'đồng nai', 'biên hòa'
    ]
    if any(k in combined for k in service_keywords):
        return 'dich-vu'
    knowledge_keywords = [
        'hướng dẫn', 'huong dan', 'cách làm', 'thủ thuật', 'ai chatbot', 'chatgpt', 'gemini'
    ]
    if any(k in combined for k in knowledge_keywords):
        return 'tin-tuc, kien-thuc'
    return 'tin-tuc'

# Cấu hình viết hàng loạt & thời gian giãn cách
POSTS_COUNT = int(os.environ.get('POSTS_COUNT', os.environ.get('POST_COUNT', '3')))
DELAY_SECONDS = int(os.environ.get('DELAY_SECONDS', '15'))

# Khung giờ vàng phát bài mỗi ngày (Giờ Việt Nam UTC+7: 06:30, 11:30, 14:30)
GOLDEN_SLOTS = [(6, 30), (11, 30), (14, 30)]

def get_next_schedule_slots(count=1, existing_history=None):
    """
    Tính toán danh sách các khung giờ vàng 06:30, 11:30, 14:30 giờ Việt Nam (UTC+7).
    Tự động nối tiếp các bài đã lên lịch trước đó để không bị trùng slot.
    """
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    min_time = now_vn + timedelta(minutes=5)

    occupied_slots = []
    if existing_history and 'history' in existing_history:
        for item in existing_history['history']:
            pub_str = item.get('published')
            if pub_str:
                try:
                    dt = datetime.fromisoformat(pub_str.replace('Z', '+00:00')).astimezone(vn_tz)
                    occupied_slots.append(dt)
                except Exception:
                    pass

    slots = []
    check_day = min_time.date()

    while len(slots) < count:
        for h, m in GOLDEN_SLOTS:
            slot_candidate = datetime(check_day.year, check_day.month, check_day.day, h, m, 0, tzinfo=vn_tz)
            if slot_candidate <= min_time:
                continue

            # Kiểm tra xem slot này đã có bài lên lịch chưa (+/- 30 phút)
            is_occupied = any(abs((slot_candidate - occ).total_seconds()) < 1800 for occ in occupied_slots)
            is_already_selected = any(abs((slot_candidate - s).total_seconds()) < 1800 for s in slots)

            if not is_occupied and not is_already_selected:
                slots.append(slot_candidate)
                if len(slots) == count:
                    break
        check_day += timedelta(days=1)

    return slots

# Thông tin thương hiệu & Kênh kết nối BNI Topaz Chapter Online
CTA_URL = os.environ.get('CTA_URL', 'https://www.facebook.com/topazchapteronline')
WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://www.bnitopaz.com')
REGISTER_URL = os.environ.get('REGISTER_URL', CTA_URL)
ZALO_URL = os.environ.get('ZALO_URL', '')
FANPAGE_URL = os.environ.get('FANPAGE_URL', CTA_URL)

TOPICS_FILE = os.path.join(os.path.dirname(__file__), 'topics.txt')
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'posted_history.json')

# ==============================================================================
# HÀM BÓC TÁCH & GIẢI MÃ JSON AN TOÀN
# ==============================================================================
def robust_json_decode(raw_text):
    """
    Giải mã JSON bài viết từ phản hồi của Google Gemini một cách an toàn và chống lỗi syntax.
    Tự động xử lý trường hợp markdown backticks, unescaped quotes, và HTML tags bên trong chuỗi.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # 1. Thử giải mã chuẩn bằng json.loads (strict=False bỏ qua các ký tự điều khiển)
    try:
        data = json.loads(cleaned, strict=False)
        if isinstance(data, dict) and data.get("title") and (data.get("content") or data.get("metaDescription")):
            return data
    except Exception:
        pass

    # 2. Thử cắt vùng nằm giữa cặp dấu ngoặc nhọn ngoài cùng { ... }
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        snippet = cleaned[first_brace:last_brace+1]
        try:
            data = json.loads(snippet, strict=False)
            if isinstance(data, dict) and data.get("title") and (data.get("content") or data.get("metaDescription")):
                return data
        except Exception:
            pass

    # 3. Khôi phục bằng Regex bóc tách từng trường (Cứu nguy khi AI xuất unescaped quotes trong content HTML)
    try:
        import re
        data = {}
        m_title = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
        if m_title:
            data['title'] = m_title.group(1).replace(r'\"', '"').replace(r'\n', ' ').strip()

        m_labels = re.search(r'"labels"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
        if m_labels:
            raw_labels = m_labels.group(1)
            data['labels'] = [lbl.strip().strip('"\'') for lbl in raw_labels.split(',') if lbl.strip().strip('"\'')]

        m_meta = re.search(r'"metaDescription"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
        if m_meta:
            data['metaDescription'] = m_meta.group(1).replace(r'\"', '"').replace(r'\n', ' ').strip()

        m_img = re.search(r'"imagePrompt"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
        if m_img:
            data['imagePrompt'] = m_img.group(1).replace(r'\"', '"').replace(r'\n', ' ').strip()

        content_idx = cleaned.find('"content"')
        if content_idx != -1:
            colon_idx = cleaned.find(':', content_idx)
            if colon_idx != -1:
                start_quote = cleaned.find('"', colon_idx)
                if start_quote != -1:
                    raw_content = cleaned[start_quote+1:]
                    last_q = raw_content.rfind('"\n}')
                    if last_q == -1:
                        last_q = raw_content.rfind('"}')
                    if last_q == -1:
                        last_q = raw_content.rfind('"')
                    
                    if last_q != -1:
                        c_str = raw_content[:last_q]
                    else:
                        c_str = raw_content

                    c_str = c_str.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\/', '/')
                    data['content'] = c_str

        if data.get('title') and (data.get('content') or data.get('metaDescription')):
            return data
    except Exception as e_repair:
        print(f"⚠️ Quá trình bóc tách regex JSON gặp lỗi: {e_repair}")

    return json.loads(cleaned)

# ==============================================================================
# HÀM GỌI GEMINI AI VIẾT BÀI CHUẨN SEO
# ==============================================================================
def generate_seo_article(topic, labels, summary='', cta_url=REGISTER_URL):
    api_keys = get_api_key_pool()
    if not api_keys:
        raise Exception("Không tìm thấy Gemini API Key nào hợp lệ!")

    print(f"\n🧠 Đang gọi Google Gemini AI viết bài cho chủ đề: '{topic}'...")
    print(f"🔑 Số lượng API Key trong hồ chứa (Key Pool): {len(api_keys)}")

    prompt = f"""
Bạn là Chuyên gia Cao cấp về Marketing B2B, Referral Networking, Cố vấn Doanh nghiệp và Copywriter hàng đầu Việt Nam, am hiểu tường tận văn hóa và quy trình vận hành của tổ chức BNI (Business Network International).
Hãy tạo một bài viết chuẩn SEO chuyên sâu, cấu trúc chặt chẽ, tối ưu tỷ lệ chuyển đổi (CRO) bằng tiếng Việt cho website chính thức của BNI Topaz Chapter Online (bnitopaz.com) theo các thông số sau:

- Chủ đề / Từ khóa chính: "{topic}"
- Nhãn chuyên mục mong muốn: "{', '.join(labels)}"
{f'- Tóm tắt gợi ý / Góc nhìn: "{summary}"' if summary else ''}
- Liên kết chuyển đổi mục tiêu (BẮT BUỘC): "{cta_url}"
- Độ dài mục tiêu: Khoảng 1500 - 2000 từ.
- Tông giọng: Chuyên gia thực chiến, đĩnh đạc, truyền cảm hứng kinh doanh mạnh mẽ, thấu hiểu sâu sắc những thách thức của chủ doanh nghiệp hiện đại và thôi thúc hành động kết nối giao thương.

CHIẾN LƯỢC NỘI DUNG & ĐIỀU HƯỚNG CHUYỂN ĐỔI (QUAN TRỌNG NHẤT):
1. ĐỐI TƯỢNG VÀ CHÂN DUNG KHÁCH HÀNG MỤC TIÊU:
   - Bài viết đánh trúng nỗi đau thực tế của: Chủ doanh nghiệp vừa và nhỏ (SMEs), Giám đốc điều hành (CEO / Founder), Trưởng phòng kinh doanh, nhà đầu tư, chủ cơ sở dịch vụ/thương mại và doanh nhân khởi nghiệp.
   - Nỗi đau:
     + Bán hàng truyền thống ngày càng khó khăn, chi phí quảng cáo (Facebook/Google/TikTok Ads) đắt đỏ nhưng tỷ lệ chuyển đổi thấp và thiếu sự gắn kết.
     + Thiếu mạng lưới quan hệ chất lượng, cô đơn trên hành trình quản trị và phát triển doanh nghiệp.
     + Tham gia các câu lạc bộ truyền thống tốn kém thời gian đi lại, kẹt xe, chi phí ăn uống gặp mặt cao, bị giới hạn phạm vi địa lý hẹp trong một quận/huyện.
     + Muốn mở rộng quy mô kinh doanh toàn quốc và vươn ra quốc tế nhưng thiếu đối tác và kênh kết nối uy tín.

2. GIẢI PHÁP ĐỘT PHÁ - BNI TOPAZ CHAPTER ONLINE (bnitopaz.com):
   - Giới thiệu BNI Topaz Chapter Online là một trong những Chapter trực tuyến kiểu mẫu, năng động và hiệu quả hàng đầu của BNI Việt Nam.
   - Triết lý kinh doanh đỉnh cao: "Givers Gain®" (Cho là Nhận) – Nuôi dưỡng sự thịnh vượng bằng cách chủ động trao đi giá trị và cơ hội kinh doanh cho đồng đội.
   - 7 Giá trị Cốt lõi của BNI: Cho là Nhận, Xây dựng mối quan hệ bền vững, Học tập suốt đời, Truyền thống và Đổi mới, Thái độ tích cực, Trách nhiệm và Tinh thần trách nhiệm, Sự công nhận xứng đáng.
   - Cơ chế Độc quyền Ngành nghề: Mỗi ngành nghề chỉ có DUY NHẤT 1 đại diện trong Chapter, không có cạnh tranh nội bộ, tất cả thành viên trở thành đội ngũ kinh doanh đại sứ giới thiệu khách hàng miễn phí cho nhau.
   - Lợi thế vượt trội của Chapter Online: Họp định kỳ hàng tuần qua nền tảng Zoom chuyên nghiệp vào sáng sớm; Tiết kiệm 100% thời gian di chuyển; Kết nối không biên giới giữa các doanh nhân khắp 63 tỉnh thành Việt Nam và giao thương quốc tế với các Chapter BNI toàn cầu.
   - Quy trình tạo Referral chất lượng: Giúp các thành viên liên tục nhận được các cơ hội kinh doanh "nóng" (Referrals) từ những mối quan hệ tin cậy, rút ngắn chu kỳ bán hàng và gia tăng doanh số bền vững.

3. ĐIỀU HƯỚNG LIÊN KẾT NỘI BỘ (INTERNAL LINKING - BẮT BUỘC):
   - Trong thân bài: BẮT BUỘC chèn tự nhiên từ 2 đến 3 liên kết ngữ cảnh (contextual anchor text) dẫn người đọc bấm vào link Fanpage đăng ký: "{cta_url}".
     Ví dụ các cụm từ chèn link: <a href="{cta_url}" target="_blank">kết nối cùng BNI Topaz Chapter Online</a>, <a href="{cta_url}" target="_blank">đăng ký tham dự buổi giao lưu doanh nhân BNI Topaz</a>, <a href="{cta_url}" target="_blank">tìm hiểu BNI Topaz Chapter</a>.
   - BẮT BUỘC chèn thêm 1 - 2 liên kết nội bộ tự nhiên đến website chính thức:
     + Khi nhắc đến website hoặc thông tin Chapter: <a href="https://www.bnitopaz.com" target="_blank">website BNI Topaz Chapter</a> hoặc <a href="https://www.bnitopaz.com" target="_blank">cộng đồng doanh nhân bnitopaz.com</a>.

4. KHỐI CALL TO ACTION (CTA) ĐẲNG CẤP Ở CUỐI BÀI:
   - BẮT BUỘC chèn khối CTA nổi bật dạng hộp bo tròn sang trọng, phối màu nhận diện BNI đẳng cấp (Đỏ Burgundy BNI đặc trưng, Xanh Navy và Vàng Kim):
     <div style="margin: 35px 0 20px; padding: 28px 24px; background: linear-gradient(135deg, #fff7ed 0%, #fef2f2 50%, #eff6ff 100%); border: 2px solid #dc2626; border-radius: 14px; text-align: center; box-shadow: 0 6px 20px rgba(220, 38, 38, 0.12);">
       <span style="background: #dc2626; color: #ffffff; font-size: 13px; font-weight: 700; text-transform: uppercase; padding: 4px 14px; border-radius: 20px; letter-spacing: 0.5px;">Cơ Hội Kết Nối Kinh Doanh Độc Quyền</span>
       <h3 style="color: #991b1b; margin: 15px 0 10px; font-size: 22px; font-weight: 800; line-height: 1.4;">🚀 Bứt Phá Doanh Số & Mở Rộng Quan Hệ Cùng BNI Topaz Chapter Online!</h3>
       <p style="color: #334155; font-size: 15px; line-height: 1.6; max-width: 720px; margin: 0 auto 22px;">Đừng để doanh nghiệp đơn độc trong thị trường cạnh tranh khốc liệt. Hãy trải nghiệm năng lượng kết nối kinh doanh đỉnh cao theo triết lý "Cho Là Nhận" (Givers Gain) và sở hữu ngay đội ngũ hàng chục chủ doanh nghiệp sẵn sàng giới thiệu khách hàng cho bạn trên toàn quốc!</p>
       <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 14px;">
         <a href="{cta_url}" target="_blank" rel="noopener" style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: #ffffff; font-weight: 700; font-size: 16px; padding: 13px 30px; border-radius: 8px; text-decoration: none; box-shadow: 0 4px 14px rgba(220, 38, 38, 0.35); display: inline-block;">👉 Đăng Ký Tham Dự Giao Lưu BNI Topaz (Miễn Phí)</a>
         <a href="{cta_url}" target="_blank" rel="noopener" style="background: #1e3a8a; color: #ffffff; font-weight: 700; font-size: 15px; padding: 13px 24px; border-radius: 8px; text-decoration: none; box-shadow: 0 4px 12px rgba(30, 58, 138, 0.25); display: inline-block;">💬 Nhắn Tin Fanpage BNI Topaz Chapter</a>
       </div>
     </div>

5. CẤU TRÚC BÀI VIẾT (BẮT BUỘC):
   - TIÊU ĐỀ (Title): BẮT BUỘC đặt TỪ KHÓA CHÍNH NGAY Ở ĐẦU TIÊU ĐỀ (dưới 60 ký tự) để Blogger tự động sinh URL slug chuẩn SEO mà không bị cắt cụt. Kích thích lượt click (CTR) cao.
   - SAPO: Mở bài cuốn hút 2-3 đoạn ngắn theo công thức PAS (Problem - Agitate - Solution).
   - THÂN BÀI: Sử dụng thẻ <h2> và <h3> rõ ràng, logic. Luôn dùng danh sách (<ul>, <li>) để thoáng mắt.
   - BẢNG BIỂU: BẮT BUỘC có 1 Bảng so sánh (HTML <table>) trực quan, viền mỏng chuyên nghiệp (border: 1px solid #cbd5e1) làm nổi bật sự vượt trội của BNI Topaz Online so với các phương thức kinh doanh hoặc kết nối truyền thống.
   - FAQ: BẮT BUỘC có mục <h2>Câu hỏi thường gặp (FAQ)</h2> với ít nhất 3 câu hỏi thực tế về BNI Topaz Chapter Online và câu trả lời thấu đáo.
   - PROMPT TẠO ẢNH: Viết 1 đoạn Prompt tiếng Anh chi tiết, chuyên nghiệp để tạo ảnh Thumbnail 16:9 chất lượng cao: mô tả các doanh nhân Việt Nam lịch lãm trong trang phục vest công sở, không khí họp kinh doanh trực tuyến hoặc hội trường kết nối doanh nhân sang trọng, gam màu chủ đạo đỏ BNI và xanh navy, ánh sáng ấm áp đẳng cấp.

ĐỊNH DẠNG TRẢ VỀ:
Hãy trả về DUY NHẤT một chuỗi JSON hợp lệ (không kèm theo bất kỳ văn bản giải thích nào ngoài JSON) theo cấu trúc:
{{
  "title": "Tiêu đề bài viết dưới 65 ký tự",
  "labels": ["Nhãn 1", "Nhãn 2"],
  "metaDescription": "Mô tả tìm kiếm tóm tắt dưới 155 ký tự chuẩn SEO",
  "imagePrompt": "English prompt for 16:9 thumbnail image featuring professional Vietnamese business executives networking, BNI corporate red and navy palette...",
  "content": "<div class='seo-post-content'><p>...</p><h2>...</h2>...</div>"
}}
"""

    models = [
        'gemini-3.8-flash',
        'gemini-2.5-flash',
        'gemini-3.5-flash-lite',
        'gemini-2.5-pro',
        'gemini-flash-latest',
        'gemini-pro-latest'
    ]
    last_err = None

    # VÒNG LẶP DỰ PHÒNG QUA TỪNG API KEY (KEY POOL ROTATION)
    for key_idx, current_key in enumerate(api_keys, 1):
        key_masked = current_key[:6] + "..." + current_key[-4:] if len(current_key) > 10 else "***"
        print(f"\n🔑 Thử gọi Gemini với API Key #{key_idx}/{len(api_keys)} [{key_masked}]...")

        key_overloaded = False
        for model in models:
            retry_delays = [3, 7, 15]
            max_attempts = len(retry_delays) + 1

            for attempt in range(1, max_attempts + 1):
                try:
                    if attempt == 1:
                        print(f"👉 Thử tạo bài với Model: {model}...")
                    else:
                        print(f"🔄 Thử lại lần {attempt}/{max_attempts} với Model: {model}...")

                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_key}"
                    
                    gen_config = {
                        "responseMimeType": "application/json"
                    }
                    if '2.5' in model:
                        gen_config["thinkingConfig"] = {"thinkingBudget": 0}

                    body = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": gen_config
                    }

                    resp = requests.post(url, json=body, timeout=120)

                    # 1. Model không hỗ trợ hoặc đã bị nâng cấp (HTTP 404) -> Chuyển ngay model kế tiếp, không tốn thời gian chờ
                    if resp.status_code == 404:
                        print(f"ℹ️ Model {model} không hỗ trợ trên tài khoản này (HTTP 404). Chuyển sang model kế tiếp...")
                        break

                    # 2. Xử lý lỗi tạm thời HTTP 503 (Spike in demand / UNAVAILABLE)
                    if resp.status_code == 503 or "UNAVAILABLE" in resp.text:
                        if attempt < max_attempts:
                            wait_sec = retry_delays[attempt - 1]
                            print(f"⏳ Máy chủ Google đang quá tải tạm thời (HTTP 503 High Demand). Đang chờ {wait_sec} giây trước khi thử lại...")
                            time.sleep(wait_sec)
                            continue
                        else:
                            print(f"⚠️ Model {model} vẫn bị quá tải sau {max_attempts} lần thử. Đang chuyển sang model tiếp theo...")
                            last_err = Exception(f"HTTP 503: {resp.text}")
                            break

                    # 3. Xử lý lỗi HTTP 429 (Hết hạn mức / RESOURCE_EXHAUSTED)
                    if resp.status_code == 429 or "RESOURCE_EXHAUSTED" in resp.text:
                        print(f"⚠️ API Key #{key_idx} gặp sự cố quá tải / hết lượt gọi (HTTP 429 / Quota Exceeded).")
                        key_overloaded = True
                        last_err = Exception(f"HTTP 429: {resp.text}")
                        break

                    if resp.status_code != 200:
                        raise Exception(f"HTTP {resp.status_code}: {resp.text}")

                    res_json = resp.json()
                    candidates = res_json.get('candidates', [])
                    if not candidates:
                        raise Exception(f"Google AI không trả về candidate nào: {resp.text}")
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if not parts:
                        raise Exception(f"Google AI không trả về nội dung text: {resp.text}")
                    raw_text = parts[0].get('text', '')

                    data = robust_json_decode(raw_text)
                    if not data.get('title') or not data.get('content'):
                        raise Exception(f"Dữ liệu bài viết thiếu trường bắt buộc (title/content): {list(data.keys())}")

                    print(f"✅ Gemini AI đã tạo xong bài viết: '{data.get('title')}' thành công với Key #{key_idx} ({model})!")
                    return data
                except Exception as e:
                    last_err = e
                    if "404" in str(e):
                        print(f"ℹ️ Model {model} không hỗ trợ (HTTP 404). Chuyển sang model tiếp theo...")
                        break
                    if "503" in str(e) or "429" in str(e):
                        break
                    print(f"⚠️ Lần {attempt}/{max_attempts} với Model {model} gặp sự cố: {e}")
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    else:
                        print(f"⚠️ Model {model} thất bại sau {max_attempts} lần thử. Đang chuyển model tiếp theo...")
                        break

            if key_overloaded:
                break

        if key_overloaded and key_idx < len(api_keys):
            print(f"🔄 Tự động chuyển sang API Key dự phòng #{key_idx + 1}...")

    raise last_err or Exception("Tất cả các API Key trong pool đều bị lỗi hoặc quá tải!")

# ==============================================================================
# HÀM XÁC THỰC VÀ ĐĂNG BÀI QUA BLOGGER API V3
# ==============================================================================
def get_blogger_service():
    if build is None or Credentials is None:
        raise Exception("Vui lòng cài đặt google-api-python-client và google-auth!")

    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REFRESH_TOKEN):
        raise Exception("Thiếu thông tin Google OAuth (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN)!")

    print(f"🔍 Kiểm tra định dạng Google OAuth:")
    print(f"   - Client ID: {GOOGLE_CLIENT_ID[:12]}...{GOOGLE_CLIENT_ID[-15:]} (Độ dài: {len(GOOGLE_CLIENT_ID)})")
    print(f"   - Client Secret: {GOOGLE_CLIENT_SECRET[:6]}... (Độ dài: {len(GOOGLE_CLIENT_SECRET)})")
    print(f"   - Refresh Token: {GOOGLE_REFRESH_TOKEN[:8]}... (Độ dài: {len(GOOGLE_REFRESH_TOKEN)})")

    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    return build('blogger', 'v3', credentials=creds)

def optimize_html_images_seo(content_html, default_alt="", default_keyword=""):
    """
    Tự động chuẩn hóa SEO cho tất cả thẻ <img> trong bài viết:
    - Bổ sung loading="lazy" (chống nghẽn tải trang)
    - Bổ sung decoding="async" (tăng tốc độ hiển thị nội dung)
    - Tự động điền alt và title chuẩn SEO nếu còn thiếu
    """
    import re
    if not content_html:
        return content_html

    def _append_attr(tag, attr_str):
        if tag.endswith('/>'):
            return tag[:-2].rstrip() + ' ' + attr_str + ' />'
        elif tag.endswith('>'):
            return tag[:-1].rstrip() + ' ' + attr_str + '>'
        return tag + ' ' + attr_str

    def _replace_img(match):
        img_tag = match.group(0)
        
        # 1. Loading lazy (chống nghẽn Core Web Vitals)
        if 'loading=' not in img_tag.lower():
            img_tag = _append_attr(img_tag, 'loading="lazy"')
            
        # 2. Decoding async (tăng tốc độ hiển thị khung chữ)
        if 'decoding=' not in img_tag.lower():
            img_tag = _append_attr(img_tag, 'decoding="async"')

        # 3. Alt text chuẩn SEO
        if 'alt=' not in img_tag.lower() or 'alt=""' in img_tag or "alt=''" in img_tag:
            alt_val = f"{default_keyword} - {default_alt}".strip(" -") if default_keyword else default_alt
            alt_val = alt_val.replace('"', '&quot;')
            img_tag = re.sub(r'\s*alt=["\'][^"\']*["\']', '', img_tag)
            img_tag = _append_attr(img_tag, f'alt="{alt_val}"')

        return img_tag

    return re.sub(r'<img[^>]+>', _replace_img, content_html, flags=re.IGNORECASE)

def post_to_blogger(service, article, original_labels, scheduled_slot=None):
    print(f"\n🚀 Đang gửi bài viết lên Blogger Blog ID: {BLOGGER_BLOG_ID}...")

    # Labels: Ưu tiên tuyệt đối nhãn do người dùng cấu hình (tin-tuc, dich-vu, v.v.)
    post_labels = []
    if original_labels:
        if isinstance(original_labels, str):
            post_labels = [l.strip() for l in original_labels.split(',') if l.strip()]
        elif isinstance(original_labels, list):
            post_labels = [str(l).strip() for l in original_labels if str(l).strip()]

    # Nếu chưa có nhãn, lấy từ AI sinh ra
    if not post_labels:
        art_labels = article.get('labels', [])
        if isinstance(art_labels, str):
            post_labels = [l.strip() for l in art_labels.split(',') if l.strip()]
        elif isinstance(art_labels, list):
            post_labels = [str(l).strip() for l in art_labels if str(l).strip()]

    # Mặc định tối thiểu luôn phải có nhãn hợp lệ để hiển thị trên website
    if not post_labels:
        post_labels = ['tin-tuc']

    print(f"🏷️ Danh sách nhãn (Labels) gắn cho bài viết Blogger: {post_labels}")

    post_body = {
        'kind': 'blogger#post',
        'title': article['title'],
        'content': article['content'],
        'labels': post_labels
    }

    # Đính kèm ảnh đại diện cho bài viết (Blogger Post images metadata)
    thumb_to_attach = article.get('thumbnail_url')
    if not thumb_to_attach:
        import re
        m_img = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', article.get('content', ''))
        if m_img:
            thumb_to_attach = m_img.group(1)
    if thumb_to_attach:
        post_body['images'] = [{'url': thumb_to_attach}]

    # Tự động điền Mô tả tìm kiếm (Search Description chuẩn SEO)
    if article.get('metaDescription'):
        post_body['customMetaData'] = article['metaDescription']

    # Tự động gắn Geotag vị trí Local SEO (Đồng Nai, Việt Nam)
    post_body['location'] = {
        'name': 'Đồng Nai, Việt Nam',
        'lat': 10.9574,
        'lng': 106.8427
    }

    # Handling schedule
    is_draft = (POST_MODE == 'draft')
    if POST_MODE == 'schedule':
        if scheduled_slot:
            post_body['published'] = scheduled_slot.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            vn_time_str = scheduled_slot.strftime('%d/%m/%Y %H:%M')
            print(f"⏰ Hẹn giờ phát hành: {vn_time_str} (Giờ Việt Nam - Khung Giờ Vàng)")
        else:
            scheduled_dt = datetime.now(timezone.utc) + timedelta(hours=SCHEDULE_HOURS_AHEAD)
            post_body['published'] = scheduled_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            print(f"⏰ Hẹn giờ phát hành: {scheduled_dt.strftime('%d/%m/%Y %H:%M UTC')}")

    request = service.posts().insert(
        blogId=BLOGGER_BLOG_ID,
        body=post_body,
        isDraft=is_draft
    )
    result = request.execute()
    post_url = result.get('url') or f"https://www.blogger.com/blog/post/edit/{BLOGGER_BLOG_ID}/{result.get('id')}"
    print(f"🎉 ĐĂNG/LÊN LỊCH THÀNH CÔNG LÊN BLOGGER!")
    print(f"📌 Tiêu đề: {result.get('title')}")
    print(f"🏷️ Nhãn đã đăng: {result.get('labels', post_labels)}")
    print(f"🔗 Link bài: {post_url}")
    return result

# ==============================================================================
# HÀM QUẢN LÝ DANH SÁCH BÀI & LỊCH SỬ & GOOGLE SHEETS
# ==============================================================================
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_updated": None, "total_posted": 0, "history": []}

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_topics_from_google_sheet(sheet_url):
    """
    Tải danh sách đề tài trực tiếp từ Google Sheets qua URL chia sẻ hoặc xuất bản CSV.
    Hỗ trợ URL dạng:
    - https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={GID}
    - https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv
    - Hoặc ID Google Sheet đơn thuần
    """
    import re
    import csv
    import io

    sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
    sheet_id = sheet_id_match.group(1) if sheet_id_match else sheet_url.strip()

    gid_match = re.search(r'[#&?]gid=([0-9]+)', sheet_url)
    gid = gid_match.group(1) if gid_match else '0'

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
    print(f"📊 Đang kết nối Google Sheets (Sheet ID: {sheet_id[:10]}..., GID: {gid})...")

    headers_req = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(csv_url, headers=headers_req, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code}: Không thể tải Google Sheet. Vui lòng kiểm tra quyền chia sẻ 'Bất kỳ ai có liên kết đều có thể xem'!")

    content = resp.content.decode('utf-8-sig', errors='replace')
    
    # Kiểm tra xem Google có chuyển hướng sang trang đăng nhập HTML không (khi chưa Share Public)
    if '<html' in content.lower() or 'accounts.google.com' in content or 'serviceLogin' in content:
        raise Exception("Google Sheets trả về trang đăng nhập HTML thay vì dữ liệu CSV. Nguyên nhân: Bảng tính chưa được BẬT quyền chia sẻ 'Bất kỳ ai có liên kết đều có thể xem' (Anyone with the link can view)!")

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        print("⚠️ Bảng tính Google Sheets hoàn toàn trống (không có dòng dữ liệu nào).")
        return []

    # Quét qua 5 dòng đầu tiên để tự động tìm dòng Header thực sự
    header_row_idx = 0
    col_title = -1
    col_keyword = -1
    col_label = -1
    col_summary = -1
    col_cta = -1
    col_status = -1
    col_id = -1
    col_image = -1

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

    headers = [str(c).strip().lower() for c in rows[header_row_idx]]
    for i, h in enumerate(headers):
        if any(k in h for k in ['tiêu đề', 'tieu de', 'title', 'chủ đề', 'chu de', 'topic']):
            col_title = i
        elif any(k in h for k in ['từ khóa', 'tu khoa', 'keyword']):
            col_keyword = i
        elif any(k in h for k in ['nhãn', 'nhan', 'label', 'chuyên mục', 'chuyen muc', 'category']):
            col_label = i
        elif any(k in h for k in ['gợi ý', 'goi y', 'tóm tắt', 'tom tat', 'nội dung', 'summary', 'note']):
            col_summary = i
        elif any(k in h for k in ['cta', 'link đích', 'link dich']):
            col_cta = i
        elif any(k in h for k in ['trạng thái', 'trang thai', 'status']):
            col_status = i
        elif any(k in h for k in ['stt', 'id']):
            col_id = i
        elif any(k in h for k in ['ảnh', 'anh', 'image', 'thumbnail', 'banner', 'hình ảnh']):
            col_image = i

    if col_title == -1:
        col_title = 1 if len(headers) > 1 else 0

    topics = []
    skipped_status_count = 0
    for row_idx, r in enumerate(rows[header_row_idx + 1:], header_row_idx + 2):  # 1-based index (tiêu đề ở dòng header)
        if not r or len(r) <= col_title:
            continue
        title = r[col_title].strip()
        if not title or title.startswith('#'):
            continue

        status = r[col_status].strip().lower() if col_status != -1 and len(r) > col_status else ''
        if any(s in status for s in ['đã đăng', 'da dang', 'posted', 'done', 'đã lên lịch', 'da len lich', 'scheduled', 'hoàn thành', 'hoan thanh']):
            skipped_status_count += 1
            continue

        keyword = r[col_keyword].strip() if col_keyword != -1 and len(r) > col_keyword else ''
        raw_label = r[col_label].strip() if col_label != -1 and len(r) > col_label else ''
        summary = r[col_summary].strip() if col_summary != -1 and len(r) > col_summary else ''
        cta = r[col_cta].strip() if col_cta != -1 and len(r) > col_cta and r[col_cta].startswith('http') else REGISTER_URL
        image_val = r[col_image].strip() if col_image != -1 and len(r) > col_image else ''

        if raw_label:
            labels = [l.strip() for l in raw_label.replace(';', ',').split(',') if l.strip()]
        else:
            labels = [determine_label(title, summary, '')]

        row_id_val = r[col_id].strip() if col_id != -1 and len(r) > col_id else str(row_idx)

        topics.append({
            "topic": title,
            "keyword": keyword,
            "labels": labels,
            "summary": summary,
            "cta_url": cta,
            "image_url": image_val,
            "sheet_row": row_idx,
            "row_id": row_id_val,
            "source": "google_sheets"
        })

    print(f"✅ Đã tải thành công {len(topics)} đề tài chưa đăng từ Google Sheets! (Đã bỏ qua {skipped_status_count} bài đã đăng/lên lịch)")
    return topics

def send_telegram_notification(topic, status_text, post_url, published_time, labels, row_index=None):
    """
    Gửi thông báo báo cáo trực tiếp tới nhóm Telegram ngay khi đăng/lên lịch thành công
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        labels_str = ", ".join(labels) if isinstance(labels, list) else str(labels)
        text = (
            f"🚀 <b>[BLOGGER AUTO-POSTER] ĐĂNG BÀI THÀNH CÔNG</b>\n\n"
            f"📌 <b>Tiêu đề:</b> {topic}\n"
            f"🏷️ <b>Nhãn:</b> <code>{labels_str}</code>\n"
            f"⏰ <b>Thời gian:</b> {published_time}\n"
        )
        if row_index and row_index > 0:
            text += f"📊 <b>Google Sheet:</b> Đã cập nhật dòng #{row_index} (<b>{status_text}</b>)\n"
        if post_url:
            text += f"🔗 <b>Link bài viết:</b> <a href=\"{post_url}\">Bấm xem bài viết ngay</a>\n"
        text += "\n💡 <i>Hệ thống AI Blogger Cloud LuViet đã xuất bản hoàn tất!</i>"

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            print(f"📱 Đã gửi thông báo báo cáo tới Telegram ({TELEGRAM_CHAT_ID}) thành công!")
        else:
            print(f"⚠️ Gửi thông báo Telegram thất bại (HTTP {resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"⚠️ Lỗi khi gửi thông báo Telegram: {e}")

def send_raw_telegram_message(text):
    """
    Gửi tin nhắn Telegram tùy biến (dùng cho thông báo Google Indexing, cảnh báo lỗi,...)
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            print(f"📱 Đã gửi thông báo Indexing tới Telegram thành công!")
    except Exception as e:
        print(f"⚠️ Lỗi khi gửi thông báo Telegram Indexing: {e}")

def notify_google_sheet(item, result, scheduled_slot=None):
    """
    Gửi thông báo cập nhật kết quả lên Google Sheet qua Webhook Google Apps Script
    """
    if not GOOGLE_SHEET_WEBHOOK_URL:
        return
    try:
        pub_time = result.get('published')
        if scheduled_slot:
            pub_time = scheduled_slot.strftime('%d/%m/%Y %H:%M') + " (Giờ VN)"

        post_url = result.get('url') or f"https://www.blogger.com/blog/post/edit/{BLOGGER_BLOG_ID}/{result.get('id')}"
        status_text = "Đã lên lịch" if POST_MODE == 'schedule' else "Đã đăng"

        payload = {
            "row_index": item.get('sheet_row'),
            "row_id": item.get('row_id'),
            "topic": item.get('topic'),
            "status": status_text,
            "post_url": post_url,
            "post_id": result.get('id'),
            "published": pub_time,
            "labels": result.get('labels', item.get('labels', []))
        }
        resp = requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=payload, timeout=30)
        if resp.status_code == 200:
            print("📊 Đã cập nhật trạng thái bài viết lên Google Sheet qua Webhook thành công!")
    except Exception as e:
        print(f"⚠️ Gửi cập nhật Webhook Google Sheet thất bại: {e}")

def get_next_topics(count=1):
    history = load_history()
    posted_topics = set(item['topic'].lower().strip() for item in history.get('history', []))

    all_candidates = []

    # 1. Ưu tiên đọc từ Google Sheets nếu có cấu hình GOOGLE_SHEET_URL
    if GOOGLE_SHEET_URL:
        print(f"🔗 Phát hiện cấu hình GOOGLE_SHEET_URL: {GOOGLE_SHEET_URL[:45]}...")
        try:
            candidates_from_sheet = fetch_topics_from_google_sheet(GOOGLE_SHEET_URL)
            if candidates_from_sheet:
                all_candidates = candidates_from_sheet
            else:
                print("⚠️ Bảng tính Google Sheets không có đề tài nào hợp lệ hoặc tất cả đã được đánh dấu 'Đã đăng'.")
                print("🔄 Tự động chuyển sang file dự phòng topics.txt...")
        except Exception as e:
            print(f"⚠️ LỖI ĐỒNG BỘ GOOGLE SHEETS: {e}")
            print("🔄 Tự động chuyển sang file dự phòng topics.txt...")
    else:
        print("💡 Chưa cấu hình biến môi trường GOOGLE_SHEET_URL (trên GitHub Secrets hoặc file .env).")
        print("📂 Mặc định chuyển sang nguồn đề tài từ file cục bộ: topics.txt")

    # 2. Nếu không có Google Sheet hoặc danh sách rỗng, đọc từ topics.txt
    if not all_candidates:
        if not os.path.exists(TOPICS_FILE):
            raise Exception(f"Không tìm thấy file danh sách đề tài: {TOPICS_FILE}")

        with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        for line in lines:
            parts = [p.strip() for p in line.split('|')]
            raw_topic = parts[0]
            summary = parts[1] if len(parts) >= 2 else ''
            cta_url = REGISTER_URL
            raw_tags = ''

            if len(parts) >= 3:
                if parts[2].startswith('http'):
                    cta_url = parts[2]
                else:
                    raw_tags = parts[2]
            if len(parts) >= 4:
                if parts[3].startswith('http'):
                    cta_url = parts[3]
                else:
                    raw_tags = parts[3]

            if raw_tags:
                labels = [l.strip() for l in raw_tags.split(',') if l.strip()]
            else:
                labels = [determine_label(raw_topic, summary, '')]

            all_candidates.append({
                "topic": raw_topic,
                "labels": labels,
                "summary": summary,
                "cta_url": cta_url,
                "source": "topics.txt"
            })

    # Lọc các đề tài chưa đăng trong lịch sử posted_history.json
    selected = []
    for item in all_candidates:
        top_name = item['topic'].lower().strip()
        if top_name not in posted_topics:
            selected.append(item)
            if len(selected) == count:
                break

    return selected, history

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
def main():
    print("=" * 65)
    print("🤖 BLOGGER GEMINI AI CLOUD AUTO-POSTER (SMART SCHEDULE ENGINE)")
    print(f"⏰ Thời gian khởi chạy: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⚙️ Chế độ phát hành: {POST_MODE.upper()}")
    print(f"📚 Số lượng bài cần xử lý đợt này: {POSTS_COUNT} bài")
    print("=" * 65)

    api_keys = get_api_key_pool()
    if not api_keys:
        print("❌ Lỗi: Thiếu biến môi trường GEMINI_API_KEY (hoặc GEMINI_API_KEYS)!")
        sys.exit(1)
    print(f"🔑 Tìm thấy {len(api_keys)} Gemini API Key sẵn sàng trong Pool.")
    if not BLOGGER_BLOG_ID:
        print("❌ Lỗi: Thiếu biến môi trường BLOGGER_BLOG_ID!")
        sys.exit(1)

    # 1. Tìm các đề tài tiếp theo chưa đăng
    selected_topics, history = get_next_topics(count=POSTS_COUNT)
    if not selected_topics:
        source_name = "Google Sheets" if GOOGLE_SHEET_URL else "topics.txt"
        print(f"ℹ️ Tất cả đề tài từ {source_name} đều đã được đăng bài hoặc không còn bài mới trong danh sách!")
        print(f"💡 Hãy thêm các đề tài mới vào {source_name} để hệ thống tiếp tục chạy.")
        return

    # 2. Tính toán trước khung giờ vàng hẹn giờ (nếu ở chế độ schedule)
    slots = []
    if POST_MODE == 'schedule':
        slots = get_next_schedule_slots(count=len(selected_topics), existing_history=history)

    print(f"\n📋 KẾ HOẠCH XỬ LÝ {len(selected_topics)} BÀI VIẾT:")
    for idx, item in enumerate(selected_topics, 1):
        if POST_MODE == 'schedule' and idx <= len(slots):
            slot_vn = slots[idx - 1].strftime('%d/%m/%Y %H:%M')
            print(f"  [{idx}/{len(selected_topics)}] '{item['topic']}' ➔ Lên lịch xuất bản: {slot_vn} (Giờ VN)")
        else:
            print(f"  [{idx}/{len(selected_topics)}] '{item['topic']}' ➔ Xuất bản trực tiếp ngay bây giờ")

    # 3. Khởi tạo dịch vụ Blogger API
    service = get_blogger_service()

    # 4. Viết và đăng từng bài theo kế hoạch
    success_count = 0
    for idx, item in enumerate(selected_topics, 1):
        topic = item['topic']
        labels = item['labels']
        summary = item['summary']
        cta_url = item['cta_url']
        scheduled_slot = slots[idx - 1] if POST_MODE == 'schedule' and idx <= len(slots) else None

        print("\n" + "=" * 65)
        print(f"📝 BẮT ĐẦU XỬ LÝ BÀI [{idx}/{len(selected_topics)}]: '{topic}'")
        if scheduled_slot:
            print(f"⏰ Hẹn giờ phát hành: {scheduled_slot.strftime('%d/%m/%Y %H:%M')} (Giờ VN)")
        print("=" * 65)

        try:
            # 4.1. Gọi Gemini AI sinh bài
            article = generate_seo_article(topic, labels, summary=summary, cta_url=cta_url)

            # 4.2. Tự động sinh ảnh Thumbnail Doanh Nhân và gắn vào đầu bài viết Blogger
            thumb_url = None
            if create_post_thumbnail:
                try:
                    custom_img = item.get('image_url', '')
                    art_title = article.get('title') or topic
                    repo_name = os.environ.get('GITHUB_REPOSITORY', '')
                    thumb_url = create_post_thumbnail(
                        title=art_title,
                        summary=summary,
                        keyword=item.get('keyword', ''),
                        custom_image_url=custom_img,
                        api_key=api_keys,
                        repo_full_name=repo_name
                    )
                    if thumb_url:
                        clean_title_esc = art_title.replace('"', '&quot;')
                        kw = item.get('keyword', '').strip()
                        if kw and kw.lower() not in art_title.lower():
                            seo_alt = f"{kw.title()} - {clean_title_esc}"
                        else:
                            seo_alt = clean_title_esc
                        seo_title = f"Hình ảnh: {clean_title_esc} - Tối ưu hóa tự động"
                        caption_text = clean_title_esc

                        banner_html = (
                            f'<figure class="separator post-featured-image" style="clear: both; text-align: center; margin: 0 0 35px 0;">\n'
                            f'  <a href="{thumb_url}" style="display: inline-block; max-width: 100%; text-decoration: none;">\n'
                            f'    <img src="{thumb_url}" alt="{seo_alt}" title="{seo_title}" width="1200" height="675" loading="lazy" decoding="async" border="0" style="max-width: 100%; height: auto; border-radius: 14px; box-shadow: 0 8px 30px rgba(0,0,0,0.15); display: block; margin: 0 auto;" />\n'
                            f'  </a>\n'
                            f'  <figcaption style="font-size: 13.5px; color: #64748b; margin-top: 10px; font-style: italic; text-align: center;">\n'
                            f'    Hình 1: {caption_text}\n'
                            f'  </figcaption>\n'
                            f'</figure>\n'
                        )
                        raw_content = banner_html + article.get('content', '')
                        article['content'] = optimize_html_images_seo(raw_content, default_alt=clean_title_esc, default_keyword=kw)
                        article['thumbnail_url'] = thumb_url
                        print(f"🖼️ Đã gắn ảnh Thumbnail Doanh Nhân (Nén WebP + SEO chuẩn Google) vào bài viết Blogger thành công!")
                except Exception as img_err:
                    print(f"⚠️ Quá trình tạo Thumbnail tự động gặp sự cố nhẹ: {img_err}")

            # 4.3. Đăng / Lên lịch lên Blogger
            result = post_to_blogger(service, article, labels, scheduled_slot=scheduled_slot)

            # 4.3. Ghi nhận lịch sử ngay lập tức
            history_entry = {
                "topic": topic,
                "title": result.get('title'),
                "post_id": result.get('id'),
                "url": result.get('url'),
                "published": result.get('published'),
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "mode": POST_MODE
            }
            history['history'].append(history_entry)
            history['total_posted'] = len(history['history'])
            history['last_updated'] = datetime.now(timezone.utc).isoformat()
            save_history(history)
            success_count += 1
            print(f"\n💾 Đã lưu lịch sử bài #{idx}. Tổng cộng đã đăng: {history['total_posted']} bài.")

            status_text = "Đã lên lịch" if POST_MODE == 'schedule' else "Đã đăng"
            pub_time_display = scheduled_slot.strftime('%d/%m/%Y %H:%M') + " (Giờ VN - Khung Giờ Vàng)" if scheduled_slot else result.get('published', '')
            post_url = result.get('url') or f"https://www.blogger.com/blog/post/edit/{BLOGGER_BLOG_ID}/{result.get('id')}"

            # 4.4. Gửi thông báo trực tiếp tới Telegram
            send_telegram_notification(
                topic=item.get('topic'),
                status_text=status_text,
                post_url=post_url,
                published_time=pub_time_display,
                labels=result.get('labels', item.get('labels', [])),
                row_index=item.get('sheet_row')
            )

            # 4.5. Thông báo cập nhật Google Sheets (nếu có cấu hình Webhook)
            notify_google_sheet(item, result, scheduled_slot=scheduled_slot)

        except Exception as e:
            print(f"❌ Xảy ra lỗi khi xử lý bài '{topic}': {e}")
            import traceback
            traceback.print_exc()

        # Nghỉ giữa các bài nếu còn bài kế tiếp
        if idx < len(selected_topics):
            print(f"\n⏳ Nghỉ {DELAY_SECONDS} giây trước khi viết bài tiếp theo để bảo vệ hạn ngạch API...")
            time.sleep(DELAY_SECONDS)

    print("\n" + "=" * 65)
    print(f"🎉 HOÀN THÀNH TIẾN TRÌNH: Đã tạo và lên lịch thành công {success_count}/{len(selected_topics)} bài!")
    print("=" * 65)

    # ==============================================================================
    # 5. TỰ ĐỘNG QUÉT & GỬI GOOGLE INDEXING CHO CÁC BÀI ĐÃ XUẤT BẢN THÀNH CÔNG (LIVE)
    # ==============================================================================
    try:
        from google_indexer import process_auto_indexing
        indexed_count = process_auto_indexing(history, notify_telegram_func=send_raw_telegram_message)
        if indexed_count > 0:
            save_history(history)
    except Exception as idx_err:
        print(f"⚠️ Quá trình tự động Google Indexing gặp lỗi: {idx_err}")

if __name__ == '__main__':
    main()
