# 📚 AI Homework Reviewer

An AI-powered homework reviewing system built with FastAPI and LangChain. This project automates the process of checking students' homework submissions, evaluates them based on technical requirements, and stores the results in Excel files. It supports both local file-based reviews and automated fetching from student GitHub repositories, with the ability to run as a serverless, weekly-scheduled job on Google Cloud.

---

## 🚀 Features

* **Flexible Homework Sources**:
    * **Local Repository**: Processes homework from a structured local directory (`homework/`).
    * **GitHub Integration**: Automatically clones or pulls student repositories from GitHub based on a naming convention (e.g., `lecture_1`) for review.
* **Automated Serverless Workflow on Google Cloud**:
    * Can be deployed as a **Google Cloud Function** for cost-effective, serverless execution.
    * Uses **Google Cloud Scheduler** to trigger the review process automatically on a weekly schedule.
    * Uses **Google Cloud Filestore** for persistent storage of cloned repositories and Excel reports.
    * Sends an email summary report upon completion using **SendGrid**.
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

1.  **Serverless Automated Reviewer (Recommended for Production)**: Deploy the application to Google Cloud to run automatically on a schedule. It will clone repos from GitHub, review them, and send an email summary. [See Serverless Deployment Guide](#️-serverless-deployment--usage-google-cloud).
2.  **Local REST API (for Development & Manual Reviews)**: Run the project as a local FastAPI server to manually trigger reviews for local files or GitHub repos via API calls. [See Local API Setup Guide](#️-local-installation--api-usage).

---

## 🏗️ Project Architecture

### Serverless Deployment on Google Cloud

1.  **Google Cloud Scheduler** acts as a scheduler (cron job), triggering the Cloud Function weekly.
2.  **Google Cloud Function** executes the review process, cloning repositories from GitHub.
3.  **Google Cloud Filestore** provides a persistent file system for storing the cloned repositories and the resulting Excel reports.
4.  **SendGrid** sends a summary email to an administrator upon completion of the weekly review cycle.

---

## ⚙️ Tech Stack

* **Backend**: FastAPI, Uvicorn
* **AI Orchestration**: LangChain, LangGraph
* **AI Model**: Google Gemini
* **Data Handling**: Pandas, openpyxl
* **Serverless**: Google Cloud Functions, Google Cloud Scheduler, Google Cloud Filestore
* **Email**: SendGrid
* **GitHub Integration**: PyGithub, GitPython

---

## ☁️ Serverless Deployment & Usage (Google Cloud)

This is the primary way to use the project for automated reviews. The Cloud Function runs independently of the FastAPI application.

### Prerequisites
* A Google Cloud Platform Account
* gcloud CLI configured
* Docker installed

### Step 1: Set Up Google Cloud Resources
Before deploying, create the necessary Google Cloud resources:
* **Google Cloud Filestore**: Create a new Filestore instance. Note the mount point.
* **SendGrid**: Create a SendGrid account and an API key. Verify a sender email address.

### Step 2: Package and Deploy the Cloud Function
The recommended way to deploy is by using a Docker container image.
1.  **Build and Push the Image**: Use the gcloud CLI to build your Docker image and push it to **Google Artifact Registry**.
2.  **Create the Cloud Function**:
    * In the Google Cloud Console, create a new Cloud Function and select "Container image". Provide the Artifact Registry image URI.
    * Connect the function to your VPC network and configure the Filestore instance as a mounted volume. Set the local mount path to `/mnt/nfs/homework`.
    * Add the required [environment variables](#-configuration).
    * Increase the **Timeout** to **540 seconds** (9 minutes) and **Memory** to at least **1024 MB**.
3.  **Set the Entry Point**: In the function's runtime settings, ensure the entry point is set to `homework_review_triggered`.

### Step 3: Schedule the Function
1.  In the Google Cloud Scheduler console, create a new job.
2.  Set the target to be your Cloud Function.
3.  Set the frequency using a cron expression. For example, `0 12 * * SUN` will run the function every Sunday at 12:00 PM UTC.

### Step 4: Configure Students to Review
Modify the `students.json` file in your Filestore instance to include the GitHub usernames of the students you want to review automatically each week.

---

## 🛠️ Local Installation & API Usage

You can also run the project locally as a REST API for manual, on-demand reviews.