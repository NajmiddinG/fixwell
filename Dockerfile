FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --no-input
RUN python manage.py migrate

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py create_admin && gunicorn --bind 0.0.0.0:8000 repair_booking.wsgi:application"]