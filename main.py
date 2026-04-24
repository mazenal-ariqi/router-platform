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

# عرض الراوترات
@app.get("/routers")
def get_routers(db: Session = Depends(get_db)):
    return db.query(Router).all()

# إضافة راوتر
@app.post("/routers")
def add_router(name: str, ip: str, db: Session = Depends(get_db)):
    router = Router(name=name, ip=ip)
    db.add(router)
    db.commit()
    db.refresh(router)
    return router



@app.get("/router-info")
def get_router_info(ip: str, username: str, password: str):
    result = run_ssh_command(
        ip=ip,
        username=username,
        password=password,
        command="ubus call system board"
    )
    return result
