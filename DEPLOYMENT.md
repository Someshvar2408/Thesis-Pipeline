# Thesis Pipeline - Containerization & Kubernetes Deployment Guide

This guide provides step-by-step instructions to containerize and deploy the Thesis Pipeline application on an EC2 instance using Kubernetes.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development with Docker Compose](#local-development)
3. [Building Docker Images](#building-docker-images)
4. [EC2 Setup](#ec2-setup)
5. [Kubernetes Cluster Setup](#kubernetes-setup)
6. [Deploying to Kubernetes](#deploying)
7. [Monitoring & Troubleshooting](#monitoring)
8. [Production Considerations](#production)

## Prerequisites {#prerequisites}

### Local Machine
- Docker Desktop (20.10+)
- Docker Compose (2.0+)
- kubectl (1.28+)
- Git

### AWS Resources
- EC2 Instance (t3.xlarge or larger recommended)
- VPC with public subnets
- Security Groups configured
- Docker Hub account or private registry (ECR)

## Local Development with Docker Compose {#local-development}

### 1. Build and Run Locally

```bash
cd /u/35/sayapas1/unix/Thesis-Pipeline

# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Access application
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 2. Test the Application

```bash
# Health check
curl http://localhost:8000/docs

# Upload test CSV (if your app has upload endpoint)
curl -X POST http://localhost:8000/upload-csv -F "file=@test.csv"
```

### 3. Stop Services

```bash
docker-compose down
docker-compose down -v  # Remove volumes too
```

## Building Docker Images {#building-docker-images}

### Option 1: Using Docker Hub

```bash
# Login to Docker Hub
docker login

# Build backend
docker build -t your-username/thesis-backend:1.0.0 ./backend
docker build -t your-username/thesis-backend:latest ./backend

# Build frontend
docker build -t your-username/thesis-frontend:1.0.0 ./frontend
docker build -t your-username/thesis-frontend:latest ./frontend

# Push to registry
docker push your-username/thesis-backend:1.0.0
docker push your-username/thesis-backend:latest
docker push your-username/thesis-frontend:1.0.0
docker push your-username/thesis-frontend:latest
```

### Option 2: Using AWS ECR

```bash
# Create repositories
aws ecr create-repository --repository-name thesis-backend --region us-east-1
aws ecr create-repository --repository-name thesis-frontend --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-backend:latest ./backend
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-frontend:latest ./frontend

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-frontend:latest
```

## EC2 Setup {#ec2-setup}

### 1. Launch EC2 Instance

**Recommended Specifications:**
- **AMI**: Ubuntu 22.04 LTS
- **Instance Type**: t3.xlarge (for Kubernetes)
- **Storage**: 50 GB EBS
- **Security Group**: Allow ports 22, 80, 443, 6443

### 2. Connect to EC2

```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

### 3. Update System

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
```

### 4. Install Docker

```bash
# Add Docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
```

### 5. Install kubectl

```bash
# Download kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify
kubectl version --client
```

## Kubernetes Cluster Setup {#kubernetes-setup}

### Option 1: minikube (Testing/Development)

```bash
# Install minikube
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start --cpus 4 --memory 8192 --disk-size 50g --driver docker

# Enable ingress addon
minikube addons enable ingress

# Get dashboard
minikube dashboard
```

### Option 2: kubeadm (Production-Ready)

#### 2.1 Install kubeadm, kubelet, and kubectl

```bash
# Add Kubernetes repository
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg

echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

#### 2.2 Prepare the System

```bash
# Disable swap
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Load required modules
sudo modprobe overlay
sudo modprobe br_netfilter

# Configure sysctl
sudo tee /etc/sysctl.d/99-kubernetes.conf <<EOF
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sudo sysctl --system
```

#### 2.3 Initialize Control Plane

```bash
# Initialize kubeadm
sudo kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --kubernetes-version=1.28.0

# Set up kubeconfig
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Verify
kubectl get nodes
```

#### 2.4 Install Container Network Interface (CNI)

```bash
# Install Flannel
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

# Verify
kubectl get pods -n kube-flannel
```

#### 2.5 Untaint Control Plane (Single-node cluster)

```bash
# For development/testing only
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

### Option 3: EKS (AWS Managed)

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create cluster
eksctl create cluster \
  --name thesis-pipeline \
  --region us-east-1 \
  --nodegroup-name thesis-nodes \
  --node-type t3.xlarge \
  --nodes 3 \
  --managed

# Update kubeconfig
aws eks update-kubeconfig --name thesis-pipeline --region us-east-1

# Verify
kubectl get nodes
```

## Deploying to Kubernetes {#deploying}

### 1. Update Image References

Edit `k8s/backend.yaml` and `k8s/frontend.yaml` to use your registry:

```bash
# Replace placeholder with your registry
sed -i 's|your-registry|your-username|g' k8s/*.yaml
```

### 2. Create Namespace

```bash
kubectl apply -f k8s/backend.yaml
# This creates the namespace with other resources
```

### 3. Deploy Backend

```bash
kubectl apply -f k8s/backend.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/backend -n thesis-pipeline

# Check status
kubectl get deployments -n thesis-pipeline
kubectl get pods -n thesis-pipeline
kubectl get svc -n thesis-pipeline
```

### 4. Deploy Frontend

```bash
kubectl apply -f k8s/frontend.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n thesis-pipeline

# Check status
kubectl get deployments -n thesis-pipeline
kubectl get pods -n thesis-pipeline
```

### 5. Install NGINX Ingress Controller

```bash
# For kubeadm/minikube
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.0/deploy/static/provider/baremetal/deploy.yaml

# For EKS
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer

# Verify
kubectl get svc -n ingress-nginx
```

### 6. Apply Autoscaling

```bash
kubectl apply -f k8s/autoscaling.yaml

# Verify HPA
kubectl get hpa -n thesis-pipeline
```

### 7. Configure Ingress (Update domain first!)

Edit `k8s/ingress.yaml` and replace `thesis-pipeline.example.com` with your domain:

```bash
# Update domain
sed -i 's|thesis-pipeline.example.com|your-domain.com|g' k8s/ingress.yaml
sed -i 's|your-email@example.com|your-email@domain.com|g' k8s/ingress.yaml

# Apply
kubectl apply -f k8s/ingress.yaml

# Check ingress
kubectl get ingress -n thesis-pipeline
kubectl describe ingress thesis-ingress -n thesis-pipeline
```

### 8. Verify Deployment

```bash
# Check all resources
kubectl get all -n thesis-pipeline

# Check logs
kubectl logs -f deployment/backend -n thesis-pipeline
kubectl logs -f deployment/frontend -n thesis-pipeline

# Port forward for testing
kubectl port-forward svc/backend 8000:8000 -n thesis-pipeline
kubectl port-forward svc/frontend 3000:80 -n thesis-pipeline

# Test
curl http://localhost:8000/docs
curl http://localhost:3000
```

## Monitoring & Troubleshooting {#monitoring}

### 1. View Logs

```bash
# Tail backend logs
kubectl logs -f deployment/backend -n thesis-pipeline

# Tail frontend logs
kubectl logs -f deployment/frontend -n thesis-pipeline

# View specific pod logs
kubectl logs -f pod/backend-xxxxx -n thesis-pipeline

# View previous logs (if pod crashed)
kubectl logs -p pod/backend-xxxxx -n thesis-pipeline
```

### 2. Describe Resources

```bash
# Describe deployment
kubectl describe deployment backend -n thesis-pipeline

# Describe pod (for events/issues)
kubectl describe pod/backend-xxxxx -n thesis-pipeline

# Describe service
kubectl describe svc backend -n thesis-pipeline
```

### 3. Check Pod Status

```bash
# Get pod status with details
kubectl get pods -n thesis-pipeline -o wide

# Watch pods
kubectl get pods -n thesis-pipeline -w

# Detailed pod info
kubectl get pods -n thesis-pipeline -o yaml
```

### 4. Access Running Container

```bash
# Execute command in pod
kubectl exec -it deployment/backend -n thesis-pipeline -- bash

# Run diagnostics
kubectl exec deployment/backend -n thesis-pipeline -- curl http://localhost:8000/docs
```

### 5. Common Issues & Solutions

**Issue: CrashLoopBackOff**
```bash
# Check logs
kubectl logs <pod-name> -n thesis-pipeline

# Describe pod
kubectl describe pod <pod-name> -n thesis-pipeline

# Common fixes:
# - Wrong image tag or registry
# - Missing environment variables
# - Port already in use
# - Insufficient resources
```

**Issue: Pending Pods**
```bash
# Check node resources
kubectl top nodes

# Check pod resource requests
kubectl describe pod <pod-name> -n thesis-pipeline

# Check events
kubectl describe node <node-name>
```

**Issue: ImagePullBackOff**
```bash
# Verify image exists
docker pull your-registry/thesis-backend:latest

# Check image pull secrets
kubectl get secrets -n thesis-pipeline

# If using private registry, create secret:
kubectl create secret docker-registry regcred \
  --docker-server=your-registry \
  --docker-username=your-username \
  --docker-password=your-password \
  -n thesis-pipeline
```

### 6. Install Monitoring Stack (Optional)

```bash
# Install Prometheus & Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# Default: admin / prom-operator
```

## Production Considerations {#production}

### 1. Update K8s Manifests for Production

```yaml
# Update image pull policy
imagePullPolicy: Always

# Set resource limits (already configured)
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

# Enable pod security policies
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
```

### 2. Setup SSL/TLS

```bash
# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Verify
kubectl get crd | grep cert-manager
```

### 3. Enable Pod Disruption Budgets

```bash
cat <<EOF | kubectl apply -f -
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: backend-pdb
  namespace: thesis-pipeline
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: thesis-backend
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: frontend-pdb
  namespace: thesis-pipeline
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: thesis-frontend
EOF
```

### 4. Setup Persistent Storage (if needed)

```bash
# Check available storage classes
kubectl get storageclass

# Example PVC for data persistence
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: thesis-data-pvc
  namespace: thesis-pipeline
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF
```

### 5. Network Policies

```bash
# Already configured in k8s/frontend.yaml
# Review and customize as needed
kubectl get networkpolicies -n thesis-pipeline
```

### 6. RBAC Configuration

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thesis-app
  namespace: thesis-pipeline
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: thesis-app-role
  namespace: thesis-pipeline
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: thesis-app-binding
  namespace: thesis-pipeline
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: thesis-app-role
subjects:
- kind: ServiceAccount
  name: thesis-app
  namespace: thesis-pipeline
EOF
```

### 7. Scaling Commands

```bash
# Manual scaling
kubectl scale deployment/backend --replicas=5 -n thesis-pipeline
kubectl scale deployment/frontend --replicas=3 -n thesis-pipeline

# Check HPA status
kubectl get hpa -n thesis-pipeline -w
```

### 8. Rolling Updates

```bash
# Update image
kubectl set image deployment/backend \
  backend=your-registry/thesis-backend:1.1.0 \
  -n thesis-pipeline

# Monitor rollout
kubectl rollout status deployment/backend -n thesis-pipeline
kubectl rollout history deployment/backend -n thesis-pipeline

# Rollback if needed
kubectl rollout undo deployment/backend -n thesis-pipeline
```

## Useful Kubectl Commands

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes
kubectl get node -o wide

# Namespaces
kubectl get namespaces
kubectl get all -n thesis-pipeline

# Debugging
kubectl describe node <node-name>
kubectl top nodes
kubectl top pods -n thesis-pipeline

# Resources
kubectl api-resources
kubectl explain deployment

# Cleanup
kubectl delete namespace thesis-pipeline  # Delete everything in namespace
```

## CI/CD Integration

Create `.github/workflows/deploy.yml` for automated deployment:

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build and push images
        run: |
          docker build -t ${{ secrets.REGISTRY }}/thesis-backend:${{ github.sha }} ./backend
          docker push ${{ secrets.REGISTRY }}/thesis-backend:${{ github.sha }}
          
      - name: Deploy to k8s
        run: |
          kubectl set image deployment/backend \
            backend=${{ secrets.REGISTRY }}/thesis-backend:${{ github.sha }} \
            -n thesis-pipeline
```

## Next Steps

1. Test locally with Docker Compose
2. Build and push images to registry
3. Set up EC2 instance with Kubernetes
4. Deploy using the provided YAML manifests
5. Configure domain and SSL/TLS
6. Monitor and scale as needed

For questions or issues, check the troubleshooting section or consult the official Kubernetes documentation.
