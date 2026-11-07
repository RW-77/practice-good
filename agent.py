"""
agent.py - Check Fold: a dummy bot for testing the heads-up tournament pipeline.

Strategy: check when it is free, otherwise fold.

Self-contained on purpose: it speaks the judge's HTTP protocol directly
instead of importing the participant bundle, so this repo holds no
challenge materials.

    pip install -r requirements.txt && python agent.py    # listens on $PORT (default 5008)
"""

import os
import random

import uvicorn
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

AGENT_NAME = "Check Fold"
TOKEN = os.environ.get("AGENT_TOKEN") or None   # set by the tournament
STATE = {"started": False, "rng": random.Random(0)}


def choose_action(obs: dict) -> str:
    """Return one of obs["legal_actions"]: FOLD, CHECK_CALL, RAISE_HALF or RAISE_POT."""
    legal = obs["legal_actions"]
    return "CHECK_CALL" if obs["to_call"] == 0 else "FOLD"


app = FastAPI()


def refused(token, path):
    if TOKEN and token != TOKEN:
        return JSONResponse({"error": "bad or missing X-Agent-Token"}, status_code=401)
    if not STATE["started"] and path != "/new-half":
        return JSONResponse({"error": "call /new-half first"}, status_code=409)
    return None


@app.get("/")
async def info():
    return {"participant": "Pipeline Test", "agent_name": AGENT_NAME}


@app.post("/new-half")
async def new_half(body: dict, x_agent_token: str | None = Header(None)):
    if (r := refused(x_agent_token, "/new-half")):
        return r
    STATE["started"] = True
    STATE["rng"] = random.Random(0)   # same choices every half, so results repeat
    return {"ok": True}


@app.post("/act")
async def act(body: dict, x_agent_token: str | None = Header(None)):
    if (r := refused(x_agent_token, "/act")):
        return r
    return {"action": choose_action(body["observation"]), "hand_end_errors": []}


@app.post("/hand-end")
async def hand_end(body: dict, x_agent_token: str | None = Header(None)):
    if (r := refused(x_agent_token, "/hand-end")):
        return r
    return {"ok": True, "hand_end_errors": []}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "5008")),
                log_level="warning", access_log=False)
