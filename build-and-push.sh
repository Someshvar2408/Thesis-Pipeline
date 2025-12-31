#!/bin/bash
# build-and-push.sh - Build Docker images and push to registry

set -e

# Configuration
REGISTRY="${1:-docker.io}"
NAMESPACE="${2:-your-username}"
VERSION="${3:-latest}"

echo "🐳 Building Docker images..."
echo "Registry: $REGISTRY"
echo "Namespace: $NAMESPACE"
echo "Version: $VERSION"

# Build backend
echo ""
echo "📦 Building backend image..."
docker build \
  --tag "$REGISTRY/$NAMESPACE/thesis-backend:$VERSION" \
  --tag "$REGISTRY/$NAMESPACE/thesis-backend:latest" \
  ./backend

# Build frontend
echo ""
echo "📦 Building frontend image..."
docker build \
  --tag "$REGISTRY/$NAMESPACE/thesis-frontend:$VERSION" \
  --tag "$REGISTRY/$NAMESPACE/thesis-frontend:latest" \
  ./frontend

# Push images
echo ""
echo "📤 Pushing images to registry..."
docker push "$REGISTRY/$NAMESPACE/thesis-backend:$VERSION"
docker push "$REGISTRY/$NAMESPACE/thesis-backend:latest"
docker push "$REGISTRY/$NAMESPACE/thesis-frontend:$VERSION"
docker push "$REGISTRY/$NAMESPACE/thesis-frontend:latest"

echo ""
echo "✅ Build and push completed successfully!"
echo ""
echo "Update k8s manifests with:"
echo "sed -i 's|your-registry|$REGISTRY/$NAMESPACE|g' k8s/*.yaml"
