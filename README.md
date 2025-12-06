# RUSS Cloud AWR Analyzer & Automation Platform  
A multi-tenant, automated cloud assessment and AWR analytics system supporting Azure, AWS, and Oracle OCI.

---

## 🚀 Overview
The **RUSS Cloud AWR Analyzer** is an end-to-end automation platform built to simplify cloud migration assessments.  
It ingests Oracle AWR files from multiple sources, analyzes workload performance, and generates cloud-optimized VM recommendations including cost estimates.

The system includes:
- Multi-customer onboarding
- Automated S3/SFTP ingestion
- Background schedulers
- AWR parsing engine
- Cloud sizing for Azure, AWS, OCI
- Reporting dashboards
- Admin management console

---

## 🧱 Key Features

### 🔐 Multi-Tenant Architecture
- Unlimited customer onboarding  
- Each customer has isolated folders:
  - `/uploads/<customer>/`
  - `/outputs/<customer>/`
- Per-customer S3/SFTP configuration  
- Per-customer scheduler jobs  

---

### 📥 Automated Ingestion Pipelines

#### **S3 Ingestion**
- Bucket + prefix polling  
- Sync only new/updated files  
- Safe filename sanitization  
- Optional event-based ingestion  

#### **SFTP Collector**
- Password OR private key authentication  
- Remote directory scanning  
- Optional remote command execution (e.g., AWR generator)  
- Downloads only allowed file types  
- Duplicate/size-based skip logic  

---

### ⏱ Automated Scheduling
- Powered by APScheduler  
- Independent cron-like jobs per customer  
- Automates:
  - S3 ingestion
  - SFTP ingestion
  - AWR analysis  
- Manual run actions also available in Admin UI  

---

### 🔍 AWR Parsing & Cloud Sizing Engine
The worker (`multi_analyze.py`) extracts:
- vCPUs  
- Memory  
- IOPS  
- Throughput  
- Workload category  

Then maps them to recommended VM sizes for:
- **Azure**  
- **AWS**  
- **OCI**  

Includes:
- Monthly cost estimates  
- Final summary, XLSX, PPTX export  

---

### 📊 Admin & Reporting Portal
- User management  
- Customer integration management  
- Test S3 / Test SFTP buttons  
- Scheduler On/Off toggle  
- Report filtering (email, cloud, date range)  
- Sorting + CSV export  
- AWR history viewer  

---

## 📁 Project Structure

```
backend/
│── app.py                 # Main FastAPI entry point
│── profile_admin.py       # Authentication + profiles
│── integrations_admin.py  # Customer integrations + automation API
│── ingestion_s3.py        # S3 ingestion engine
│── collector_sftp.py      # SFTP ingestion engine
│── history_utils.py       # Report history utilities
│── licenses.db            # Users + integration settings
│
worker/
│── multi_analyze.py       # Core AWR parsing & cloud sizing engine
│
frontend/
│── admin.html             # Admin console
│── dashboard.html         # User dashboard
│── index.html             # File upload/manual inputs
│── profile.html           # Profile settings
│── style.css
│── script.js
│
uploads/                   # Per-customer ingestion folders
outputs/                   # Per-customer analysis results
```

---

## 🛑 Requirements

### Python Libraries
```
fastapi
uvicorn
passlib
boto3
paramiko
apscheduler
pandas
openpyxl
python-pptx
reportlab
```

### System Requirements
- Python 3.9+  
- AWS IAM role or key (for S3 ingestion)  
- SFTP credentials  
- Docker (optional)  

---

## ▶️ Running Locally

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Run the API

```
uvicorn backend.app:app --reload
```

### 3. Access the UI

```
http://localhost:8000/frontend/login.html
```

---

## 🐳 Docker Deployment

### Build image:
```
docker build -t russ-analyser .
```

### Run container:
```
docker run -p 8000:8000 russ-analyser
```

For AWS:
- Assign IAM role to EC2/ECS for S3 access  
- No local AWS keys required  

---

## 🔄 End-to-End Workflow

### 1️⃣ Ingestion
AWR files come from:
- S3 → auto-sync  
- SFTP → auto-collect  
- Manual upload → UI  

### 2️⃣ Processing
`multi_analyze.py` performs:
- Parsing  
- Metrics extraction  
- VM recommendation  
- Cost estimation  

### 3️⃣ Reporting
System outputs:
- summary.json  
- summary.xlsx  
- final_excels.zip  
- history.json  

Admin UI displays:
- History  
- Reports  
- Trends  
- Cost analysis  

---

## 🏆 Impact
- Reduced manual AWR analysis time by **90%**  
- Standardized cloud sizing recommendations  
- Automated multi-cloud comparison  
- Scalable for enterprise-level customer onboarding  

---

## 📄 License
Proprietary — RUSS Consultancy Services, 2025

---

## 👤 Author
**Brendan Nicholas**  
Lead Developer & Architect  
RUSS Consultancy Services  
