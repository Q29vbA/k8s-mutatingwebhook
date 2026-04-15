import base64
import json
from fastapi import FastAPI, Request

app = FastAPI(title="my-mutating-webhook")

# The CPU request value to be injected into containers that do not have it set.
CPU_REQUEST = "500m"


def build_cpu_request_patch(spec: dict) -> list[dict]:
    """Builds a JSON Patch to add the CPU request to containers that do not have it set.
    Args:
        spec: The pod spec from the admission request.
    Returns:
        A list of JSON Patch operations to add the CPU request to the containers.
    """
    patch = []
    for group in ("containers", "initContainers"):
        for i, container in enumerate(spec.get(group, [])):
            resources = container.get("resources")
            requests = resources.get("requests") if resources else None

            # switch case: no resources, no requests, requests without cpu/different cpu value
            if resources is None:
                patch.append({"op": "add", "path": f"/spec/{group}/{i}/resources", "value": {"requests": {"cpu": CPU_REQUEST}}})
            elif requests is None:
                patch.append({"op": "add", "path": f"/spec/{group}/{i}/resources/requests", "value": {"cpu": CPU_REQUEST}})
            elif requests.get("cpu") != CPU_REQUEST:
                patch.append({"op": "add", "path": f"/spec/{group}/{i}/resources/requests/cpu", "value": CPU_REQUEST})
    return patch


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"ok": True}


@app.post("/webhook/mutate")
async def mutate(request: Request):
    """Main endpoint for the mutating webhook
    Args:
        request: The incoming admission review request from Kubernetes.
    Returns:
        An admission review response with the appropriate JSON Patch to add the CPU request if needed."""
    # Parse the incoming admission review request
    body = await request.json()
    admission_request = body.get("request", {})
    spec = admission_request.get("object", {}).get("spec", {})
    patch = build_cpu_request_patch(spec)

    response = {
        "uid": admission_request.get("uid"),
        "allowed": True,
    }

    if patch:
        response["patchType"] = "JSONPatch"
        response["patch"] = base64.b64encode(json.dumps(patch).encode()).decode()

    return {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": response,
    }