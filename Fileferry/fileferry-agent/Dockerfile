FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements files
COPY requirements.txt requirements-dev.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ ./src/
COPY config/ ./config/
COPY .env.example ./.env
COPY docker-compose.yml ./
COPY buildspec.yml ./

# Expose the necessary port (if applicable)
EXPOSE 8080

# Command to run the application
CMD ["python", "src/handlers/transfer_handler.py"]