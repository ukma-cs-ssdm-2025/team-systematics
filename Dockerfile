# Build the Vue.js Frontend ----
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

# Set the working directory in the final image
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python backend source code from our local machine
COPY src/ ./src/

# Copy the built frontend static files from the 'builder' stage
COPY --from=builder /app/client/dist ./client/dist

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
