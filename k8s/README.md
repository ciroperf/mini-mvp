# Deploy su Kubernetes

Manifest di esempio per girare l'API su un cluster Kubernetes. Non
richiedono CRD esterne (eccetto l'HPA, che usa `autoscaling/v2` gia'
presente su cluster recenti).

## File

- `deployment.yaml` — Deployment con readiness/liveness probe su
  `/health`, resource requests/limits, `terminationGracePeriodSeconds`
  per lo shutdown graceful su `SIGTERM`.
- `service.yaml` — Service `ClusterIP` sulla porta 80 verso il
  container (8000).
- `configmap.yaml` — variabili non sensibili (es. `REDIS_URL`).
- `secret.example.yaml` — placeholder per le variabili sensibili
  (`DATABASE_URL`, credenziali Postgres). Copiare in `secret.yaml`
  (non versionato) con i valori reali prima di applicare.
- `hpa.yaml` — autoscaling orizzontale basato sulla CPU (2-5 replica,
  target 70% di utilizzo).

## Minikube

```bash
minikube start
kubectl apply -f k8s/configmap.yaml -f k8s/secret.example.yaml \
  -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/hpa.yaml
kubectl port-forward svc/mini-mvp 8000:80
```

Se l'immagine non e' su un registry, buildarla nel registry Docker di
minikube prima di applicare il Deployment:

```bash
eval $(minikube docker-env)
docker build -t mini-mvp:latest .
```

## Validazione (CI)

`kubectl apply --dry-run=client` contatta comunque l'API server per la
discovery delle risorse (RESTMapper), anche in modalita' client. Senza
un cluster reale, in CI basta un cluster `kind` effimero solo per la
validazione:

```bash
kind create cluster --name k8s-validate
kubectl apply --dry-run=client -f k8s/
kind delete cluster --name k8s-validate
```

## EKS

Serve un metrics-server attivo nel cluster perche' l'HPA funzioni
(su EKS gestito di solito e' gia' installato come addon). Pubblicare
l'immagine su un registry raggiungibile dal cluster (es. ECR) e
aggiornare `image:` in `deployment.yaml` di conseguenza, poi:

```bash
kubectl apply -f k8s/configmap.yaml -f k8s/secret.example.yaml \
  -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/hpa.yaml
```

Per esporre il servizio fuori dal cluster, aggiungere un `Ingress` o
cambiare il `type` del Service in `LoadBalancer` (non incluso qui
perche' dipende dal controller/ALB scelto).
