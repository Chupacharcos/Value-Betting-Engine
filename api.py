"""Value Betting Engine — FastAPI App"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.valuebet import router

app = FastAPI(title="Value Betting Engine", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "value-engine", "port": 8003}
