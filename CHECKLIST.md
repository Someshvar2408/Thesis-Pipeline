# Deployment Checklist

Use this checklist to ensure all steps are completed correctly.

## Phase 1: Local Development & Testing

- [ ] Clone/pull latest code
- [ ] Review [QUICKSTART.md](QUICKSTART.md) for local testing
- [ ] Test with Docker Compose locally
  ```bash
  docker-compose up -d
  curl http://localhost:8000/docs
  curl http://localhost
  docker-compose down
  ```
- [ ] Verify all endpoints work correctly
- [ ] Review Dockerfiles for any needed adjustments
- [ ] Test with different environment configurations

## Phase 2: Build & Registry Setup

- [ ] Choose Docker registry (Docker Hub, ECR, etc.)
  - [ ] Docker Hub: Create account and login
  - [ ] ECR: Create repositories in AWS
  - [ ] Other: Set up authentication

- [ ] Make scripts executable:
  ```bash
  chmod +x build-and-push.sh deploy-to-k8s.sh cleanup.sh setup-ec2.sh
  ```

- [ ] Build and push images
  ```bash
  ./build-and-push.sh docker.io your-username v1.0.0
  # or
  ./build-and-push.sh <ecr-uri> <namespace> latest
  ```

- [ ] Verify images are in registry
  - [ ] Backend image pushed
  - [ ] Frontend image pushed
  - [ ] Tags are correct (latest and version)

## Phase 3: EC2 Setup

- [ ] Launch EC2 instance
  - [ ] AMI: Ubuntu 22.04 LTS
  - [ ] Type: t3.xlarge or larger
  - [ ] Storage: 50GB or more
  - [ ] Security Group: Allow ports 22, 80, 443, 6443

- [ ] Connect to EC2
  ```bash
  ssh -i your-key.pem ec2-user@your-instance-ip
  ```

- [ ] Run setup script
  ```bash
  chmod +x setup-ec2.sh
  ./setup-ec2.sh
  ```

- [ ] Verify installations
  ```bash
  docker --version
  kubectl version --client
  kubeadm version
  ```

## Phase 4: Kubernetes Cluster Setup

### Option A: Using kubeadm (Production)

- [ ] Initialize control plane
  ```bash
  sudo kubeadm init --pod-network-cidr=10.244.0.0/16
  ```

- [ ] Setup kubeconfig
  ```bash
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config
  ```

- [ ] Install CNI (Flannel)
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
  ```

- [ ] Verify cluster
  ```bash
  kubectl get nodes
  kubectl get pods --all-namespaces
  ```

- [ ] Untaint control plane (if single-node)
  ```bash
  kubectl taint nodes --all node-role.kubernetes.io/control-plane-
  ```

### Option B: Using EKS (AWS Managed)

- [ ] Install eksctl
- [ ] Create cluster
  ```bash
  eksctl create cluster --name thesis-pipeline --region us-east-1
  ```
- [ ] Update kubeconfig
  ```bash
  aws eks update-kubeconfig --name thesis-pipeline --region us-east-1
  ```

### Option C: Using minikube (Development)

- [ ] Install minikube
- [ ] Start cluster
  ```bash
  minikube start --cpus 4 --memory 8192
  ```
- [ ] Enable ingress
  ```bash
  minikube addons enable ingress
  ```

## Phase 5: Pre-Deployment Preparation

- [ ] Update image references in k8s manifests
  ```bash
  sed -i 's|your-registry|<your-registry>|g' k8s/*.yaml
  ```

- [ ] Review and update domain in `k8s/ingress.yaml`
  ```bash
  # Update: thesis-pipeline.example.com
  # Update: your-email@example.com
  ```

- [ ] Review resource limits/requests in k8s manifests
- [ ] Check environment variables in k8s/backend.yaml
- [ ] Verify all config maps and secrets are set

## Phase 6: Deploy to Kubernetes

- [ ] Copy k8s folder to EC2
  ```bash
  scp -r k8s your-user@your-instance-ip:~/
  scp deploy-to-k8s.sh your-user@your-instance-ip:~/
  ```

- [ ] Deploy application
  ```bash
  ./deploy-to-k8s.sh
  # or manually:
  kubectl apply -f k8s/backend.yaml
  kubectl apply -f k8s/frontend.yaml
  ```

- [ ] Wait for deployments
  ```bash
  kubectl get all -n thesis-pipeline
  kubectl get pods -n thesis-pipeline -w
  ```

- [ ] Verify all pods are running
  - [ ] Backend pods: 3 running
  - [ ] Frontend pods: 2 running
  - [ ] All pods in Ready state

- [ ] Check logs for errors
  ```bash
  kubectl logs -f deployment/backend -n thesis-pipeline
  kubectl logs -f deployment/frontend -n thesis-pipeline
  ```

## Phase 7: Networking & Ingress

- [ ] Install NGINX Ingress Controller
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.0/deploy/static/provider/baremetal/deploy.yaml
  ```

- [ ] Verify ingress controller
  ```bash
  kubectl get svc -n ingress-nginx
  ```

- [ ] (Optional) Install cert-manager for SSL/TLS
  ```bash
  helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --set installCRDs=true
  ```

- [ ] Apply ingress configuration
  ```bash
  kubectl apply -f k8s/ingress.yaml
  ```

- [ ] Get ingress IP/hostname
  ```bash
  kubectl get ingress -n thesis-pipeline
  ```

- [ ] Update DNS records to point to ingress IP/hostname

## Phase 8: Autoscaling & Advanced Features

- [ ] Apply autoscaling policies
  ```bash
  kubectl apply -f k8s/autoscaling.yaml
  ```

- [ ] Verify HPA is working
  ```bash
  kubectl get hpa -n thesis-pipeline
  ```

- [ ] Test horizontal scaling (generate load)
  ```bash
  kubectl get hpa -n thesis-pipeline -w
  ```

## Phase 9: Testing & Validation

- [ ] Port forward to test services
  ```bash
  kubectl port-forward svc/frontend 8080:80 -n thesis-pipeline
  kubectl port-forward svc/backend 8000:8000 -n thesis-pipeline
  ```

- [ ] Test frontend
  - [ ] Access http://localhost:8080
  - [ ] Verify UI loads correctly
  - [ ] Check browser console for errors

- [ ] Test backend API
  - [ ] Access http://localhost:8000/docs
  - [ ] Test endpoints (upload CSV, fetch data, etc.)
  - [ ] Verify responses are correct

- [ ] Test inter-service communication
  - [ ] Frontend can reach backend
  - [ ] API calls work correctly
  - [ ] CORS configured properly

- [ ] Monitor pod behavior
  ```bash
  watch kubectl get pods -n thesis-pipeline
  ```

## Phase 10: Monitoring & Logging

- [ ] Setup log aggregation (optional)
  ```bash
  # Using ELK, Loki, or similar
  ```

- [ ] Setup monitoring (optional)
  ```bash
  helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring --create-namespace
  ```

- [ ] Configure alerts (optional)
  - [ ] Pod crash alerts
  - [ ] Resource exhaustion alerts
  - [ ] High error rate alerts

- [ ] Test monitoring
  - [ ] Kill a pod and verify alert
  - [ ] Scale pods and verify metrics

## Phase 11: Backup & Disaster Recovery

- [ ] Document cluster backup procedure
  ```bash
  # For etcd backup
  sudo etcdctl snapshot save /tmp/etcd-backup.db \
    --endpoints=127.0.0.1:2379 \
    --cert /etc/kubernetes/pki/etcd/server.crt \
    --key /etc/kubernetes/pki/etcd/server.key \
    --cacert /etc/kubernetes/pki/etcd/ca.crt
  ```

- [ ] Test disaster recovery procedure
- [ ] Document restore procedure
- [ ] Create backup schedule

## Phase 12: Security Hardening

- [ ] Enable RBAC (role-based access control)
  ```bash
  kubectl apply -f k8s/rbac.yaml  # Create this file if needed
  ```

- [ ] Enable Pod Security Policies
  ```bash
  kubectl apply -f k8s/psp.yaml  # Create this file if needed
  ```

- [ ] Configure Network Policies
  - [ ] Review k8s/frontend.yaml (already has network policy)
  - [ ] Add additional policies as needed

- [ ] Secure container images
  - [ ] Scan images for vulnerabilities
  - [ ] Use minimal base images
  - [ ] Don't run as root

- [ ] Setup secret management
  - [ ] Use sealed-secrets or similar
  - [ ] Never commit secrets to git
  - [ ] Rotate secrets regularly

## Phase 13: Documentation & Handoff

- [ ] Document cluster configuration
  - [ ] Node count and types
  - [ ] Network configuration
  - [ ] Storage configuration

- [ ] Document deployment procedure
- [ ] Document troubleshooting guide
- [ ] Document runbook for common tasks
- [ ] Document contacts and escalation path

- [ ] Create post-deployment checklist:
  - [ ] What to monitor
  - [ ] Common issues and solutions
  - [ ] How to scale
  - [ ] How to update

## Phase 14: Post-Deployment

- [ ] Monitor cluster for 24 hours
- [ ] Test failover scenarios
- [ ] Load test the application
- [ ] Document any issues found
- [ ] Create optimization list for future

## Useful Commands Reference

```bash
# Cluster information
kubectl cluster-info
kubectl get nodes -o wide

# Namespace operations
kubectl get all -n thesis-pipeline

# Deployment operations
kubectl describe deployment backend -n thesis-pipeline
kubectl logs -f deployment/backend -n thesis-pipeline
kubectl exec -it deployment/backend -n thesis-pipeline -- bash
kubectl scale deployment/backend --replicas=5 -n thesis-pipeline

# Pod operations
kubectl get pods -n thesis-pipeline -o wide
kubectl describe pod <pod-name> -n thesis-pipeline

# Troubleshooting
kubectl get events -n thesis-pipeline
kubectl top nodes
kubectl top pods -n thesis-pipeline

# Cleanup
./cleanup.sh
```

---

## Sign-Off

- **Deployed By**: ________________
- **Date**: ________________
- **Version**: ________________
- **Cluster**: ________________
- **Notes**: 
