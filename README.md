# GymAI - Production-Grade Fitness Platform

GymAI is a scalable, production-ready AI-powered fitness coaching platform built with a **Modular Monolith** architecture.

---

## 🚀 Tech Stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, React Hook Form, Zod, Axios
- **Backend**: FastAPI, Python 3.10+, SQLAlchemy, Alembic, Pydantic
- **Database**: PostgreSQL
- **API**: REST
- **Containerization**: Docker, Docker Compose
- **Architecture**: Modular Monolith & Clean Architecture

---

## 📁 Repository Structure

```text
gym-ai/
├── backend/          # FastAPI server (Clean Architecture)
├── frontend/         # Next.js App Router UI
├── docker/           # Dockerfiles & container configs
├── docs/             # Technical documentation & AI guidelines
├── config/           # Service configurations
├── scripts/          # Automation & seed scripts
└── docker-compose.yml# Multi-container orchestration
```

---

## 🛠️ Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Verify backend health: `http://localhost:8000/health`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Access UI at `http://localhost:3000`

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```
- Backend API: `http://localhost:8000`
- Frontend UI: `http://localhost:3000`
- PostgreSQL: `localhost:5432`

---

## 📚 Documentation

For engineering standards, architectural rules, and development guidelines, refer to:
- [AI Development Guide](file:///c:/Users/Dell/Desktop/gym-ai/docs/ai/development_guide.md)
