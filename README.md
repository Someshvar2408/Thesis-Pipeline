# Thesis Pipeline - Containerization & Kubernetes Deployment Summary

## 🎯 What Has Been Set Up

- This Thesis Pipeline application helps to visualize the resource consumption of an industrial metal 3D printer(gas flow, power, energy consumption). The data is collected using a standalone PLC architecture which sends data to a python script in the same subnet as the PLC. The application is now fully containerized and ready for Kubernetes deployment.

- A standalone PLC (OMRON NX1P2-9B24DT1) architecture is connected to proprietary gas flow sensors  and power meter (SMC's • PF2M725S-C6-L3-S: Compressed gas (Low Flow) sensor • PF2M721S-N2-L3: Argon Flow sensor • PF3A703H-F10-L3: Compressed gas (High Flow) sensor  •Carlo Gavazzi EM 340 S1 power meter). The PLC is configured with sensors in Sysmac Studio Program and made sure it sends data over ethernet to the data logging script **pylogix_main.py**.

- The Python logging script **pylogix_main.py**  pings the PLC's IP address to collect the data attributes like : Timestamp, HighFlow, HighFlowRAW, LowFlow, LowFlowRAW, ArgonFlow, ArgonFlowRAW, Energy_kWh, Power_W

- The accuracy of the analog flow sensors is not captured by a linear formula, so a machine learning model is used to capture the non-linear nature of the RAW values which is used to calibrate the sensors based on a manually noted RAW Values and their corresponding sensor output values is used to train a machine learning model **ML(1).ipynb**. 



### Docker Configuration
- **Backend Dockerfile** - Multi-stage build for FastAPI application (Python 3.11-slim)
- **Frontend Dockerfile** - Nginx-based frontend with static file serving
- **Docker Compose** - Local development environment with networking and health checks
- **.dockerignore** - Optimized image building

### Kubernetes Manifests (in `k8s/` directory)
- **backend.yaml** - Backend deployment with 3 replicas, liveness/readiness probes, resource limits
- **frontend.yaml** - Frontend deployment with 2 replicas, network policies, ingress configuration
- **ingress.yaml** - NGINX ingress controller config with SSL/TLS support (via cert-manager)
- **autoscaling.yaml** - Horizontal Pod Autoscaler (HPA) for both services

### Documentation & Scripts
- **DEPLOYMENT.md** - Comprehensive 500+ line deployment guide
- **QUICKSTART.md** - Quick reference for common tasks
- **CHECKLIST.md** - Complete deployment checklist with phases
- **build-and-push.sh** - Script to build and push Docker images to registry
- **deploy-to-k8s.sh** - Script to deploy application to Kubernetes
- **cleanup.sh** - Script to remove all resources
- **setup-ec2.sh** - Automated EC2 setup script

---

## 🚀 Quick Start (Choose One Path)

### Path 1: Local Testing with Docker Compose (5 minutes)
```bash
cd /u/35/sayapas1/unix/Thesis-Pipeline
docker-compose up -d
curl http://localhost:8000/docs  # Backend API
curl http://localhost              # Frontend
docker-compose down
```

### Path 2: Full Kubernetes on EC2 (30-60 minutes)

1. **Launch EC2 instance**
   - Ubuntu 22.04 LTS, t3.xlarge, 50GB storage
   - Security group: Allow ports 22, 80, 443, 6443

2. **Connect and setup**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   chmod +x setup-ec2.sh
   ./setup-ec2.sh
   ```

3. **Initialize Kubernetes**
   ```bash
   sudo kubeadm init --pod-network-cidr=10.244.0.0/16
   mkdir -p $HOME/.kube
   sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
   sudo chown $(id -u):$(id -g) $HOME/.kube/config
   kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
   ```

4. **Build and push images**
   ```bash
   chmod +x build-and-push.sh
   ./build-and-push.sh docker.io your-username v1.0.0
   ```

5. **Deploy to Kubernetes**
   ```bash
   # Update image references
   sed -i 's|your-registry|docker.io/your-username|g' k8s/*.yaml
   
   chmod +x deploy-to-k8s.sh
   ./deploy-to-k8s.sh
   ```

6. **Access your application**
   ```bash
   kubectl port-forward svc/frontend 8080:80 -n thesis-pipeline
   # Visit http://localhost:8080
   ```

---

## 📁 Project Structure

```
Thesis-Pipeline/
├── backend/
│   ├── Dockerfile              (Backend container image)
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── ...
│   └── __pycache__/
│
├── frontend/
│   ├── Dockerfile              (Frontend container image)
│   ├── nginx.conf              (Nginx configuration)
│   ├── index.html
│   └── ...
│
├── k8s/                        (Kubernetes manifests)
│   ├── backend.yaml            (Backend deployment & service)
│   ├── frontend.yaml           (Frontend deployment & service)
│   ├── ingress.yaml            (Ingress & SSL/TLS config)
│   └── autoscaling.yaml        (HPA configuration)
│
├── docker-compose.yml          (Local dev environment)
├── .dockerignore               (Optimization)
│
├── DEPLOYMENT.md               (Detailed guide - 500+ lines)
├── QUICKSTART.md               (Quick reference)
├── CHECKLIST.md                (Deployment checklist)
│
├── build-and-push.sh           (Build & push images)
├── deploy-to-k8s.sh            (Deploy to K8s)
├── cleanup.sh                  (Remove resources)
└── setup-ec2.sh                (Setup EC2 instance)
```

---

## 🔑 Key Features

### Docker Setup
✅ Multi-stage builds for optimized images
✅ Health checks for container monitoring
✅ Proper signal handling and logging
✅ Security best practices
✅ Docker Compose for local development

### Kubernetes Configuration
✅ 3 backend replicas for high availability
✅ 2 frontend replicas with load balancing
✅ Horizontal Pod Autoscaler (2-10 for backend, 2-5 for frontend)
✅ Liveness and readiness probes
✅ Resource requests and limits
✅ Pod anti-affinity for node distribution
✅ Network policies for frontend
✅ Namespace isolation (thesis-pipeline)

### Networking
✅ NGINX ingress controller
✅ SSL/TLS support (cert-manager integration)
✅ Service-to-service communication
✅ Frontend-to-backend proxying
✅ External domain mapping

### Advanced Features
✅ Automatic pod restart on failure
✅ Rolling updates with zero downtime
✅ Resource-based autoscaling
✅ Container security context
✅ Environment variable management
✅ ConfigMaps for configuration

---

## 📋 What You Need to Do

### Before Local Testing
Nothing additional needed - files are ready to use

### Before Kubernetes Deployment

1. **Choose a Docker Registry**
   - Docker Hub (free public, paid private)
   - AWS ECR (Amazon Elastic Container Registry)
   - Other: GCR, Artifactory, etc.

2. **Setup Registry Authentication**
   - Create account and login
   - Configure credentials for CI/CD (optional)

3. **Update Configuration Files**
   ```bash
   # Replace placeholder registry in k8s manifests
   sed -i 's|your-registry|docker.io/your-username|g' k8s/*.yaml
   
   # Update domain in ingress
   sed -i 's|thesis-pipeline.example.com|your-domain.com|g' k8s/ingress.yaml
   sed -i 's|your-email@example.com|your-email@domain.com|g' k8s/ingress.yaml
   ```

4. **Launch EC2 Instance**
   - See DEPLOYMENT.md for detailed specs
   - Ensure security group allows necessary ports

---

## 🎓 Learning Resources

### Docker
- [Docker Documentation](https://docs.docker.com/)
- [Best Practices for Python Docker Images](https://docs.docker.com/language/python/build-images/)

### Kubernetes
- [Kubernetes Official Documentation](https://kubernetes.io/docs/)
- [kubeadm Setup Guide](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/)
- [EKS User Guide](https://docs.aws.amazon.com/eks/latest/userguide/)

### AWS
- [EC2 Getting Started](https://docs.aws.amazon.com/ec2/index.html)
- [ECR Documentation](https://docs.aws.amazon.com/ecr/)

---

## 🔍 File Descriptions

### Configuration Files

| File | Purpose |
|------|---------|
| backend/Dockerfile | Backend image definition with Python dependencies |
| frontend/Dockerfile | Frontend image with Nginx base |
| frontend/nginx.conf | Nginx configuration for serving frontend and proxying API |
| docker-compose.yml | Local development environment orchestration |
| .dockerignore | Optimizations for Docker build context |

### Kubernetes Manifests

| File | Purpose |
|------|---------|
| k8s/backend.yaml | Backend Deployment, ConfigMap, and Service |
| k8s/frontend.yaml | Frontend Deployment, Service, and NetworkPolicy |
| k8s/ingress.yaml | NGINX Ingress with SSL/TLS and ClusterIssuer |
| k8s/autoscaling.yaml | HorizontalPodAutoscaler for both services |

### Documentation

| File | Purpose |
|------|---------|
| DEPLOYMENT.md | Comprehensive deployment guide (500+ lines) |
| QUICKSTART.md | Quick reference for common tasks |
| CHECKLIST.md | 14-phase deployment checklist |
| README.md | This file |

### Scripts

| Script | Purpose |
|--------|---------|
| build-and-push.sh | Build images and push to registry |
| deploy-to-k8s.sh | Deploy to Kubernetes with health checks |
| cleanup.sh | Remove all Kubernetes resources |
| setup-ec2.sh | Automated EC2 setup (Docker, K8s tools) |

---

## 🧪 Testing Checklist

### Local Docker Test
- [ ] `docker-compose up -d`
- [ ] `curl http://localhost:8000/docs` (should return FastAPI docs)
- [ ] `curl http://localhost` (should return HTML)
- [ ] `docker-compose logs` (check for errors)
- [ ] `docker-compose down`

### Kubernetes Test
- [ ] `kubectl get pods -n thesis-pipeline` (3 backend, 2 frontend running)
- [ ] `kubectl logs -f deployment/backend -n thesis-pipeline` (no errors)
- [ ] `kubectl logs -f deployment/frontend -n thesis-pipeline` (no errors)
- [ ] `kubectl port-forward svc/frontend 8080:80 -n thesis-pipeline`
- [ ] Visit `http://localhost:8080` in browser
- [ ] Check `http://localhost:8080/api/docs` for backend API docs

---

## 🚨 Troubleshooting Quick Reference

```bash
# Pod won't start?
kubectl describe pod <pod-name> -n thesis-pipeline
kubectl logs <pod-name> -n thesis-pipeline

# Image pull errors?
kubectl describe pod <pod-name> -n thesis-pipeline | grep -A 5 Events
# Solution: Update image references in k8s/*.yaml

# No connectivity?
kubectl get svc -n thesis-pipeline
kubectl exec -it deployment/backend -n thesis-pipeline -- curl http://localhost:8000/docs

# Resource issues?
kubectl top nodes
kubectl top pods -n thesis-pipeline
```

For more troubleshooting, see **DEPLOYMENT.md** section "Monitoring & Troubleshooting"

---

## 📞 Support & Next Steps

1. **Review Documentation**
   - Start with QUICKSTART.md for quick overview
   - Read DEPLOYMENT.md for detailed steps
   - Use CHECKLIST.md during actual deployment

2. **Test Locally First**
   - Use Docker Compose for local testing
   - Verify application works correctly
   - Fix any issues before deploying to Kubernetes

3. **Prepare Kubernetes Infrastructure**
   - Launch EC2 instance
   - Run setup-ec2.sh script
   - Initialize Kubernetes cluster

4. **Build and Push Images**
   - Create Docker Hub/ECR account
   - Run build-and-push.sh script
   - Verify images in registry

5. **Deploy to Kubernetes**
   - Update configuration files with your details
   - Run deploy-to-k8s.sh script
   - Monitor logs and verify deployment

6. **Setup Ingress and DNS**
   - Install NGINX ingress controller
   - Configure ingress rules
   - Update DNS records

7. **Monitor and Scale**
   - Watch HPA auto-scaling
   - Monitor pod performance
   - Adjust resource limits as needed

---

## 📝 Configuration Examples

### Environment Variables
Backend environment variables can be added to `k8s/backend.yaml` ConfigMap:
```yaml
data:
  DATABASE_URL: "postgresql://user:pass@db:5432/thesis"
  LOG_LEVEL: "INFO"
```

### Resource Limits
Edit `k8s/backend.yaml` and `k8s/frontend.yaml`:
```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### Domain Configuration
Edit `k8s/ingress.yaml`:
```yaml
spec:
  rules:
  - host: your-domain.com  # Change this
```

---

## ✨ Advanced Optional Setup

### 1. Container Registry Authentication
```bash
kubectl create secret docker-registry regcred \
  --docker-server=docker.io \
  --docker-username=your-username \
  --docker-password=your-token \
  -n thesis-pipeline
```

### 2. Persistent Storage
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: thesis-data
  namespace: thesis-pipeline
spec:
  accessModes: [ "ReadWriteOnce" ]
  resources:
    requests:
      storage: 10Gi
EOF
```

### 3. Monitoring with Prometheus
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### 4. Log Aggregation
See DEPLOYMENT.md for ELK/Loki setup instructions

---

## 🔐 Security Recommendations

- [ ] Use private Docker registry for production
- [ ] Implement container image scanning
- [ ] Enable RBAC in Kubernetes
- [ ] Use network policies for traffic control
- [ ] Implement secrets management (Sealed Secrets/Vault)
- [ ] Regular security updates and patches
- [ ] Monitor for vulnerabilities
- [ ] Implement pod security policies

---

## 📊 Performance Tuning

### Backend Performance
- **Replicas**: Default 3, can scale to 10
- **CPU Request**: 100m, Limit: 500m
- **Memory Request**: 256Mi, Limit: 512Mi
- **Scale Trigger**: CPU >70% or Memory >80%

### Frontend Performance
- **Replicas**: Default 2, can scale to 5
- **CPU Request**: 50m, Limit: 200m
- **Memory Request**: 128Mi, Limit: 256Mi
- **Scale Trigger**: CPU >75%

See DEPLOYMENT.md "Production Considerations" for optimization tips.

---

## 📅 Maintenance Schedule

- **Daily**: Monitor logs and pod health
- **Weekly**: Check resource utilization, review alerts
- **Monthly**: Update base images, security patches
- **Quarterly**: Disaster recovery drills, capacity planning
- **Annually**: Major version upgrades, architecture review

---

**Deployment Date**: December 31, 2025
**Documentation Version**: 1.0
**Kubernetes Version**: 1.28+
**Docker Version**: 20.10+

For detailed information, please refer to **DEPLOYMENT.md**
