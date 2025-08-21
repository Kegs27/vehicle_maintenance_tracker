from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content="<h1>MINIMAL TEST</h1>")

@app.get("/test")
def test():
    return {"message": "JSON test"}
