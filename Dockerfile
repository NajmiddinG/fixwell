FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_data && python manage.py create_admin && gunicorn --bind 0.0.0.0:8000 repair_booking.wsgi:application"]