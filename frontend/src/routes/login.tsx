import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { ShieldCheck, Fingerprint, KeyRound, Loader2, ArrowRight } from "lucide-react";
import { setAuthUser } from "@/lib/auth";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Secure Access — ResolveMesh" },
      {
        name: "description",
        content:
          "Authenticate into the ResolveMesh dispute resolution OS. Staff-only secure gateway.",
      },
      { property: "og:title", content: "Secure Access — ResolveMesh" },
      {
        property: "og:description",
        content: "Staff-only secure gateway to the ResolveMesh dispute resolution OS.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [staffId, setStaffId] = useState("");
  const [accessKey, setAccessKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (loading) return;

    setError(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: staffId,
          password: accessKey,
        }),
      });

      const payload = (await response.json()) as {
        status?: "login" | "signup";
        message?: string;
        user?: { id: string; email: string };
        detail?: string;
      };

      if (!response.ok) {
        throw new Error(payload.detail || payload.message || "Authentication failed.");
      }

      if (payload.user) {
        setAuthUser(payload.user);
      }

      navigate({ to: "/dashboard", replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center px-4 py-12">
      {/* Ambient corner glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-0"
        style={{
          background:
            "radial-gradient(ellipse 50% 40% at 50% 30%, oklch(0.72 0.18 245 / 0.18), transparent 70%)",
        }}
      />

      <div className="relative z-10 w-full max-w-md">
        {/* Brand */}
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl glass-strong glow-electric">
            <ShieldCheck className="h-6 w-6 text-electric" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">
            <span className="gradient-text">ResolveMesh</span>
          </h1>
          <p className="mt-1 text-xs uppercase tracking-[0.22em] text-muted-foreground">
            Security Gateway
          </p>
        </div>

        {/* Card */}
        <div className="glass-strong rounded-2xl p-7 shadow-[var(--shadow-elegant)]">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Authenticate</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Verified staff access only.
              </p>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-md border border-electric/30 bg-electric/10 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-electric">
              <span className="h-1.5 w-1.5 rounded-full bg-electric" />
              Tier-3
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <SecureField
              id="staff-id"
              label="Email"
              icon={<Fingerprint className="h-4 w-4" />}
              value={staffId}
              onChange={setStaffId}
              placeholder="example@gmail.com"
              autoComplete="username"
              disabled={loading}
            />

            <SecureField
              id="access-key"
              label="Password"
              icon={<KeyRound className="h-4 w-4" />}
              value={accessKey}
              onChange={setAccessKey}
              placeholder="••••••••••••"
              type="password"
              autoComplete="current-password"
              disabled={loading}
            />

            {error && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="group relative flex h-11 w-full items-center justify-center gap-2 overflow-hidden rounded-lg bg-mint text-sm font-semibold text-mint-foreground transition-all hover:glow-mint disabled:cursor-not-allowed disabled:opacity-90"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="font-mono text-xs tracking-wide">
                    Authenticating with Ledger
                    <span className="caret" />
                  </span>
                </>
              ) : (
                <>
                  <span>Initiate Secure Session</span>
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 flex items-center gap-3 text-[11px] text-muted-foreground">
            <div className="h-px flex-1 bg-border" />
            <span className="font-mono uppercase tracking-wider">Hashed with bcrypt · TLS 1.3</span>
            <div className="h-px flex-1 bg-border" />
          </div>
        </div>

        {/* System status footer */}
        <div className="mt-6 flex items-center justify-between px-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-card/50 px-3 py-1.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mint opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-mint" />
            </span>
            <span className="font-mono uppercase tracking-wider text-foreground/80">
              System Status: Active
            </span>
          </span>
          <span className="font-mono text-[10px] uppercase tracking-wider">
            v4.2.1 · Mesh
          </span>
        </div>
      </div>
    </main>
  );
}

interface SecureFieldProps {
  id: string;
  label: string;
  icon: React.ReactNode;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  autoComplete?: string;
  disabled?: boolean;
}

function SecureField({
  id,
  label,
  icon,
  value,
  onChange,
  placeholder,
  type = "text",
  autoComplete,
  disabled,
}: SecureFieldProps) {
  const [focused, setFocused] = useState(false);

  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground"
      >
        {label}
      </label>
      <div
        className={`relative flex items-center rounded-lg border bg-background/40 transition-all duration-200 ${
          focused
            ? "border-electric ring-2 ring-electric/30 glow-electric"
            : "border-border hover:border-border/80"
        }`}
      >
        <span
          className={`pl-3 transition-colors ${focused ? "text-electric" : "text-muted-foreground"}`}
        >
          {icon}
        </span>
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          disabled={disabled}
          className="h-11 w-full bg-transparent px-3 font-mono text-sm tracking-wide outline-none placeholder:text-muted-foreground/50 disabled:cursor-not-allowed"
        />
      </div>
    </div>
  );
}
