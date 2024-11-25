from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": "not configured",
        "version": "1.0.0"
    }
