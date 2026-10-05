#!/usr/bin/env python3
"""
Công cụ hỗ trợ lấy GOOGLE_REFRESH_TOKEN cho Blogger API v3
Chỉ cần chạy script này một lần duy nhất để lấy mã Refresh Token vĩnh viễn!
"""

import sys
import os

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Vui lòng cài đặt thư viện trước bằng lệnh:")
    print("pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = [
    'https://www.googleapis.com/auth/blogger',
    'https://www.googleapis.com/auth/blogger.readonly'
]

def main():
    print("=" * 65)
    print("🔑 CÔNG CỤ TẠO GOOGLE REFRESH TOKEN CHO BLOGGER API")
    print("=" * 65)
    print("\nTrước khi chạy, bạn cần có:")
    print("1. Google Client ID (dạng: xxxx.apps.googleusercontent.com)")
    print("2. Google Client Secret (dạng: GOCSPX-xxxx)")
    print("(Nếu chưa có, hãy tạo tại: https://console.cloud.google.com/apis/credentials)\n")

    client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()

    if not client_id:
        client_id = input("Nhập Google Client ID (dạng xxxx.apps.googleusercontent.com): ").strip()
    if not client_secret:
        client_secret = input("Nhập Google Client Secret (dạng GOCSPX-xxxx): ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }

    print("\n🌐 Đang mở trình duyệt để bạn đăng nhập và cấp quyền cho Blogger...")
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline')

    print("\n" + "=" * 65)
    print("🎉 ĐĂNG NHẬP THÀNH CÔNG! ĐÂY LÀ MÃ REFRESH TOKEN CỦA BẠN:")
    print("=" * 65)
    print(f"\nGOOGLE_REFRESH_TOKEN={creds.refresh_token}\n")
    print("👉 Hãy sao chép chuỗi mã trên và lưu vào GitHub Repository Secrets!")
    print("=" * 65)

if __name__ == '__main__':
    main()
