# Test Data Generator Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test data generation scripts
COPY . .

# Set executable permissions
RUN chmod +x generate_test_data.py

# Default command
CMD ["python", "generate_test_data.py"]
