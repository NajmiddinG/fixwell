# Edge Cases

1. Two customers book the same slot.
   - The conflict check blocks the second booking.
   - The database state keeps exactly one booking record.

2. Two bookings partially overlap.
   - The overlap rule rejects the second booking whenever the ranges intersect.

3. Booking starts exactly when another ends.
   - This is allowed because the condition is strict inequality: existing end > new start and new end > existing start.

4. Technician has a lunch break.
   - The working hours model allows multiple intervals per day, which permits lunch periods.

5. Technician is unavailable.
   - Unavailability filters out any slot that intersects the blocked range.

6. Service is deactivated.
   - Service records remain in the database but cannot be used for new bookings.

7. Technician is deactivated.
   - Inactive technicians are rejected during booking validation.

8. Service price changes after booking.
   - The historical price snapshot remains protected by the model structure.

9. Service duration changes after booking.
   - The booking keeps the original duration snapshot in the database.

10. Customer tries to access another customer’s booking.
   - Permission checks reject access to non-owned records.

11. Customer cancels too late.
   - The cancellation policy blocks bookings that are less than two hours away.

12. Customer cancels an already cancelled booking.
   - Status-transition validation prevents a cancelled booking from being cancelled again.

13. Invalid status transition.
   - The booking model enforces allowed transitions to avoid arbitrary state changes.

14. Booking starts in the past.
   - Validation rejects this before creating a booking record.

15. Technician does not provide selected service.
   - Validation rejects the booking and returns a clear validation error.

16. Two concurrent booking requests.
   - The transaction and technician-row lock prevent a double booking when both requests arrive nearly simultaneously.
