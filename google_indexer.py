# ==============================================================================
# Google Indexing & IndexNow Auto-Submission Engine
# Tự động hóa gửi URL bài viết đã LIVE lên Google Indexing API & Bing IndexNow
# ==============================================================================

import os
import json
import logging
from datetime import datetime, timezone, timedelta
import requests

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    service_account = None
    build = None

logger = logging.getLogger("GoogleIndexer")
INDEXING_SCOPES = ["https://www.googleapis.com/auth/indexing"]


def get_service_account_credentials():
    """
    Nạp Google Service Account Credentials từ:
    1. Biến môi trường INDEXING_SERVICE_ACCOUNT_JSON (chuỗi JSON trong GitHub Secrets)
    2. File service_account.json cục bộ
    """
    # 1. Kiểm tra từ biến môi trường
    env_json = os.environ.get("INDEXING_SERVICE_ACCOUNT_JSON", "").strip()
    if env_json:
        try:
            cred_dict = json.loads(env_json)
            return service_account.Credentials.from_service_account_info(
                cred_dict, scopes=INDEXING_SCOPES
            )
        except Exception as e:
            print(f"⚠️ Không thể phân tích cú pháp INDEXING_SERVICE_ACCOUNT_JSON: {e}")

    # 2. Kiểm tra file cục bộ
    local_file = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(local_file):
        try:
            return service_account.Credentials.from_service_account_file(
                local_file, scopes=INDEXING_SCOPES
            )
        except Exception as e:
            print(f"⚠️ Không thể nạp file {local_file}: {e}")

    return None


def check_url_live(url):
    """
    Kiểm tra xem URL bài viết đã thực sự xuất bản và LIVE (HTTP 200) chưa.
    Tránh tuyệt đối việc gửi URL đang ở trạng thái 404.
    """
    if not url or not url.startswith("http"):
        return False
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        return resp.status_code == 200
    except Exception as e:
        print(f"⚠️ Kiểm tra URL {url} thất bại: {e}")
        return False


def submit_to_google_indexing(url, credentials, action_type="URL_UPDATED"):
    """
    Gửi URL bài viết lên Google Indexing API.
    action_type: "URL_UPDATED" (mặc định) hoặc "URL_DELETED"
    """
    if not credentials or not build:
        raise ValueError("Chưa cấu hình Google Service Account hoặc thiếu thư viện googleapiclient.")

    service = build("indexing", "v3", credentials=credentials, cache_discovery=False)
    body = {
        "url": url,
        "type": action_type
    }
    response = service.urlNotifications().publish(body=body).execute()
    return response


def submit_to_indexnow(url, host=None, api_key=None):
    """
    Tùy chọn: Gửi URL lên Bing & IndexNow (hỗ trợ Microsoft Bing, Yahoo, Yandex).
    Chỉ chạy nếu có cấu hình INDEXNOW_API_KEY.
    """
    api_key = api_key or os.environ.get("INDEXNOW_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = host or parsed.netloc

        endpoint = "https://api.indexnow.org/indexnow"
        payload = {
            "host": host,
            "key": api_key,
            "keyLocation": f"https://{host}/{api_key}.txt",
            "urlList": [url]
        }
        headers = {"Content-Type": "application/json; charset=utf-8"}
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        return resp.status_code in [200, 202]
    except Exception as e:
        print(f"⚠️ IndexNow submission error: {e}")
        return False


def process_auto_indexing(history_data, notify_telegram_func=None):
    """
    Quét danh sách các bài viết đã lên lịch trong lịch sử:
    1. Chỉ chọn các bài có thời gian xuất bản <= Hiện tại (đã đến giờ phát hành).
    2. Chỉ chọn bài chưa từng được gửi indexing (indexed != True).
    3. Kiểm tra URL thực tế đã LIVE (HTTP 200).
    4. Gửi lên Google Indexing API và cập nhật trạng thái.
    """
    credentials = get_service_account_credentials()
    if not credentials:
        print("💡 Chưa cấu hình Google Service Account cho Indexing API. Bỏ qua bước lập chỉ mục tự động.")
        print("   (Để kích hoạt, hãy thêm Secret INDEXING_SERVICE_ACCOUNT_JSON trên GitHub).")
        return 0

    if not history_data or "history" not in history_data:
        return 0

    now_utc = datetime.now(timezone.utc)
    indexed_count = 0

    print("\n🔍 Đang quét các bài viết đã LIVE để gửi lập chỉ mục Google Indexing API...")

    for item in history_data["history"]:
        url = item.get("url", "").strip()
        is_already_indexed = item.get("indexed", False)

        if not url or is_already_indexed:
            continue

        pub_str = item.get("published")
        if not pub_str:
            continue

        try:
            pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
        except Exception:
            continue

        # Kiểm tra xem bài đã đến hoặc qua giờ hẹn chưa
        if pub_dt > now_utc:
            # Chưa đến giờ phát hành, bỏ qua
            continue

        print(f"👉 Phát hiện bài viết đã đến giờ phát hành: {item.get('title', '')[:50]}...")
        print(f"   URL: {url}")

        # Kiểm tra xem URL thực sự đã Live (200 OK) chưa
        is_live = check_url_live(url)
        if not is_live:
            print("   ⏳ Bài viết chưa phản hồi HTTP 200 (Blogger có thể đang cập nhật cache). Sẽ thử lại ở chu kỳ kế tiếp.")
            continue

        # Gửi lên Google Indexing API
        try:
            res = submit_to_google_indexing(url, credentials)
            notify_time = res.get("urlNotificationMetadata", {}).get("latestUpdate", {}).get("notifyTime", "")
            print(f"   🚀 GOOGLE INDEXING THÀNH CÔNG! (Notify Time: {notify_time})")

            item["indexed"] = True
            item["indexed_at"] = now_utc.isoformat()
            indexed_count += 1

            # Gửi thêm IndexNow nếu có key
            submit_to_indexnow(url)

            # Báo cáo Telegram nếu có hàm callback
            if notify_telegram_func:
                try:
                    title = item.get("title", "Bài viết mới")
                    vn_tz = timezone(timedelta(hours=7))
                    vn_time_str = pub_dt.astimezone(vn_tz).strftime("%d/%m/%Y %H:%M")
                    msg = (
                        f"🚀 <b>GOOGLE INDEXING: BẮN LẬP CHỈ MỤC THÀNH CÔNG!</b>\n\n"
                        f"📌 <b>Tiêu đề:</b> {title}\n"
                        f"🔗 <b>URL:</b> {url}\n"
                        f"⏰ <b>Thời điểm xuất bản:</b> {vn_time_str} (Giờ VN)\n"
                        f"⚡ <b>Trạng thái:</b> Google Bot đã nhận lệnh lập chỉ mục (URL_UPDATED)!"
                    )
                    notify_telegram_func(msg)
                except Exception as tele_err:
                    print(f"   ⚠️ Lỗi gửi thông báo Telegram Indexing: {tele_err}")

        except Exception as err:
            print(f"   ❌ Gửi Google Indexing thất bại: {err}")

    if indexed_count > 0:
        print(f"✅ Hoàn thành: Đã gửi lập chỉ mục thành công cho {indexed_count} bài viết mới LIVE!")
    else:
        print("ℹ️ Không có bài viết mới nào cần gửi lập chỉ mục trong đợt quét này.")

    return indexed_count
