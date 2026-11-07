
import yaml

# 1. ตรวจสอบข้อมูล Request จาก YAML


def validate_request(data):


    # 1.1 ตรวจสอบ Version

    # ต้องมี Key version และต้องมีค่าเป็น Integer 1 เท่านั้น
    if 'version' not in data:
        return {"status": "error", "result": "invalid_version"}

    version = data.get('version')

    # ป้องกันค่า String, Float และ Boolean
    if type(version) is not int or isinstance(version, bool) or version != 1:
        return {"status": "error", "result": "invalid_version"}

    # 1.2 ตรวจสอบ Router

    # ต้องมี IP Address ของ Router
    if 'router' not in data:
        return {"status": "error", "result": "missing_router"}

    router = data.get('router')

    # รายการ IP Address ของ Router ที่อนุญาต
    allowed_routers = [
        "10.0.29.101",
        "10.0.29.102",
        "10.0.29.103",
        "10.0.29.104",
        "10.0.29.105"
    ]

    # ตรวจสอบว่า Router อยู่ในรายการที่อนุญาตหรือไม่
    if router not in allowed_routers:
        return {"status": "error", "result": "invalid_router"}

    # 1.3 ตรวจสอบ Method

    # ต้องมี Key method
    if 'method' not in data:
        return {"status": "error", "result": "missing_method"}

    method = data.get('method')

    # Method ที่ระบบรองรับ
    allowed_methods = [
        "restconf",
        "netconf",
        "ansible",
        "netmiko-textfsm"
    ]

    # ตรวจสอบว่าเป็น Method ที่รองรับหรือไม่
    if method not in allowed_methods:
        return {"status": "error", "result": "invalid_method"}

    # 1.4 ตรวจสอบ Action

    # ต้องมี Key action
    if 'action' not in data:
        return {"status": "error", "result": "missing_action"}

    action = data.get('action')

    # กำหนด Action ที่แต่ละ Method สามารถใช้งานได้
    valid_combinations = {
        "restconf": ["status", "plan", "apply"],
        "netconf": ["status", "plan", "apply"],
        "ansible": ["apply"],
        "netmiko-textfsm": ["status", "delete"]
    }

    # ตรวจสอบว่า Action สามารถใช้กับ Method นี้ได้หรือไม่
    if action not in valid_combinations.get(method, []):
        return {"status": "error", "result": "invalid_action"}

    # --------------------------------------
    # 1.5 ตรวจสอบ Desired และ Interface
    # --------------------------------------

    # ต้องมี desired และข้อมูลต้องเป็น Dictionary
    if 'desired' not in data or not isinstance(data['desired'], dict):
        return {"status": "error", "result": "missing_desired"}

    desired = data.get('desired')

    # ต้องมี interface และข้อมูลต้องเป็น Dictionary
    if 'interface' not in desired or not isinstance(desired['interface'], dict):
        return {"status": "error", "result": "missing_interface"}

    interface = desired.get('interface')

    # ต้องมีชื่อ Interface และห้ามเป็น None
    if 'name' not in interface or interface.get('name') is None:
        return {"status": "error", "result": "missing_interface_name"}

    # 1.6 ตรวจสอบข้อมูลเพิ่มเติม
    # เฉพาะ Action plan และ apply


    if action in ["plan", "apply"]:

        # ตรวจสอบ IPv4
        if 'ipv4' not in interface or interface.get('ipv4') is None:
            return {"status": "error", "result": "missing_ipv4"}

        # ตรวจสอบ Description
        if 'description' not in interface or interface.get('description') is None:
            return {"status": "error", "result": "missing_description"}

        # ตรวจสอบ Admin State
        if 'admin_state' not in interface or interface.get('admin_state') is None:
            return {"status": "error", "result": "missing_admin_state"}

        admin_state = interface.get('admin_state')

        # Admin State ต้องเป็น up หรือ down เท่านั้น
        if admin_state not in ["up", "down"]:
            return {"status": "error", "result": "invalid_admin_state"}

    # 1.7 ข้อมูลผ่านการตรวจสอบทั้งหมด

    return {
        "status": "ok",
        "result": "accepted"
    }

# ==========================================
# 2. อ่านและตรวจสอบไฟล์ YAML

def process_request_file(path):
    """
    อ่านไฟล์ YAML
    ตรวจสอบรูปแบบข้อมูล
    และส่งข้อมูลไปตรวจสอบด้วย validate_request()
    """

    try:

        # เปิดไฟล์ในโหมดอ่าน โดยใช้ UTF-8
        with open(path, 'r', encoding='utf-8') as file:

            # อ่าน YAML และแปลงเป็น Python Object
            data = yaml.safe_load(file)

        # ข้อมูลที่อ่านได้ต้องเป็น Dictionary
        if not isinstance(data, dict):
            return {"status": "error", "result": "invalid_yaml"}

        # ส่งข้อมูลไปตรวจสอบเงื่อนไขต่าง ๆ
        return validate_request(data)

    # กรณีรูปแบบ YAML ไม่ถูกต้อง
    except yaml.YAMLError:
        return {"status": "error", "result": "invalid_yaml"}

    # กรณีเกิด Error อื่น เช่น ไม่พบไฟล์หรือเปิดไฟล์ไม่ได้
    except Exception:
        return {"status": "error", "result": "invalid_yaml"}
