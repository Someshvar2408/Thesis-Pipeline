#!/bin/bash
# cleanup.sh - Remove all Kubernetes resources and cleanup

NAMESPACE="thesis-pipeline"

echo "⚠️  WARNING: This will delete all resources in the $NAMESPACE namespace"
read -p "Continue? (yes/no) " -n 3 -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
  echo "Aborted."
  exit 1
fi

echo "🗑️  Cleaning up..."

# Delete namespace (this will delete all resources in it)
kubectl delete namespace $NAMESPACE --ignore-not-found=true

echo "⏳ Waiting for cleanup..."
sleep 5

# Verify deletion
if kubectl get namespace $NAMESPACE 2>/dev/null; then
  echo "❌ Namespace still exists, force deleting..."
  kubectl delete namespace $NAMESPACE --grace-period=0 --force
else
  echo "✅ Cleanup completed successfully"
fi
