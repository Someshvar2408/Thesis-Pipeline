# Quick Start - Docker & Kubernetes

## Quick Local Test (5 minutes)

```bash
cd /u/35/sayapas1/unix/Thesis-Pipeline

# Start services
docker-compose up -d

# Wait for services to be healthy
sleep 10

# Test backend
curl http://localhost:8000/docs

# Test frontend
curl http://localhost

# View logs
docker-compose logs

# Stop everything
docker-compose down
```

## Quick Kubernetes Deployment

### Prerequisites
- kubectl installed and configured
- Images already pushed to registry
- Update image tags in k8s/*.yaml

### Deploy (3 commands)

```bash
# 1. Create namespace and deploy
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml

# 2. Wait for readiness
kubectl wait --for=condition=available --timeout=300s deployment/backend -n thesis-pipeline
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n thesis-pipeline

# 3. Check status
kubectl get all -n thesis-pipeline

# Access application
kubectl port-forward svc/frontend 8080:80 -n thesis-pipeline
# Visit http://localhost:8080
```

## Useful Quick Commands

```bash
# Watch pods starting up
kubectl get pods -n thesis-pipeline -w

# View logs in real-time
kubectl logs -f deployment/backend -n thesis-pipeline

# Connect to a pod
kubectl exec -it deployment/backend -n thesis-pipeline -- bash

# Scale deployment
kubectl scale deployment/backend --replicas=5 -n thesis-pipeline

# Restart deployment
kubectl rollout restart deployment/backend -n thesis-pipeline

# Delete everything
kubectl delete namespace thesis-pipeline
```

## Troubleshooting

```bash
# Pod not running?
kubectl describe pod <pod-name> -n thesis-pipeline

# Image pull errors?
kubectl describe pod <pod-name> -n thesis-pipeline | grep -A 5 Events

# Check resource availability
kubectl top nodes
kubectl top pods -n thesis-pipeline
```
