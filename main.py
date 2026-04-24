from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import engine, Base, SessionLocal
from models import Router
from ssh_client import run_ssh_command

app = FastAPI()

# إنشاء الجداول
Base.metadata.create_all(bind=engine)

# الاتصال بقاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# الصفحة الرئيسية
@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# =========================
# الراوترات (CRUD)
# =========================

# عرض الراوترات
@app.get("/routers")
def get_routers(db: Session = Depends(get_db)):
    return db.query(Router).all()

# إضافة راوتر
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
# AGENT SYSTEM (الأهم 🔥)
# =========================

# تخزين الحالات
routers_status = {}

# استقبال بيانات من الراوتر
@app.post("/agent/update")
def update_router(data: dict):
    router_id = str(data.get("router_id"))

    routers_status[router_id] = data

    return {"status": "received"}


# =========================
# COMMAND SYSTEM
# =========================

commands = {}

# ✅ تعديل مهم: حذف الأمر بعد استلامه (مهم جدًا)
@app.get("/agent/command/{router_id}")
def get_command(router_id: str):
    cmd = commands.get(router_id)

    if cmd:
        del commands[router_id]  # حذف بعد الإرسال

    return cmd or {}


# إرسال أمر من السيرفر للراوتر
@app.post("/agent/command/{router_id}")
def send_command(router_id: str, cmd: dict):
    commands[router_id] = cmd
    return {"status": "sent"}


# =========================
# STATUS APIs
# =========================

# كل الحالات
@app.get("/agent/status")
def get_all_status():
    return routers_status

# حالة راوتر واحد
@app.get("/agent/status/{router_id}")
def get_router_status(router_id: str):
    return routers_status.get(router_id, {"error": "not found"})
