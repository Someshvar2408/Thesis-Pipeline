# Thesis Pipeline - Containerization & Kubernetes Deployment Summary

## 🎯 What Has Been Set Up

- This Thesis Pipeline application helps to visualize the resource consumption of an industrial metal 3D printer(gas flow, power, energy consumption). The data is collected using a standalone PLC architecture which sends data to a python script in the same subnet as the PLC. The application is now fully containerized and ready for Kubernetes deployment.

- A standalone PLC (OMRON NX1P2-9B24DT1) architecture is connected to proprietary gas flow sensors  and power meter (SMC's • PF2M725S-C6-L3-S: Compressed gas (Low Flow) sensor • PF2M721S-N2-L3: Argon Flow sensor • PF3A703H-F10-L3: Compressed gas (High Flow) sensor  •Carlo Gavazzi EM 340 S1 power meter). The PLC is configured with sensors in Sysmac Studio Program and made sure it sends data over ethernet to the data logging script **pylogix_main.py**.

- The Python logging script **pylogix_main.py**  pings the PLC's IP address to collect the data attributes like : Timestamp, HighFlow, HighFlowRAW, LowFlow, LowFlowRAW, ArgonFlow, ArgonFlowRAW, Energy_kWh, Power_W

- The accuracy of the analog flow sensors is not captured by a linear formula, so a machine learning model is used to capture the non-linear nature of the RAW values which is used to calibrate the sensors based on a manually noted RAW Values and their corresponding sensor output values is used to train a machine learning model **ML(1).ipynb**. 

# Sensor Flow Calibration using Linear Regression

The following section implements a simple, interpretable machine learning model to improve the calibration of industrial flow sensors. The model learns a mapping from raw sensor values (as seen by the PLC) to accurate flow rates in L/min using a small, high‑quality calibration dataset and then applies this mapping to a larger set of logged operational data.

---

## 1. Overview

In the existing system, the PLC converts raw analog sensor values to flow rates using a fixed linear formula. This formula is approximate and introduces systematic errors, especially outside the nominal calibration points. To address this, a supervised regression model is trained on calibration data consisting of:

- Raw sensor values (input feature)
- Manually measured flow values in L/min (ground truth)

The trained model is then used to compute corrected flow values for all records in the PLC log.

The approach is applied separately to three flow sensors:

- `LowFlow`
- `ArgonFlow`
- `HighFlow`

Each sensor receives its own regression model and corresponding corrected flow column in the output CSV.

---

## 2. Data Description

### 2.1 Calibration Data

**File:** `Sensor_Calibration(Sheet1).csv`  
**Purpose:** Ground truth for training the regression models.

Expected columns:

- `SensorType`: Categorical identifier of the sensor (e.g., `"LowFlow"`, `"ArgonFlow"`, `"HighFlow"`).
- `RAW_value`: Raw sensor reading as recorded during calibration.
- `Flow_Lmin`: Manually measured true flow in L/min corresponding to `RAW_value`.

Each sensor type typically has **about 5 calibration points** spanning its operating range.

### 2.2 Operational (PLC Log) Data

**File:** `FlowLog_20251215_095220.csv`  
**Purpose:** Unlabeled operational data to which the learned calibration is applied.

Expected columns (minimum):

- `Timestamp`: Time of the log entry.
- `LowFlowRAW`: Raw reading for the low‑flow sensor.
- `ArgonFlowRAW`: Raw reading for the argon flow sensor.
- `HighFlowRAW`: Raw reading for the high‑flow sensor.
- Existing PLC‑computed flow columns (e.g., `LowFlow`, `ArgonFlow`, `HighFlow`) may exist and are retained for comparison, but are **not** used as ground‑truth labels.

### 2.3 Output Data

**File (generated):** `plc_operational_data_with_corrected_flows.csv`  

Contains all original PLC log columns plus calibrated flow columns:

- `LowFlow_Lmin`
- `ArgonFlow_Lmin`
- `HighFlow_Lmin`

These are the model‑predicted calibrated flows in L/min.

---

## 3. Model Description

### 3.1 Problem Formulation

For each sensor type, calibration is treated as a univariate regression problem:

- Input feature: raw sensor value \( x_{\text{raw}} \)
- Target label: true flow in L/min \( y_{\text{true}} \)

Objective:
\[
\hat{y} = f(x_{\text{raw}})
\]
where \( \hat{y} \) is the calibrated flow prediction.

### 3.2 Final Model: Linear Regression

The production model used is **ordinary least squares (OLS) linear regression**:

\[
\hat{y} = w_1 \cdot x_{\text{raw}} + w_0,
\]

where:

- \( w_1 \) is the learned gain (slope),
- \( w_0 \) is the learned offset (intercept).

**Why this model:**

- Extremely **low capacity** (only two parameters per sensor) – ideal for very small calibration datasets.
- Coefficients are **physically interpretable** as gain and offset corrections.
- Closed‑form solution; easy to implement directly in PLC logic or any processing pipeline.
- Matches the typical approximately linear behavior of many industrial flow sensors over their calibrated range.

---

## 4. Code Structure

### 4.1 Loading Data

```python
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR

INPUT_PLC_CSV = DATA_DIR / "FlowLog_20251215_095220.csv"
INPUT_CALIB_CSV = DATA_DIR / "Sensor_Calibration(Sheet1).csv"
OUTPUT_CSV = DATA_DIR / "plc_operational_data_with_corrected_flows.csv"

def load_operational_data(path):
    df = pd.read_csv(path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True)
    return df

def load_calibration_data(path):
    # expected columns: SensorType, RAW_value, Flow_Lmin
    return pd.read_csv(path)

plc_df = load_operational_data(INPUT_PLC_CSV)
calib_df = load_calibration_data(INPUT_CALIB_CSV)
```

### 4.2 Training Per‑Sensor Linear Models

```python
def train_linear_sensor(cal_df, sensor_name):
    df = cal_df[cal_df["SensorType"] == sensor_name].copy()

    X = df[["RAW_value"]].values        # raw feature
    y = df["Flow_Lmin"].values          # true flow (L/min)

    model = LinearRegression()
    model.fit(X, y)
    return model
```

### 4.3 Applying Models to Operational Data

```python
def apply_all_sensor_models(plc_df, calib_df):

    sensor_specs = [
        ("LowFlow",  "LowFlowRAW",  "LowFlow_Lmin"),
        ("ArgonFlow","ArgonFlowRAW","ArgonFlow_Lmin"),
        ("HighFlow", "HighFlowRAW", "HighFlow_Lmin"),
    ]

    for sensor_name, raw_col, out_col in sensor_specs:
        print(f"Training linear model for {sensor_name} sensor")
        model = train_linear_sensor(calib_df, sensor_name)

        # Predict calibrated flow for each operational row
        plc_df[out_col] = model.predict(plc_df[[raw_col]].values)

    return plc_df

plc_df = apply_all_sensor_models(plc_df, calib_df)
plc_df.to_csv(OUTPUT_CSV, index=False)
print("Corrected CSV saved to:", OUTPUT_CSV)
```

---

## 5. Model Comparison

Two approaches were tested for mapping raw sensor values to calibrated flow:

1. **Linear Regression (final choice)**
2. **LightGBM Gradient Boosting Regressor (`LGBMRegressor`)** as an initial, more flexible candidate

### 5.1 Initial Attempt: LightGBM (`LGBMRegressor`)

A gradient‑boosted tree model was first explored using `lightgbm.LGBMRegressor`, with parameters such as:

- `n_estimators=800`
- `learning_rate=0.04`
- `max_depth=5`
- `monotone_constraints=[1, 1]`
- TimeSeriesSplit cross‑validation

Conceptually, gradient boosting is powerful for capturing complex non‑linear relationships in data and is widely used for regression tasks.[web:70][web:66] However, in this project it **did not perform well** and produced almost constant predictions across all samples for each sensor (e.g., the same L/min value repeated for all rows).

**Reasons it failed in this context:**

- **Extremely small calibration sample size**  
  Each sensor had only ~5 calibration points. Gradient boosting methods are high‑capacity, non‑parametric models that typically require tens to hundreds (or more) samples to reliably learn meaningful structure without collapsing or overfitting.[web:65][web:66]

- **Over‑parameterization relative to data**  
  With `n_estimators=800` and `max_depth=5`, the LightGBM model had far more degrees of freedom than the number of data points. In such regimes, boosting can either overfit noise or fail to find informative splits, resulting in trivial models that default to predicting something close to the mean of the training targets.[web:60][web:66]

- **Cross‑validation on almost no data**  
  Using `TimeSeriesSplit(n_splits=5)` on just 5 points means some folds contained 1 or 2 training samples. Tree‑based learners have difficulty building meaningful trees from such tiny subsets, again pushing the model toward near‑constant predictions and unstable behavior.[web:53][web:65]

- **Use of non‑ground‑truth labels in the original hybrid idea**  
  In early code, operational PLC‑computed flows (from an inaccurate formula) were inadvertently mixed as targets along with true calibration labels, with only sample‑weighting to favor calibration points. This effectively taught the model to reproduce the old (incorrect) PLC formula on most rows, weakening the influence of the true calibration anchors.

These issues are all symptoms of a mismatch between **model capacity** and **available labeled data**: high‑flexibility models like gradient boosting are not appropriate with such limited calibration samples.[web:65][web:71]

### 5.2 Why Linear Regression Worked Better

In contrast, **linear regression** performed well despite the small dataset:

- **Very low complexity**  
  Each sensor model has only **two parameters** (slope and intercept). This matches the data regime (5 points) far better than a large ensemble of trees. Theory and practice both indicate that with small sample sizes, low‑capacity models generalize more reliably than flexible ones.[web:65][web:59]

- **Approximate linearity of physical sensors**  
  Many industrial flow sensors have an approximately linear transfer function over their operating range, with deviations mainly in gain and offset. A straight line is therefore a reasonable model for the underlying physics, especially when only a few calibration points are available.[web:59]

- **Stable behavior and no collapse to constants**  
  OLS on 5 points always produces a definite line through the data, not a constant. As long as the calibration points are reasonably spread out, the fitted line yields distinct predictions across the raw value range and corrects the PLC’s approximate formula.

- **Interpretability and deployment simplicity**  
  The learned parameters can be directly implemented in PLC logic as:
  \[
  \text{Flow\_Lmin} = \hat{w}_1 \cdot \text{Raw} + \hat{w}_0,
  \]
  with no dependency on external libraries or complex runtime dependencies.

**Conclusion of comparison:**  
Given the **very small number of calibration samples**, linear regression is a better match for this problem than a high‑capacity ensemble model like LightGBM. Once more calibration data are collected (e.g., 15–20+ points per sensor spanning the full range), more flexible models such as LightGBM or polynomial regression could be revisited and compared under proper validation.[web:65][web:68]

---

## 6. How to Run

1. Place the following files in the same directory as the script:
   - `FlowLog_20251215_095220.csv`
   - `Sensor_Calibration(Sheet1).csv`
2. Install Python and required packages:
   - `pandas`
   - `scikit-learn`
3. Run the script, for example:
   ```bash
   python ML(1).ipynb
   ```
4. Inspect the generated `plc_operational_data_with_corrected_flows.csv` for calibrated flow values.

---

## 7. Assumptions and Limitations

- **Linearity:** The model assumes the relationship between raw sensor values and flow is adequately described by a straight line within the calibration range.
- **Limited Calibration Points:** With ~5 calibration points per sensor, the model cannot robustly detect or fit subtle non‑linearities.
- **Extrapolation:** Predictions outside the calibrated raw range are linear extrapolations and may be unreliable.
- **Per‑Sensor Independence:** Each sensor is calibrated independently; cross‑sensor dependencies are not modeled.

---

## 8. Possible Extensions

- Collect more calibration points across low, medium, and high flow regimes.
- Experiment with polynomial regression (e.g., quadratic) if residuals show systematic non‑linearity.
- Include temperature, pressure, or other process variables as additional features if they influence sensor behavior.
- Periodically retrain models on updated calibration datasets to handle sensor drift.

---

## 9. Summary

This section demonstrates a lightweight, interpretable machine learning solution for sensor calibration using linear regression. Although a more complex LightGBM model was initially considered, it under‑performed in this small‑sample setting and tended toward constant predictions. A simple linear model proved more robust, better aligned with the data size and physical intuition of the sensors, and easier to deploy in an industrial PLC environment.[web:59][web:65][web:66]

# Containerization and Deployment

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
