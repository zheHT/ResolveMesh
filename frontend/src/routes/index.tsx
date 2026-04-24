import { createFileRoute, Link } from "@tanstack/react-router";
import { motion, useMotionValue, useSpring, useScroll, useTransform } from "framer-motion";
import { useEffect, useRef } from "react";
import {
  ShieldCheck,
  BrainCircuit,
  FileCheck2,
  ArrowRight,
  FileText,
  Search,
  Scale,
  MessageSquareWarning,
  Gavel,
  Sparkles,
} from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ResolveMesh — Dispute Resolution at the Speed of Light" },
      {
        name: "description",
        content:
          "ResolveMesh is the agentic AI command center for fintech dispute resolution: zero-trust security, audit-ready reports, and verifiable verdicts.",
      },
      { property: "og:title", content: "ResolveMesh — Dispute Resolution at the Speed of Light" },
      {
        property: "og:description",
        content:
          "Agentic AI command center for fintech disputes — multi-agent reasoning, zero-trust security, and audit-ready verdicts.",
      },
    ],
  }),
  component: LandingPage,
});

/* ---------- Reusable scroll-fade wrapper ---------- */
function FadeIn({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ---------- Mouse-reactive grid background ---------- */
function InteractiveGrid() {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 60, damping: 20, mass: 0.6 });
  const sy = useSpring(y, { stiffness: 60, damping: 20, mass: 0.6 });

  // Translate grid by a few px based on cursor
  const tx = useTransform(sx, (v) => `${v * 18}px`);
  const ty = useTransform(sy, (v) => `${v * 18}px`);

  // Move radial glow inversely for parallax depth
  const gx = useTransform(sx, (v) => `${50 + v * 12}%`);
  const gy = useTransform(sy, (v) => `${30 + v * 10}%`);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const nx = (e.clientX / window.innerWidth) * 2 - 1;
      const ny = (e.clientY / window.innerHeight) * 2 - 1;
      x.set(nx);
      y.set(ny);
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [x, y]);

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {/* Grid */}
      <motion.div
        className="absolute -inset-[10%]"
        style={{
          x: tx,
          y: ty,
          backgroundImage:
            "linear-gradient(to right, oklch(1 0 0 / 0.05) 1px, transparent 1px), linear-gradient(to bottom, oklch(1 0 0 / 0.05) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage:
            "radial-gradient(ellipse 70% 60% at 50% 30%, #000 30%, transparent 80%)",
        }}
      />
      {/* Electric blue glow */}
      <motion.div
        className="absolute h-[60vh] w-[60vw] rounded-full blur-[120px]"
        style={{
          left: gx,
          top: gy,
          translateX: "-50%",
          translateY: "-50%",
          background:
            "radial-gradient(circle, oklch(0.72 0.18 245 / 0.35), transparent 70%)",
        }}
      />
      {/* Deep purple glow */}
      <motion.div
        className="absolute h-[50vh] w-[50vw] rounded-full blur-[140px]"
        style={{
          right: useTransform(sx, (v) => `${10 - v * 8}%`),
          bottom: useTransform(sy, (v) => `${5 - v * 6}%`),
          background:
            "radial-gradient(circle, oklch(0.45 0.22 295 / 0.38), transparent 70%)",
        }}
      />
    </div>
  );
}

/* ---------- Header ---------- */
function Header() {
  return (
    <header className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6">
      <Link to="/" className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg glass-strong glow-electric">
          <ShieldCheck className="h-4 w-4 text-electric" />
        </div>
        <span className="text-base font-semibold tracking-tight">
          Resolve<span className="text-electric">Mesh</span>
        </span>
      </Link>
      <nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
        <a href="#features" className="hover:text-foreground transition-colors">
          Features
        </a>
        <a href="#agents" className="hover:text-foreground transition-colors">
          Agents
        </a>
        <a href="#trust" className="hover:text-foreground transition-colors">
          Trust
        </a>
      </nav>
      <Link
        to="/login"
        className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border/70 bg-card/50 px-4 text-sm font-medium transition-all hover:border-electric/50 hover:text-electric"
      >
        Sign In
      </Link>
    </header>
  );
}

/* ---------- Hero ---------- */
function Hero() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const heroOpacity = useTransform(scrollYProgress, [0, 1], [1, 0.3]);

  return (
    <section ref={ref} className="relative mx-auto w-full max-w-7xl px-6 pt-16 pb-28 md:pt-24 md:pb-36">
      <motion.div style={{ y: heroY, opacity: heroOpacity }} className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-border/70 bg-card/40 px-3.5 py-1.5 text-xs text-muted-foreground backdrop-blur"
        >
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mint opacity-75" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-mint" />
          </span>
          <span className="font-mono uppercase tracking-wider">
            Live · 12,418 disputes resolved this hour
          </span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.05 }}
          className="mx-auto max-w-5xl text-5xl font-semibold leading-[1.05] tracking-tight md:text-7xl"
        >
          Dispute Resolution at the{" "}
          <span className="gradient-text">Speed of Light</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.15 }}
          className="mx-auto mt-6 max-w-2xl text-base text-muted-foreground md:text-lg"
        >
          The agentic operating system for fintech disputes. Multi-agent reasoning,
          cryptographically verifiable verdicts, and zero-trust security — in milliseconds, not days.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.25 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-3"
        >
          <Link
            to="/login"
            className="group inline-flex h-12 items-center gap-2 rounded-lg bg-mint px-6 text-sm font-semibold text-mint-foreground shadow-[0_0_40px_-6px_oklch(0.86_0.19_165/0.6)] transition-all hover:shadow-[0_0_56px_-4px_oklch(0.86_0.19_165/0.85)]"
          >
            Launch Dashboard
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <a
            href="#features"
            className="inline-flex h-12 items-center gap-2 rounded-lg border border-border/70 bg-card/40 px-6 text-sm font-medium backdrop-blur transition-all hover:border-electric/60 hover:text-electric"
          >
            <FileText className="h-4 w-4" />
            View Technical Brief
          </a>
        </motion.div>

        {/* KPI strip */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.4 }}
          className="mx-auto mt-16 grid max-w-3xl grid-cols-3 gap-px overflow-hidden rounded-2xl border border-border/60 bg-border/40"
        >
          {[
            { v: "94ms", l: "Median verdict latency" },
            { v: "99.97%", l: "Audit pass rate" },
            { v: "$1.2B", l: "Disputed volume / mo" },
          ].map((s) => (
            <div key={s.l} className="bg-background/60 px-6 py-5 text-center backdrop-blur">
              <div className="font-mono text-2xl font-semibold tracking-tight text-foreground">
                {s.v}
              </div>
              <div className="mt-1 text-[11px] uppercase tracking-wider text-muted-foreground">
                {s.l}
              </div>
            </div>
          ))}
        </motion.div>
      </motion.div>
    </section>
  );
}

/* ---------- Bento ---------- */
const BENTO = [
  {
    title: "Agentic Reasoning",
    icon: BrainCircuit,
    desc: "A swarm of specialized agents debate evidence, score confidence, and converge on a verdict — with full chain-of-thought.",
    accent: "electric",
  },
  {
    title: "Zero-Trust Security",
    icon: ShieldCheck,
    desc: "PII shielded at ingest. Every action signed, every payload encrypted. SOC 2, PCI-DSS, and GDPR by default.",
    accent: "mint",
  },
  {
    title: "Audit-Ready Reports",
    icon: FileCheck2,
    desc: "Verdicts ship with cryptographic receipts, evidence trails, and regulator-grade narrative — exportable in one click.",
    accent: "purple",
  },
] as const;

function Bento() {
  return (
    <section id="features" className="relative mx-auto w-full max-w-7xl px-6 py-24">
      <FadeIn className="mx-auto mb-14 max-w-2xl text-center">
        <p className="mb-3 font-mono text-xs uppercase tracking-[0.22em] text-electric">
          The Platform
        </p>
        <h2 className="text-3xl font-semibold tracking-tight md:text-5xl">
          Built for the disputes that matter most
        </h2>
        <p className="mt-4 text-muted-foreground">
          Three pillars. Zero compromises. Designed alongside risk leaders at the
          world's largest issuers.
        </p>
      </FadeIn>

      <div className="grid gap-5 md:grid-cols-3">
        {BENTO.map((b, i) => (
          <FadeIn key={b.title} delay={i * 0.08}>
            <div className="group relative h-full overflow-hidden rounded-2xl border border-border/70 bg-card/40 p-7 backdrop-blur transition-all hover:border-electric/40 hover:bg-card/60">
              {/* Accent glow */}
              <div
                aria-hidden
                className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full blur-3xl opacity-40 transition-opacity group-hover:opacity-70"
                style={{
                  background:
                    b.accent === "electric"
                      ? "oklch(0.72 0.18 245 / 0.5)"
                      : b.accent === "mint"
                        ? "oklch(0.86 0.19 165 / 0.4)"
                        : "oklch(0.55 0.22 295 / 0.55)",
                }}
              />
              <div className="relative">
                <div className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-xl border border-border/70 bg-background/60">
                  <b.icon
                    className={
                      b.accent === "electric"
                        ? "h-5 w-5 text-electric"
                        : b.accent === "mint"
                          ? "h-5 w-5 text-mint"
                          : "h-5 w-5"
                    }
                    style={
                      b.accent === "purple" ? { color: "oklch(0.72 0.2 295)" } : undefined
                    }
                  />
                </div>
                <h3 className="text-xl font-semibold tracking-tight">{b.title}</h3>
                <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">
                  {b.desc}
                </p>
              </div>
            </div>
          </FadeIn>
        ))}
      </div>
    </section>
  );
}

/* ---------- Agents ---------- */
const AGENTS = [
  {
    name: "Investigator",
    icon: Search,
    desc: "Mines transaction graphs and merchant reputation signals to surface hidden patterns of fraud.",
  },
  {
    name: "Advocate",
    icon: MessageSquareWarning,
    desc: "Reconstructs the cardholder's narrative from messages, receipts, and behavioral history.",
  },
  {
    name: "Arbiter",
    icon: Scale,
    desc: "Weighs competing evidence under network rules and issues a calibrated, explainable verdict.",
  },
  {
    name: "Auditor",
    icon: Gavel,
    desc: "Signs every decision with a cryptographic receipt and produces a regulator-ready dossier.",
  },
];

function Agents() {
  return (
    <section id="agents" className="relative mx-auto w-full max-w-7xl px-6 py-24">
      <FadeIn className="mx-auto mb-14 max-w-2xl text-center">
        <p className="mb-3 font-mono text-xs uppercase tracking-[0.22em] text-mint">
          <Sparkles className="-mt-0.5 mr-1 inline h-3.5 w-3.5" />
          The Mesh
        </p>
        <h2 className="text-3xl font-semibold tracking-tight md:text-5xl">
          Meet the Agents
        </h2>
        <p className="mt-4 text-muted-foreground">
          Four autonomous specialists, one consensus verdict. Each agent has a sworn role,
          a memory, and a verifiable signature.
        </p>
      </FadeIn>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {AGENTS.map((a, i) => (
          <FadeIn key={a.name} delay={i * 0.07}>
            <div className="glass relative h-full overflow-hidden rounded-2xl p-6 transition-all hover:glow-electric">
              <div
                aria-hidden
                className="pointer-events-none absolute inset-0 opacity-0 transition-opacity hover:opacity-100"
                style={{
                  background:
                    "linear-gradient(135deg, oklch(0.72 0.18 245 / 0.08), transparent 60%)",
                }}
              />
              <div className="relative">
                <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-lg bg-electric/10 ring-1 ring-electric/30">
                  <a.icon className="h-5 w-5 text-electric" />
                </div>
                <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                  Agent · 0{i + 1}
                </div>
                <h3 className="text-lg font-semibold tracking-tight">{a.name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {a.desc}
                </p>
              </div>
            </div>
          </FadeIn>
        ))}
      </div>
    </section>
  );
}

/* ---------- Trust strip + CTA ---------- */
function ClosingCTA() {
  return (
    <section id="trust" className="relative mx-auto w-full max-w-7xl px-6 pb-28 pt-12">
      <FadeIn>
        <div className="relative overflow-hidden rounded-3xl border border-border/70 bg-card/40 p-10 text-center backdrop-blur md:p-16">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(ellipse 60% 80% at 50% 100%, oklch(0.72 0.18 245 / 0.25), transparent 70%), radial-gradient(ellipse 40% 60% at 50% 0%, oklch(0.55 0.22 295 / 0.22), transparent 70%)",
            }}
          />
          <div className="relative">
            <h2 className="mx-auto max-w-3xl text-3xl font-semibold tracking-tight md:text-5xl">
              Ship verdicts your auditors will <span className="gradient-text">love</span>.
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
              Trusted by leading neobanks and processors. Deploy in your VPC in under an hour.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/login"
                className="group inline-flex h-12 items-center gap-2 rounded-lg bg-mint px-6 text-sm font-semibold text-mint-foreground shadow-[0_0_40px_-6px_oklch(0.86_0.19_165/0.6)] transition-all hover:shadow-[0_0_56px_-4px_oklch(0.86_0.19_165/0.9)]"
              >
                Launch Dashboard
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
              <Link
                to="/login"
                className="inline-flex h-12 items-center gap-2 rounded-lg border border-border/70 bg-background/60 px-6 text-sm font-medium backdrop-blur transition-all hover:border-electric/60 hover:text-electric"
              >
                Request Access
              </Link>
            </div>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              <span>SOC 2 Type II</span>
              <span className="opacity-30">•</span>
              <span>PCI-DSS L1</span>
              <span className="opacity-30">•</span>
              <span>GDPR</span>
              <span className="opacity-30">•</span>
              <span>ISO 27001</span>
            </div>
          </div>
        </div>
      </FadeIn>
    </section>
  );
}

/* ---------- Footer ---------- */
function Footer() {
  return (
    <footer className="relative border-t border-border/60">
      <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-3 px-6 py-8 text-xs text-muted-foreground md:flex-row">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-3.5 w-3.5 text-electric" />
          <span>© {new Date().getFullYear()} ResolveMesh, Inc.</span>
        </div>
        <div className="font-mono uppercase tracking-wider">
          v4.2.1 · All systems nominal
        </div>
      </div>
    </footer>
  );
}

/* ---------- Page ---------- */
function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "#050505" }}>
      <InteractiveGrid />
      <Header />
      <Hero />
      <Bento />
      <Agents />
      <ClosingCTA />
      <Footer />
    </div>
  );
}
