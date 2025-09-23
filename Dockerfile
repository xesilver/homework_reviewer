# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# We also install git, which is needed to clone repositories.
RUN apt-get update && apt-get install -y git && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Install the local project package
RUN pip install -e .

# Set the command to be executed when the container starts for Lambda
# This specifies the file and the handler function.
CMD [ "lambda_handler.handler" ]
