# Architecture Overview

## Why Django/DRF?
Django and DRF provide a practical, focused foundation for a small monolithic scheduling backend. The assignment is domain-heavy but not large enough to justify additional infrastructure. This keeps the code easier to read, validate, and audit.

## Why PostgreSQL?
PostgreSQL is the natural data store for a booking system because it supports transactional consistency and atomic validation. The application uses it as the source of truth for booking safety, especially under concurrency.

## Why a custom User model?
The custom user model gives the application a single email-based login identity while still using Django’s built-in password hashing and authentication framework. This avoids ad hoc password storage and keeps a clear administrator/customer split.

## Why price_at_booking?
The booking model stores a snapshot of the service’s price and duration at booking time. This guarantees that historical records remain correct even if the service configuration changes later.

## Why duration_at_booking?
The same reasoning applies to duration. An appointment history must always show the exact duration that was originally booked, not a later edited value.

## Why business logic is separated from serializers?
Serializers should validate the incoming request body. The actual booking rules belong in dedicated services so they are easy to test and reason about. This prevents complex logic from being hidden inside generic DRF code.

## How availability is calculated?
The availability service reads the technician’s weekday schedule, excludes lunch breaks and other unavailable windows, filters out conflicting bookings, and returns only slots that fit completely inside the technician’s working period.

## How overlapping appointments are detected?
The overlap check uses the standard interval condition:
- existing.start_datetime < new_end_datetime
- existing.end_datetime > new_start_datetime
This catches both partial and full overlap while allowing adjacent bookings to start exactly when another ends.

## How double booking is prevented?
The project uses a transactional booking service plus a row lock on the technician record. This is the selected concurrency safeguard for the MVP because it is explicit, testable, and reliable without introducing more complex PostgreSQL range constraints into this version of the project.

## How transactions are used?
Booking creation occurs inside `transaction.atomic()` so the conflict check and insert happen as one atomic operation. If the slot is no longer available in that transaction window, the system exits with a conflict instead of creating a duplicate.

## Why this concurrency strategy was chosen?
The chosen approach is simpler to reason about than a database exclusion constraint while still addressing the critical double-booking requirement. It keeps the booking state safe under concurrent requests and is easier for a mid-level Django developer to maintain.

## How permissions work?
- Customers can list and view only their own bookings.
- Customers can cancel eligible bookings they own.
- Admins can manage services, technicians, working hours, unavailability, and all bookings.
- Booking status transitions are routed through dedicated actions instead of generic patch endpoints.
