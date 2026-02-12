import Head from "next/head";
import Link from "next/link";
import { SignedIn, SignedOut, SignInButton, UserButton, useAuth, useUser } from "@clerk/nextjs";
import { ChangeEvent, FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  createJob,
  getJob,
  getTranscript,
  listJobs,
  type Job,
  type JobStatus,
  uploadToPresignedPost,
} from "@/lib/api";

const SUPPORTED_AUDIO_MIME = new Set([
  "audio/mpeg",
  "audio/wav",
  "audio/mp4",
  "audio/ogg",
  "audio/flac",
]);

const POLL_INTERVAL_MS = 4000;
const MAX_POLL_ROUNDS = 150;

function isAudioFile(file: File): boolean {
  return SUPPORTED_AUDIO_MIME.has(file.type);
}

function formatDate(input: string): string {
  if (!input) return "-";
  try {
    return new Date(input).toLocaleString();
  } catch {
    return input;
  }
}

export default function DashboardPage() {
  const { getToken } = useAuth();
  const { user } = useUser();
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("en");
  const [isWorking, setIsWorking] = useState(false);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [transcript, setTranscript] = useState("");
  const [statusNote, setStatusNote] = useState("Waiting for submission");
  const [error, setError] = useState("");
  const [showTranscriptPanel, setShowTranscriptPanel] = useState(false);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const userEmail = useMemo(
    () => user?.primaryEmailAddress?.emailAddress?.trim() ?? "",
    [user?.primaryEmailAddress?.emailAddress],
  );

  const clearPollTimer = useCallback(() => {
    if (pollTimer.current) {
      clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  }, []);

  const refreshJobs = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    const data = await listJobs(token);
    setJobs(data.jobs);
  }, [getToken]);

  useEffect(() => {
    const run = async () => {
      try {
        await refreshJobs();
      } catch {
        // ignore first paint load errors
      }
    };
    run();
  }, [refreshJobs]);

  useEffect(() => {
    return () => clearPollTimer();
  }, [clearPollTimer]);

  const pollJobUntilTerminal = useCallback(
    async (jobId: string) => {
      let rounds = 0;
      clearPollTimer();

      const loop = async () => {
        rounds += 1;
        const token = await getToken();
        if (!token) {
          setError("Session is missing. Please sign in again.");
          setIsWorking(false);
          return;
        }

        const job = await getJob(token, jobId);
        setCurrentJob(job);
        setStatusNote(`Job ${job.status}`);

        if (job.status === "COMPLETED") {
          setIsWorking(false);
          setShowTranscriptPanel(true);
          try {
            const transcriptResult = await getTranscript(token, jobId);
            setTranscript(transcriptResult.transcript);
          } catch (transcriptErr) {
            setTranscript("");
            setError(
              transcriptErr instanceof Error
                ? `${transcriptErr.message}. Transcript may still be syncing.`
                : "Transcript fetch failed.",
            );
          }
          await refreshJobs();
          return;
        }

        if (job.status === "FAILED") {
          setIsWorking(false);
          setError(job.error_message || "Transcription failed.");
          await refreshJobs();
          return;
        }

        if (rounds >= MAX_POLL_ROUNDS) {
          setIsWorking(false);
          setError("Polling timed out. Check job history below.");
          await refreshJobs();
          return;
        }

        pollTimer.current = setTimeout(() => {
          void loop();
        }, POLL_INTERVAL_MS);
      };

      await loop();
    },
    [clearPollTimer, getToken, refreshJobs],
  );

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setError("");
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
  };

  const submitAudio = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setTranscript("");
    setShowTranscriptPanel(false);

    if (!file) {
      setError("Select an audio file first.");
      return;
    }

    if (!isAudioFile(file)) {
      setError("Unsupported audio type. Use mp3, wav, m4a, ogg, or flac.");
      return;
    }

    const token = await getToken();
    if (!token) {
      setError("Not authenticated.");
      return;
    }

    setIsWorking(true);
    setStatusNote("Creating job...");
    try {
      const created = await createJob(token, {
        filename: file.name,
        file_size: file.size,
        content_type: file.type,
        language,
        email: userEmail,
      });
      setCurrentJob({
        clerk_user_id: "",
        created_at: "",
        updated_at: "",
        filename: file.name,
        language,
        status: created.status,
        job_id: created.job_id,
      });

      setStatusNote("Uploading to S3...");
      await uploadToPresignedPost(created.upload, file);

      setStatusNote("Upload complete. Waiting for worker...");
      await pollJobUntilTerminal(created.job_id);
    } catch (submitErr) {
      setIsWorking(false);
      setError(submitErr instanceof Error ? submitErr.message : "Request failed.");
    }
  };

  const statusClass = useCallback((status: JobStatus) => {
    if (status === "COMPLETED") return "status-completed";
    if (status === "FAILED") return "status-failed";
    if (status === "PROCESSING") return "status-processing";
    return "status-pending";
  }, []);

  const completedCount = jobs.filter((job) => job.status === "COMPLETED").length;
  const processingCount = jobs.filter((job) => job.status === "PROCESSING").length;
  const failedCount = jobs.filter((job) => job.status === "FAILED").length;

  return (
    <>
      <Head>
        <title>EchoScribe Dashboard</title>
      </Head>
      <div className="page-shell min-h-screen">
        <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
          <div>
            <Link href="/" className="font-mono text-xs tracking-[0.22em] text-cyan-700">
              ECHOSCRIBE
            </Link>
            <h1 className="text-2xl font-semibold text-slate-900">Transcription Workspace</h1>
            <p className="mt-1 text-sm text-slate-500">Submit audio jobs and review completed conversations.</p>
          </div>
          <div className="flex items-center gap-4">
            <SignedIn>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
          </div>
        </header>

        <SignedOut>
          <section className="mx-auto mt-12 w-full max-w-3xl px-6">
            <div className="glass-panel p-10 text-center">
              <h2 className="text-2xl font-semibold text-slate-900">Sign in to access your jobs</h2>
              <p className="mt-3 text-slate-600">
                Authentication is required to access protected API endpoints and user-scoped job history.
              </p>
              <div className="mt-6">
                <SignInButton mode="modal">
                  <button className="btn-primary">Sign In</button>
                </SignInButton>
              </div>
            </div>
          </section>
        </SignedOut>

        <SignedIn>
          <main className="mx-auto grid w-full max-w-6xl gap-6 px-6 pb-12 md:grid-cols-[1.1fr_0.9fr]">
            <section className="glass-panel p-6">
              <div className="mb-5 grid gap-3 sm:grid-cols-3">
                <div className="metric-card">
                  <p className="metric-label">Completed</p>
                  <p className="metric-value">{completedCount}</p>
                </div>
                <div className="metric-card">
                  <p className="metric-label">Processing</p>
                  <p className="metric-value">{processingCount}</p>
                </div>
                <div className="metric-card">
                  <p className="metric-label">Failed</p>
                  <p className="metric-value">{failedCount}</p>
                </div>
              </div>
              <h2 className="text-xl font-semibold text-slate-900">Create Transcription Job</h2>
              <p className="mt-2 text-sm text-slate-600">
                Upload a supported audio file, submit it to the processing pipeline, and monitor status in real time.
              </p>
              <form className="mt-6 space-y-4" onSubmit={submitAudio}>
                <label className="block text-sm text-slate-700">
                  Audio File
                  <input
                    className="input-field mt-2"
                    type="file"
                    accept=".mp3,.wav,.m4a,.ogg,.flac,audio/*"
                    onChange={onFileChange}
                    disabled={isWorking}
                  />
                </label>

                <label className="block text-sm text-slate-700">
                  Language
                  <select
                    className="input-field mt-2"
                    value={language}
                    onChange={(event) => setLanguage(event.target.value)}
                    disabled={isWorking}
                  >
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="es">Spanish</option>
                  </select>
                </label>

                {file ? (
                  <p className="font-mono text-xs text-slate-500">
                    {file.name} - {(file.size / 1024 / 1024).toFixed(2)} MB - {file.type}
                  </p>
                ) : null}

                <button className="btn-primary w-full" type="submit" disabled={isWorking}>
                  {isWorking ? "Running Pipeline..." : "Submit Job"}
                </button>
              </form>

              <div className="mt-5 rounded-xl border border-slate-300 bg-white/80 p-4">
                <p className="text-sm text-slate-700">Execution Status</p>
                <p className="mt-1 font-mono text-sm text-cyan-700">{statusNote}</p>
                {currentJob ? (
                  <div className="mt-3 text-xs text-slate-500">
                    <p>job_id: {currentJob.job_id}</p>
                    <p>state: {currentJob.status}</p>
                  </div>
                ) : null}
                {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
              </div>

              {showTranscriptPanel ? (
                <article className="mt-5 rounded-xl border border-cyan-200 bg-cyan-50/70 p-4">
                  <p className="text-sm font-semibold text-cyan-700">Transcript</p>
                  <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-sm text-slate-700">
                    {transcript || "Transcript is not available yet. Check email notification as fallback."}
                  </pre>
                </article>
              ) : null}
            </section>

            <section className="glass-panel p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-900">Recent Job History</h2>
                <button
                  className="btn-secondary text-xs"
                  onClick={() => {
                    void refreshJobs();
                  }}
                  type="button"
                >
                  Refresh
                </button>
              </div>
              <div className="mt-5 space-y-3">
                {jobs.length === 0 ? (
                  <p className="text-sm text-slate-500">No jobs yet.</p>
                ) : (
                  jobs.map((job) => (
                    <div className="rounded-xl border border-slate-300 bg-white/80 p-3" key={job.job_id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium text-slate-800">{job.filename}</p>
                          <p className="mt-1 font-mono text-xs text-slate-500">{job.job_id}</p>
                        </div>
                        <span className={`status-tag ${statusClass(job.status)}`}>{job.status}</span>
                      </div>
                      <p className="mt-2 text-xs text-slate-500">{formatDate(job.updated_at)}</p>
                    </div>
                  ))
                )}
              </div>
            </section>
          </main>
        </SignedIn>
      </div>
    </>
  );
}
