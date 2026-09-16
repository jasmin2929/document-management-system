# Paperless Document Management System 
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Java](https://img.shields.io/badge/Java-25%2B-orange)
![.NET](https://img.shields.io/badge/.NET-10.0-blue)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.5%2B-green)
![Docker](https://img.shields.io/badge/Docker-Monorepo-blue)

An automated **Document Management System** for archiving, extracting, indexing, and summarizing documents asynchronously using modern cloud-native architectures.

This repository is structured as a **Monorepo** and contains all microservices and workers required for the application lifecycle.

---

## Table of Contents
- [Architecture Overview](#-architecture-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)


---

## Architecture Overview

The system processes uploaded PDF documents asynchronously through a queue-based pipeline:

1. **Upload & Storage**: The Web UI sends documents to the REST API server, which stores raw files in **MinIO** object storage and metadata in **PostgreSQL**.
2. **Message Queue**: An upload event is pushed to **RabbitMQ**.
3. **OCR Worker**: Picks up the message, fetches the PDF from MinIO, executes OCR text extraction via Tesseract, and sends extracted text to the queue.
4. **ElasticSearch Indexer**: Indexes extracted text for full-text and fuzzy search.
5. **GenAI Worker**: Passes extracted text to **Google Gemini** to generate an automated document summary, which is stored back into PostgreSQL.

---

## Features

-  **Document Upload & Archiving**: Secure object storage with MinIO.
-  **Full-Text & Fuzzy Search**: Powered by ElasticSearch for fast retrieval.
-  **Automated OCR Pipeline**: Asynchronous optical character recognition using Tesseract.
-  **AI-Powered Summarization**: Automatic document summaries generated via Google Gemini.
-  **Scheduled Batch Processing**: Daily background processing of external XML access log files.
-  **Cross-Platform Access**: Web UI and dedicated mobile app client.

---

## Tech Stack

- **Backend Framework**: Java 25 / Spring Boot 3.5+
- **Database**: PostgreSQL
- **Object Storage**: MinIO
- **Search Engine**: ElasticSearch
- **Message Broker**: RabbitMQ
- **OCR Engine**: Tesseract / Ghostscript
- **Generative AI**: Google Gemini API
- **Containerization**: Docker & Docker Compose
- **Web UI**: Nginx / Web Frontend

---

## Project Structure

```text
.
├── docker-compose.yml          # Container orchestration for all services
├── docs/                       # Project documentation & diagrams
├── src/
│   ├── web-ui/                 # Frontend Web Application (Nginx / Webserver)
│   ├── rest-api/               # REST API Server & Business Logic
│   ├── ocr-worker/             # Asynchronous OCR Worker
│   ├── genai-worker/           # Google Gemini AI Summarization Worker
│   └── batch-processor/        # Daily scheduled XML batch processing service
└── README.md
