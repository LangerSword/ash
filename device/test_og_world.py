"""Tests for the 0G mock/adapter and the World verify parser. No network."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from og import MockRouter, RouterDecider
from world_idkit import StaticWorld, WorldError, _human_id


def case_mock() -> None:
    r = MockRouter()
    out = r.classify({"edges": 3})
    assert out["mock"] is True and out["decision"] == "hold"
    rel = r.release({"container": "C-1"}, "human-1")
    assert rel["mock"] is True and rel["decision"] == "release"
    ok, reason, meta = RouterDecider(r).release({"container": "C-1"}, "human-1")
    assert ok and meta["mock"] is True
    print("mock router + decider ok")


def case_human_id() -> None:
    assert _human_id({"nullifier": "0xabc"}) == "0xabc"
    assert _human_id({"responses": [{"nullifier": "0xdef"}]}) == "0xdef"
    assert _human_id({"responses": [{"identifier": "orb", "nullifier_hash": "0x123"}]}) == "0x123"
    try:
        _human_id({"responses": []})
    except WorldError:
        print("nullifier parsing      ok")
        return
    raise AssertionError("missing nullifier accepted")


def case_static_world() -> None:
    w = StaticWorld({"good": "human-1"})
    assert w.verify("good") == "human-1"
    try:
        w.verify("bad")
    except WorldError:
        print("world rejection        ok")
        return
    raise AssertionError("bad proof accepted")


if __name__ == "__main__":
    case_mock(); case_human_id(); case_static_world()
    print("all og/world tests passed")
