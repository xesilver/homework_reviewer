# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory, which will be the root for all commands
WORKDIR /app

# Copy only the requirements file first to leverage Docker's build cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now, copy all of your project code into the container
# This will create /app/main.py and the /app/fastapi_app/ directory
COPY . .

# Set the entrypoint for Google Cloud Functions.
# The --source flag is the most reliable way to point to the entrypoint file.
CMD ["functions-framework", "--source=main.py", "--target=homework_review_triggered"]