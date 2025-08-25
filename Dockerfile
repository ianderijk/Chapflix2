# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /media/idr/ExtDrive/Chapflix

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code into the container
COPY . .

# Expose the port your app runs on
EXPOSE 8042

# Set up app user
RUN useradd app
USER app

# Run the app
CMD ["python", "main.py"]