from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Vehicle Maintenance Tracker")

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content="<h1>Vehicle Maintenance Tracker</h1><p>App is running!</p>")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Vehicle Maintenance Tracker is running"}

@app.get("/test")
async def test_endpoint():
    return {"message": "App is working!", "timestamp": "2024-08-21"}
