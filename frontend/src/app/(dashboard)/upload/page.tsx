"use client";
import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload as UploadIcon, FileText, CheckCircle2, Loader2, Sparkles,
  DollarSign, Users, ShieldCheck, Code2, Package, Megaphone, Briefcase,
  Scale, Lock, Boxes, Tag,
} from "lucide-react";
import { useUploadDocument, useRecentUploads } from "@/lib/hooks/use-ingestion";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { formatRelativeTime } from "@/lib/utils/format";
import { toast } from "sonner";
import type { UploadResult } from "@/lib/api/ingestion";

const EASE = [0.16, 1, 0.3, 1] as const;

const ACCEPTED_EXTENSIONS = [".txt", ".md", ".csv", ".pdf", ".docx", ".xlsx"];

const DOMAIN_META: Record<string, { icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>; color: string }> = {
  finance: { icon: DollarSign, color: "#4FD1C5" },
  hr: { icon: Users, color: "#F472B6" },
  policy: { icon: ShieldCheck, color: "#E8B84B" },
  engineering: { icon: Code2, color: "#A78BFA" },
  product: { icon: Package, color: "#38BDF8" },
  sales: { icon: Briefcase, color: "#F5A623" },
  operations: { icon: Boxes, color: "#3FCF8E" },
  legal: { icon: Scale, color: "#F45B5B" },
  marketing: { icon: Megaphone, color: "#EC4899" },
  security: { icon: Lock, color: "#F45B5B" },
  other: { icon: Tag, color: "#A69C8C" },
};

function domainMeta(domain: string) {
  return DOMAIN_META[domain] ?? DOMAIN_META.other;
}

function ResultCard({ result }: { result: UploadResult }) {
  const meta = domainMeta(result.domain);
  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: EASE }}
      className="card-surface relative overflow-hidden border-l-2 p-5"
      style={{ borderLeftColor: meta.color }}
    >
      <div className="flex items-start gap-3">
        <span
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${meta.color}1F` }}
        >
          <CheckCircle2 className="h-4.5 w-4.5" style={{ color: meta.color }} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-aion-ink">{result.title}</p>
            <span
              className="rounded-full px-2 py-0.5 text-2xs font-medium uppercase tracking-wide"
              style={{ backgroundColor: `${meta.color}1F`, color: meta.color }}
            >
              {result.domain}
            </span>
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-aion-ink-muted">{result.plain_summary}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {result.tags.map((t) => (
              <span key={t} className="rounded-full border border-aion-border bg-aion-surface2 px-2 py-0.5 text-2xs text-aion-ink-faint">
                {t}
              </span>
            ))}
          </div>
          <p className="mt-3 text-2xs text-aion-ink-faint">
            {result.word_count.toLocaleString()} words &middot; relevance {Math.round(result.relevance_score * 100)}%
            &middot; now feeding your Intelligence Index, Disease Scan, and Org MRI
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export default function UploadPage() {
  const [dragOver, setDragOver] = useState(false);
  const [justUploaded, setJustUploaded] = useState<UploadResult[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadDocument();
  const { data: recent, isLoading: recentLoading } = useRecentUploads();

  const doUpload = useCallback(
    (files: FileList | File[]) => {
      const list = Array.from(files);
      for (const file of list) {
        upload.mutate(file, {
          onSuccess: (result) => {
            setJustUploaded((prev) => [result, ...prev]);
            toast.success(`Read "${result.title}" — now factored into your live analysis`);
          },
          onError: (err: unknown) => {
            const message =
              (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
              "Couldn't process that file. Please try again.";
            toast.error(message);
          },
        });
      }
    },
    [upload],
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.length) doUpload(e.dataTransfer.files);
  };

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <h1 className="page-title flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-white shadow-glow-violet">
            <UploadIcon className="h-4 w-4" />
          </span>
          Upload Organizational Data
        </h1>
        <p className="page-subtitle mt-1">
          Upload any real document — finance policies, HR records, salary bands, engineering docs, meeting
          notes, anything. AION reads it and immediately factors it into your Intelligence Index, Disease Scan,
          Decay Engine, and Org MRI.
        </p>
      </motion.div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-colors duration-200",
          dragOver
            ? "border-aion-accent bg-aion-accent-tint"
            : "border-aion-border bg-aion-surface/60 hover:border-aion-accent/40 hover:bg-aion-surface",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(",")}
          className="hidden"
          onChange={(e) => e.target.files && doUpload(e.target.files)}
        />
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient shadow-glow-accent">
          {upload.isPending ? (
            <Loader2 className="h-6 w-6 animate-spin text-white" />
          ) : (
            <UploadIcon className="h-6 w-6 text-white" />
          )}
        </span>
        <div>
          <p className="text-sm font-semibold text-aion-ink">
            {upload.isPending ? "Axon is reading your document..." : "Drop files here, or click to browse"}
          </p>
          <p className="mt-1 text-xs text-aion-ink-faint">
            Supports {ACCEPTED_EXTENSIONS.join(", ")} &middot; up to 8MB each
          </p>
        </div>
      </div>

      <AnimatePresence>
        {justUploaded.length > 0 && (
          <div className="mt-6 space-y-3">
            <p className="flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-widest text-aion-accent">
              <Sparkles className="h-3.5 w-3.5" />
              Just analyzed
            </p>
            {justUploaded.map((r) => (
              <ResultCard key={r.knowledge_id} result={r} />
            ))}
          </div>
        )}
      </AnimatePresence>

      <div className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-aion-ink">Previously uploaded</h2>
        <Card>
          <CardContent className="p-0">
            {recentLoading ? (
              <div className="space-y-3 p-5">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : !recent || recent.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-10 text-center">
                <FileText className="h-8 w-8 text-aion-ink-faint" />
                <p className="text-sm text-aion-ink-muted">No documents uploaded yet</p>
                <p className="max-w-xs text-xs text-aion-ink-faint">
                  Upload your first document above — it&apos;s what powers every other page in this dashboard.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-aion-border">
                {recent.map((item) => {
                  const meta = domainMeta(item.domain ?? "other");
                  const Icon = meta.icon;
                  return (
                    <div key={item.knowledge_id} className="flex items-start gap-3 px-5 py-3.5">
                      <span
                        className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
                        style={{ backgroundColor: `${meta.color}1F` }}
                      >
                        <Icon className="h-4 w-4" style={{ color: meta.color }} />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-aion-ink">{item.title}</p>
                        {item.plain_summary && (
                          <p className="mt-0.5 line-clamp-1 text-xs text-aion-ink-muted">{item.plain_summary}</p>
                        )}
                      </div>
                      <span className="shrink-0 text-2xs text-aion-ink-faint">
                        {item.created_at ? formatRelativeTime(item.created_at) : ""}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
