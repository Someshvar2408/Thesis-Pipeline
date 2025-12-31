# Environment Configuration Template

Copy this file and customize for your environment.

## Development Environment (.env.development)

```
# FastAPI
PYTHONENV=development
LOG_LEVEL=DEBUG
DEBUG=true

# Database (if applicable)
DATABASE_URL=sqlite:///./thesis.db
# Or PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/thesis

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Upload Configuration
MAX_UPLOAD_SIZE=104857600  # 100MB
UPLOAD_DIR=/tmp

# Features
ENABLE_SWAGGER=true
```

## Production Environment (.env.production)

```
# FastAPI
PYTHONENV=production
LOG_LEVEL=INFO
DEBUG=false

# Database
DATABASE_URL=postgresql://user:secure_password@db-host:5432/thesis_prod

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# Upload Configuration
MAX_UPLOAD_SIZE=104857600  # 100MB
UPLOAD_DIR=/data/uploads

# Features
ENABLE_SWAGGER=false

# Security
SECRET_KEY=your-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring
SENTRY_DSN=https://your-sentry-token@sentry.io/project-id
DATADOG_API_KEY=your-datadog-key
```

## Kubernetes ConfigMap Template (k8s/configmap.yaml)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: thesis-backend-config
  namespace: thesis-pipeline
data:
  PYTHONENV: "production"
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  API_WORKERS: "4"
  CORS_ORIGINS: '["https://yourdomain.com"]'
  MAX_UPLOAD_SIZE: "104857600"
  UPLOAD_DIR: "/data/uploads"
  ENABLE_SWAGGER: "false"
---
apiVersion: v1
kind: Secret
metadata:
  name: thesis-backend-secret
  namespace: thesis-pipeline
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@db-host:5432/thesis"
  SECRET_KEY: "your-random-secret-key"
  ALGORITHM: "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"
  SENTRY_DSN: "https://your-sentry-token@sentry.io/project-id"
  DATADOG_API_KEY: "your-datadog-key"
```

## Docker Environment Variables

### Backend Dockerfile Build Args

```dockerfile
ARG PYTHON_VERSION=3.11
ARG BASE_IMAGE=python:${PYTHON_VERSION}-slim

# Usage:
# docker build --build-arg PYTHON_VERSION=3.11 -t thesis-backend .
```

### Docker Compose Environment

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - PYTHONENV=development
      - LOG_LEVEL=DEBUG
      - DATABASE_URL=sqlite:///./thesis.db
      - CORS_ORIGINS=["http://localhost:3000"]
```

## AWS Secrets Manager

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name thesis-prod/db-password \
  --secret-string "your-secure-password"

aws secretsmanager create-secret \
  --name thesis-prod/api-key \
  --secret-string "your-api-key"

# In Kubernetes, reference with:
# https://docs.aws.amazon.com/secretsmanager/latest/userguide/integrating_how-it-works.html
```

## Sealed Secrets (Kubernetes)

```bash
# Install sealed-secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create a secret
kubectl create secret generic thesis-secret \
  --from-literal=DATABASE_URL="postgresql://..." \
  -n thesis-pipeline \
  -o yaml > secret.yaml

# Seal it
kubeseal -f secret.yaml -w sealed-secret.yaml -n thesis-pipeline

# Apply sealed secret
kubectl apply -f sealed-secret.yaml
```

## HashiCorp Vault Integration

```bash
# Example Vault configuration
vault write secret/data/thesis-pipeline \
  DATABASE_URL="postgresql://..." \
  API_KEY="your-key" \
  SECRET_KEY="your-secret"

# Kubernetes Agent Injector
# https://www.vaultproject.io/docs/platform/k8s/injector
```

## Environment Variables in Application Code

```python
# backend/app/config.py
import os
from typing import Optional

class Settings:
    # API Settings
    PYTHONENV: str = os.getenv("PYTHONENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Server Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "4"))
    
    # Database Settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # CORS Settings
    CORS_ORIGINS: list = eval(os.getenv("CORS_ORIGINS", '["*"]'))
    
    # Upload Settings
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "104857600"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    # Features
    ENABLE_SWAGGER: bool = os.getenv("ENABLE_SWAGGER", "true").lower() == "true"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    DATADOG_API_KEY: Optional[str] = os.getenv("DATADOG_API_KEY")

settings = Settings()
```

## Loading Environment Files in Docker

### docker-compose.yml

```yaml
services:
  backend:
    env_file:
      - .env
      - .env.development
```

### Dockerfile

```dockerfile
# Multi-stage with environment-specific builds
FROM python:3.11-slim as builder

ARG ENVIRONMENT=development
ENV ENVIRONMENT=${ENVIRONMENT}

COPY .env.${ENVIRONMENT} .env
# ... rest of Dockerfile
```

### Run Container with Env File

```bash
docker run --env-file .env -p 8000:8000 thesis-backend:latest
```

## Kubernetes Secret Management

### Create Secret from File

```bash
# From a file
kubectl create secret generic thesis-secret \
  --from-file=.env \
  -n thesis-pipeline

# From literal values
kubectl create secret generic thesis-secret \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=SECRET_KEY="your-secret" \
  -n thesis-pipeline
```

### Use Secret in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: example-pod
spec:
  containers:
  - name: backend
    image: thesis-backend:latest
    env:
    # From Secret
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: thesis-secret
          key: DATABASE_URL
    # From ConfigMap
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: thesis-backend-config
          key: LOG_LEVEL
    # Direct value
    - name: PYTHONENV
      value: "production"
```

## AWS Parameter Store

```bash
# Put parameter
aws ssm put-parameter \
  --name "/thesis/production/db-url" \
  --value "postgresql://..." \
  --type "SecureString"

# Get parameter in Kubernetes
# Use IRSA (IAM Roles for Service Accounts)
# https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html
```

## Environment Variable Validation

```python
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    database_url: str
    api_key: str
    
    @validator('database_url')
    def validate_db_url(cls, v):
        if not v.startswith(('postgresql://', 'mysql://', 'sqlite://')):
            raise ValueError('Invalid database URL')
        return v
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
```

## Common Environment Variables

| Variable | Required | Development | Production | Notes |
|----------|----------|-------------|------------|-------|
| PYTHONENV | No | development | production | Python environment |
| LOG_LEVEL | No | DEBUG | INFO | Logging level |
| DEBUG | No | true | false | Debug mode |
| DATABASE_URL | Yes | sqlite | postgresql | Database connection |
| API_HOST | No | 0.0.0.0 | 0.0.0.0 | API host |
| API_PORT | No | 8000 | 8000 | API port |
| CORS_ORIGINS | No | ["*"] | specific domains | CORS allowed origins |
| SECRET_KEY | Yes | dev-key | random-key | Secret key for signing |
| ENABLE_SWAGGER | No | true | false | Enable Swagger UI |
| SENTRY_DSN | No | - | set | Error tracking |

## Migration Strategy

When changing environment variables:

1. **Add new variable** with default value in code
2. **Test** with Docker Compose locally
3. **Update** ConfigMap/Secret in k8s manifests
4. **Deploy** with rolling updates (zero downtime)
5. **Verify** with `kubectl get configmap -o yaml`
6. **Remove** old variables after deployment

Example:
```bash
# 1. Add to k8s/configmap.yaml
# 2. Deploy new version
./deploy-to-k8s.sh

# 3. Verify update
kubectl get configmap thesis-backend-config -n thesis-pipeline -o yaml

# 4. Restart pods to pick up changes
kubectl rollout restart deployment/backend -n thesis-pipeline

# 5. Monitor update
kubectl rollout status deployment/backend -n thesis-pipeline
```

## Troubleshooting Environment Issues

```bash
# Check ConfigMap
kubectl get configmap -n thesis-pipeline
kubectl describe configmap thesis-backend-config -n thesis-pipeline
kubectl get configmap thesis-backend-config -o yaml -n thesis-pipeline

# Check Secret
kubectl get secret -n thesis-pipeline
kubectl describe secret thesis-backend-secret -n thesis-pipeline
# Note: Secrets are base64-encoded, not encrypted by default

# Check pod environment
kubectl exec -it deployment/backend -n thesis-pipeline -- env | grep -i python

# Check if app loaded variables correctly
kubectl logs deployment/backend -n thesis-pipeline | grep -i environ
```

## Security Best Practices

1. **Never commit** `.env` files to git
2. **Use `.env.example`** with template values
3. **Rotate** secrets regularly
4. **Use encrypted** secret storage (Sealed Secrets, Vault)
5. **Limit** secret access with RBAC
6. **Audit** who accesses secrets
7. **Use different** secrets per environment
8. **Monitor** secret usage in logs
9. **Validate** all environment variables
10. **Document** required environment variables

## Example .env.example

```
# Copy this file to .env and fill in your values
# DO NOT commit .env to version control

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/thesis

# Security
SECRET_KEY=your-random-secret-key-here
API_KEY=your-api-key-here

# Monitoring
SENTRY_DSN=https://your-token@sentry.io/project-id

# Feature Flags
ENABLE_SWAGGER=true
ENABLE_MONITORING=false
```

---

**For detailed configuration, see DEPLOYMENT.md section "Environment Configuration"**
