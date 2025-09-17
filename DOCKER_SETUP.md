# DeviceWatch - Docker Setup

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git (to clone the repository)

### Running the Application

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/exame-fullstack-setembro-dtlabs-2025.git
cd exame-fullstack-setembro-dtlabs-2025
```

2. **Start all services:**
```bash
docker-compose up -d
```

3. **Check service status:**
```bash
docker-compose ps
```

4. **View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f simulator
```

## Services

### Backend API
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Database
- **PostgreSQL**: localhost:5432
- **Database**: devicewatch
- **User**: devicewatch
- **Password**: devicewatch123

### Redis
- **URL**: localhost:6379
- **Purpose**: Pub/Sub for real-time communication

### Device Simulator
- **Purpose**: Simulates IoT devices sending heartbeats
- **Devices**: 10 devices (3 servers, 4 IoT, 3 routers)
- **Heartbeat Interval**: 60 seconds

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Current user info

### Devices
- `GET /api/v1/devices/` - List devices
- `POST /api/v1/devices/` - Create device
- `GET /api/v1/devices/{id}` - Get device
- `PUT /api/v1/devices/{id}` - Update device
- `DELETE /api/v1/devices/{id}` - Delete device

### Heartbeats
- `POST /api/v1/heartbeats/{device_id}` - Send heartbeat
- `GET /api/v1/heartbeats/{device_id}` - Get device heartbeats
- `GET /api/v1/heartbeats/{device_id}/latest` - Latest heartbeat
- `GET /api/v1/heartbeats/{device_id}/health-score` - Health score stats

### Alerts
- `GET /api/v1/alerts/` - List alerts
- `POST /api/v1/alerts/` - Create alert
- `GET /api/v1/alerts/{id}` - Get alert
- `PUT /api/v1/alerts/{id}` - Update alert
- `DELETE /api/v1/alerts/{id}` - Delete alert

## Testing with Postman

### 1. Register a new user
```bash
POST http://localhost:8000/api/v1/auth/register
Content-Type: application/json

{
  "email": "test@example.com",
  "full_name": "Test User",
  "password": "testpassword123"
}
```

### 2. Login
```bash
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=test@example.com&password=testpassword123
```

### 3. Get current user (with token)
```bash
GET http://localhost:8000/api/v1/auth/me
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up --build -d
```

### Database connection issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U devicewatch -d devicewatch
```

### Backend not responding
```bash
# Check backend logs
docker-compose logs backend

# Check health
curl http://localhost:8000/health
```

## Development

### Making changes
- Backend code is mounted as volume, changes are reflected immediately
- Database migrations run automatically on startup
- Simulator restarts automatically when backend changes

### Stopping services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Production Notes

- Change `SECRET_KEY` in `backend/docker.env`
- Use proper database credentials
- Configure proper CORS origins
- Set up SSL/TLS termination
- Use Docker secrets for sensitive data
