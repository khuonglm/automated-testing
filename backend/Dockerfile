FROM python:3.9-slim

WORKDIR /app

ENV FLASK_APP=/app/autoapp.py
ENV FLASK_DEBUG=1

COPY . .

RUN pip install --no-cache-dir -r requirements/dev.txt

RUN flask db init && flask db migrate && flask db upgrade

EXPOSE 5000

# Command to run the application
CMD ["flask", "run", "--with-threads"]