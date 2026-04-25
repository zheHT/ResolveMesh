import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  CheckCircle2,
  CreditCard,
  Mail,
  MapPin,
  Sparkles,
  XCircle,
  FileSearch,
  Eye,
  Download,
  X,
} from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { AuditFeed } from "@/components/AuditFeed";
import { ConfidenceGauge } from "@/components/ConfidenceGauge";
import { PrivacyShield } from "@/components/PrivacyShield";
import { StatusBadge, RiskBadge } from "@/components/StatusBadge";
import { getDispute, maskEmail, maskPII, type Dispute } from "@/lib/disputes";
import { generateStaffSummary } from "@/lib/staffSummary";
import jsPDF from "jspdf";

export const Route = createFileRoute("/disputes/$id")({
  loader: ({ params }) => {
    const dispute = getDispute(params.id);
    if (!dispute) throw notFound();
    return { dispute };
  },
  component: DossierPage,
  notFoundComponent: () => (
    <AppShell>
      <div className="p-12 text-center text-muted-foreground">
        Case not found.{" "}
        <Link to="/" className="text-mint underline">
          Return to inbox
        </Link>
      </div>
    </AppShell>
  ),
  errorComponent: ({ error }) => (
    <AppShell>
      <div className="p-12 text-center text-muted-foreground">
        Failed to load case: {error.message}
      </div>
    </AppShell>
  ),
});

function DossierPage() {
  const { dispute } = Route.useLoaderData();
  const [masked, setMasked] = useState(true);
  const [verdict, setVerdict] = useState<"pending" | "sent" | "rejected">("pending");
  const [reportOpen, setReportOpen] = useState(false);
  const [staffTldr, setStaffTldr] = useState<string>("");

  const customer = maskPII(dispute.customer, masked);
  const email = maskEmail(dispute.customerEmail, masked);
  const card = masked ? "•••• •••• •••• ••••" : `•••• •••• •••• ${dispute.cardLast4}`;

  useEffect(() => {
    let cancelled = false;
    const caseText = [
      `Case ${dispute.caseId}`,
      `Channel: ${dispute.channel}`,
      `Merchant: ${dispute.merchant}`,
      `Amount: ${dispute.amount} ${dispute.currency}`,
      `Reason: ${dispute.reason}`,
      `Mesh synthesis: ${dispute.agentSummary}`,
    ].join("\n");

    generateStaffSummary(caseText)
      .then((tldr) => {
        if (!cancelled) setStaffTldr(tldr);
      })
      .catch(() => {
        if (!cancelled) setStaffTldr("");
      });

    return () => {
      cancelled = true;
    };
  }, [dispute]);

  return (
    <AppShell>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="px-4 md:px-8 py-6 max-w-7xl mx-auto"
      >
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="h-8 w-8 grid place-items-center rounded-lg border border-border/60 hover:bg-accent/50"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="font-mono">{dispute.caseId}</span>
                <span>·</span>
                <span>{dispute.channel}</span>
              </div>
              <h1 className="text-2xl font-semibold tracking-tight">Investigation Dossier</h1>
            </div>
          </div>
          <PrivacyShield masked={masked} onToggle={() => setMasked((m) => !m)} />
        </div>

        <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Left col: case details */}
          <div className="lg:col-span-2 space-y-5">
            <div className="glass rounded-2xl p-6">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-4">
                  <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-electric/40 to-mint/40 border border-border/60 grid place-items-center text-base font-mono">
                    {dispute.customer
                      .split(" ")
                      .map((n: string) => n[0])
                      .join("")}
                  </div>
                  <div>
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={`${customer}-${masked}`}
                        initial={{ opacity: 0, filter: "blur(4px)" }}
                        animate={{ opacity: 1, filter: "blur(0px)" }}
                        exit={{ opacity: 0, filter: "blur(4px)" }}
                        transition={{ duration: 0.2 }}
                        className="text-lg font-semibold tracking-tight font-mono"
                      >
                        {customer}
                      </motion.div>
                    </AnimatePresence>
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5 font-mono">
                      <Mail className="h-3 w-3" />
                      {email}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={dispute.status} pulse />
                  <RiskBadge risk={dispute.risk} />
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-5 border-t border-border/60">
                <Field label="Amount">
                  <span className="text-lg font-semibold tabular-nums">
                    {new Intl.NumberFormat("en-US", {
                      style: "currency",
                      currency: dispute.currency,
                    }).format(dispute.amount)}
                  </span>
                </Field>
                <Field label="Card">
                  <span className="text-sm font-mono inline-flex items-center gap-1.5">
                    <CreditCard className="h-3.5 w-3.5 text-muted-foreground" /> {card}
                  </span>
                </Field>
                <Field label="Merchant">
                  <span className="text-sm">{dispute.merchant}</span>
                </Field>
                <Field label="Origin">
                  <span className="text-sm inline-flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                    {masked ? "•••••, ••" : "Brooklyn, NY"}
                  </span>
                </Field>
              </div>
            </div>

            <div className="glass rounded-2xl p-6">
              <div className="flex items-center gap-2 text-xs text-muted-foreground uppercase tracking-[0.18em]">
                <FileSearch className="h-3.5 w-3.5" /> Mesh Synthesis
              </div>
              {staffTldr ? (
                <div className="mt-3 rounded-xl border border-border/60 bg-background/30 p-3">
                  <div className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                    Staff TL;DR (≤ 30 words)
                  </div>
                  <div className="mt-1 text-sm text-foreground/90">{staffTldr}</div>
                </div>
              ) : null}
              <p className="mt-3 text-[15px] leading-relaxed text-foreground/90">
                {dispute.agentSummary}
              </p>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                {[
                  { k: "Reason code", v: dispute.reason },
                  { k: "Recommendation", v: "Issue provisional credit" },
                  { k: "Citations", v: "4 sources · Reg E, ToS §7.2" },
                ].map((x) => (
                  <div key={x.k} className="rounded-xl border border-border/60 p-3 bg-background/30">
                    <div className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                      {x.k}
                    </div>
                    <div className="mt-1 text-sm">{x.v}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Verdict panel */}
            <div className="glass rounded-2xl p-6 relative overflow-hidden">
              <div
                className="absolute inset-0 pointer-events-none opacity-60"
                style={{
                  background:
                    "radial-gradient(ellipse 60% 80% at 90% 50%, oklch(0.86 0.19 165 / 0.18), transparent 70%)",
                }}
              />
              <div className="relative flex items-center justify-between gap-6 flex-wrap">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                    Verdict Action
                  </div>
                  <div className="mt-1 text-lg font-semibold tracking-tight">
                    Approve provisional credit & notify cardholder
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Mesh has prepared a Reg E-compliant response. Verify before sending.
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => setReportOpen(true)}
                    className="h-10 px-4 rounded-xl border border-border/60 text-sm hover:bg-accent/50 inline-flex items-center gap-2"
                  >
                    <Eye className="h-4 w-4" /> View Report
                  </button>
                  <button
                    onClick={() => downloadVerdictPDF(dispute)}
                    className="h-10 px-4 rounded-xl border border-border/60 text-sm hover:bg-accent/50 inline-flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" /> Download PDF
                  </button>
                  <button
                    onClick={() => setVerdict("rejected")}
                    disabled={verdict !== "pending"}
                    className="h-10 px-4 rounded-xl border border-border/60 text-sm hover:bg-accent/50 disabled:opacity-40 inline-flex items-center gap-2"
                  >
                    <XCircle className="h-4 w-4" /> Reject
                  </button>
                  <motion.button
                    whileTap={{ scale: 0.97 }}
                    onClick={() => setVerdict("sent")}
                    disabled={verdict !== "pending"}
                    className="relative h-10 px-5 rounded-xl bg-mint text-mint-foreground text-sm font-semibold inline-flex items-center gap-2 transition-all hover:glow-mint disabled:opacity-70"
                  >
                    <AnimatePresence mode="wait">
                      {verdict === "sent" ? (
                        <motion.span
                          key="sent"
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className="inline-flex items-center gap-2"
                        >
                          <CheckCircle2 className="h-4 w-4" /> Sent
                        </motion.span>
                      ) : (
                        <motion.span
                          key="idle"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="inline-flex items-center gap-2"
                        >
                          <Sparkles className="h-4 w-4" /> Verify & Send
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </motion.button>
                </div>
              </div>

              <AnimatePresence>
                {verdict === "sent" && (
                  <motion.div
                    initial={{ opacity: 0, y: 8, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: "auto" }}
                    exit={{ opacity: 0 }}
                    className="relative mt-4 rounded-xl border border-mint/30 bg-mint/10 px-4 py-3 text-xs text-mint inline-flex items-center gap-2 w-full"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Provisional credit posted · cardholder notified · audit hash{" "}
                    <span className="font-mono">0x8a21…b04f</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Right col: gauge + audit feed */}
          <div className="space-y-5">
            <div className="glass rounded-2xl p-6 flex flex-col items-center">
              <ConfidenceGauge value={dispute.confidence} />
              <div className="mt-4 grid grid-cols-3 gap-2 w-full text-center">
                {[
                  { k: "Forensics", v: "94%" },
                  { k: "Policy", v: "100%" },
                  { k: "Risk", v: "71%" },
                ].map((x) => (
                  <div
                    key={x.k}
                    className="rounded-lg border border-border/60 bg-background/30 p-2"
                  >
                    <div className="text-[9px] uppercase tracking-[0.14em] text-muted-foreground">
                      {x.k}
                    </div>
                    <div className="text-sm font-mono text-mint">{x.v}</div>
                  </div>
                ))}
              </div>
            </div>

            <AuditFeed />
          </div>
        </div>
      </motion.div>
      <ReportModal open={reportOpen} onClose={() => setReportOpen(false)} dispute={dispute} />
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-1">{children}</div>
    </div>
  );
}

function ReportModal({
  open,
  onClose,
  dispute,
}: {
  open: boolean;
  onClose: () => void;
  dispute: Dispute;
}) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 grid place-items-center p-4 bg-background/70 backdrop-blur-md"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.98 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto glass rounded-2xl border border-border/60"
          >
            <div className="sticky top-0 flex items-center justify-between px-6 py-4 border-b border-border/60 bg-background/80 backdrop-blur-xl">
              <div>
                <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                  Verdict Report
                </div>
                <div className="text-base font-semibold font-mono">{dispute.caseId}</div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => downloadVerdictPDF(dispute)}
                  className="h-9 px-3 rounded-lg border border-border/60 text-xs hover:bg-accent/50 inline-flex items-center gap-1.5"
                >
                  <Download className="h-3.5 w-3.5" /> PDF
                </button>
                <button
                  onClick={onClose}
                  className="h-9 w-9 grid place-items-center rounded-lg border border-border/60 hover:bg-accent/50"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-5 text-sm">
              <section>
                <h3 className="text-xs uppercase tracking-[0.16em] text-muted-foreground mb-2">
                  Case Summary
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <ReportField k="Customer" v={dispute.customer} />
                  <ReportField k="Email" v={dispute.customerEmail} />
                  <ReportField k="Card" v={`•••• ${dispute.cardLast4}`} />
                  <ReportField k="Channel" v={dispute.channel} />
                  <ReportField k="Merchant" v={dispute.merchant} />
                  <ReportField
                    k="Amount"
                    v={new Intl.NumberFormat("en-US", {
                      style: "currency",
                      currency: dispute.currency,
                    }).format(dispute.amount)}
                  />
                  <ReportField k="Status" v={dispute.status} />
                  <ReportField k="Risk Level" v={dispute.risk} />
                </div>
              </section>

              <section>
                <h3 className="text-xs uppercase tracking-[0.16em] text-muted-foreground mb-2">
                  Reason Code
                </h3>
                <p className="text-foreground/90">{dispute.reason}</p>
              </section>

              <section>
                <h3 className="text-xs uppercase tracking-[0.16em] text-muted-foreground mb-2">
                  Mesh Synthesis
                </h3>
                <p className="text-foreground/90 leading-relaxed">{dispute.agentSummary}</p>
              </section>

              <section>
                <h3 className="text-xs uppercase tracking-[0.16em] text-muted-foreground mb-2">
                  AI Verdict
                </h3>
                <div className="rounded-xl border border-mint/25 bg-mint/5 p-4">
                  <div className="text-mint font-semibold">
                    Approve provisional credit & notify cardholder
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Confidence: {dispute.confidence}% · Reg E compliant · 4 citations
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-xs uppercase tracking-[0.16em] text-muted-foreground mb-2">
                  Audit Trail
                </h3>
                <div className="font-mono text-xs text-muted-foreground space-y-1">
                  <div>↳ Forensics scan complete · 94% match</div>
                  <div>↳ Policy check passed · Reg E §1005.11</div>
                  <div>↳ Risk model evaluated · 71% confidence</div>
                  <div>↳ Verdict assembled · hash 0x8a21…b04f</div>
                </div>
              </section>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function ReportField({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-background/30 p-3">
      <div className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{k}</div>
      <div className="mt-0.5 text-sm font-mono text-foreground/90">{v}</div>
    </div>
  );
}

function downloadVerdictPDF(dispute: Dispute) {
  const doc = new jsPDF({ unit: "pt", format: "letter" });
  const pageW = doc.internal.pageSize.getWidth();
  let y = 56;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.text("ResolveMesh Verdict Report", 56, y);
  y += 22;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(110);
  doc.text(`Case ${dispute.caseId} · Generated ${new Date().toLocaleString()}`, 56, y);
  y += 24;
  doc.setDrawColor(220);
  doc.line(56, y, pageW - 56, y);
  y += 24;

  const section = (title: string) => {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(40);
    doc.text(title.toUpperCase(), 56, y);
    y += 16;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.setTextColor(60);
  };

  const row = (k: string, v: string) => {
    doc.setTextColor(120);
    doc.text(k, 56, y);
    doc.setTextColor(30);
    doc.text(v, 200, y);
    y += 16;
  };

  section("Case Summary");
  row("Customer", dispute.customer);
  row("Email", dispute.customerEmail);
  row("Card", `•••• ${dispute.cardLast4}`);
  row("Channel", dispute.channel);
  row("Merchant", dispute.merchant);
  row(
    "Amount",
    new Intl.NumberFormat("en-US", { style: "currency", currency: dispute.currency }).format(
      dispute.amount,
    ),
  );
  row("Status", dispute.status);
  row("Risk Level", dispute.risk);
  y += 8;

  section("Reason Code");
  doc.text(doc.splitTextToSize(dispute.reason, pageW - 112), 56, y);
  y += 24;

  section("Mesh Synthesis");
  const summary = doc.splitTextToSize(dispute.agentSummary, pageW - 112);
  doc.text(summary, 56, y);
  y += summary.length * 13 + 12;

  section("AI Verdict");
  doc.setFont("helvetica", "bold");
  doc.setTextColor(20);
  doc.text("Approve provisional credit & notify cardholder", 56, y);
  y += 14;
  doc.setFont("helvetica", "normal");
  doc.setTextColor(110);
  doc.text(`Confidence: ${dispute.confidence}% · Reg E compliant · 4 citations`, 56, y);
  y += 20;

  section("Audit Trail");
  [
    "Forensics scan complete · 94% match",
    "Policy check passed · Reg E §1005.11",
    "Risk model evaluated · 71% confidence",
    "Verdict assembled · hash 0x8a21…b04f",
  ].forEach((line) => {
    doc.text(`> ${line}`, 56, y);
    y += 14;
  });

  doc.save(`ResolveMesh_${dispute.caseId}.pdf`);
}
