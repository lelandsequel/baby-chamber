"""Minimal REST wrapper for STRATA-mini.

POST a raw game tick to /action and get the chosen game action back.
The strata_mini package itself has zero runtime dependencies; only this optional
server needs FastAPI/uvicorn.

    uvicorn app:app --reload --port 8099
"""
from fastapi import FastAPI, Request

from strata_mini.bot import choose_action

app = FastAPI(title="STRATA-mini", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/action")
async def action(request: Request):
    raw = await request.json()
    return choose_action(raw)
