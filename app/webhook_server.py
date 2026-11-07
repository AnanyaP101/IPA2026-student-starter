
# ใช้จัดการงานที่ทำงานเบื้องหลัง
from concurrent.futures import ThreadPoolExecutor

# ใช้สร้าง HTTP Server เพื่อรับ Webhook จาก Webex
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Library สำหรับจัดการ JSON
import json

# Library สำหรับจัดการ Environment Variable
import os

# ใช้จัดการ Path ของไฟล์
from pathlib import Path

# ใช้สร้างโฟลเดอร์ชั่วคราว
from tempfile import TemporaryDirectory

# Import ฟังก์ชันประมวลผล Request
from app.integration import process_request

# Import Webex Client และ URL ของ Webex API
from app.webex_client import WEBEX_API_BASE, WebexClient


# ==========================================
# 1. จัดการ Event ที่ได้รับจาก Webex
# ==========================================

class WebexEventHandler:

    def __init__(self, client, bot_person_id, processor=None):
        # Webex Client สำหรับเรียก API
        self.client = client

        # ID ของ Bot เพื่อใช้ตรวจสอบข้อความจากตัวเอง
        self.bot_person_id = bot_person_id

        # ฟังก์ชันสำหรับประมวลผล Request
        self.processor = processor or process_request

    def handle_event(self, event):

        # ตรวจสอบว่า Event เป็น Dictionary หรือไม่
        if not isinstance(event, dict):
            return None

        # รับเฉพาะ Event ที่เป็นข้อความใหม่
        if event.get("resource") != "messages":
            return None

        if event.get("event") != "created":
            return None

        # ดึงข้อมูลภายใน Event
        event_data = event.get("data", {})

        if not isinstance(event_data, dict):
            return None

        # ดึง Message ID
        message_id = event_data.get("id")

        if not message_id:
            return None

        # ไม่ประมวลผลข้อความที่ Bot ส่งเอง
        if event_data.get("personId") == self.bot_person_id:
            return None

        # ดึงรายละเอียดข้อความจาก Webex
        message = self.client.get_message(message_id)

        # ตรวจสอบอีกครั้งว่าเป็นข้อความจาก Bot หรือไม่
        if message.get("personId") == self.bot_person_id:
            return None

        # ดึงข้อมูลที่จำเป็นจากข้อความ
        room_id = message.get("roomId")
        mentioned_people = message.get("mentionedPeople", [])
        files = message.get("files", [])

        # ======================================
        # 2. ตรวจสอบไฟล์แนบ
        # ======================================

        # กรณีมีไฟล์แนบมากกว่า 1 ไฟล์
        if len(files) > 1:

            result = {
                "status": "error",
                "result": "multiple_attachments"
            }

        # กรณีมีไฟล์แนบ 1 ไฟล์
        elif len(files) == 1:

            # ดาวน์โหลดไฟล์จาก Webex
            file_bytes = self.client.download_file(files[0])

            # สร้างโฟลเดอร์ชั่วคราว
            with TemporaryDirectory() as temp_dir:

                # กำหนดชื่อไฟล์ YAML
                file_path = Path(temp_dir) / "request.yaml"

                # บันทึกข้อมูลไฟล์ลงในเครื่อง
                file_path.write_bytes(file_bytes)

                try:
                    # ส่งไฟล์ไปตรวจสอบและประมวลผล
                    result = self.processor(
                        mentioned_people,
                        file_path,
                        self.bot_person_id
                    )

                finally:
                    # ลบไฟล์ชั่วคราวหลังประมวลผลเสร็จ
                    if file_path.exists():
                        file_path.unlink()

        # กรณีไม่มีไฟล์แนบ
        else:

            # ส่ง None เพื่อให้ Request Handler ตรวจสอบ
            result = self.processor(
                mentioned_people,
                None,
                self.bot_person_id
            )

        # ======================================
        # 3. ส่งผลลัพธ์กลับไปยัง Webex
        # ======================================

        if room_id and result is not None:

            # แปลงผลลัพธ์เป็น JSON แล้วส่งกลับไปยัง Room
            self.client.send_message(
                room_id,
                json.dumps(result)
            )

        return result


# ==========================================
# 4. สร้าง HTTP Handler สำหรับรับ Webhook
# ==========================================

def make_http_handler(submit_event):

    class RequestHandler(BaseHTTPRequestHandler):

        # รองรับ GET Request
        def do_GET(self):

            # ใช้ตรวจสอบว่า Webhook Server ทำงานอยู่หรือไม่
            if self.path == "/health":

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                response = {
                    "status": "ok",
                    "result": "healthy"
                }

                self.wfile.write(json.dumps(response).encode())

            else:
                # ไม่พบ URL ที่ร้องขอ
                self.send_response(404)
                self.end_headers()

        # รองรับ POST Request
        def do_POST(self):

            # รับเฉพาะ URL /webhook
            if self.path != "/webhook":
                self.send_response(404)
                self.end_headers()
                return

            # อ่านขนาดข้อมูลที่ส่งเข้ามา
            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            # ตรวจสอบว่าข้อมูลไม่ว่างและไม่ใหญ่เกินไป
            if content_length < 1 or content_length > 1_000_000:

                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                response = {
                    "status": "error",
                    "result": "invalid_event"
                }

                self.wfile.write(json.dumps(response).encode())
                return

            # อ่านข้อมูลจาก Request Body
            raw_body = self.rfile.read(content_length)

            # แปลง JSON เป็น Python Dictionary
            try:
                event_data = json.loads(raw_body.decode("utf-8"))

                # Event ต้องเป็น Dictionary
                if not isinstance(event_data, dict):
                    raise ValueError()

            except Exception:

                # หาก JSON ไม่ถูกต้อง ให้ตอบกลับ 400
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                response = {
                    "status": "error",
                    "result": "invalid_event"
                }

                self.wfile.write(json.dumps(response).encode())
                return

            # ตอบกลับ Webex ว่าได้รับ Event แล้ว
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response = {
                "status": "ok",
                "result": "accepted"
            }

            self.wfile.write(json.dumps(response).encode())

            # ส่ง Event ไปประมวลผลเบื้องหลัง
            submit_event(event_data)

        # ปิด Log ของ HTTP Server
        def log_message(self, format, *args):
            pass

    return RequestHandler


# ==========================================
# 5. เริ่มต้น Webhook Server
# ==========================================

def main():

    # --------------------------------------
    # 5.1 โหลดค่าจากไฟล์ .env
    # --------------------------------------

    env_file = Path(".env")

    if env_file.exists():

        # อ่านข้อมูลทั้งหมดในไฟล์ .env
        lines = env_file.read_text(encoding="utf-8").splitlines()

        for line in lines:

            line = line.strip()

            # ข้ามบรรทัดว่างและ Comment
            if line and not line.startswith("#") and "=" in line:

                # แยกชื่อตัวแปรและค่า
                key, value = line.split("=", 1)

                # บันทึกลง Environment Variable
                os.environ.setdefault(
                    key.strip(),
                    value.strip().strip("'\"")
                )

    # --------------------------------------
    # 5.2 เชื่อมต่อกับ Webex Bot
    # --------------------------------------

    token = os.getenv("WEBEX_BOT_TOKEN")

    # สร้าง Webex Client
    client = WebexClient(token=token)

    # ตรวจสอบตัวตนของ Bot ผ่าน Webex API
    response = client.session.get(
        f"{WEBEX_API_BASE}/people/me",
        headers=client.headers,
        timeout=10
    )

    response.raise_for_status()

    # ดึง Person ID ของ Bot
    bot_person_id = response.json().get("id")

    # สร้าง Event Handler
    handler = WebexEventHandler(
        client,
        bot_person_id
    )

    # --------------------------------------
    # 5.3 ตั้งค่าการประมวลผลเบื้องหลัง
    # --------------------------------------

    # กำหนดให้ประมวลผลทีละ 1 Event
    executor = ThreadPoolExecutor(max_workers=1)

    # --------------------------------------
    # 5.4 ตั้งค่า HTTP Server
    # --------------------------------------

    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", 8000))

    # สร้าง HTTP Server
    server = ThreadingHTTPServer(
        (host, port),
        make_http_handler(
            lambda event: executor.submit(
                handler.handle_event,
                event
            )
        )
    )

    print(f"Webhook server started at http://{host}:{port}")

    # เริ่มเปิด Server เพื่อรอรับ Event
    try:
        server.serve_forever()

    finally:
        # ปิดการทำงานของ Executor เมื่อ Server หยุด
        executor.shutdown(wait=True)



if __name__ == "__main__":
    main()
