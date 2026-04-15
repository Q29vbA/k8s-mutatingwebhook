"""Unit tests for the mutating webhook logic in app/main.py. These tests use FastAPI's TestClient to simulate admission review requests and verify that the correct JSON Patch is generated to add CPU requests to containers when needed. The tests cover various scenarios, including missing resources, missing requests, and already set CPU values.
Run pytest in the taskone directory to execute these tests:
$ pytest tests/test_webhook.py
"""
import json
import base64

import pytest
from fastapi.testclient import TestClient

from app.main import app, CPU_REQUEST

client = TestClient(app)


def make_review(obj: dict) -> dict:
    return {
        "request": {
            "uid": "test-uid-1234",
            "object": obj,
        }
    }


def decode_patch(patch_b64: str) -> list:
    return json.loads(base64.b64decode(patch_b64).decode())


# --- no containers ---

def test_no_containers_no_patch():
    review = make_review({"spec": {}})
    res = client.post("/webhook/mutate", json=review)
    assert res.status_code == 200
    body = res.json()
    assert body["response"]["allowed"] is True
    assert "patch" not in body["response"]


# --- containers missing resources entirely ---

def test_container_missing_resources():
    review = make_review({
        "spec": {
            "containers": [{"name": "app", "image": "nginx"}]
        }
    })
    res = client.post("/webhook/mutate", json=review)
    patch = decode_patch(res.json()["response"]["patch"])
    assert any(
        p["path"] == "/spec/containers/0/resources"
        and p["value"]["requests"]["cpu"] == CPU_REQUEST
        for p in patch
    )


# --- containers missing requests ---

def test_container_missing_requests():
    review = make_review({
        "spec": {
            "containers": [{"name": "app", "image": "nginx", "resources": {}}]
        }
    })
    res = client.post("/webhook/mutate", json=review)
    patch = decode_patch(res.json()["response"]["patch"])
    assert any(
        p["path"] == "/spec/containers/0/resources/requests"
        and p["value"]["cpu"] == CPU_REQUEST
        for p in patch
    )


# --- containers missing cpu ---

def test_container_missing_cpu():
    review = make_review({
        "spec": {
            "containers": [{"name": "app", "image": "nginx", "resources": {"requests": {"memory": "128Mi"}}}]
        }
    })
    res = client.post("/webhook/mutate", json=review)
    patch = decode_patch(res.json()["response"]["patch"])
    assert any(
        p["path"] == "/spec/containers/0/resources/requests/cpu"
        and p["value"] == CPU_REQUEST
        for p in patch
    )


# --- containers already have correct cpu ---

def test_container_cpu_already_set():
    review = make_review({
        "spec": {
            "containers": [{"name": "app", "image": "nginx", "resources": {"requests": {"cpu": CPU_REQUEST}}}]
        }
    })
    res = client.post("/webhook/mutate", json=review)
    assert "patch" not in res.json()["response"]


# --- initContainers patched as well ---

def test_init_container_missing_resources():
    review = make_review({
        "spec": {
            "containers": [{"name": "app", "image": "nginx", "resources": {"requests": {"cpu": CPU_REQUEST}}}],
            "initContainers": [{"name": "init", "image": "busybox"}],
        }
    })
    res = client.post("/webhook/mutate", json=review)
    patch = decode_patch(res.json()["response"]["patch"])
    assert any("/spec/initContainers/0" in p["path"] for p in patch)


# --- uid is preserved ---

def test_uid_preserved():
    review = make_review({"spec": {}})
    res = client.post("/webhook/mutate", json=review)
    assert res.json()["response"]["uid"] == "test-uid-1234"