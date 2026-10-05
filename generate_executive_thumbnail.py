#!/usr/bin/env python3
"""
Bộ tạo ảnh Thumbnail YouTube Chuẩn Chuyển Đổi Cao (High-Converting YouTube Thumbnail)
Đặc điểm:
- Nền ảnh sinh động 100% bám sát tiêu đề và nội dung bài viết (Thematic Dynamic Background)
- Thư viện 36+ ảnh nền doanh nhân chất lượng cao (12 chủ đề x 3 góc chụp) + Fallback đồ họa vector procedural
- Tự động nhận diện chủ đề: BNI Networking, Họp Zoom Online, Trao Referral, Độc quyền ngành, Văn hóa Cho Là Nhận, v.v.
- Chữ 2 hàng, mỗi hàng tối đa 3 chữ, chữ TO cực nét, viền sáng phát quang (Neon Glow) + Khối 3D
- Badge danh mục thông minh biến đổi linh hoạt theo tiêu đề
- Nén tự động chuẩn WebP (<80KB) + JPEG Progressive chuẩn Google Core Web Vitals
"""

import os
import sys
import re
import math
import random
import hashlib
import requests
import io
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Ensure utf-8 stdout on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==============================================================================
# BỘ SƯU TẬP ẢNH NỀN THEO CHỦ ĐỀ CHUẨN DOANH NHÂN & CÔNG NGHỆ (1920x1080)
# ==============================================================================
THEME_PHOTOS = {
    'bni_networking': [
        'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1920&q=80',  # Phòng họp lãnh đạo cao cấp
        'https://images.unsplash.com/photo-1515187029135-18ee286d815b?auto=format&fit=crop&w=1920&q=80',  # Hội nghị kết nối doanh nhân
        'https://images.unsplash.com/photo-1528605248644-14dd04022da1?auto=format&fit=crop&w=1920&q=80',  # Bàn tiệc giao thương B2B
    ],
    'online_zoom': [
        'https://images.unsplash.com/photo-1588196749597-9ff075ee6b5b?auto=format&fit=crop&w=1920&q=80',  # Họp video Zoom trực tuyến
        'https://images.unsplash.com/photo-1593642532400-2682810df593?auto=format&fit=crop&w=1920&q=80',  # Bàn làm việc laptop hiện đại
        'https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=1920&q=80',  # Kết nối thảo luận từ xa
    ],
    'handshake_referral': [
        'https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1920&q=80',  # Bắt tay hợp tác doanh nhân
        'https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=1920&q=80',  # Doanh nhân đĩnh đạc tự tin
        'https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1920&q=80',  # Thỏa thuận hợp tác thành công
    ],
    'sales_growth': [
        'https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=1920&q=80',  # Biểu đồ phân tích tài chính
        'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1920&q=80',  # Dashboard tăng trưởng doanh số
        'https://images.unsplash.com/photo-1553729459-efe14ef6055d?auto=format&fit=crop&w=1920&q=80',  # Bứt phá doanh thu kỷ lục
    ],
    'presentation_pitch': [
        'https://images.unsplash.com/photo-1475721027785-f74eccf877e2?auto=format&fit=crop&w=1920&q=80',  # Thuyết trình trước hội trường
        'https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=1920&q=80',  # Diễn thuyết sân khấu hội nghị
        'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1920&q=80',  # Giới thiệu sản phẩm dự án
    ],
    'global_digital': [
        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80',  # Quả địa cầu kết nối mạng lưới số
        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1920&q=80',  # Mạng lưới công nghệ toàn cầu
        'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1920&q=80',  # Hạ tầng kết nối kỷ nguyên số
    ],
    'leadership_culture': [
        'https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1920&q=80',  # Tinh thần đồng đội gắn kết
        'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1920&q=80',  # Ban lãnh đạo phụng sự
        'https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1920&q=80',  # Nhà lãnh đạo bản lĩnh
    ],
    'diamond_success': [
        'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1920&q=80',  # Cúp vàng danh dự chiến thắng
        'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1920&q=80',  # Hào quang hoàng kim kim cương
        'https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1920&q=80',  # Ánh sáng điện ảnh đẳng cấp
    ],
    'strategy_monopoly': [
        'https://images.unsplash.com/photo-1529699211952-734e80c4d42b?auto=format&fit=crop&w=1920&q=80',  # Quân cờ vua chiến lược độc quyền
        'https://images.unsplash.com/photo-1586165368502-1bad197a6461?auto=format&fit=crop&w=1920&q=80',  # Bàn cờ thế chiến lược dẫn đầu
        'https://images.unsplash.com/photo-1508739773434-c26b3d09e071?auto=format&fit=crop&w=1920&q=80',  # Tầm nhìn chiến lược từ tòa cao ốc
    ],
    'training_university': [
        'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=1920&q=80',  # Thư viện tri thức doanh nhân
        'https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=1920&q=80',  # Giảng đường đào tạo quốc tế
        'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=1920&q=80',  # Học tập đổi mới tư duy
    ],
    'retail_b2b': [
        'https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1920&q=80',  # Không gian bán lẻ cao cấp
        'https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=1920&q=80',  # Cửa hàng thương mại sang trọng
        'https://images.unsplash.com/photo-1556742044-3c52d6e88c62?auto=format&fit=crop&w=1920&q=80',  # Quầy thanh toán POS hiện đại
    ],
    'young_entrepreneur': [
        'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1920&q=80',  # Đội ngũ khởi nghiệp trẻ trung
        'https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&w=1920&q=80',  # Không gian co-working sáng tạo
        'https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=1920&q=80',  # Doanh nhân số thế hệ mới
    ]
}

def detect_topic_theme(title, summary="", keyword=""):
    """
    Phân loại đề tài vào 12 chủ đề hình ảnh tương ứng dựa trên tiêu đề, tóm tắt và từ khóa
    """
    text = f"{title} {summary} {keyword}".lower()

    if any(k in text for k in ['zoom', 'họp online', 'online thay vì offline', 'trực tuyến', 'giữ lửa năng lượng']):
        return 'online_zoom'
    if any(k in text for k in ['độc quyền', 'doc quyen', 'thâu tóm', 'bảo vệ ngành']):
        return 'strategy_monopoly'
    if any(k in text for k in ['referral', 'cơ hội kinh doanh', 'trao referral', 'cấp độ 4, 5', 'chắc chắn thành tiền']):
        return 'handshake_referral'
    if any(k in text for k in ['30 giây', '30s', 'showcase 8 phút', '8 phút', 'thuyết trình', 'diễn thuyết', 'pitch']):
        return 'presentation_pitch'
    if any(k in text for k in ['toàn quốc', 'xuyên biên giới', 'quốc tế', 'bni global', 'kỷ nguyên số', 'đột phá kỷ nguyên']):
        return 'global_digital'
    if any(k in text for k in ['cho là nhận', 'givers gain', 'giá trị cốt lõi', 'văn hóa bni', 'ban điều hành', 'leadership team']):
        return 'leadership_culture'
    if any(k in text for k in ['kim cương', 'thank you for closed business', 'tyfcb', 'cảm ơn bằng doanh thu', 'doanh thu kỷ lục', 'bứt phá']):
        return 'diamond_success'
    if any(k in text for k in ['kpi', 'đo lường', 'doanh số', 'tăng trưởng', 'doanh thu', 'chi phí', 'đầu tư', 'sinh lời', 'hợp đồng']):
        return 'sales_growth'
    if any(k in text for k in ['học tập suốt đời', 'đào tạo', 'university', 'tri thức', 'kỹ năng']):
        return 'training_university'
    if any(k in text for k in ['doanh nhân trẻ', 'thế hệ mới', 'khởi nghiệp', 'sáng lập']):
        return 'young_entrepreneur'
    if any(k in text for k in ['bán lẻ', 'sản phẩm', 'dịch vụ', 'giỏ quà', 'pos', 'hóa đơn']):
        return 'retail_b2b'

    return 'bni_networking'

def create_procedural_background(theme, w=1920, h=1080):
    """
    Sinh ảnh nền đồ họa thuật toán (Procedural Vector Background) độc bản theo chủ đề:
    - Gradient chuyển sắc sang trọng phù hợp đề tài
    - Mạng lưới chòm sao kết nối (Constellation Network Nodes) biểu trưng BNI Networking
    - Ánh sáng tỏa hào quang (Radial Glow Flare)
    - Hoàn toàn độc lập, không phụ thuộc vào internet hay API bên ngoài
    """
    palettes = {
        'online_zoom': ((8, 15, 32), (14, 116, 144), (6, 182, 212)),
        'strategy_monopoly': ((15, 10, 28), (88, 28, 135), (234, 179, 8)),
        'handshake_referral': ((5, 25, 20), (4, 120, 87), (245, 158, 11)),
        'leadership_culture': ((30, 10, 15), (159, 18, 57), (251, 191, 36)),
        'diamond_success': ((10, 15, 40), (30, 64, 175), (147, 197, 253)),
        'sales_growth': ((10, 20, 35), (22, 101, 52), (52, 211, 153)),
        'global_digital': ((5, 12, 28), (3, 105, 161), (56, 189, 248)),
        'presentation_pitch': ((18, 12, 30), (126, 34, 206), (250, 204, 21)),
        'training_university': ((12, 20, 32), (15, 118, 110), (94, 234, 212)),
        'retail_b2b': ((25, 15, 12), (180, 83, 9), (253, 186, 116)),
        'young_entrepreneur': ((10, 18, 30), (79, 70, 229), (167, 139, 250)),
        'bni_networking': ((12, 18, 38), (153, 27, 27), (250, 204, 21))
    }
    c_start, c_end, c_accent = palettes.get(theme, palettes['bni_networking'])

    # 1. Vẽ Gradient nền
    base = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(base)
    for y in range(h):
        ratio = y / h
        r = int(c_start[0] + (c_end[0] - c_start[0]) * ratio)
        g = int(c_start[1] + (c_end[1] - c_start[1]) * ratio)
        b = int(c_start[2] + (c_end[2] - c_start[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # 2. Layer mạng lưới các điểm kết nối (Network Constellation Nodes)
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    # Đặt các hạt mạng lưới ở nửa bên phải (x > 820) để bên trái thoáng cho chữ to
    random.seed(int(c_start[0] * 100 + c_end[1]))
    nodes = [(random.randint(820, w - 70), random.randint(70, h - 70)) for _ in range(26)]
    for i, p1 in enumerate(nodes):
        for p2 in nodes[i + 1:]:
            dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            if dist < 320:
                alpha = int(90 * (1 - dist / 320))
                ov_draw.line([p1, p2], fill=(c_accent[0], c_accent[1], c_accent[2], alpha), width=2)

    for x, y in nodes:
        rad = random.randint(4, 9)
        ov_draw.ellipse(
            [x - rad, y - rad, x + rad, y + rad],
            fill=(255, 255, 255, 200),
            outline=(c_accent[0], c_accent[1], c_accent[2], 240),
            width=2
        )

    # 3. Quầng sáng phát quang (Radial Light Flare)
    flare = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(flare)
    fx, fy = int(w * 0.75), int(h * 0.38)
    for r in range(460, 0, -10):
        alpha = int(45 * (1 - r / 460))
        f_draw.ellipse([fx - r, fy - r, fx + r, fy + r], fill=(c_accent[0], c_accent[1], c_accent[2], alpha))
    flare = flare.filter(ImageFilter.GaussianBlur(30))

    base = base.convert('RGBA')
    base = Image.alpha_composite(base, flare)
    base = Image.alpha_composite(base, overlay)
    return base

def download_thematic_background(theme, title, output_path):
    """
    Tải ảnh nền chất lượng cao từ CDN Unsplash theo chủ đề đã nhận diện.
    - Dùng hash của tiêu đề để chọn ảnh khác nhau cho các bài cùng chủ đề
    - Nếu tải thất bại hoặc mất mạng, tự động chuyển sang sinh ảnh thuật toán Procedural
    """
    photo_urls = THEME_PHOTOS.get(theme, THEME_PHOTOS['bni_networking'])
    # Băm tiêu đề để chọn góc chụp phong phú, ổn định cho từng bài
    h_val = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
    selected_url = photo_urls[h_val % len(photo_urls)]

    try:
        print(f"🖼️ Đang tải ảnh nền sinh động theo chủ đề [{theme.upper()}]...")
        resp = requests.get(selected_url, timeout=12, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        if resp.status_code == 200:
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            img.save(output_path, "JPEG", quality=90)
            print(f"✅ Đã tải ảnh nền doanh nhân thành công ({len(resp.content) / 1024:.1f} KB)")
            return True
        else:
            print(f"⚠️ Tải ảnh nền thất bại (HTTP {resp.status_code}). Chuyển sang sinh ảnh thuật toán...")
    except Exception as e:
        print(f"⚠️ Kết nối tải ảnh nền gặp sự cố ({e}). Chuyển sang sinh ảnh thuật toán...")

    # Fallback: Tự động sinh ảnh thuật toán procedural không cần mạng
    try:
        p_img = create_procedural_background(theme)
        p_img.convert("RGB").save(output_path, "JPEG", quality=92)
        print(f"✨ Đã tự động kiến tạo ảnh nền Gradient đồ họa chuẩn chủ đề [{theme.upper()}]!")
        return True
    except Exception as e:
        print(f"⚠️ Lỗi sinh nền đồ họa ({e})")
        return False

def get_best_font(size, bold=True):
    """Tìm font tiếng Việt Unicode chuẩn đẹp nhất trên hệ thống"""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Roboto-Bold.ttf"),
        r"C:\Users\Admin\.gemini\antigravity-ide\scratch\blogger-auto-cloud\Roboto-Bold.ttf",
        r"D:\blogger-auto-cloud\Roboto-Bold.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_glowing_text(base_img, draw, pos, text, font, text_color, glow_color=(255, 215, 0, 220), glow_radius=22, stroke_color=(0, 0, 0, 255), stroke_width=9, depth=14):
    """
    Vẽ chữ phong cách YouTube Thumbnail:
    - Viền sáng phát quang tỏa nhiệt (Glowing Aura / Neon Glow)
    - Viền nét sắc đen đậm (Dark Stroke) tách biệt khỏi nền
    - Khối 3D dày đổ bóng tạo chiều sâu
    - Mặt chữ màu sắc tương phản cao
    """
    x, y = pos
    target_w, target_h = base_img.size

    # 1. Quầng sáng phát quang (Luminous Aura Glow)
    if glow_radius > 0 and glow_color:
        glow_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        glow_draw.text((x, y), text, font=font, fill=glow_color, stroke_width=stroke_width + 12, stroke_fill=glow_color)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow_radius))
        # Ghép 2 lần để ánh sáng đậm nét, bắt mắt
        base_img.alpha_composite(glow_layer)
        base_img.alpha_composite(glow_layer)

    # 2. Khối nổi 3D & Viền Stroke đen
    txt_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    t_draw = ImageDraw.Draw(txt_layer)

    shadow_color = (10, 10, 15, 245)
    for d in range(depth, 0, -1):
        t_draw.text((x + d, y + d), text, font=font, fill=shadow_color, stroke_width=stroke_width, stroke_fill=shadow_color)

    # Viền đen sắc nét + Mặt chữ chính
    t_draw.text((x, y), text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color)

    base_img.alpha_composite(txt_layer)

def extract_smart_hook(title, summary="", keyword=""):
    """
    Trích xuất đúng 2 hàng chữ giật tít chuẩn YouTube + Badge danh mục bám sát tiêu đề:
    - Đúng 2 hàng
    - Mỗi hàng tối đa 3 chữ (len <= 3 words)
    - Chữ to, ngắn gọn, biến đổi sinh động theo từng đề tài
    """
    clean_title = re.sub(r'\[.*?\]|\(.*?\)|2026|Năm 2026', '', title).strip()
    corpus = (clean_title + " " + summary + " " + keyword).lower()

    # Nhận diện theo từ khóa chuyên biệt bám sát 30 đề tài BNI Topaz
    if any(k in corpus for k in ['kim cương', 'chapter kim cương']):
        return "CHAPTER BNI", "KIM CƯƠNG", "DANH HIỆU CAO QUÝ"
    if any(k in corpus for k in ['power team']):
        return "POWER TEAM", "NHÂN DOANH SỐ", "ĐÒN BẨY B2B"
    if any(k in corpus for k in ['showcase 8 phút', '8 phút']):
        return "SHOWCASE 8 PHÚT", "THUYẾT PHỤC CEO", "BÀI DIỄN THUYẾT"
    if any(k in corpus for k in ['30 giây', '30s']):
        return "THUYẾT TRÌNH 30S", "CHỐT ĐƠN NGAY", "KỸ NĂNG PITCH"
    if any(k in corpus for k in ['1-2-1', 'one to one']):
        return "QUY TRÌNH 1-2-1", "HỢP ĐỒNG TỶ ĐỒNG", "KẾT NỐI SÂU"
    if any(k in corpus for k in ['độc quyền', 'doc quyen']):
        return "VỊ THẾ ĐỘC QUYỀN", "TRONG CHAPTER", "LỢI THẾ CẠNH TRANH"
    if any(k in corpus for k in ['cho là nhận', 'givers gain']):
        return "CHO LÀ NHẬN", "GIVERS GAIN", "VĂN HÓA BNI"
    if any(k in corpus for k in ['thank you for closed business', 'cảm ơn bằng doanh thu', 'tyfcb']):
        return "CẢM ƠN DOANH THU", "TYFCB TIỀN TỶ", "VĂN HÓA BIẾT ƠN"
    if any(k in corpus for k in ['trao referral', 'nghệ thuật trao referral']):
        return "TRAO REFERRAL", "CHẮC CHẮN THÀNH TIỀN", "CƠ HỘI KINH DOANH"
    if any(k in corpus for k in ['nhận hàng trăm', 'nhận referral', 'referral chất lượng']):
        return "HÀNG TRĂM REFERRAL", "TĂNG TRƯỞNG GẤP 3", "KẾT NỐI B2B"
    if any(k in corpus for k in ['20 bước']):
        return "QUY TRÌNH 20 BƯỚC", "CHUẨN QUỐC TẾ", "VẬN HÀNH BNI"
    if any(k in corpus for k in ['đội ngũ bán hàng 50 người', '50 người miễn phí']):
        return "ĐỘI BÁN HÀNG", "50 GIÁM ĐỐC", "BÁN HÀNG HỘ BẠN"
    if any(k in corpus for k in ['toàn quốc']):
        return "MỞ RỘNG TOÀN QUỐC", "KHÔNG CẦN CHI NHÁNH", "CHIẾN LƯỢC 0 ĐỒNG"
    if any(k in corpus for k in ['xuyên biên giới', 'quốc tế']):
        return "KẾT NỐI TOÀN CẦU", "XUẤT KHẨU QUỐC TẾ", "BNI GLOBAL"
    if any(k in corpus for k in ['thương hiệu cá nhân']):
        return "THƯƠNG HIỆU DOANH NHÂN", "UY TÍN ĐỈNH CAO", "NÂNG TẦM VỊ THẾ"
    if any(k in corpus for k in ['doanh nhân trẻ']):
        return "DOANH NHÂN TRẺ", "BỨT PHÁ KHỞI NGHIỆP", "THẾ HỆ MỚI"
    if any(k in corpus for k in ['học tập suốt đời', 'university']):
        return "HỌC TẬP SUỐT ĐỜI", "BNI UNIVERSITY", "TRI THỨC ĐỈNH CAO"
    if any(k in corpus for k in ['ban điều hành', 'leadership team']):
        return "BAN ĐIỀU HÀNH", "DẪN DẮT BỨT PHÁ", "PHỤNG SỰ CHAPTER"
    if any(k in corpus for k in ['chuyển đổi số']):
        return "CHUYỂN ĐỔI SỐ B2B", "GIAO THƯƠNG ĐỘT PHÁ", "KỶ NGUYÊN SỐ"
    if any(k in corpus for k in ['smes', 'doanh nghiệp vừa & nhỏ']):
        return "GIẢI PHÁP SMES", "HẾT CÔ ĐƠN", "TĂNG TRƯỞNG NHANH"
    if any(k in corpus for k in ['giá trị cốt lõi', '7 giá trị']):
        return "7 GIÁ TRỊ CỐT LÕI", "BẢN LĨNH DOANH NHÂN", "BỀN VỮNG"
    if any(k in corpus for k in ['khách mời', 'sáng thứ năm', 'tham quan']):
        return "THAM QUAN BNI", "KẾT NỐI 50+ CEO", "SÁNG THỨ NĂM"
    if any(k in corpus for k in ['chi phí', 'đầu tư hay chi phí']):
        return "CHI PHÍ BNI", "ĐẦU TƯ SINH LỜI", "PHÂN TÍCH BÓC TÁCH"
    if any(k in corpus for k in ['kpi', 'đo lường']):
        return "ĐO LƯỜNG KPI", "TĂNG TRƯỞNG DOANH THU", "HIỆU QUẢ THỰC TẾ"
    if any(k in corpus for k in ['bán lẻ']):
        return "DOANH NGHIỆP BÁN LẺ", "TIẾP CẬN DOANH NHÂN", "GIỎ QUÀ B2B"
    if any(k in corpus for k in ['họp online', 'online thay vì offline', 'zoom', 'tiết kiệm 3 giờ', 'giữ lửa năng lượng']):
        return "HỌP BNI ONLINE", "TIẾT KIỆM 3 GIỜ", "TỐI ƯU CHI PHÍ"
    if any(k in corpus for k in ['kỷ nguyên số', 'đột phá kỷ nguyên']):
        return "GIAO THƯƠNG ĐỘT PHÁ", "KỶ NGUYÊN SỐ", "BNI TOPAZ ONLINE"

    # Tự động cắt tách thông minh từ tiêu đề nếu là chủ đề khác
    stop_words = {'tại', 'sao', 'là', 'gì', 'của', 'và', 'để', 'cho', 'trong', 'với', 'như', 'thế', 'nào', 'khi', 'vì', 'bởi'}
    words = [w for w in re.sub(r'[:,\-?]', ' ', clean_title).split() if w.lower() not in stop_words]
    w1 = words[:min(3, len(words))]
    w2 = words[len(w1):min(len(w1) + 3, len(words))] or ["BÍ QUYẾT 2026"]
    line1 = " ".join(w1).upper()
    line2 = " ".join(w2).upper()
    return line1, line2, "BNI TOPAZ ONLINE"

def extract_2lines_hook(title, summary="", keyword=""):
    """Hàm tương thích ngược trả về 2 hàng hook"""
    l1, l2, _ = extract_smart_hook(title, summary=summary, keyword=keyword)
    return l1, l2

def generate_bg_prompt_from_summary(title, summary=""):
    """
    Sinh prompt tiếng Anh cho Imagen / AI sinh ảnh nền sát với đề tài bài blog
    """
    combined = (str(title) + " " + str(summary)).lower()

    if any(k in combined for k in ['zoom', 'họp online', 'online']):
        topic_desc = "High-tech executive video conference on a sleek laptop screen, Zoom meeting with diverse business leaders, coffee cup, modern minimal workspace"
    elif any(k in combined for k in ['bni', 'topaz', 'referral', 'kết nối kinh doanh', 'networking', 'givers gain']):
        topic_desc = "Prestigious executive business boardroom with confident Asian business leaders in bespoke suits networking and shaking hands, BNI corporate red and rich navy accents"
    elif any(k in combined for k in ['bất động sản', 'nhà đất']):
        topic_desc = "Modern luxury architectural villa with glass facade at golden hour sunset, warm interior lighting, sleek infinity pool"
    elif any(k in combined for k in ['hóa đơn', 'invoice', 'bán lẻ', 'pos']):
        topic_desc = "Upscale modern boutique retail store interior, illuminated smart digital POS touchscreen terminal on a sleek wooden counter"
    elif any(k in combined for k in ['quảng cáo', 'ads', 'marketing']):
        topic_desc = "High-tech digital marketing workspace, dual curved monitors glowing with sleek upward business analytical graphs"
    else:
        topic_desc = f"Cinematic executive business scene relevant to {title[:35]}, BNI red and navy corporate atmosphere, professional ambient lighting"

    prompt = (
        f"Cinematic 16:9 YouTube thumbnail background photography. {topic_desc}. "
        "Left side has a smooth dark shadowy negative space for title overlay, right side has clean focused subject with shallow depth of field bokeh. "
        "Photorealistic 8k, hyper-detailed, dramatic studio lighting, clean composition, absolutely no text, no letters, no watermark."
    )
    return prompt

def build_executive_thumbnail(
    bg_path,
    output_path,
    headline_top="BẤT ĐỘNG SẢN",
    headline_bottom="CHỐT TRIỆU ĐÔ",
    badge_label="BNI TOPAZ ONLINE",
    title="",
    keyword=""
):
    """
    Dựng ảnh Thumbnail YouTube hoàn chỉnh:
    - Chữ 2 hàng, mỗi hàng tối đa 3 chữ, chữ TO, viền sáng phát quang
    - Ít chữ và ít icon, tập trung độ tương phản cao
    - Badge danh mục thông minh theo tiêu đề
    - Logo Watermark tinh tế BNI TOPAZ™
    """
    print("🎨 Đang khởi tạo bộ máy thiết kế Thumbnail YouTube Chuẩn Cao...")
    target_w, target_h = 1920, 1080

    if os.path.exists(bg_path):
        try:
            base_img = Image.open(bg_path).convert("RGBA")
            if base_img.size != (target_w, target_h):
                orig_w, orig_h = base_img.size
                orig_ratio = orig_w / orig_h
                target_ratio = target_w / target_h
                if abs(orig_ratio - target_ratio) > 0.05:
                    if orig_ratio > target_ratio:
                        new_w = int(orig_h * target_ratio)
                        left = (orig_w - new_w) // 2
                        base_img = base_img.crop((left, 0, left + new_w, orig_h))
                    else:
                        new_h = int(orig_w / target_ratio)
                        top = (orig_h - new_h) // 2
                        base_img = base_img.crop((0, top, orig_w, top + new_h))
                base_img = base_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        except Exception:
            base_img = Image.new("RGBA", (target_w, target_h), (12, 18, 32, 255))
    else:
        base_img = Image.new("RGBA", (target_w, target_h), (12, 18, 32, 255))

    # 1. Thêm lớp Gradient đen mờ (Dark Vignette) phía bên trái tạo tương phản tối ưu cho chữ
    vignette = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    vig_draw = ImageDraw.Draw(vignette)
    for x in range(1250):
        alpha = int(240 * (1 - (x / 1250) ** 1.3))
        vig_draw.line([(x, 0), (x, target_h)], fill=(5, 8, 18, alpha))
    base_img = Image.alpha_composite(base_img, vignette)

    draw = ImageDraw.Draw(base_img)

    # 2. Dynamic font sizing để chữ TO NHẤT CÓ THỂ mà không bị tràn lề
    start_x = 100
    start_y = 300
    max_text_width = 1100

    font_size = 140
    font_main = get_best_font(font_size, bold=True)

    # Kiểm tra kích thước của 2 hàng chữ, nếu dài thì tự co giãn nhẹ
    for line in [headline_top, headline_bottom]:
        while font_size > 95:
            box = draw.textbbox((0, 0), line, font=font_main)
            if (box[2] - box[0]) <= max_text_width:
                break
            font_size -= 5
            font_main = get_best_font(font_size, bold=True)

    font_badge = get_best_font(38, bold=True)
    font_logo = get_best_font(42, bold=True)

    # 3. Badge nhỏ gọn gàng phía trên (tối giản, trang nhã, biến đổi linh hoạt theo đề tài)
    clean_badge = re.sub(r'[^\w\s\d\-+]', '', badge_label).strip() or "BNI TOPAZ ONLINE"
    b_box = draw.textbbox((0, 0), clean_badge, font=font_badge)
    bw = b_box[2] - b_box[0] + 44
    bh = b_box[3] - b_box[1] + 24
    badge_x = start_x
    badge_y = start_y - 115

    # Khung badge bo góc nền đỏ ruby viền sáng
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + bw, badge_y + bh)],
        radius=12,
        fill=(220, 38, 38, 235),
        outline=(254, 202, 202, 255),
        width=3
    )
    draw.text((badge_x + 22, badge_y + 10), clean_badge, font=font_badge, fill=(255, 255, 255, 255))

    # 4. HÀNG 1: Chữ Vàng Hoàng Kim Ánh Sáng (Glow vàng neon tỏa nhiệt, mặt chữ vàng sáng)
    gold_text = (255, 240, 100, 255)
    gold_glow = (255, 200, 0, 230)
    draw_glowing_text(
        base_img=base_img,
        draw=draw,
        pos=(start_x, start_y),
        text=headline_top,
        font=font_main,
        text_color=gold_text,
        glow_color=gold_glow,
        glow_radius=22,
        stroke_color=(15, 10, 0, 255),
        stroke_width=10,
        depth=14
    )

    # 5. HÀNG 2: Chữ Trắng Tuyết Viền Sáng Cyan/Neon (Glow xanh ngọc / trắng sáng cực nổi)
    line_spacing = int(font_size * 1.35)
    line2_y = start_y + line_spacing
    white_text = (255, 255, 255, 255)
    cyan_glow = (6, 182, 212, 230)
    draw_glowing_text(
        base_img=base_img,
        draw=draw,
        pos=(start_x, line2_y),
        text=headline_bottom,
        font=font_main,
        text_color=white_text,
        glow_color=cyan_glow,
        glow_radius=22,
        stroke_color=(0, 25, 35, 255),
        stroke_width=10,
        depth=14
    )

    # 6. Logo Watermark nhỏ tinh tế ở góc phải trên
    logo_w, logo_h = 240, 65
    lx = target_w - logo_w - 70
    ly = 60
    draw.rounded_rectangle(
        [(lx, ly), (lx + logo_w, ly + logo_h)],
        radius=10,
        fill=(15, 23, 42, 190),
        outline=(56, 189, 248, 160),
        width=2
    )
    draw.text((lx + 20, ly + 10), "BNI TOPAZ™", font=font_logo, fill=(255, 255, 255, 255))

    # 7. Tối ưu hóa & nén ảnh đa tầng (WebP + JPEG Progressive 1200x675)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if output_path.endswith('.webp'):
        webp_path = output_path
        jpg_path = output_path[:-5] + '.jpg'
    else:
        jpg_path = output_path
        webp_path = os.path.splitext(output_path)[0] + '.webp'

    compress_and_save_image(
        base_img=base_img,
        output_webp_path=webp_path,
        output_jpg_path=jpg_path,
        title=title,
        keyword=keyword
    )
    print(f"🎉 Đã xuất thành công Thumbnail YouTube chuẩn SEO tại: {output_path}")
    return output_path

def compress_and_save_image(base_img, output_webp_path, output_jpg_path=None, title="", keyword="", target_size=(1200, 675)):
    """
    Hàm tối ưu hóa & nén ảnh tự động chuẩn Google Core Web Vitals:
    - Resize về chuẩn vàng 16:9 (1200x675) bằng thuật toán Lanczos chống vỡ hạt
    - Nhúng siêu dữ liệu EXIF / IPTC bản quyền & SEO (Title, Description, Copyright)
    - Xuất file định dạng WebP siêu nhẹ (giảm 85-90% dung lượng, ~60-80KB)
    - Đồng thời xuất thêm bản JPEG Progressive dự phòng (~90-110KB)
    """
    # 1. Chuyển sang RGB nếu là RGBA để tương thích hoàn toàn
    if base_img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new("RGB", base_img.size, (15, 23, 42))
        if base_img.mode == 'RGBA':
            background.paste(base_img, mask=base_img.split()[3])
        else:
            background.paste(base_img.convert("RGB"))
        rgb_img = background
    else:
        rgb_img = base_img.convert("RGB")

    # 2. Resize thông minh về 1200x675 chuẩn vàng Google Discover
    target_w, target_h = target_size
    if rgb_img.size != (target_w, target_h):
        orig_w, orig_h = rgb_img.size
        orig_ratio = orig_w / orig_h
        target_ratio = target_w / target_h
        if abs(orig_ratio - target_ratio) > 0.05:
            if orig_ratio > target_ratio:
                new_w = int(orig_h * target_ratio)
                left = (orig_w - new_w) // 2
                rgb_img = rgb_img.crop((left, 0, left + new_w, orig_h))
            else:
                new_h = int(orig_w / target_ratio)
                top = (orig_h - new_h) // 2
                rgb_img = rgb_img.crop((0, top, orig_w, top + new_h))
        rgb_img = rgb_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # 3. Tạo siêu dữ liệu EXIF cho SEO Hình Ảnh
    exif = rgb_img.getexif()
    desc = f"{keyword} - {title}".strip(" -") if keyword else title
    if desc:
        exif[0x010E] = desc[:120]  # ImageDescription
    exif[0x013B] = "BNI Topaz Chapter Online"  # Artist / Thương hiệu
    exif[0x8298] = "Bản quyền hình ảnh thuộc về BNI Topaz Chapter Online (bnitopaz.com)"  # Copyright

    # 4. Lưu định dạng WebP (Google Next-Gen Format)
    os.makedirs(os.path.dirname(os.path.abspath(output_webp_path)), exist_ok=True)
    try:
        rgb_img.save(output_webp_path, "WEBP", quality=82, method=6, exif=exif)
    except Exception:
        rgb_img.save(output_webp_path, "WEBP", quality=82, method=6)
    webp_kb = os.path.getsize(output_webp_path) / 1024

    # 5. Lưu định dạng JPEG Progressive dự phòng
    if output_jpg_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_jpg_path)), exist_ok=True)
        try:
            rgb_img.save(output_jpg_path, "JPEG", quality=84, optimize=True, progressive=True, exif=exif)
        except Exception:
            rgb_img.save(output_jpg_path, "JPEG", quality=84, optimize=True, progressive=True)
        jpg_kb = os.path.getsize(output_jpg_path) / 1024
        print(f"📦 [Nén Ảnh Tự Động] WebP: {webp_kb:.1f} KB | JPEG: {jpg_kb:.1f} KB (Tiết kiệm >85% dung lượng)")
    else:
        print(f"📦 [Nén Ảnh Tự Động] WebP: {webp_kb:.1f} KB (Tiết kiệm >85% dung lượng)")

    return output_webp_path

def slugify(text, keyword=""):
    """Tạo slug chuẩn SEO không dấu an toàn cho tên file ảnh"""
    import unicodedata
    full_text = text
    if keyword and keyword.strip().lower() not in text.lower():
        full_text = f"{keyword.strip()} {text}"
    text = unicodedata.normalize('NFKD', full_text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    s = re.sub(r'[-\s]+', '-', text)[:60].strip('-')
    return s or "article-thumbnail"

def call_imagen_api(prompt, api_keys, output_bg_path):
    """
    Thử gọi Gemini / Imagen API sinh ảnh AI nếu tài khoản Google AI Studio có kích hoạt tính năng tạo ảnh
    Hỗ trợ xoay vòng nhiều API key
    """
    if isinstance(api_keys, str):
        keys = [api_keys] if api_keys else []
    else:
        keys = list(api_keys) if api_keys else []

    if not keys:
        return False

    for idx, k in enumerate(keys, 1):
        if not k:
            continue

        # 1. Thử gemini-3.1-flash-image generateContent
        try:
            url_flash_img = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image:generateContent?key={k}"
            payload_flash = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseModalities": ["IMAGE"],
                    "imageConfig": {"aspectRatio": "16:9"}
                }
            }
            resp = requests.post(url_flash_img, json=payload_flash, timeout=30)
            if resp.status_code == 200:
                res_j = resp.json()
                candidates = res_j.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    for part in parts:
                        if 'inlineData' in part and 'data' in part['inlineData']:
                            raw_bytes = base64.b64decode(part['inlineData']['data'])
                            with open(output_bg_path, 'wb') as f:
                                f.write(raw_bytes)
                            print(f"✅ Gemini 3.1 Flash Image đã tạo ảnh nền AI thành công!")
                            return True
        except Exception:
            pass

        # 2. Thử Imagen 4.0 predict
        for model in ["imagen-4.0-generate-001", "imagen-4.0-fast-generate-001"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={k}"
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "16:9",
                    "outputOptions": {"mimeType": "image/jpeg"}
                }
            }
            try:
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    res_json = resp.json()
                    predictions = res_json.get('predictions', [])
                    if predictions and 'bytesBase64Encoded' in predictions[0]:
                        img_data = base64.b64decode(predictions[0]['bytesBase64Encoded'])
                        with open(output_bg_path, 'wb') as f:
                            f.write(img_data)
                        print(f"✅ Google Imagen ({model}) đã tạo ảnh nền thành công!")
                        return True
            except Exception:
                pass

    return False

def create_post_thumbnail(title, summary="", keyword="", custom_image_url="", api_key="", repo_full_name=""):
    """
    Hàm tổng thể chuẩn YouTube Thumbnail:
    1. Kiểm tra ảnh có sẵn trên Sheet (nếu có, tự động tải về, nén WebP + SEO)
    2. Nếu không có ảnh trên Sheet:
       - Thử AI Imagen nếu khả dụng
       - Tự động nhận diện chủ đề tiêu đề và tải ảnh nền sinh động tương ứng từ kho 36+ ảnh nền doanh nhân
       - Fallback tự động sang nền đồ họa thuật toán Procedural Vector nếu mất mạng
    3. Trích xuất 2 hàng chữ giật tít chuẩn YouTube (mỗi hàng <= 3 chữ) + Badge chủ đề linh hoạt
    4. Dựng ảnh YouTube Thumbnail với hiệu ứng Neon Glow phát quang + bóng 3D
    5. Nén chuẩn WebP + JPEG Progressive 1200x675 (>85% nhẹ hơn)
    6. Nhúng siêu dữ liệu EXIF SEO bản quyền BNI Topaz Chapter Online
    7. Trả về link CDN vĩnh viễn WebP siêu tốc
    """
    if not repo_full_name:
        repo_full_name = os.environ.get("GITHUB_REPOSITORY", "").strip() or "owner/blogger-auto-cloud"
    clean_slug = slugify(title, keyword=keyword)
    thumb_dir = os.path.join(os.path.dirname(__file__), "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)
    out_webp = os.path.join(thumb_dir, f"{clean_slug}.webp")
    out_jpg = os.path.join(thumb_dir, f"{clean_slug}.jpg")

    # 1. Nếu người dùng đã cung cấp sẵn link ảnh trên Google Sheets (cột F)
    if custom_image_url and custom_image_url.startswith("http"):
        print(f"🖼️ Phát hiện ảnh tùy chỉnh từ Google Sheets: {custom_image_url}")
        try:
            resp = requests.get(custom_image_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code == 200:
                ext_img = Image.open(io.BytesIO(resp.content))
                compress_and_save_image(ext_img, out_webp, out_jpg, title=title, keyword=keyword)
                cdn_url = f"https://raw.githubusercontent.com/{repo_full_name}/main/thumbnails/{clean_slug}.webp"
                print(f"✅ Đã nén và chuẩn hóa SEO ảnh tùy chỉnh từ Sheets thành công: {cdn_url}")
                return cdn_url
        except Exception as e:
            print(f"⚠️ Không thể tải hoặc nén ảnh tùy chỉnh ({e}). Sử dụng link gốc.")
            return custom_image_url

    # 2. Chuẩn bị ảnh nền sinh động theo tiêu đề
    default_sample_bg = os.path.join(os.path.dirname(__file__), "sample_bg.jpg")
    temp_bg = os.path.join(thumb_dir, f"temp_bg_{clean_slug}.jpg")
    bg_used = default_sample_bg

    # Thử gọi Imagen nếu có API key
    ai_success = False
    if api_key:
        prompt_ai = generate_bg_prompt_from_summary(title, summary=summary)
        if call_imagen_api(prompt_ai, api_key, temp_bg):
            bg_used = temp_bg
            ai_success = True

    # Nếu AI Imagen không khả dụng (phổ biến với key miễn phí), tự động lấy ảnh nền sinh động theo chủ đề tiêu đề!
    if not ai_success:
        theme = detect_topic_theme(title, summary=summary, keyword=keyword)
        if download_thematic_background(theme, title, temp_bg):
            bg_used = temp_bg

    # 3. Trích xuất đúng 2 hàng hook (mỗi hàng tối đa 3 chữ) + Badge chủ đề linh hoạt
    line1, line2, badge_label = extract_smart_hook(title, summary=summary, keyword=keyword)

    # 4. Dựng Thumbnail YouTube & Nén tối ưu WebP / JPEG
    build_executive_thumbnail(
        bg_path=bg_used,
        output_path=out_webp,
        headline_top=line1,
        headline_bottom=line2,
        badge_label=badge_label,
        title=title,
        keyword=keyword
    )

    # Xóa file nền tạm nếu có
    if bg_used == temp_bg and os.path.exists(temp_bg):
        try:
            os.remove(temp_bg)
        except Exception:
            pass

    # 5. Link CDN vĩnh viễn trên GitHub (định dạng WebP siêu nhẹ)
    cdn_url = f"https://raw.githubusercontent.com/{repo_full_name}/main/thumbnails/{clean_slug}.webp"
    print(f"🔗 Link ảnh CDN WebP chuẩn bị nhúng vào Blogger: {cdn_url}")
    return cdn_url

if __name__ == '__main__':
    demo_title = "Triết Lý Givers Gain (Cho Là Nhận) Được Vận Hành Như Thế Nào Tại BNI Topaz Chapter?"
    demo_out = os.path.join(os.path.dirname(__file__), "demo_thumbnail.webp")
    create_post_thumbnail(demo_title, summary="Khám phá triết lý Cho Là Nhận tại BNI", repo_full_name="luvietseo-stack/blogger-auto-cloud")
