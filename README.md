## Project Overview

Two REST APIs for managing device registrations:
- **StatisticsAPI**: Publicly accessible endpoint for logging authentication and retrieving statistics
- **DeviceRegistrationAPI**: Internal-only endpoint for device registration
- **PostgreSQL**: Database for persisting device registrations

## Architecture
```
[Internet/Users]
        ↓
[StatisticsAPI - Public via Ingress]
        ↓
[DeviceRegistrationAPI - Internal Only]
        ↓
[PostgreSQL Database]
```

## Tech Stack

- **Language**: Python 3.12
- **Framework**: FastAPI
- **Database**: PostgreSQL 16
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Container Registry**: DockerHub

## Repository Structure
```
device-registration-challenge/
├── DeviceRegistrationAPI/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── StatisticsAPI/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── kubernetes/
│   ├── namespace/
│   ├── secrets/
│   ├── postgres/
│   ├── device-registration-api/
│   ├── statistics-api/
│   ├── ingress/
│   └── network-policies/
├── docker-compose.yml
└── README.md
```
## API Endpoints

### StatisticsAPI (Public - Port 8000)

**POST /Log/auth**
- Logs user authentication event
- Calls DeviceRegistrationAPI internally
- Input: `{"userKey": "string", "deviceType": "iOS|Android|Watch|TV"}`
- Output: `{"statusCode": 200|400, "message": "success|bad_request"}`

**GET /Log/auth/statistics?deviceType={type}**
- Retrieves device count by type
- Input: deviceType query parameter
- Output: `{"deviceType": "string", "count": number}`

**GET /health**
- Health check endpoint
- Output: `{"status": "healthy", "service": "StatisticsAPI"}`

**API Documentation**: http://localhost:8000/docs (Swagger UI)

### DeviceRegistrationAPI (Internal - Port 8001)

**POST /Device/register**
- Registers a device for a user
- Input: `{"userKey": "string", "deviceType": "iOS|Android|Watch|TV"}`
- Output: `{"statusCode": 200|400}`

**GET /health**
- Health check endpoint
- Output: `{"status": "healthy", "service": "DeviceRegistrationAPI"}`

**API Documentation**: http://localhost:8001/docs (Swagger UI)

## Quick Start

### Option 1: Docker Compose (Local Development)
```bash
# Start all services
docker-compose up -d

# Test the APIs
curl http://localhost:8000/health
curl http://localhost:8001/health

# Stop services
docker-compose down
```

### Option 2: Kubernetes (Production-like)

```bash
# Deploy everything
kubectl apply -f kubernetes/namespace/
kubectl apply -f kubernetes/secrets/
kubectl apply -f kubernetes/postgres/
kubectl apply -f kubernetes/device-registration-api/
kubectl apply -f kubernetes/statistics-api/
kubectl apply -f kubernetes/ingress/
kubectl apply -f kubernetes/network-policies/

# Port-forward to access
kubectl port-forward -n deviceapp svc/statistics-api 8000:8000
```

## DockerHub Images

- `migsouto/device-registration-api:latest`
- `migsouto/statistics-api:latest`
```bash
# Pull images
docker pull migsouto/device-registration-api:latest
docker pull migsouto/statistics-api:latest
```

## Security Features

### Kubernetes Security

- **Secrets Management**: Database credentials stored in Kubernetes Secrets
- **NetworkPolicies**: Restricts traffic between pods
  - StatisticsAPI: Public ingress, can reach DeviceRegistrationAPI and PostgreSQL
  - DeviceRegistrationAPI: Internal only, can only reach PostgreSQL
  - PostgreSQL: Only accessible by APIs
- **Resource Limits**: CPU and memory limits on all containers
- **Least Privilege**: Default deny-all with specific allow rules

### postgres-secret.yaml example (to be created in kubernetes\secrets\postgres-secret.yaml)
```bash
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: deviceapp
type: Opaque
stringData:
  POSTGRES_USER: device_schema_owner
  POSTGRES_PASSWORD: device_schema_owner_pass
  POSTGRES_DB: devicedb
```
### Security Note
- in case of production use postgres-secret yaml shouldn't be used 
- examples of production grade secret managment solutions
- AWS Secrets Manager, Azure Key Vault, HashiCorp Vault

### Network Segmentation

- StatisticsAPI: Publicly accessible via Ingress
- DeviceRegistrationAPI: ClusterIP only (internal)
- PostgreSQL: ClusterIP only (internal)

## Development

### Local Development Setup
```bash
# DeviceRegistrationAPI
cd DeviceRegistrationAPI
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
python main.py

# StatisticsAPI
cd StatisticsAPI
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
python main.py

# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=device_schema_owner \
  -e POSTGRES_PASSWORD=device_schema_owner_pass \
  -e POSTGRES_DB=devicedb \
  postgres:16-alpine
```

## Environment Variables

### DeviceRegistrationAPI
- `DATABASE_URL`: PostgreSQL connection string (from secret)

### StatisticsAPI
- `DATABASE_URL`: PostgreSQL connection string (from secret)
- `DEVICE_API_URL`: DeviceRegistrationAPI internal URL

### PostgreSQL
- `POSTGRES_USER`: Database username (from secret)
- `POSTGRES_PASSWORD`: Database password (from secret)
- `POSTGRES_DB`: Database name (from secret)

## Troubleshooting

**Pods not starting:**
```bash
kubectl logs -n deviceapp 
kubectl describe pod -n deviceapp 
```

**Cannot connect to APIs:**
```bash
# Check services
kubectl get svc -n deviceapp

# Check NetworkPolicies
kubectl get networkpolicies -n deviceapp

# Test connectivity
kubectl run test --image=alpine --rm -it -n deviceapp -- sh
```

Test procedure on powershell
```bash
# Port-forward
kubectl port-forward -n deviceapp svc/statistics-api 8000:8000

# Test all device types
Invoke-RestMethod -Uri http://localhost:8000/Log/auth -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"userKey":"test1","deviceType":"iOS"}'
Invoke-RestMethod -Uri http://localhost:8000/Log/auth -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"userKey":"test2","deviceType":"Android"}'
Invoke-RestMethod -Uri http://localhost:8000/Log/auth -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"userKey":"test3","deviceType":"Watch"}'
Invoke-RestMethod -Uri http://localhost:8000/Log/auth -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"userKey":"test4","deviceType":"TV"}'

# Get all statistics
Invoke-RestMethod -Uri "http://localhost:8000/Log/auth/statistics?deviceType=iOS"
Invoke-RestMethod -Uri "http://localhost:8000/Log/auth/statistics?deviceType=Android"
Invoke-RestMethod -Uri "http://localhost:8000/Log/auth/statistics?deviceType=Watch"
Invoke-RestMethod -Uri "http://localhost:8000/Log/auth/statistics?deviceType=TV"

# Test invalid device type (should return 400)
Invoke-RestMethod -Uri http://localhost:8000/Log/auth -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"userKey":"test5","deviceType":"Xbox"}'

# Test empty userKey (should return 400)
Invoke-RestMethod -Uri http://localhost:8000/Log/auth -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"userKey":"","deviceType":"iOS"}'

```

GitHub Repository:
https://github.com/migsouto/device-registration-challenge

DockerHub Images:
- migsouto/device-registration-api:latest
- migsouto/statistics-api:latest
