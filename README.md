# Audio Transcription Platform

From upload to transcript delivery, this platform turns raw audio into production-ready text through a scalable, event-driven AWS pipeline.

<p>
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/TypeScript-5.0-3178C6.svg" alt="TypeScript">
  <img src="https://img.shields.io/badge/Next.js-15.5-000000.svg" alt="Next.js">
  <img src="https://img.shields.io/badge/Terraform-IaC-7B42BC.svg" alt="Terraform">
  <img src="https://img.shields.io/badge/AWS-Serverless-FF9900.svg" alt="AWS">
  <img src="https://img.shields.io/badge/Amazon_ECS-Fargate-FF9900.svg" alt="Amazon ECS Fargate">
  <img src="https://img.shields.io/badge/Amazon_DynamoDB-NoSQL-4053D6.svg" alt="Amazon DynamoDB">
  <img src="https://img.shields.io/badge/Amazon_S3-Storage-569A31.svg" alt="Amazon S3">
  <img src="https://img.shields.io/badge/Amazon_SQS-Queues-FF4F8B.svg" alt="Amazon SQS">
</p>

## Overview

This project implements an end-to-end async transcription architecture on AWS:

- users authenticate and create jobs
- audio uploads go directly to S3 via presigned requests
- S3 events push jobs to SQS
- ECS workers transcribe and write results
- notification Lambda sends completion emails
- frontend polls job status and shows transcript

Core flow:

`Client -> API -> Presigned URL -> S3 Upload -> SQS -> Worker -> Transcript -> Notification`

---

## System Architecture

<div align="center">

<img width="1422" height="1484" alt="final diagram" src="https://github.com/user-attachments/assets/0a3e4f87-ed63-4378-ab28-e4e9b32094ad" />
 
</div>

---

## User Interface

<div align="center">

 <img width="935" height="877" alt="Screenshot 2026-02-13 092513" src="https://github.com/user-attachments/assets/9a01ee51-bceb-452e-87bf-65c73b6a6f8f" />
<img width="938" height="769" alt="Screenshot 2026-02-13 092650" src="https://github.com/user-attachments/assets/9691db8e-e72a-4bf8-8a38-13241de9944f" />

</div>   

---

## Requirements & Targets

| Requirement | Specification |
|-------------|---------------|
| **Throughput** | 100,000 files/day (spikes to 300k) |
| **File Size** | Average 20 MB, ~10 minutes |
| **Processing** | Asynchronous (non-blocking) |
| **Availability** | 99.99% uptime |
| **Budget** | $50k/month |
| **Accuracy** | >= 95% transcription accuracy |
| **Languages** | English + Spanish |
| **Notifications** | User notified on completion |

## Tech Stack

### Infrastructure
- **Auth**: Clerk
- **API**: API Gateway HTTP API + FastAPI Lambda
- **Storage**: S3 (audio + transcripts)
- **Database**: DynamoDB (users + jobs)
- **Queueing**: SQS + DLQ (transcription + notification)
- **Transcription Compute**: ECS/Fargate worker (Whisper-tiny)
- **Notification Compute**: Lambda (SES + SendGrid fallback path)
- **CDN**: CloudFront
- **IaC**: Terraform
- **Observability**: CloudWatch

### Application
- **Frontend**: Next.js + React (static export)
- **Backend API**: FastAPI (Python)
- **Worker Services**: Python

## Key Design Decisions

### 1) Async uploads with presigned S3
The API creates a job and returns upload form data. Browser uploads directly to S3.

Why:
- API never handles large binaries
- upload capacity scales with S3
- no API upload bottleneck

### 2) Event-driven processing
S3 upload completion emits event to SQS transcription queue, consumed by ECS workers.

Why:
- decouples upload from processing
- buffers traffic spikes
- supports retries + DLQ

### 3) Separate notification pipeline
Worker pushes completion event to notification queue. Notification Lambda handles email delivery.

Why:
- clean separation of concerns
- email failures do not block transcription
- simpler operations and debugging

### 4) Data model
- `users` table: user metadata
- `jobs` table: lifecycle (`PENDING_UPLOAD -> PROCESSING -> COMPLETED/FAILED`)

## Autoscaling Logic (Simple)

- metric: `messages_in_queue / active_workers`
- scale up if `> 500`
- scale down if `< 200`
- scaling change: `max(20%, 10 workers)`

Example:
- `10,000 / 10 = 1,000` -> scale up
- add `max(2, 10) = 10`
- new worker count: `20`

## Cost Estimation

Assumptions (approx, us-east-1 style):
- Fargate vCPU: `$0.04048 / vCPU-hour`
- Fargate memory: `$0.004445 / GB-hour`
- worker size: `2 vCPU + 4 GB`
- S3 Standard: `$0.023 / GB-month`
- SQS: `$0.40 / 1M requests`
- SES: `$0.10 / 1,000 emails`

### A) MVP baseline (always-on minimal stack)

Worker cost:
```text
Hourly = (2 x 0.04048) + (4 x 0.004445) = 0.09874
Monthly = 0.09874 x 730 = ~$72.08
```

Reference extras:
- S3 100 GB: `~$2.30/month`
- SQS (100 jobs/day): negligible
- SES (100 emails/day): `~$0.30/month`

**MVP ballpark:** `~$80-$150/month` (depends on uptime, logs, storage growth).

### B) 100k/day thought experiment

```text
100,000 files/day x 10 min = 1,000,000 audio-min/day
Required workers at ~real-time = 1,000,000 / 1,440 = ~694
Worker compute only = 694 x $72.08 = ~$50,024/month
```

Other monthly costs at this scale are lower-order:
- storage (60 TB raw-audio retention) `~$1,380`
- SQS `~$7.20`
- SES `~$300`

**Conclusion:** compute is the main cost driver; optimization is required at true peak scale.

## Repository Structure

```text
audio_transcription/
├── guides/
│   ├── START_HERE.md
│   ├── 01-database.md
│   ├── 02-queues.md
│   ├── 03-storage.md
│   ├── 04-api-gateway-lambda.md
│   ├── 05-workers.md
│   ├── 06-notifications.md
│   ├── 07-end-to-end-validation.md
│   └── 09-frontend.md
├── terraform/
│   ├── 01_database/
│   ├── 02_queues/
│   ├── 03_storage/
│   ├── 04_api/
│   ├── 05_workers/
│   ├── 06_notifications/
│   └── 07_frontend/
├── backend/
│   ├── api/
│   ├── database/
│   ├── queues/
│   ├── worker/
│   └── notify/
└── frontend/
```

## Getting Started

Follow the runbook in strict order:

1. `guides/01-database.md`
2. `guides/02-queues.md`
3. `guides/03-storage.md`
4. `guides/04-api-gateway-lambda.md`
5. `guides/05-workers.md`
6. `guides/06-notifications.md`
7. `guides/07-end-to-end-validation.md`
8. `guides/09-frontend.md`

Entry point: `guides/START_HERE.md`

## 👤 Author

**Harsh Patel**  
📧 code.by.hp@gmail.com  
🔗 GitHub: https://github.com/CodeBy-HP/  
🔗 LinkedIn: https://www.linkedin.com/in/harsh-patel-389593292/

⭐ Star this repo if you found it insightful.
