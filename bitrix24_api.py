import requests
from datetime import datetime

BITRIX_WEBHOOK = "https://happycake.bitrix24.kz/rest/92/e9fs2tnd889fndl0/"

def get_tasks():
    try:
        r = requests.post(BITRIX_WEBHOOK + "task.item.list").json()
        return r.get("result", [])
    except:
        return []

def get_users():
    try:
        r = requests.post(BITRIX_WEBHOOK + "user.list").json()
        return r.get("result", [])
    except:
        return []

def analyze_tasks():
    tasks = get_tasks()
    users = {u.get("ID"): u.get("NAME") for u in get_users()}
    overdue = sum(1 for t in tasks if t.get("status") not in ["5","6"])
    return {"total": len(tasks), "overdue": overdue, "users": len(users)}

def get_report():
    a = analyze_tasks()
    return f"📊 Задач: {a['total']}\n🔴 Просрочено: {a['overdue']}\n👥 Людей: {a['users']}"
