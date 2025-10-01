# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- This is the key change ---
# Copy the main.py with your cloud function entrypoint to the root
COPY main.py .

# Copy the entire fastapi_app directory, which contains all your code
COPY fastapi_app/ ./fastapi_app

# We no longer need `pip install -e .` as this is not a package installation

# Set the entrypoint for Google Cloud Functions
# This will now work because main.py is in the root of the WORKDIR
CMD ["functions-framework", "--target=homework_review_triggered"]