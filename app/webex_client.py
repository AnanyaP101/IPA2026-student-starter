
import os
import requests


# URL หลักของ Webex REST API
WEBEX_API_BASE = "https://webexapis.com/v1"


class WebexClient:

    # ==========================================
    # 1. สร้าง Webex Client
    # ==========================================

    def __init__(self, token=None, session=None):

        # รับ Token จาก Parameter หรือ Environment Variable
        self.token = token or os.environ.get("WEBEX_BOT_TOKEN")

        # ตรวจสอบว่ามี Token หรือไม่
        if not self.token:
            raise PermissionError("Webex token is missing")

        # สร้าง Session สำหรับส่ง HTTP Request
        # หากมี Session จากภายนอกให้ใช้ Session นั้น
        self.session = session or requests.Session()

    # ==========================================
    # 2. กำหนด Header สำหรับ Authentication
    # ==========================================

    @property
    def headers(self):

        # ส่ง Token เพื่อยืนยันตัวตนกับ Webex API
        return {
            "Authorization": f"Bearer {self.token}"
        }

    # ==========================================
    # 3. ดึงข้อความจาก Webex
    # ==========================================

    def get_message(self, message_id):

        # สร้าง URL สำหรับดึงข้อความตาม Message ID
        url = f"{WEBEX_API_BASE}/messages/{message_id}"

        # ส่ง GET Request ไปยัง Webex API
        response = self.session.get(
            url,
            headers=self.headers,
            timeout=10
        )

        # ตรวจสอบ HTTP Error
        response.raise_for_status()

        # แปลงข้อมูล JSON เป็น Python Dictionary
        return response.json()

    # ==========================================
    # 4. ดาวน์โหลดไฟล์จาก Webex
    # ==========================================

    def download_file(self, file_url):

        # ส่ง GET Request เพื่อดาวน์โหลดไฟล์
        response = self.session.get(
            file_url,
            headers=self.headers,
            timeout=10
        )

        # ตรวจสอบ HTTP Error
        response.raise_for_status()

        # ส่งคืนข้อมูลไฟล์ในรูปแบบ Bytes
        return response.content

    # ==========================================
    # 5. ส่งข้อความกลับไปยัง Webex
    # ==========================================

    def send_message(self, room_id, text):

        # URL สำหรับส่งข้อความ
        url = f"{WEBEX_API_BASE}/messages"

        # กำหนดข้อมูลที่จะส่งไปยัง Webex
        payload = {
            "roomId": room_id,
            "text": text
        }

        # ส่ง POST Request เพื่อสร้างข้อความใหม่
        response = self.session.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=10
        )

        # ตรวจสอบ HTTP Error
        response.raise_for_status()

        # ส่งคืนผลลัพธ์จาก Webex API
        return response.json()
