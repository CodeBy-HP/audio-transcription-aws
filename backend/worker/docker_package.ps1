param(
    [string]$EnvFile = "",
    [string]$RepositoryUrl = "",
    [string]$ImageTag = "",
    [switch]$BuildOnly,
    [switch]$PushOnly
)

$ErrorActionPreference = "Stop"

if ($BuildOnly -and $PushOnly) {
    throw "Use either -BuildOnly or -PushOnly, not both."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\\..")).Path

if ([string]::IsNullOrWhiteSpace($EnvFile)) {
    $EnvFile = Join-Path $repoRoot ".env"
} elseif (-not [System.IO.Path]::IsPathRooted($EnvFile)) {
    $EnvFile = Join-Path (Get-Location) $EnvFile
}

function Require-Command {
    param([string]$CommandName)
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $CommandName"
    }
}

function Set-EnvFromDotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        if ($line -match "^([A-Za-z_][A-Za-z0-9_]*)=(.*)$") {
            $key = $matches[1]
            $value = $matches[2].Trim()

            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }

            if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key))) {
                [Environment]::SetEnvironmentVariable($key, $value)
            }
        }
    }
}

function Run-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    Write-Host "==> $Name"
    & $Action
}

Require-Command "aws"
Require-Command "docker"

Set-EnvFromDotEnv -Path $EnvFile

$awsRegion = [Environment]::GetEnvironmentVariable("AWS_REGION")
if ([string]::IsNullOrWhiteSpace($awsRegion)) {
    $awsRegion = [Environment]::GetEnvironmentVariable("DEFAULT_AWS_REGION")
}
if ([string]::IsNullOrWhiteSpace($awsRegion)) {
    throw "Missing required setting: AWS_REGION (or DEFAULT_AWS_REGION)"
}

$workerModelId = [Environment]::GetEnvironmentVariable("WHISPER_MODEL_ID")
if ([string]::IsNullOrWhiteSpace($workerModelId)) {
    $workerModelId = "openai/whisper-tiny"
}

if ([string]::IsNullOrWhiteSpace($RepositoryUrl)) {
    $RepositoryUrl = [Environment]::GetEnvironmentVariable("WORKER_ECR_REPOSITORY_URL")
}
$RepositoryUrl = "$RepositoryUrl".Trim()
if ([string]::IsNullOrWhiteSpace($RepositoryUrl)) {
    throw "Missing required setting: WORKER_ECR_REPOSITORY_URL (or pass -RepositoryUrl)"
}

if ([string]::IsNullOrWhiteSpace($ImageTag)) {
    $ImageTag = [Environment]::GetEnvironmentVariable("WORKER_IMAGE_TAG")
}
if ([string]::IsNullOrWhiteSpace($ImageTag)) {
    $ImageTag = "latest"
}

$registry = ($RepositoryUrl -split "/")[0]
$localImageName = "audiotrans-worker:$ImageTag"
$remoteImageName = "$RepositoryUrl`:$ImageTag"

Run-Step "AWS identity check" {
    aws sts get-caller-identity | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "AWS credentials check failed." }
}

Run-Step "Docker daemon check" {
    docker info | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Docker daemon is not reachable." }
}

Run-Step "Login to ECR registry: $registry" {
    $password = aws ecr get-login-password --region $awsRegion
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($password)) {
        throw "Failed to get ECR login password."
    }
    $password | docker login --username AWS --password-stdin $registry | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Docker login to ECR failed." }
}

if (-not $PushOnly) {
    Run-Step "Build worker image: $localImageName" {
        docker build --build-arg "WHISPER_MODEL_ID=$workerModelId" -t $localImageName $scriptDir
        if ($LASTEXITCODE -ne 0) { throw "Docker build failed." }
    }

    Run-Step "Tag image: $remoteImageName" {
        docker tag $localImageName $remoteImageName
        if ($LASTEXITCODE -ne 0) { throw "Docker tag failed." }
    }
}

if (-not $BuildOnly) {
    Run-Step "Push image: $remoteImageName" {
        docker push $remoteImageName
        if ($LASTEXITCODE -ne 0) { throw "Docker push failed." }
    }
}

Write-Host ""
Write-Host "Worker image ready: $remoteImageName"
Write-Host "Set terraform/05_workers/terraform.tfvars:"
Write-Host "worker_image_uri = `"$remoteImageName`""
