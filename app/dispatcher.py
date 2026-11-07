
from app.backends import ansible, netconf, netmiko_textfsm, restconf

def dispatch_request(data):

    action = data["action"]

    method = data["method"]

    router = data["router"]

    # อ่านข้อมูล Interface จากส่วน desired.interface
    desired_interface = data.get("desired", {}).get("interface")

    # ดึงชื่อ Interface เช่น Loopback123
    # ถ้าไม่มี desired.interface ให้ลองอ่าน desired.interface_name แทน
    interface_name = (
        desired_interface["name"]
        if desired_interface
        else data.get("desired", {}).get("interface_name")
    )

    if action == "status":

        # Netmiko + TextFSM ใช้อ่านสถานะ Interface ผ่าน CLI
        if method == "netmiko-textfsm":
            return netmiko_textfsm.get_interface_state(
                router,
                interface_name
            )

        # RESTCONF ใช้ GET Request อ่านข้อมูล Interface
        if method == "restconf":
            return restconf.get_interface_state(
                router,
                interface_name
            )

        # NETCONF ใช้ get-config อ่านข้อมูล Interface
        if method == "netconf":
            return netconf.get_interface_state(
                router,
                interface_name
            )

    elif action == "delete":

        # Netmiko + TextFSM ใช้คำสั่ง CLI ลบ Interface
        if method == "netmiko-textfsm":
            return netmiko_textfsm.delete_interface(
                router,
                interface_name
            )

    elif action == "apply":

        # Ansible ใช้ Playbook เพื่อกำหนด Configuration
        if method == "ansible":
            return ansible.apply_interface(
                router,
                desired_interface
            )

        # RESTCONF ใช้ PUT Request เพื่อกำหนด Configuration
        if method == "restconf":
            return restconf.apply_interface(
                router,
                desired_interface
            )

        # NETCONF ใช้ edit-config เพื่อกำหนด Configuration
        if method == "netconf":
            return netconf.apply_interface(
                router,
                desired_interface
            )

    elif action == "plan":

        # RESTCONF อ่านสถานะปัจจุบันแล้วสร้างแผน
        if method == "restconf":
            return restconf.plan_interface(
                router,
                desired_interface
            )

        # NETCONF อ่านสถานะปัจจุบันแล้วสร้างแผน
        if method == "netconf":
            return netconf.plan_interface(
                router,
                desired_interface
            )
    # แจ้ง Error หากเลือก Backend หรือ Action ที่ไม่รองรับ
    raise ValueError(
        f"Unsupported action/method: {action}/{method}"
    )
