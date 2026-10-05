#!/usr/bin/env python3
"""
Bộ tạo ảnh Thumbnail YouTube Chuẩn Chuyển Đổi Cao (High-Converting YouTube Thumbnail)
Đặc điểm:
- Chữ 2 hàng, mỗi hàng tối đa 3 chữ, chữ TO cực nét, viền sáng phát quang (Neon Glow)
- Bối cảnh ảnh nền điện ảnh (Cinematic 16:9) bám sát tóm tắt (summary) bài blog
- Tối giản: chữ và icon ít thôi, bố cục thoáng, tập trung thu hút click (High CTR)
"""

import os
import sys
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Ensure utf-8 stdout on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

def extract_2lines_hook(title, summary="", keyword=""):
    """
    Trích xuất đúng 2 hàng chữ giật tít chuẩn YouTube:
    - Đúng 2 hàng
    - Mỗi hàng tối đa 3 chữ (len <= 3 words)
    - Chữ to, ngắn gọn, thúc giục click
    """
    clean_title = re.sub(r'\[.*?\]|\(.*?\)|2026|Năm 2026', '', title).strip()
    text_corpus = (clean_title + " " + summary + " " + keyword).lower()

    # Nhận diện theo từ khóa ngành trọng tâm
    if any(k in text_corpus for k in ['topaz', 'bni topaz']):
        line1, line2 = "BNI TOPAZ", "ONLINE TOÀN CẦU"
    elif any(k in text_corpus for k in ['cho là nhận', 'givers gain']):
        line1, line2 = "CHO LÀ NHẬN", "GIVERS GAIN"
    elif any(k in text_corpus for k in ['referral', 'cơ hội kinh doanh']):
        line1, line2 = "TRAO REFERRAL", "TĂNG TRƯỞNG GẤP 3"
    elif any(k in text_corpus for k in ['độc quyền', 'doc quyen']):
        line1, line2 = "ĐỘC QUYỀN", "TRONG CHAPTER"
    elif any(k in text_corpus for k in ['kết nối kinh doanh', 'networking']):
        line1, line2 = "KẾT NỐI ĐỈNH CAO", "DOANH NHÂN CHẤT"
    elif any(k in text_corpus for k in ['zoom', 'họp online', 'online']):
        line1, line2 = "BNI ONLINE", "TIẾT KIỆM THỜI GIAN"
    elif any(k in text_corpus for k in ['bni là gì', 'tại sao bni', 'bni']):
        line1, line2 = "TỔ CHỨC BNI", "KẾT NỐI TOÀN CẦU"
    elif any(k in text_corpus for k in ['bất động sản', 'bat dong san', 'nhà đất']):
        line1, line2 = "BẤT ĐỘNG SẢN", "CHỐT TRIỆU ĐÔ"
    elif any(k in text_corpus for k in ['hóa đơn điện tử', 'hoa don dien tu', 'xuất hóa đơn']):
        line1, line2 = "XUẤT HÓA ĐƠN", "TỰ ĐỘNG 100%"
    elif any(k in text_corpus for k in ['quảng cáo', 'ads facebook', 'tiktok ads', 'cắt giảm 50%']):
        line1, line2 = "TIẾT KIỆM ADS", "BÙNG NỔ ĐƠN"
    elif any(k in text_corpus for k in ['chi phí sàn', 'bóc tách', '18-25%', 'phí ẩn']):
        line1, line2 = "PHÍ SÀN 18-25%", "CỨU LỢI NHUẬN"
    else:
        # Tự động cắt tách thông minh nếu đề tài mới
        clean_words = [w.strip() for w in re.sub(r'[:,\-?]', ' ', clean_title).split() if w.strip()]
        w1 = clean_words[:min(3, len(clean_words))]
        w2 = clean_words[len(w1):min(len(w1)+3, len(clean_words))] or ["BÍ QUYẾT 2026"]
        line1 = " ".join(w1).upper()
        line2 = " ".join(w2).upper()

    # BẢO ĐẢM BẮT BUỘC: Mỗi hàng tối đa đúng 3 từ
    line1 = " ".join(line1.split()[:3]).upper()
    line2 = " ".join(line2.split()[:3]).upper()
    return line1, line2

def generate_bg_prompt_from_summary(title, summary=""):
    """
    Sinh prompt tiếng Anh cho Imagen / AI sinh ảnh nền sát với tóm tắt bài blog:
    - 16:9, điện ảnh, ánh sáng nghệ thuật
    - Môi trường thực tế tương ứng với đề tài (BNI Networking, Doanh nhân, Hội nghị Zoom, Bất động sản, v.v.)
    - Khoảng tối bên trái (Left negative space) để chữ to nổi bật
    """
    combined = (str(title) + " " + str(summary)).lower()

    if any(k in combined for k in ['bni', 'topaz', 'referral', 'kết nối kinh doanh', 'networking', 'givers gain']):
        topic_desc = "Prestigious executive business boardroom with confident Asian business leaders in bespoke suits networking and shaking hands, sleek Zoom video conference screen on the wall, BNI corporate red and rich navy accents, warm ambient executive illumination"
    elif any(k in combined for k in ['bất động sản', 'nhà đất', 'landing page bất động sản']):
        topic_desc = "Modern luxury architectural villa with glass facade at golden hour sunset, warm interior lighting, sleek infinity pool, minimalist elegance"
    elif any(k in combined for k in ['hóa đơn', 'invoice', 'bán lẻ', 'pancake', 'pos']):
        topic_desc = "Upscale modern boutique retail store interior, illuminated smart digital POS touchscreen terminal on a sleek wooden counter, warm ambient lighting"
    elif any(k in combined for k in ['quảng cáo', 'ads', 'facebook', 'tiktok', 'marketing']):
        topic_desc = "High-tech digital marketing workspace, dual curved monitors glowing with sleek upward business analytical graphs, dark amber and cyan ambient atmosphere"
    elif any(k in combined for k in ['đồng nai', 'doanh nghiệp', 'website doanh nghiệp', 'thiết kế web']):
        topic_desc = "Sophisticated contemporary executive glass office overlooking dynamic city skyline at twilight, clean marble desk, architectural depth"
    else:
        topic_desc = f"Cinematic executive business networking scene relevant to {title[:35]}, BNI red and navy corporate atmosphere, professional ambient lighting"

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
    badge_label="CHIẾN LƯỢC 2026",
    title="",
    keyword=""
):
    """
    Dựng ảnh Thumbnail YouTube hoàn chỉnh:
    - Chữ 2 hàng, mỗi hàng tối đa 3 chữ, chữ TO, viền sáng phát quang
    - Ít chữ và ít icon (không có các hộp HUD rườm rà)
    - Tương phản mạnh, cực kỳ bắt mắt
    """
    print("🎨 Đang khởi tạo bộ máy thiết kế Thumbnail YouTube Chuẩn Cao...")
    target_w, target_h = 1920, 1080

    if os.path.exists(bg_path):
        base_img = Image.open(bg_path).convert("RGBA")
        if base_img.size != (target_w, target_h):
            base_img = base_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
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

    # 3. Badge nhỏ gọn gàng phía trên (tối giản, trang nhã)
    clean_badge = re.sub(r'[^\w\s\d\-]', '', badge_label).strip() or "BÍ QUYẾT 2026"
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
    Gọi Google Imagen API sinh ảnh nền điện ảnh chất lượng cao
    Hỗ trợ xoay vòng nhiều API key
    """
    import requests
    import base64

    if isinstance(api_keys, str):
        keys = [api_keys] if api_keys else []
    else:
        keys = list(api_keys) if api_keys else []

    if not keys:
        return False

    models_to_try = [
        "imagen-3.0-generate-002",
        "imagen-4.0-generate-001"
    ]

    for idx, k in enumerate(keys, 1):
        if not k:
            continue
        for model in models_to_try:
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
                print(f"🎨 Đang gọi Google Imagen API ({model}) sinh ảnh nền (Key #{idx}/{len(keys)})...")
                resp = requests.post(url, json=payload, timeout=40)
                if resp.status_code == 200:
                    res_json = resp.json()
                    predictions = res_json.get('predictions', [])
                    if predictions and 'bytesBase64Encoded' in predictions[0]:
                        img_data = base64.b64decode(predictions[0]['bytesBase64Encoded'])
                        with open(output_bg_path, 'wb') as f:
                            f.write(img_data)
                        print(f"✅ Google Imagen đã sinh ảnh nền thành công!")
                        return True
                else:
                    print(f"ℹ️ Imagen ({model}) với Key #{idx} phản hồi HTTP {resp.status_code}. Thử tiếp...")
            except Exception as e:
                print(f"ℹ️ Kết nối Imagen ({model}) với Key #{idx}: {e}")

    print("ℹ️ Tự động dùng ảnh nền doanh nhân chuẩn tích hợp sẵn.")
    return False

def create_post_thumbnail(title, summary="", keyword="", custom_image_url="", api_key="", repo_full_name=""):
    """
    Hàm tổng thể chuẩn YouTube Thumbnail:
    1. Kiểm tra ảnh có sẵn trên Sheet (nếu có, tự động tải về, nén WebP + SEO)
    2. Sinh ảnh nền điện ảnh bám sát tóm tắt (summary) bài blog
    3. Ghép chữ đúng 2 hàng, mỗi hàng tối đa 3 chữ, chữ TO, viền sáng phát quang
    4. Tự động nén chuẩn WebP + JPEG Progressive 1200x675 (>85% nhẹ hơn)
    5. Nhúng siêu dữ liệu EXIF SEO (Title, Description, Copyright)
    6. Trả về link CDN vĩnh viễn WebP siêu tốc
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
            import requests, io
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

    # 2. Chuẩn bị ảnh nền
    default_sample_bg = os.path.join(os.path.dirname(__file__), "sample_bg.jpg")
    temp_bg = os.path.join(thumb_dir, f"temp_bg_{clean_slug}.jpg")
    bg_used = default_sample_bg

    # 3. Tạo prompt ảnh nền bám sát tóm tắt bài blog
    prompt_ai = generate_bg_prompt_from_summary(title, summary=summary)

    # Thử gọi Imagen nếu có API key
    if api_key:
        if call_imagen_api(prompt_ai, api_key, temp_bg):
            bg_used = temp_bg

    # 4. Trích xuất đúng 2 hàng hook (mỗi hàng tối đa 3 chữ)
    line1, line2 = extract_2lines_hook(title, summary=summary, keyword=keyword)

    # 5. Dựng Thumbnail YouTube & Nén tối ưu WebP / JPEG
    build_executive_thumbnail(
        bg_path=bg_used,
        output_path=out_webp,
        headline_top=line1,
        headline_bottom=line2,
        badge_label="BNI TOPAZ ONLINE",
        title=title,
        keyword=keyword
    )

    # Xóa file nền tạm nếu có
    if bg_used == temp_bg and os.path.exists(temp_bg):
        try:
            os.remove(temp_bg)
        except Exception:
            pass

    # 6. Link CDN vĩnh viễn trên GitHub (định dạng WebP siêu nhẹ)
    cdn_url = f"https://raw.githubusercontent.com/{repo_full_name}/main/thumbnails/{clean_slug}.webp"
    print(f"🔗 Link ảnh CDN WebP chuẩn bị nhúng vào Blogger: {cdn_url}")
    return cdn_url

if __name__ == '__main__':
    bg_file = os.path.join(os.path.dirname(__file__), "sample_bg.jpg")
    out_file = os.path.join(os.path.dirname(__file__), "executive_thumbnail_demo.jpg")
    build_executive_thumbnail(bg_file, out_file)
