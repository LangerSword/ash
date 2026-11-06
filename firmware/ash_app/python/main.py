"""Ash board app: the bridge that answers HTTP, and the Tier 1 0G decision.

The container cannot do TLS on this platform, so every outbound call goes to the
laptop relay on the USB link (tools/relay.py). Tier 1 runs *here*, on the board,
so the decision is made next to the sensor, not on the laptop.
"""
import json, os, time, urllib.request
from arduino.app_utils import App, Bridge
import server

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
key = ""
envp = os.path.join(ROOT, ".env")
if os.path.exists(envp):
    for line in open(envp).read().splitlines():
        if line.startswith("OG_API_KEY="):
            key = line.split("=", 1)[1].strip()

MODEL = os.environ.get("OG_MODEL", "0gm-1.0-35b-a3b")
RELAY = os.environ.get("ASH_RELAY", "http://172.17.0.1:9001/relay")

# Same semantics as device/og.py: the vector is digital, not analog.
TIER1_SYSTEM = (
    "You are a custody incident classifier for a tamper-evident seal. "
    "The input is a JSON feature vector from a wire loop read by a digital pin; "
    "there are no analog values, only edges and timings. Fields: "
    "edges (open transitions in the last 500 ms), open_ms (how long the loop was open "
    "in the most recent event), since_arm_ms (uptime when the event fired), "
    "counter (wipes so far), policy, deadline_ms. "
    "Return strict JSON only: "
    '{"decision":"hold|wipe","cause":"handling|intrusion|unknown"}. '
    "hold when the event is short and clean: open_ms under 250, edges 1 or 2, loop closed "
    "again — a box being moved, a lid seated, a cable brushed. "
    "wipe when the open is long (open_ms 250 or more), when edges keep recurring, or when "
    "the input is malformed or missing fields — fail closed. "
    "Never invent events that are not in the input."
)

pending = []


def on_amb(*a):
    pending.append(str(a[0]) if a else "{}")


def on_tamper(*a):
    print("TAMPER", a, flush=True)


def on_hold(*a):
    print("HOLD", a, flush=True)


Bridge.provide("ev_ambiguous", on_amb)
Bridge.provide("ev_tamper", on_tamper)
Bridge.provide("ev_hold", on_hold)


def og_classify(features):
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": TIER1_SYSTEM},
            {"role": "user", "content": features},
        ],
        "max_tokens": 200,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "verify_tee": True,
        "reasoning_effort": "minimal",
        "chat_template_kwargs": {"enable_thinking": False},
    }
    env = {
        "url": "https://router-api.0g.ai/v1/chat/completions",
        "method": "POST",
        "headers": {"Content-Type": "application/json", "Authorization": "Bearer " + key},
        "body": json.dumps(body),
    }
    req = urllib.request.Request(RELAY, data=json.dumps(env).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        out = json.loads(r.read().decode())
    if out.get("status", 200) >= 400:
        raise RuntimeError(str(out)[:160])
    p = json.loads(out["body"])
    d = json.loads(p["choices"][0]["message"]["content"])
    trace = p.get("x_0g_trace") or {}
    d["request_id"] = trace.get("request_id") or p.get("id")
    d["model"] = p.get("model")
    d["tee_verified"] = trace.get("tee_verified")
    return d


def loop():
    if pending:
        feats = pending.pop(0)
        try:
            d = og_classify(feats)
        except Exception as e:
            d = {"decision": "wipe", "cause": "unknown", "error": repr(e)[:160]}
        Bridge.call("decision", d.get("decision", "wipe"))
        print("TIER1", json.dumps(d), flush=True)
    time.sleep(0.2)


server.start(8080)
App.run(user_loop=loop)
