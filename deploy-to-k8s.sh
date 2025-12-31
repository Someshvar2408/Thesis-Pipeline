#!/bin/bash
# deploy-to-k8s.sh - Deploy application to Kubernetes cluster

set -e

NAMESPACE="thesis-pipeline"
TIMEOUT=300

echo "🚀 Deploying Thesis Pipeline to Kubernetes"
echo "Namespace: $NAMESPACE"
echo ""

# Create namespace and deploy backend
echo "📦 Deploying backend..."
kubectl apply -f k8s/backend.yaml

# Create frontend
echo "📦 Deploying frontend..."
kubectl apply -f k8s/frontend.yaml

# Wait for deployments to be ready
echo ""
echo "⏳ Waiting for backend to be ready (timeout: ${TIMEOUT}s)..."
kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/backend -n $NAMESPACE || {
  echo "❌ Backend deployment timeout"
  kubectl describe deployment backend -n $NAMESPACE
  exit 1
}

echo "⏳ Waiting for frontend to be ready (timeout: ${TIMEOUT}s)..."
kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/frontend -n $NAMESPACE || {
  echo "❌ Frontend deployment timeout"
  kubectl describe deployment frontend -n $NAMESPACE
  exit 1
}

# Get service endpoints
echo ""
echo "✅ Deployment successful!"
echo ""
echo "📊 Deployment Status:"
kubectl get all -n $NAMESPACE

echo ""
echo "🔗 Port forwarding commands:"
echo "  Backend:  kubectl port-forward svc/backend 8000:8000 -n $NAMESPACE"
echo "  Frontend: kubectl port-forward svc/frontend 8080:80 -n $NAMESPACE"

echo ""
echo "📋 View logs:"
echo "  Backend:  kubectl logs -f deployment/backend -n $NAMESPACE"
echo "  Frontend: kubectl logs -f deployment/frontend -n $NAMESPACE"
