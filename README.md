# DeviceWatch - IoT Monitoring Platform

A comprehensive IoT device monitoring platform built with FastAPI, React, and real-time WebSocket communication.

## Features

- **Real-time Monitoring**: Live device health monitoring with WebSocket updates
- **Health Scoring**: Intelligent algorithm combining CPU, RAM, temperature, and connectivity metrics
- **Alert System**: Configurable alerts with compound conditions and real-time notifications
- **Device Management**: Complete CRUD operations with bulk actions
- **Data Visualization**: Interactive charts and historical data analysis
- **Export Capabilities**: CSV/JSON data export for integration
- **Responsive Design**: Mobile-first design with dark mode support

## Architecture

```
devicewatch/
├── backend/              # FastAPI application
├── frontend/             # React + TypeScript
├── device-simulator/     # Python heartbeat simulator
├── docker-compose.yaml   # Complete stack
└── docs/                 # Documentation
```

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Primary database
- **Redis** - Pub/sub for real-time communication
- **Alembic** - Database migrations
- **JWT** - Authentication

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Recharts** - Data visualization
- **Axios** - HTTP client

### Infrastructure
- **Docker** - Containerization
- **WebSockets** - Real-time communication
- **Redis Pub/Sub** - Message broadcasting

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/exame-fullstack-setembro-dtlabs-2025.git
cd exame-fullstack-setembro-dtlabs-2025

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend setup
cd frontend
npm install
npm run dev

# Device Simulator
cd device-simulator
pip install -r requirements.txt
python simulator.py
```

## Device Data Model

Each device sends heartbeats every minute with the following metrics:

- **CPU Usage** (%) - Current CPU utilization
- **RAM Usage** (%) - Current memory usage
- **Free Disk Space** (%) - Available disk space
- **Temperature** (°C) - Device temperature
- **DNS Latency** (ms) - Latency to 8.8.8.8
- **Connectivity** (0/1) - Online/offline status
- **Boot Timestamp** (UTC) - Last boot time

## Health Scoring Algorithm

The health score (0-100) is calculated using weighted metrics:

- **CPU Usage**: 25% weight
- **RAM Usage**: 25% weight
- **Temperature**: 30% weight
- **Disk Space**: 15% weight
- **Connectivity**: 5% weight

## Configuration

Environment variables can be configured in `.env` files:

```bash
# Backend
DATABASE_URL=postgresql://user:password@localhost/devicewatch
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Monitoring

The platform includes built-in monitoring capabilities:

- Real-time device status
- Historical performance trends
- Alert notifications
- Health score tracking
- Connectivity monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Project Goals

This project demonstrates:

- **Full-stack development** with modern technologies
- **Real-time communication** using WebSockets
- **Scalable architecture** with microservices
- **Professional code quality** and best practices
- **Production-ready** deployment with Docker

Built as a technical assessment for dtLabs - Edge AI and Computer Vision solutions.
