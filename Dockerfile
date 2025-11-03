# Build the Vue.js Frontend
FROM node:20-alpine AS builder

# Set the working directory for the frontend
WORKDIR /app/client

# Copy package.json and package-lock.json first to leverage Docker layer caching.
COPY client/package.json client/package-lock.json ./

# Install frontend dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY client/ ./

# Build the frontend for production.
RUN npm run build

# Build the Final Production Image ----
FROM python:3.11-slim

# 1) створити non-root користувача
RUN groupadd -g 10001 app && useradd -r -u 10001 -g app app

WORKDIR /app

# Python looks in app directory
ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy Python source code from the src directory into the container.
COPY --chown=app:app --chmod=0555 src/ /app/src/

COPY --from=builder --chown=app:app --chmod=0555 /app/client/dist /app/client/dist

# запустити від non-root
USER app

EXPOSE 3000

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "3000"]

