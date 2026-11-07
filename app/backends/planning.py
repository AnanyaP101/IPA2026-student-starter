from app.planner import build_plan

def plan_interface(router, desired_interface, get_interface_state):
    """Build a Part 2 plan from backend status."""

    response = get_interface_state(router, desired_interface["name"])

    if response["status"] == "error":
        return response

    current_interface = response.get("interface")

    return build_plan(desired_interface, current_interface)