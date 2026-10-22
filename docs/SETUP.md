# InfraPulse Setup & Deployment Guide

## Prerequisites
- **Python**: 3.11+
- **Node.js**: v18+ & npm
- **Container Runtime**: Podman 4.0+ (or Docker)

---

## Local Development Setup

### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed default users (admin/operator), rules, and demo fixtures
python seed_demo_data.py

# Run one-off metrics collection
python manage.py collect_metrics

# Start backend server
python manage.py runserver 127.0.0.1:8000
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Open **http://127.0.0.1:5173** in your browser.

### 3. Background Collector Daemon
To continuously collect container stats and evaluate alert rules every 5 seconds:
```bash
cd backend
source venv/bin/activate
python manage.py collect_metrics --daemon --interval 5
```

---

## Automated Test Execution

Run the complete pytest test suite:
```bash
cd backend
source venv/bin/activate
python -m pytest
```

---

## Podman Compose Deployment

```bash
cd deploy
podman-compose -f podman-compose.yml up -d
```
Services deployed:
- **InfraPulse Frontend**: `http://localhost:5173`
- **InfraPulse Backend**: `http://localhost:8000`
- **Prometheus Scraper**: `http://localhost:9090`
- **Collector Daemon**: runs host-side queries and feeds backend
