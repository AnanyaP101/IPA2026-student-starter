
# Import ฟังก์ชันสำหรับอ่านและตรวจสอบไฟล์ YAML
from .core import process_request_file


# ==========================================
# 1. ตรวจสอบข้อมูล Webex Envelope
# ==========================================

def validate_webex_envelope(
    mentioned_people,
    attachment_path,
    bot_person_id,
):

    # ตรวจสอบว่า Bot มี ID ที่ถูกต้องหรือไม่
    # bot_person_id ต้องเป็น String และห้ามเป็นค่าว่าง
    if not isinstance(bot_person_id, str) or not bot_person_id:
        return {
            "status": "error",
            "result": "missing_bot_mention"
        }

    # ตรวจสอบว่าข้อมูลผู้ที่ถูก Mention เป็น List หรือไม่
    # และต้องมี ID ของ Bot อยู่ใน List
    if (
        not isinstance(mentioned_people, list)
        or bot_person_id not in mentioned_people
    ):
        return {
            "status": "error",
            "result": "missing_bot_mention"
        }

    # ตรวจสอบว่ามีไฟล์ YAML แนบมาหรือไม่
    # หากไม่มีไฟล์แนบ ให้ส่ง Error no_yaml
    if attachment_path is None:
        return {
            "status": "error",
            "result": "no_yaml"
        }

    # หากผ่านการตรวจสอบทั้งหมด ให้คืนค่า None
    # หมายถึงไม่พบ Error
    return None


# ==========================================
# 2. จัดการ Webex Request
# ==========================================

def handle_webex_request(
    mentioned_people,
    attachment_path,
    bot_person_id,
):
    """
    ตรวจสอบ Webex Envelope ก่อน
    จากนั้นส่งไฟล์ YAML ไปตรวจสอบใน core.py
    และคืนผลลัพธ์เป็น Dictionary
    """

    # ขั้นตอนที่ 1: ตรวจสอบ Webex Envelope
    envelope_error = validate_webex_envelope(
        mentioned_people,
        attachment_path,
        bot_person_id
    )

    # หากพบ Error ให้ส่งกลับทันที
    # โดยไม่ต้องอ่านไฟล์ YAML ต่อ
    if envelope_error is not None:
        return envelope_error

    # ขั้นตอนที่ 2: ตรวจสอบไฟล์ YAML
    # ส่ง Path ของไฟล์ไปให้ core.py ประมวลผล
    return process_request_file(attachment_path)
