# Architecture & Deployment Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Users                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              NGINX Ingress Controller                        │
│  (SSL/TLS termination, Load balancing, Routing)            │
└────────────┬──────────────────────────┬────────────────────┘
             │                          │
    ┌────────▼─────────┐      ┌────────▼─────────┐
    │   Frontend       │      │    Backend       │
    │   Nginx (x2)     │      │   FastAPI (x3)   │
    │  Port: 80/443    │      │   Port: 8000     │
    │  - Static files  │      │  - API endpoints │
    │  - Single Page   │      │  - CSV upload    │
    │    Application   │      │  - Data queries  │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             └──────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │   Kubernetes Services      │
          │  (Service Discovery)       │
          └────────────────────────────┘
```

## Deployment Architecture

```
EC2 Instance (Ubuntu 22.04)
├─ Docker Engine
├─ Kubernetes Control Plane (kubeadm)
│  ├─ API Server (6443)
│  ├─ etcd (key-value store)
│  ├─ Scheduler
│  └─ Controller Manager
│
└─ Kubernetes Cluster
   └─ thesis-pipeline namespace
      ├─ Backend Deployment
      │  ├─ Pod 1 (FastAPI)
      │  ├─ Pod 2 (FastAPI)
      │  └─ Pod 3 (FastAPI)
      │
      ├─ Frontend Deployment
      │  ├─ Pod 1 (Nginx)
      │  └─ Pod 2 (Nginx)
      │
      ├─ Backend Service (ClusterIP:8000)
      ├─ Frontend Service (ClusterIP:80)
      │
      ├─ NGINX Ingress Controller
      │  └─ Ingress Resource
      │     ├─ Route: / → Frontend Service
      │     └─ Route: /api/ → Backend Service
      │
      └─ HPA (Horizontal Pod Autoscaler)
         ├─ Backend: 3-10 replicas (CPU/Memory triggered)
         └─ Frontend: 2-5 replicas (CPU triggered)
```

## Container Communication Flow

```
User Request
    │
    ▼
Internet → Port 80/443 (NGINX Ingress)
    │
    ├─ Static files (/) → Frontend Nginx Pods
    │  ├─ Pod 1: Serves HTML/CSS/JS
    │  └─ Pod 2: Serves HTML/CSS/JS
    │
    └─ API calls (/api/) → Backend FastAPI Pods
       ├─ Pod 1: Processes requests
       ├─ Pod 2: Processes requests
       └─ Pod 3: Processes requests
           │
           ▼
       (CSV Processing, Database Queries, etc.)
```

## Scaling Behavior

```
User Load
    ▼
HPA Monitors:
├─ CPU Utilization
├─ Memory Utilization
└─ Request Rate (via metrics-server)
    │
    ├─ If CPU > 70% (Backend) → Scale UP
    │  └─ Add 1 pod per 30 seconds (max 10)
    │
    ├─ If CPU < 70% (Backend) for 5min → Scale DOWN
    │  └─ Remove 50% of pods (min 3)
    │
    └─ If CPU > 75% (Frontend) → Scale UP
       └─ Add pods (max 5)

Result: Auto-scaling from 2-5 replicas based on demand
```

## Data Flow During CSV Upload

```
User Browser
    │
    ├─ POST /api/upload-csv (multipart/form-data)
    │  └─ File: data.csv
    │
    ▼ (Routed through Ingress)
Frontend Nginx
    │ (Proxy pass to backend)
    ▼
Backend FastAPI (Load balanced across 3 pods)
    │
    ├─ Write temp file: /tmp/uuid.csv
    ├─ Parse CSV: pandas.read_csv()
    ├─ Process rows
    ├─ Insert to database (SQLAlchemy ORM)
    └─ Return: {"rows_inserted": N}
    │
    ▼
Browser receives response
```

## File Organization

```
/u/35/sayapas1/unix/Thesis-Pipeline/
│
├─ DOCKER FILES
│  ├─ backend/Dockerfile (Multi-stage build)
│  ├─ frontend/Dockerfile (Nginx-based)
│  ├─ frontend/nginx.conf (Configuration)
│  ├─ docker-compose.yml (Local dev)
│  └─ .dockerignore (Build optimization)
│
├─ KUBERNETES MANIFESTS (k8s/)
│  ├─ backend.yaml (Deployment + Service + ConfigMap)
│  ├─ frontend.yaml (Deployment + Service + NetworkPolicy)
│  ├─ ingress.yaml (Ingress + SSL/TLS config)
│  └─ autoscaling.yaml (HPA for both services)
│
├─ DOCUMENTATION
│  ├─ README.md (This document - Quick overview)
│  ├─ DEPLOYMENT.md (Comprehensive 500+ line guide)
│  ├─ QUICKSTART.md (Quick reference)
│  └─ CHECKLIST.md (14-phase deployment checklist)
│
├─ AUTOMATION SCRIPTS
│  ├─ build-and-push.sh (Build Docker images)
│  ├─ deploy-to-k8s.sh (Deploy to Kubernetes)
│  ├─ cleanup.sh (Remove resources)
│  └─ setup-ec2.sh (Setup EC2 instance)
│
├─ CI/CD
│  └─ .github/workflows/docker-build.yml (GitHub Actions)
│
└─ APPLICATION
   ├─ backend/ (FastAPI application)
   │  ├─ requirements.txt
   │  └─ app/ (Main application code)
   │
   └─ frontend/ (React/HTML application)
       └─ index.html
```

## Deployment Steps Overview

```
PHASE 1: Local Development (5 min)
├─ docker-compose up -d
├─ Test on localhost:8000 (backend)
├─ Test on localhost (frontend)
└─ docker-compose down

PHASE 2: Image Building (10 min)
├─ ./build-and-push.sh docker.io username latest
├─ Verify images in registry
└─ Update k8s manifests

PHASE 3: EC2 Setup (15 min)
├─ Launch t3.xlarge instance (Ubuntu 22.04)
├─ ssh to instance
├─ ./setup-ec2.sh
└─ Verify: docker --version, kubectl --version

PHASE 4: Kubernetes Cluster (10 min)
├─ sudo kubeadm init --pod-network-cidr=10.244.0.0/16
├─ Setup kubeconfig
├─ kubectl apply -f flannel.yml
└─ Verify: kubectl get nodes

PHASE 5: Deploy Application (5 min)
├─ Update image references
├─ ./deploy-to-k8s.sh
├─ kubectl wait for deployments
└─ Verify: kubectl get all -n thesis-pipeline

PHASE 6: Networking (5 min)
├─ Install NGINX Ingress
├─ Update domain in ingress.yaml
├─ kubectl apply -f k8s/ingress.yaml
└─ DNS propagation (5-24 hours)

PHASE 7: Verification (5 min)
├─ kubectl port-forward to test
├─ Test API endpoints
├─ Monitor with: kubectl get pods -w
└─ View logs: kubectl logs -f deployment/backend

Total Time: ~60 minutes for full deployment
```

## Resource Consumption

```
BACKEND (3 initial replicas)
├─ Per Pod Request:    CPU 100m,  Memory 256Mi
├─ Per Pod Limit:      CPU 500m,  Memory 512Mi
├─ Total Min (3 pods): CPU 300m,  Memory 768Mi
└─ Total Max (10 pods): CPU 5000m, Memory 5Gi

FRONTEND (2 initial replicas)
├─ Per Pod Request:    CPU 50m,   Memory 128Mi
├─ Per Pod Limit:      CPU 200m,  Memory 256Mi
├─ Total Min (2 pods): CPU 100m,  Memory 256Mi
└─ Total Max (5 pods): CPU 1000m, Memory 1.25Gi

TOTAL SYSTEM
├─ Minimum: CPU 400m,  Memory 1024Mi
└─ Maximum: CPU 6000m, Memory 6.25Gi

Recommended EC2: t3.xlarge (4 vCPU, 16GB RAM)
```

## High Availability Features

```
BACKEND
├─ 3 replicas across different nodes
├─ Pod anti-affinity (prefer different nodes)
├─ Liveness probe (30s interval, 3 failures = restart)
├─ Readiness probe (10s interval, detects when ready)
├─ Rolling updates (max surge 1, max unavailable 0)
└─ HPA (auto-scale 3-10 based on load)

FRONTEND
├─ 2 replicas across different nodes
├─ Pod anti-affinity (prefer different nodes)
├─ Liveness probe (30s interval)
├─ Readiness probe (10s interval)
├─ Rolling updates (max surge 1, max unavailable 0)
└─ HPA (auto-scale 2-5 based on load)

NETWORK
├─ ClusterIP services (internal communication)
├─ NGINX Ingress (external access)
├─ Network policies (restrict traffic)
└─ Service discovery (automatic DNS)
```

## Environment Comparison

```
LOCAL DEVELOPMENT (Docker Compose)
├─ Full application stack
├─ Simplified networking (bridge network)
├─ No load balancing
├─ No auto-scaling
├─ Perfect for development/testing
└─ Startup time: ~10 seconds

PRODUCTION (Kubernetes on EC2)
├─ Full application stack with HA
├─ Kubernetes networking (advanced)
├─ Load balancing (NGINX Ingress)
├─ Auto-scaling (HPA)
├─ Multiple replicas
├─ SSL/TLS support
├─ Better monitoring/debugging
└─ Startup time: ~30 seconds
```

## Monitoring Points

```
KUBELET METRICS (Built-in)
├─ Pod CPU utilization
├─ Pod memory utilization
├─ Node CPU/Memory
└─ Container restarts

APPLICATION METRICS
├─ FastAPI startup time
├─ Nginx request latency
├─ CSV processing time
└─ Database query time

SYSTEM LOGS
├─ Pod logs (stdout/stderr)
├─ Kubernetes events
├─ Ingress logs
└─ Container exit codes
```

## Security Architecture

```
NETWORK SECURITY
├─ Namespace isolation (thesis-pipeline)
├─ Network policies (restrict traffic)
├─ Service discovery (internal DNS)
└─ No direct pod exposure

POD SECURITY
├─ Security context (non-root not enforced)
├─ Resource limits (prevent DoS)
├─ Liveness/readiness probes (detect failures)
└─ Container image scanning (vulnerabilities)

DATA SECURITY
├─ ConfigMaps (non-sensitive data)
├─ Secrets (sensitive data - encrypted at rest)
├─ SSL/TLS in transit (cert-manager)
└─ Read-only filesystem (optional)

ACCESS CONTROL
├─ RBAC (role-based access control)
├─ ServiceAccount (per-application identity)
├─ kubeconfig (secure API access)
└─ Audit logging (track changes)
```

## Troubleshooting Decision Tree

```
Application not accessible?
├─ Check pod status: kubectl get pods
│  ├─ Pending? → Insufficient resources
│  ├─ CrashLoopBackOff? → Check logs
│  └─ Running? → Check service/ingress
│
├─ Check service: kubectl get svc
│  ├─ Service exists? → Check endpoints
│  └─ No service? → Apply manifests again
│
├─ Check logs: kubectl logs <pod>
│  ├─ Image not found? → Update image reference
│  ├─ Port in use? → Change port or kill process
│  └─ Startup error? → Fix application code
│
└─ Check ingress: kubectl get ingress
   ├─ Ingress exists? → Check DNS
   └─ No ingress? → Install ingress controller
```

## Quick Reference Commands

```bash
# Deployment
kubectl apply -f k8s/backend.yaml    # Deploy backend
kubectl apply -f k8s/frontend.yaml   # Deploy frontend

# Monitoring
kubectl get pods -n thesis-pipeline -w          # Watch pods
kubectl logs -f deployment/backend -n thesis-pipeline

# Scaling
kubectl scale deployment/backend --replicas=5 -n thesis-pipeline

# Updates
kubectl set image deployment/backend \
  backend=docker.io/user/thesis-backend:v1.1.0 -n thesis-pipeline

# Troubleshooting
kubectl describe pod <pod-name> -n thesis-pipeline
kubectl exec -it <pod-name> -n thesis-pipeline -- bash
kubectl top pods -n thesis-pipeline

# Cleanup
kubectl delete namespace thesis-pipeline
```

---

For detailed information, see:
- **DEPLOYMENT.md** - Comprehensive setup guide
- **QUICKSTART.md** - Quick reference
- **CHECKLIST.md** - Deployment phases
