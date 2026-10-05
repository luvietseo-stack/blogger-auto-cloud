/**
 * Google Apps Script Webhook - Tự động cập nhật Google Sheets & Gửi thông báo Email + Telegram
 * 
 * ==============================================================================
 * CẤU HÌNH THÔNG BÁO TELEGRAM & EMAIL
 * ==============================================================================
 */
// Cấu hình Telegram Bot (@BotFather) & Chat ID nhóm nhận thông báo
var TELEGRAM_BOT_TOKEN = "8480459173:AAHhSTEGSCG5zwq1jp6Dtycw97NQ2dqA8QM";
var TELEGRAM_CHAT_ID = "-5074952407"; // Nhóm Content Luviet

// Email nhận thông báo: Điền email nhận thông báo báo cáo xuất bản bài viết (để trống nếu không cần)
var NOTIFICATION_EMAIL = "";

/**
 * ==============================================================================
 * HÀM XỬ LÝ YÊU CẦU POST TỪ GITHUB ACTIONS WEBHOOK
 * ==============================================================================
 */
function doPost(e) {
  // 1. Kiểm tra an toàn: nếu hàm bị gọi bởi trigger "On edit" hoặc không có postData
  if (!e || !e.postData || !e.postData.contents) {
    Logger.log("⚠️ doPost được gọi nhưng không có postData (do kích hoạt nhầm trigger On Edit trong Apps Script). Bỏ qua an toàn.");
    return ContentService.createTextOutput(JSON.stringify({
      status: "ignored",
      message: "Không có dữ liệu HTTP POST. Nếu bạn đang cài Trigger 'Khi chỉnh sửa / On edit' trong mục Triggers của Apps Script, vui lòng xóa trigger đó đi (Webhook hoạt động qua bản Triển khai Web App, không cần Trigger)."
    })).setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var data = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Ke_Hoach_Dang_Bai") || ss.getActiveSheet();
    var rows = sheet.getDataRange().getValues();

    var targetTopic = (data.topic || "").trim().toLowerCase();
    var rowIndex = data.row_index; // 1-based index từ kịch bản Python

    var matchedRow = -1;

    // 1. Kiểm tra theo rowIndex nếu có
    if (rowIndex && rowIndex <= rows.length) {
      var checkTitle = (rows[rowIndex - 1][1] || "").toString().trim().toLowerCase();
      if (checkTitle === targetTopic || !targetTopic) {
        matchedRow = rowIndex;
      }
    }

    // 2. Tìm theo tiêu đề nếu chưa khớp rowIndex
    if (matchedRow === -1 && targetTopic) {
      for (var i = 1; i < rows.length; i++) {
        var rowTitle = (rows[i][1] || "").toString().trim().toLowerCase();
        if (rowTitle === targetTopic) {
          matchedRow = i + 1;
          break;
        }
      }
    }

    var statusText = data.status || "Đã đăng";
    var publishedTime = data.published || new Date().toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
    var postUrl = data.post_url || "";
    var labelsStr = Array.isArray(data.labels) ? data.labels.join(", ") : (data.labels || "tin-tuc");
    var topicTitle = data.topic || (matchedRow > 0 ? rows[matchedRow - 1][1] : "Bài viết mới");

    // Cập nhật Google Sheets nếu tìm thấy dòng
    if (matchedRow > 0) {
      // Cột 7 (G): Trạng Thái
      var statusCell = sheet.getRange(matchedRow, 7);
      statusCell.setValue(statusText);
      statusCell.setBackground("#DCFCE7"); // Xanh lá nhạt
      statusCell.setFontColor("#166534");  // Xanh lá đậm
      statusCell.setFontWeight("bold");

      // Cột 8 (H): Ngày Lên Lịch / Đăng
      sheet.getRange(matchedRow, 8).setValue(publishedTime);

      // Cột 9 (I): Link Bài Viết
      if (postUrl) {
        sheet.getRange(matchedRow, 9).setValue(postUrl);
      }
    }

    // Gửi thông báo đến Telegram
    try {
      sendTelegramMessage(topicTitle, statusText, postUrl, publishedTime, labelsStr, matchedRow);
    } catch (teleErr) {
      Logger.log("Lỗi gửi Telegram: " + teleErr.toString());
    }

    // Gửi thông báo đến Email
    try {
      sendEmailNotification(topicTitle, statusText, postUrl, publishedTime, labelsStr, matchedRow);
    } catch (mailErr) {
      Logger.log("Lỗi gửi Email: " + mailErr.toString());
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      matched_row: matchedRow,
      topic: topicTitle
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * ==============================================================================
 * HÀM GỬI THÔNG BÁO TELEGRAM
 * ==============================================================================
 */
function sendTelegramMessage(topic, status, postUrl, publishedTime, labels, rowIndex) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) return;

  var url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage";

  var text = "🚀 <b>[BLOGGER AUTO-POSTER] ĐĂNG BÀI THÀNH CÔNG</b>\n\n" +
    "📌 <b>Tiêu đề:</b> " + topic + "\n" +
    "🏷️ <b>Nhãn:</b> <code>" + labels + "</code>\n" +
    "⏰ <b>Thời gian:</b> " + publishedTime + "\n" +
    (rowIndex > 0 ? "📊 <b>Google Sheet:</b> Đã cập nhật dòng #" + rowIndex + " (<b>" + status + "</b>)\n" : "") +
    (postUrl ? "🔗 <b>Link bài viết:</b> <a href=\"" + postUrl + "\">Bấm xem ngay</a>\n" : "") +
    "\n💡 <i>Hệ thống AI Blogger Cloud LuViet đã xử lý hoàn tất!</i>";

  var payload = {
    chat_id: TELEGRAM_CHAT_ID,
    text: text,
    parse_mode: "HTML",
    disable_web_page_preview: false
  };

  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  UrlFetchApp.fetch(url, options);
}

/**
 * ==============================================================================
 * HÀM GỬI THÔNG BÁO EMAIL
 * ==============================================================================
 */
function sendEmailNotification(topic, status, postUrl, publishedTime, labels, rowIndex) {
  var recipient = (NOTIFICATION_EMAIL || "").trim();
  if (!recipient) {
    try {
      recipient = Session.getEffectiveUser().getEmail();
    } catch (e) { }
  }
  if (!recipient) {
    Logger.log("⚠️ Không tìm thấy email nhận thông báo! Vui lòng điền vào biến NOTIFICATION_EMAIL.");
    return;
  }

  var subject = "🚀 [Blogger Auto] Xuất bản thành công: " + topic;

  var htmlBody =
    '<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">' +
    '<div style="background: linear-gradient(135deg, #1e3a8a 0%, #0284c7 100%); padding: 24px; color: #ffffff; text-align: center;">' +
    '<h2 style="margin: 0; font-size: 20px;">🚀 Blogger Auto-Poster: Báo Cáo Xuất Bản</h2>' +
    '<p style="margin: 6px 0 0; opacity: 0.9; font-size: 14px;">Hệ thống AI tự động hóa LuViet (my.luviet.com)</p>' +
    '</div>' +
    '<div style="padding: 24px; background: #ffffff;">' +
    '<p style="font-size: 15px; color: #334155; line-height: 1.6;">Xin chào, hệ thống vừa xuất bản và lên lịch thành công một bài viết mới:</p>' +
    '<div style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 16px; margin: 18px 0; border-radius: 4px;">' +
    '<p style="margin: 0 0 10px; font-size: 16px; font-weight: bold; color: #0f172a;">📌 ' + topic + '</p>' +
    '<p style="margin: 6px 0; font-size: 14px; color: #475569;">🏷️ <b>Nhãn chuyên mục:</b> <span style="background: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 4px; font-weight: 600;">' + labels + '</span></p>' +
    '<p style="margin: 6px 0; font-size: 14px; color: #475569;">⏰ <b>Thời gian:</b> ' + publishedTime + '</p>' +
    (rowIndex > 0 ? '<p style="margin: 6px 0; font-size: 14px; color: #475569;">📊 <b>Google Sheet:</b> Đã cập nhật dòng #' + rowIndex + ' (<b>' + status + '</b>)</p>' : '') +
    '</div>' +
    (postUrl ?
      '<div style="text-align: center; margin-top: 25px;">' +
      '<a href="' + postUrl + '" target="_blank" style="background: #2563eb; color: #ffffff; font-weight: bold; padding: 12px 25px; border-radius: 8px; text-decoration: none; display: inline-block; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);">👉 Bấm Xem Bài Viết Ngay</a>' +
      '</div>' : '') +
    '</div>' +
    '<div style="background: #f1f5f9; padding: 14px; text-align: center; font-size: 12px; color: #64748b;">' +
    'Hệ sinh thái tự động hóa nội dung & Website bán hàng AILADI LuViet' +
    '</div>' +
    '</div>';

  MailApp.sendEmail({
    to: recipient,
    subject: subject,
    htmlBody: htmlBody
  });
  Logger.log("✅ Đã gửi email thông báo thành công tới: " + recipient);
}

/**
 * ==============================================================================
 * HÀM TEST TRỰC TIẾP TRÊN APPS SCRIPT
 * Bấm chọn hàm này và nhấn "Run" (Chạy) để nhận ngay 1 thông báo thử nghiệm!
 * ==============================================================================
 */
function testNotification() {
  var testTopic = "Landing Page Bất Động Sản Chuẩn SEO: Bí Quyết Chốt Khách Hàng Triệu Đô 2026";
  var testStatus = "Đã lên lịch";
  var testUrl = "https://www.luviet.com";
  var testTime = new Date().toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
  var testLabels = "dich-vu, tin-tuc";

  sendTelegramMessage(testTopic, testStatus, testUrl, testTime, testLabels, 2);
  sendEmailNotification(testTopic, testStatus, testUrl, testTime, testLabels, 2);
  Logger.log("✅ Đã gửi thông báo test thành công tới Telegram & Email!");
}

function doGet(e) {
  return ContentService.createTextOutput("✅ Blogger Google Sheets Webhook đang hoạt động bình thường! Đã tích hợp gửi Email & Telegram.").setMimeType(ContentService.MimeType.TEXT);
}
