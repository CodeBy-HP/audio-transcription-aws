# 07 - End-to-End Validation (Backend)

## Goal

Prove full backend flow works:

API -> S3 upload -> queue -> ECS worker -> transcript -> email.

## Required `.env` Values

```env
API_BASE_URL="https://<api-id>.execute-api.us-east-1.amazonaws.com"
CLERK_SECRET_KEY="<clerk-secret-key>"
CLERK_API_BASE_URL="https://api.clerk.com"
CLERK_TEST_USER_PASSWORD="P@ssw0rd!test123"
E2E_AUDIO_FILE="backend/api/harvard.wav"
TRANSCRIPT_BUCKET_NAME="<terraform output transcript_bucket_name>"
```

## Commands

1. API health check:

```powershell
curl "$env:API_BASE_URL/health"
```

2. Run automated E2E test:

```powershell
uv run backend/api/test_deployed_api_with_clerk.py --audio-file backend/api/harvard.wav --show-transcript
```

Optional: force specific user email for SES sandbox testing:

```powershell
uv run backend/api/test_deployed_api_with_clerk.py --audio-file backend/api/harvard.wav --user-email your_verified_recipient@example.com --show-transcript
```

Optional: save transcript to local file:

```powershell
uv run backend/api/test_deployed_api_with_clerk.py --audio-file backend/api/harvard.wav --show-transcript --save-transcript-path out/transcript.txt
```

## Pass Criteria

- script prints: `PASS: Full flow completed (API -> S3 upload -> queue/worker -> job completion).`
- final payload status is `COMPLETED`
- transcript text is printed when `--show-transcript` is used
- notification email is received (SES sandbox rules apply)

## Fast Troubleshooting Commands

```powershell
aws logs tail /ecs/audiotrans-dev-transcription-worker --follow --region us-east-1
aws logs tail /aws/lambda/audiotrans-dev-notification-worker --follow --region us-east-1
```

Next: `guides/09-frontend.md`
