# Repair Service Booking System

## 1. Project Goal

Build a backend-focused appointment booking system for a small repair service business.

Customers can:
- register/login
- browse repair services
- view technicians
- view available time slots
- create bookings
- view booking history
- cancel eligible bookings

Admins can:
- manage services
- manage technicians
- manage technician services
- manage working hours
- manage unavailability
- manage bookings

The most important technical requirement is preventing double booking,
including concurrent booking requests.

---

## 2. Technology Stack

- Python 3.12+
- Django 5.x
- Django REST Framework
- PostgreSQL
- SimpleJWT
- pytest
- pytest-django
- drf-spectacular
- Docker
- Docker Compose

Do not introduce unnecessary technologies.

Do not use microservices, Kafka, Kubernetes, GraphQL, CQRS,
or other unnecessary architecture.

---

## 3. Architecture

Use a modular Django monolith.

Applications:

- users
- services
- technicians
- availability
- bookings

Business logic should be separated from HTTP/API code.

Important booking logic should live in:

    apps/bookings/services/

Use PostgreSQL as the source of truth for critical booking constraints.

---

## 4. Users

Create a custom Django User model.

Fields:

- id
- email
- first_name
- last_name
- is_active
- is_staff
- date_joined
- created_at
- updated_at

Email is unique and is used for authentication.

Roles:

- customer
- admin

Do not create a complicated permission system.

---

## 5. Services

Model:

    Service

Fields:

- id
- name
- description
- duration_minutes
- price
- is_active
- created_at
- updated_at

Rules:

- name is required
- duration_minutes > 0
- price >= 0
- inactive services cannot be booked
- historical bookings must remain valid after service deactivation

Use DecimalField for price.

---

## 6. Technicians

Model:

    Technician

Fields:

- id
- user
- bio
- is_active
- created_at
- updated_at

Relationship:

    Technician <-> Service

A technician can provide multiple services.

A service can have multiple technicians.

Use a through model if useful:

    TechnicianService

with a unique constraint on:

    technician + service

A customer can only book a service with a technician who provides
that service.

---

## 7. Working Hours

Model:

    WorkingHour

Fields:

- id
- technician
- weekday
- start_time
- end_time

Rules:

- start_time < end_time
- working-hour intervals for the same technician/day cannot overlap
- multiple intervals are allowed

Example:

    Monday
    09:00 - 13:00
    14:00 - 18:00

---

## 8. Unavailability

Model:

    Unavailability

Fields:

- id
- technician
- start_datetime
- end_datetime
- reason
- created_at

Rules:

- start_datetime < end_datetime
- unavailability overrides normal working hours

Examples:

- vacation
- holiday
- personal leave

---

## 9. Booking

Model:

    Booking

Fields:

- id
- customer
- technician
- service
- start_datetime
- end_datetime
- status
- price_at_booking
- duration_at_booking
- customer_note
- created_at
- updated_at
- cancelled_at

The customer is taken from the authenticated user.

The client must NOT provide:

- customer
- end_datetime
- price
- duration
- status

The backend calculates these values.

---

## 10. Booking Status

Statuses:

- PENDING
- CONFIRMED
- CANCELLED
- COMPLETED

Allowed transitions:

    PENDING -> CONFIRMED
    PENDING -> CANCELLED

    CONFIRMED -> COMPLETED
    CONFIRMED -> CANCELLED

Do not allow arbitrary status changes.

---

## 11. Price and Duration Snapshot

When a booking is created:

    price_at_booking = service.price
    duration_at_booking = service.duration_minutes

These values must never change when the service is modified later.

Example:

Service initially:

    price = 100000
    duration = 60

Existing booking must keep:

    price_at_booking = 100000
    duration_at_booking = 60

even if the service later changes.

---

## 12. Booking Time

The client sends:

    service_id
    technician_id
    start_datetime
    customer_note

The backend calculates:

    end_datetime =
        start_datetime + service.duration_minutes

Use timezone-aware datetimes.

Django must use:

    USE_TZ = True

Store timestamps in UTC.

---

## 13. Availability

Implement:

    get_available_slots(
        technician,
        service,
        date
    )

The algorithm must consider:

1. technician status
2. service status
3. technician/service relationship
4. working hours
5. unavailability
6. existing bookings
7. service duration
8. current time

Default slot interval:

    15 minutes

A generated slot must fit completely inside working hours.

---

## 14. Booking Overlap

Two appointments overlap when:

    existing.start_datetime < new_end_datetime
    AND
    existing.end_datetime > new_start_datetime

Example:

    Existing: 14:00 - 15:00
    New:      14:30 - 15:30

These overlap.

Example:

    Existing: 14:00 - 15:00
    New:      15:00 - 16:00

These do not overlap.

CANCELLED bookings do not block availability.

---

## 15. Double Booking Protection

This is a critical requirement.

Do NOT rely only on:

    Booking.objects.filter(...).exists()

because two concurrent requests can both pass the check.

Booking creation must be atomic.

Use:

    transaction.atomic()

and PostgreSQL-safe concurrency protection.

Prefer a database-level solution when practical.

The final implementation must guarantee:

    Same technician
    +
    overlapping time
    =
    maximum one active booking

If a concurrent request loses the race, return:

    HTTP 409 Conflict

with:

```json
{
    "error": {
        "code": "BOOKING_CONFLICT",
        "message": "The selected time slot is no longer available."
    }
}