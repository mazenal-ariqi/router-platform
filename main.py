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


    
@app.get("/router/{router_id}")
def get_router_info(router_id: int, db: Session = Depends(get_db)):
    router = db.query(Router).filter(Router.id == router_id).first()

    if not router:
        return {"error": "Router not found"}

    result = run_ssh_command(
        ip=router.ip,
        username=router.username,
        password=router.password,
        command="ubus call system board"
    )

    return result
