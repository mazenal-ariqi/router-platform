from fastapi import FastAPI

app = FastAPI()

routers = []

@app.get("/")
def home():
    return {"message": "API is running 🚀"}

@app.get("/routers")
def get_routers():
    return routers

@app.post("/routers")
def add_router(name: str, ip: str):
    router = {"name": name, "ip": ip}
    routers.append(router)
    return {"status": "added", "router": router}
