# Repair Service Booking System

## 1. Project purpose
This project is a backend-focused appointment booking system for a small repair service business. Customers can browse services, inspect technician availability, and create repair appointments. Administrators manage technicians, schedules, and booking lifecycle states.

## 2. Business domain
The business model is a monolithic Django application with five core domains:
- users
- services
- technicians
- availability
- bookings

The system stores technician schedules, service definitions, customer bookings, and booking status transitions without allowing destructive deletes for historical data.

## 3. Features
- Email-based authentication with JWT
- Service catalog with deactivation instead of hard deletes
- Technician model with many-to-many service assignment
- Working hours and date-specific unavailability
- Availability slot calculation for a requested date
- Booking creation, confirmation, cancellation, and completion
- Business rules and validation for working hours, conflicts, timing, and permission checks
- PostgreSQL-ready architecture with transaction-safe booking protection

## 4. Architecture
This is a Django monolith built with DRF and a structured app-per-domain layout. The most important business logic lives under the booking service modules instead of inside serializers or view logic.

## 5. Tech stack
- Python 3.9+ in this workspace
- Django 4.2
- Django REST Framework
- PostgreSQL-ready settings
- SimpleJWT
- pytest and pytest-django
- drf-spectacular
- Docker and Docker Compose

## 6. Database relationships
- User: custom email-based authentication model
- Technician: one-to-one with User
- Service: service catalog record
- TechnicianService: many-to-many link between technicians and services
- WorkingHour: weekday-specific technician schedule
- Unavailability: date ranges when a technician is unavailable
- Booking: customer + technician + service + time slots + status snapshot

## 7. Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
```

## 8. Environment variables
Use values from `.env.example` for local development. The project reads `SECRET_KEY`, `DEBUG`, `POSTGRES_*` variables automatically.

## 9. Docker setup
```bash
docker-compose up --build
```
The stack includes:
- `web` for Django
- `db` for PostgreSQL

## 10. Running migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## 11. Seed data
A demo command is not yet implemented in this workspace; the code is structured to support it and can be added with a management command in a follow-up iteration.

## 12. Running tests
```bash
pytest -q
```

## 13. API documentation
OpenAPI endpoints are available at:
- /api/schema/
- /api/docs/
- /api/redoc/

## 14. Authentication
The service supports:
- POST /api/auth/register/
- POST /api/auth/login/
- POST /api/auth/refresh/
- GET /api/auth/me/

## 15. Booking flow
Customer flow:
1. Authenticate
2. Request availability with service_id, technician_id, and date
3. Receive slot list
4. Create booking with a chosen slot
5. The backend calculates end time, price, and duration
6. Admin confirms or cancels the booking as needed

## 16. Double-booking protection
The application uses a transactional booking service with `transaction.atomic()` and a lock on the technician row during conflict validation. This is the selected concurrency strategy because it is straightforward, reliable, and avoids competing PostgreSQL exclusion-constraint complexity for the MVP while still preventing overlapping booking creation in the same transaction window.

## 17. Edge cases
The business logic explicitly handles past bookings, inactive services, inactive technicians, lunch breaks, unavailability periods, service mismatches, and invalid cancellation windows.

## 18. AI usage
This workspace was developed with AI assistance for scaffolding, database modeling, and API refactoring. All business logic and validation decisions were reviewed and adjusted to match the repair-booking requirements before validation.

## 19. Known limitations
- The current workspace uses SQLite for local development by default, while the system is designed to use PostgreSQL in production.
- Seed data and a full admin management command are not yet in place.
- The code is intentionally kept small and monotonic to match the assignment goals.
