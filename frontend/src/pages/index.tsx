import Head from "next/head";
import Link from "next/link";
import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";

export default function Home() {
  return (
    <>
      <Head>
        <title>EchoScribe | Audio Transcription Conversation</title>
      </Head>
      <div className="page-shell min-h-screen">
        <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
          <div>
            <p className="font-mono text-xs tracking-[0.2em] text-cyan-700">ECHOSCRIBE</p>
            <h1 className="text-xl font-semibold text-slate-900">Audio Transcription Conversation</h1>
          </div>
          <div className="flex items-center gap-3">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="btn-secondary">Sign In</button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="btn-primary">Create Account</button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <Link className="btn-primary" href="/dashboard">
                Open Dashboard
              </Link>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
          </div>
        </header>

        <main className="mx-auto mt-10 w-full max-w-6xl space-y-6 px-6 pb-12">
          <section className="glass-panel p-8">
            <p className="status-chip mb-5">ENTERPRISE READY</p>
            <h2 className="max-w-3xl text-4xl font-semibold leading-tight text-slate-900">
              Turn raw audio into clean, readable conversations in minutes.
            </h2>
            <p className="mt-4 max-w-3xl text-base text-slate-600">
              EchoScribe helps teams capture meetings, interviews, and voice notes with fast
              transcription and a simple review experience.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <SignedOut>
                <SignUpButton mode="modal">
                  <button className="btn-primary">Get Started</button>
                </SignUpButton>
                <SignInButton mode="modal">
                  <button className="btn-secondary">Existing Customer Sign In</button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <Link className="btn-primary" href="/dashboard">
                  Open Dashboard
                </Link>
              </SignedIn>
            </div>
          </section>

          <section className="glass-panel p-6">
            <p className="font-mono text-xs tracking-[0.22em] text-cyan-700">CORE VALUE</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <div className="metric-card">
                <p className="metric-label">Turnaround</p>
                <p className="metric-value">Near Real-Time Queueing</p>
              </div>
              <div className="metric-card">
                <p className="metric-label">Output</p>
                <p className="metric-value">Structured Transcript Text</p>
              </div>
              <div className="metric-card">
                <p className="metric-label">Security</p>
                <p className="metric-value">Authenticated User Sessions</p>
              </div>
            </div>
          </section>

          <section className="glass-panel p-6">
            <p className="font-mono text-xs tracking-[0.22em] text-cyan-700">SUPPORTED LANGUAGES</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="lang-chip">English</span>
              <span className="lang-chip">Hindi</span>
              <span className="lang-chip">Spanish</span>
            </div>
          </section>

          <section className="glass-panel p-6">
            <p className="font-mono text-xs tracking-[0.22em] text-cyan-700">WHY TEAMS CHOOSE ECHOSCRIBE</p>
            <div className="pipeline-row mt-4">
              <div className="pipeline-node">
                <span className="flow-step">01</span>
                <p className="pipeline-title">Upload Audio</p>
                <p className="pipeline-copy">Submit file in seconds.</p>
              </div>
              <span className="pipeline-arrow">→</span>
              <div className="pipeline-node">
                <span className="flow-step">02</span>
                <p className="pipeline-title">Monitor Progress</p>
                <p className="pipeline-copy">Live status in dashboard.</p>
              </div>
              <span className="pipeline-arrow">→</span>
              <div className="pipeline-node">
                <span className="flow-step">03</span>
                <p className="pipeline-title">Email Notify</p>
                <p className="pipeline-copy">Get completion alert.</p>
              </div>
              <span className="pipeline-arrow">→</span>
              <div className="pipeline-node">
                <span className="flow-step">04</span>
                <p className="pipeline-title">Transcript Ready</p>
                <p className="pipeline-copy">Read or export instantly.</p>
              </div>
            </div>
            <p className="mt-6 text-xs text-slate-500">
              Built for product teams, researchers, and operators who need transcription that is dependable.
            </p>
          </section>
        </main>
      </div>
    </>
  );
}
