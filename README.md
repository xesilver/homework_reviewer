# 📚 AI Homework Reviewer

An AI-powered homework reviewing system built with FastAPI and LangChain. This project automates the process of checking students' homework submissions, evaluates them based on technical requirements, and stores the results in Excel files. It supports both local file-based reviews and automated fetching from student GitHub repositories, with the ability to run as a serverless, weekly-scheduled job on AWS Lambda.

---

## 🚀 Features

* **Flexible Homework Sources**:
    * **Local Repository**: Processes homework from a structured local directory (`homework/`).
    * **GitHub Integration**: Automatically clones or pulls student repositories from GitHub based on a naming convention (e.g., `lecture_1`) for review.
* **Automated Serverless Workflow on AWS**:
    * Can be deployed as an **AWS Lambda** function for cost-effective, serverless execution.
    * Uses **Amazon EventBridge** to trigger the review process automatically on a weekly schedule.
    * Uses **Amazon EFS** for persistent storage of cloned repositories and Excel reports.
    * Sends an email summary report upon completion using **Amazon SES**.
* **Automated AI Agent Review**:
    * Uses LangChain and LangGraph to orchestrate a multi-step evaluation of each task.
    * Checks for technical correctness, code style, documentation, and performance.
    * Assigns a percentage score and generates detailed, constructive feedback for each submission.
* **Comprehensive Reporting**:
    * Stores detailed review results in structured **Excel files** (`.xlsx`).
    * Supports exporting results to **CSV** format via the API.
* **RESTful API Layer**:
    * Built with **FastAPI** to provide endpoints for triggering reviews, checking results, and managing the repository.

---

## 🎯 Project Usage Models

This project can be used in two primary ways. Choose the one that best fits your needs.

1.  **Serverless Automated Reviewer (Recommended for Production)**: Deploy the application to AWS Lambda to run automatically on a schedule. It will clone repos from GitHub, review them, and send an email summary. [See Serverless Deployment Guide](#️-serverless-deployment--usage-aws-lambda).
2.  **Local REST API (for Development & Manual Reviews)**: Run the project as a local FastAPI server to manually trigger reviews for local files or GitHub repos via API calls. [See Local API Setup Guide](#️-local-installation--api-usage).

---

## 🏗️ Project Architecture

### Serverless Deployment on AWS



1.  **Amazon EventBridge** acts as a scheduler (cron job), triggering the Lambda function weekly.
2.  **AWS Lambda** executes the review process, cloning repositories from GitHub.
3.  **Amazon EFS** provides a persistent file system for storing the cloned repositories and the resulting Excel reports.
4.  **Amazon SES** sends a summary email to an administrator upon completion of the weekly review cycle.

---

## ⚙️ Tech Stack

* **Backend**: FastAPI, Uvicorn
* **AI Orchestration**: LangChain, LangGraph
* **AI Model**: OpenAI (GPT series)
* **Data Handling**: Pandas, openpyxl
* **Serverless**: AWS Lambda, Amazon EventBridge, Amazon EFS, Amazon SES
* **GitHub Integration**: PyGithub, GitPython
* **AWS SDK**: Boto3

---

## ☁️ Serverless Deployment & Usage (AWS Lambda)

This is the primary way to use the project for automated reviews. The Lambda function runs independently of the FastAPI application.

### Prerequisites
* An AWS Account
* AWS CLI configured
* Docker installed

### Step 1: Set Up AWS Resources
Before deploying, create the necessary AWS resources:
* **Amazon EFS**: Create a new Elastic File System in a VPC. Create an access point and note down its ID. Ensure its security group will allow inbound NFS traffic from the Lambda function's security group.
* **Amazon SES**: Verify a sender email address in the SES console (e.g., `reviews@yourdomain.com`). This address will be used to send the summary reports. Remember to move your SES account out of the sandbox for production use.

### Step 2: Package and Deploy the Lambda Function
The recommended way to deploy is by using a Docker container image.
1.  **Build and Push the Image**: Use the AWS CLI to build your Docker image and push it to **Amazon ECR** (Elastic Container Registry).
2.  **Create the Lambda Function**:
    * In the AWS Lambda console, create a new function and select "Container image". Provide the ECR image URI.
    * **Configuration -> File systems**: Attach your EFS file system using the access point you created. Set the local mount path to `/mnt/efs`.
    * **Configuration -> Environment variables**: Add the required [environment variables](#-configuration).
    * **Configuration -> General configuration**: Increase the **Timeout** to **15 minutes** and **Memory** to at least **1024 MB**.
    * **Configuration -> Permissions**: Attach policies to the function's IAM role that allow it to access EFS and send emails via SES (`AmazonSESFullAccess`).
3.  **Set the Handler**: In the function's runtime settings, ensure the handler is set to `lambda_handler.handler`.

### Step 3: Schedule the Function
1.  In the AWS Lambda console, click **Add trigger**.
2.  Select **EventBridge (CloudWatch Events)**.
3.  Create a new rule with a **Schedule expression**. For example, `cron(0 12 ? * SUN *)` will run the function every Sunday at 12:00 PM UTC.

### Step 4: Configure Students to Review
Modify the `STUDENTS_TO_REVIEW` list in `lambda_handler.py` to include the GitHub nicknames of the students you want to review automatically each week.

---

## 🛠️ Local Installation & API Usage

You can also run the project locally as a REST API for manual, on-demand reviews.

