# Mutating Admission Webhook

Inspired by [Kristijan Mitevski awesome blog post](https://kmitevski.com/kubernetes-mutating-webhook-with-python-and-fastapi/)!

A Kubernetes mutating admission webhook that automatically injects a `500m` CPU request into any pod container that doesn't already have one. Built with FastAPI.

## How It Works

The webhook intercepts pod CREATE requests via a `MutatingWebhookConfiguration`. For each container (and init container), if a CPU request is missing or different from `500m`, it generates a JSON Patch to set it.

## Setup

### 1. Generate TLS Certs

The webhook must serve over HTTPS. Generate a self-signed cert with the SAN matching the in-cluster service DNS name:

```bash
openssl req -x509 -sha256 -newkey rsa:2048 \
  -keyout webhook.key -out webhook.crt \
  -days 1024 -nodes \
  -addext "subjectAltName = DNS.1:my-webhook.default.svc"
```

Create the Kubernetes secret (referenced by the deployment):

```bash
kubectl create secret tls my-webhook-certs \
  --cert=webhook.crt \
  --key=webhook.key \
  -n default
```

### 2. Set the CA Bundle

Paste the base64-encoded cert into `k8s/mutatingwebhookconfiguration.yaml` under `caBundle`:

```bash
cat webhook.crt | base64 | tr -d '\n'
```

### 3. Build the Image

Built locally with minikube to avoid pushing to an external registry:

```bash
minikube image build -t my-webhook:v1 .
```

> Since the image is loaded directly into minikube, `imagePullPolicy` is set to `Never` in the deployment manifest.

### 4. Deploy

Use `kubectl apply -f` on files under k8s folder. Make sure to apply the MutatingWebhookConfiguration **last** (or with failurePolicy: ignore instead of Fail), or else your pod won't be able to start.

### 5. Test It

Create a test pod manually and verify the CPU request was injected:

```bash
kubectl apply -f tests/flasktestpod.yaml
kubectl get pod flasktest -o jsonpath='{.spec.containers[*].resources}'
```
Or automatically:
```bash
pytest -v tests/test_webhook.py
```
