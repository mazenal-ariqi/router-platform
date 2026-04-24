from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import engine, Base, SessionLocal
from models import Router
from ssh_client import run_ssh_command

app = FastAPI()

# 🔐 مفتاح الحماية
SECRET_KEY = "my-secret-key"

# إنشاء الجداول
Base.metadata.create_all(bind=engine)

# الاتصال بقاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# الصفحة الرئيسية
# =========================

@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# =========================
# الراوترات (CRUD)
# =========================

@app.get("/routers")
def get_routers(db: Session = Depends(get_db)):
    return db.query(Router).all()


@app.post("/routers")
def add_router(
    name: str,
    ip: str,
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    router = Router(
        name=name,
        ip=ip,
        username=username,
        password=password
    )
    db.add(router)
    db.commit()
    db.refresh(router)
    return router


# =========================
# SSH مباشر (اختياري)
# =========================

@app.get("/router/{router_id}")
def get_router_info(router_id: int, db: Session = Depends(get_db)):
    router = db.query(Router).filter(Router.id == router_id).first()

    if not router:
        return {"error": "Router not found"}

    try:
        result = run_ssh_command(
            ip=router.ip,
            username=router.username,
            password=router.password,
            command="ubus call system board"
        )
        return result
    except Exception as e:
        return {"error": str(e)}


# =========================
# AGENT SYSTEM (🔥 الأساس)
# =========================

routers_status = {}


@app.post("/agent/register")
def register_router(data: dict, db: Session = Depends(get_db)):
    if data.get("key") != SECRET_KEY:
        return {"error": "unauthorized"}

    mac = data.get("mac")
    name = data.get("name", "unknown")

    if not mac:
        return {"error": "MAC is required"}

    router = db.query(Router).filter(Router.mac == mac).first()

    if router:
        return {"router_id": router.id}

    new_router = Router(
        name=name,
        ip="unknown",
        username="root",
        password="root",
        mac=mac
    )

    db.add(new_router)
    db.commit()
    db.refresh(new_router)

    return {"router_id": new_router.id}


@app.post("/agent/update")
def update_router(data: dict, db: Session = Depends(get_db)):
    if data.get("key") != SECRET_KEY:
        return {"error": "unauthorized"}

    router_id = data.get("router_id")

    if not router_id:
        return {"error": "router_id required"}

    # حفظ الحالة في الذاكرة
    routers_status[str(router_id)] = data

    # تحديث IP في قاعدة البيانات
    router = db.query(Router).filter(Router.id == router_id).first()

    if router:
        router.ip = data.get("ip", router.ip)
        db.commit()

    return {"status": "received"}


# =========================
# COMMAND SYSTEM
# =========================

commands = {}


@app.get("/agent/command/{router_id}")
def get_command(router_id: str):
    cmd = commands.get(router_id)

    if cmd:
        del commands[router_id]  # حذف بعد الإرسال

    return cmd or {}


@app.post("/agent/command/{router_id}")
def send_command(router_id: str, cmd: dict):
    commands[router_id] = cmd
    return {"status": "sent"}


# =========================
# STATUS APIs
# =========================

@app.get("/agent/status")
def get_all_status():
    return routers_status


@app.get("/agent/status/{router_id}")
def get_router_status(router_id: str):
    return routers_status.get(router_id, {"error": "not found"})
