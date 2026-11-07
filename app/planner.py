def build_plan(desired_interface, current_interface):
    """
    Compare desired interface state with normalized current state
    and return a plan according to specs/plan-spec-v1.md.
    """

    managed_fields = ["ipv4", "description", "admin_state"]

    if current_interface is None:
        return {
            "status": "ok",
            "result": "planned",
            "operation": "create",
            "changes": {
                "ipv4": {"to": desired_interface.get("ipv4")},
                "description": {"to": desired_interface.get("description")},
                "admin_state": {"to": desired_interface.get("admin_state")}
            }
        }

    changes = {}

    for field in managed_fields:
        desired_val = desired_interface.get(field)
        current_val = current_interface.get(field)
        
        if desired_val != current_val:
            changes[field] = {
                "from": current_val,
                "to": desired_val
            }

    if changes:
        return {
            "status": "ok",
            "result": "planned",
            "operation": "update",
            "changes": changes
        }
    else:
        return {
            "status": "ok",
            "result": "planned",
            "operation": "no_change",
            "changes": {}
        }