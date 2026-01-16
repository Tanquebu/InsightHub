from fastapi import FastAPI

app = FastAPI(title="InsightHub", version="0.1.0")

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "insighthub", "version": "v1"}
