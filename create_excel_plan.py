#!/usr/bin/env python3
"""
Tạo file Excel Kế Hoạch Bài Viết Blogger LuViet 2026 chuẩn hóa
Gồm 2 Sheet:
1. Ke_Hoach_Dang_Bai: Bảng quản lý bài đăng tự động (STT, Tiêu đề, Từ khóa, Nhãn tin-tuc/dich-vu, Gợi ý, CTA, Trạng thái, Link bài)
2. Kho_Tu_Khoa_SEO: Toàn bộ 1000 từ khóa Search Console phân loại P1 -> P5
"""

import os
import sys
import csv
import json

# Ensure utf-8 stdout on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

CSV_KEYWORDS_FILE = os.path.join(os.path.dirname(__file__), "Bang_Phan_Loai_Tu_Khoa_SEO_LuViet_2026.csv")
if not os.path.exists(CSV_KEYWORDS_FILE):
    CSV_KEYWORDS_FILE = r"C:\Users\Admin\Downloads\Bang_Phan_Loai_Tu_Khoa_SEO_LuViet_2026.csv"

TOPICS_FILE = os.path.join(os.path.dirname(__file__), "topics.txt")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "posted_history.json")

OUTPUT_XLSX_DOWNLOADS = r"C:\Users\Admin\Downloads\Ke_Hoach_Bai_Viet_Blogger_LuViet_2026.xlsx"
OUTPUT_XLSX_LOCAL = os.path.join(os.path.dirname(__file__), "Ke_Hoach_Bai_Viet_Blogger_LuViet_2026.xlsx")
OUTPUT_CSV_LOCAL = os.path.join(os.path.dirname(__file__), "Ke_Hoach_Dang_Bai.csv")

def determine_label(title, summary, raw_tags=""):
    """
    Phân loại nhãn chuẩn theo quy ước của LuViet:
    - dich-vu: Bài về dịch vụ thiết kế web, landing page doanh nghiệp, báo giá, Đồng Nai/Biên Hòa
    - tin-tuc: Tin tức thị trường, phân tích kinh doanh, sàn TMĐT, mẹo bán hàng
    - kien-thuc: Hướng dẫn kỹ thuật, tool AI, thủ thuật
    """
    combined = (title + " " + summary + " " + raw_tags).lower()
    
    # Từ khóa dịch vụ đặc trưng
    service_keywords = [
        "dịch vụ", "dich vu", "thiết kế web", "thiet ke web", "báo giá", "bảng giá",
        "thuê đơn vị làm website", "thiết kế landing page", "đồng nai", "biên hòa"
    ]
    if any(k in combined for k in service_keywords):
        return "dich-vu"
    
    # Từ khóa thủ thuật / kiến thức
    knowledge_keywords = [
        "hướng dẫn", "huong dan", "cách làm", "thủ thuật", "ai chatbot", "chatgpt", "gemini"
    ]
    if any(k in combined for k in knowledge_keywords):
        return "tin-tuc, kien-thuc"
        
    return "tin-tuc"

def main():
    print("🚀 Bắt đầu tạo file Excel Kế Hoạch Bài Viết Blogger LuViet 2026...")
    
    # 1. Đọc lịch sử đã đăng
    posted_titles = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                hdata = json.load(f)
                for item in hdata.get("history", []):
                    top = item.get("topic", "").strip().lower()
                    posted_titles[top] = item
        except Exception as e:
            print("Lỗi đọc history:", e)

    wb = openpyxl.Workbook()
    
    # ==============================================================================
    # SHEET 1: KẾ HOẠCH ĐĂNG BÀI (CONTENT CALENDAR)
    # ==============================================================================
    ws1 = wb.active
    ws1.title = "Ke_Hoach_Dang_Bai"
    ws1.views.sheetView[0].showGridLines = True
    
    headers1 = [
        "STT", 
        "Tiêu Đề Bài Viết (Blogger Title)", 
        "Từ Khóa Chính (Focus Keyword)", 
        "Nhãn Chuyên Mục (Labels)", 
        "Gợi Ý Nội Dung / Góc Nhìn", 
        "Link Đích CTA", 
        "Trạng Thái", 
        "Ngày Lên Lịch / Đăng", 
        "Link Bài Viết (URL)"
    ]
    
    # Styling styles
    header_fill1 = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Blue
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    bold_font = Font(name="Calibri", size=10, bold=True)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    
    ws1.append(headers1)
    for col_idx in range(1, len(headers1) + 1):
        cell = ws1.cell(row=1, column=col_idx)
        cell.fill = header_fill1
        cell.font = header_font
        cell.alignment = center_align
        cell.border = thin_border
    ws1.row_dimensions[1].height = 28
    
    # Đọc từ topics.txt
    rows_plan = []
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
        
        for idx, line in enumerate(lines, 1):
            parts = [p.strip() for p in line.split("|")]
            title = parts[0]
            summary = parts[1] if len(parts) >= 2 else ""
            cta = parts[2] if len(parts) >= 3 and parts[2].startswith("http") else "https://my.luviet.com/register"
            raw_tags = parts[3] if len(parts) >= 4 else (parts[2] if len(parts) >= 3 and not parts[2].startswith("http") else "")
            
            # Tách từ khóa chính từ đầu tiêu đề
            keyword = title.split(":")[0].strip() if ":" in title else title
            label = determine_label(title, summary, raw_tags)
            
            # Kiểm tra xem đã đăng chưa
            is_posted = title.strip().lower() in posted_titles
            post_info = posted_titles.get(title.strip().lower(), {})
            
            status = "Đã đăng" if is_posted else "Chưa đăng"
            pub_date = post_info.get("published", "") if is_posted else ""
            post_url = post_info.get("url", "") if is_posted else ""
            
            rows_plan.append([
                idx,
                title,
                keyword,
                label,
                summary,
                cta,
                status,
                pub_date,
                post_url
            ])
            
    # Ghi dữ liệu vào sheet 1
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    posted_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Xanh lá nhạt
    
    for row_idx, rdata in enumerate(rows_plan, 2):
        ws1.append(rdata)
        ws1.row_dimensions[row_idx].height = 36
        is_posted = (rdata[6] == "Đã đăng")
        
        for col_idx in range(1, len(rdata) + 1):
            cell = ws1.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            
            # Căn lề
            if col_idx in [1, 4, 7, 8]:
                cell.alignment = center_align
            else:
                cell.alignment = left_align
                
            # Tô màu nền
            if is_posted:
                cell.fill = posted_fill
                if col_idx == 7:
                    cell.font = bold_font
            elif row_idx % 2 == 1:
                cell.fill = zebra_fill
                
            # Highlight nhãn
            if col_idx == 4:
                cell.font = bold_font
                
    # Data Validation cho Nhãn (tin-tuc, dich-vu, tin-tuc, kien-thuc)
    dv_label = DataValidation(
        type="list", 
        formula1='"tin-tuc,dich-vu,tin-tuc, kien-thuc,dich-vu, tin-tuc"', 
        allow_blank=True
    )
    ws1.add_data_validation(dv_label)
    dv_label.add(f"D2:D{len(rows_plan) + 200}")
    
    # Data Validation cho Trạng thái
    dv_status = DataValidation(
        type="list", 
        formula1='"Chưa đăng,Đang viết,Đã lên lịch,Đã đăng"', 
        allow_blank=True
    )
    ws1.add_data_validation(dv_status)
    dv_status.add(f"G2:G{len(rows_plan) + 200}")

    # Set column widths cho Sheet 1
    widths1 = {
        "A": 7,   # STT
        "B": 48,  # Tiêu đề
        "C": 28,  # Từ khóa
        "D": 18,  # Nhãn (tin-tuc, dich-vu)
        "E": 45,  # Gợi ý nội dung
        "F": 32,  # Link CTA
        "G": 14,  # Trạng thái
        "H": 22,  # Ngày đăng
        "I": 42   # Link bài viết
    }
    for col_letter, w in widths1.items():
        ws1.column_dimensions[col_letter].width = w

    # ==============================================================================
    # SHEET 2: TOÀN BỘ KHO TỪ KHÓA TỪ SEARCH CONSOLE
    # ==============================================================================
    ws2 = wb.create_sheet(title="Kho_Tu_Khoa_Search_Console")
    ws2.views.sheetView[0].showGridLines = True
    
    header_fill2 = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid") # Emerald Green
    
    if os.path.exists(CSV_KEYWORDS_FILE):
        with open(CSV_KEYWORDS_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            csv_rows = list(reader)
            
        if csv_rows:
            headers2 = csv_rows[0]
            ws2.append(headers2)
            ws2.row_dimensions[1].height = 28
            for col_idx in range(1, len(headers2) + 1):
                cell = ws2.cell(row=1, column=col_idx)
                cell.fill = header_fill2
                cell.font = header_font
                cell.alignment = center_align
                cell.border = thin_border
                
            for row_idx, r in enumerate(csv_rows[1:], 2):
                ws2.append(r)
                ws2.row_dimensions[row_idx].height = 20
                for col_idx in range(1, len(r) + 1):
                    cell = ws2.cell(row=row_idx, column=col_idx)
                    cell.font = data_font
                    cell.border = thin_border
                    if col_idx in [1, 3, 4, 5, 6, 9]:
                        cell.alignment = center_align
                    else:
                        cell.alignment = left_align
                    if row_idx % 2 == 1:
                        cell.fill = zebra_fill
                        
            # Set widths for sheet 2
            widths2 = {
                "A": 7,   # STT
                "B": 35,  # Từ khóa
                "C": 14,  # Impressions
                "D": 12,  # Clicks
                "E": 12,  # CTR
                "F": 12,  # Rank
                "G": 30,  # Cluster
                "H": 22,  # Intent
                "I": 30,  # Priority
                "J": 30,  # Funnel
                "K": 18   # Status
            }
            for col_letter, w in widths2.items():
                ws2.column_dimensions[col_letter].width = w

    # Lưu file Excel
    os.makedirs(os.path.dirname(OUTPUT_XLSX_DOWNLOADS), exist_ok=True)
    wb.save(OUTPUT_XLSX_DOWNLOADS)
    wb.save(OUTPUT_XLSX_LOCAL)
    print(f"✅ Đã tạo file Excel thành công tại:")
    print(f"   📁 {OUTPUT_XLSX_DOWNLOADS}")
    print(f"   📁 {OUTPUT_XLSX_LOCAL}")

    # Đồng thời xuất ra file CSV chuẩn sạch để dễ import trực tiếp lên Google Sheets
    with open(OUTPUT_CSV_LOCAL, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers1)
        writer.writerows(rows_plan)
    print(f"✅ Đã tạo file CSV hỗ trợ Import tại: {OUTPUT_CSV_LOCAL}")

if __name__ == "__main__":
    main()
