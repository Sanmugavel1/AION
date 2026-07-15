"use client";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2, Check, ChevronRight, FileText, Plus, ShieldCheck, Trash2, Users,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import {
  useDepartments, useCreateDepartment, useBulkCreatePeople, useBulkCreatePolicies,
} from "@/lib/hooks/use-graph";

type Step = 0 | 1 | 2 | 3;

const STEPS = [
  { label: "Departments", icon: Building2 },
  { label: "People", icon: Users },
  { label: "Policies", icon: ShieldCheck },
  { label: "Review", icon: Check },
];

const selectClass =
  "h-9 w-full rounded-lg border border-aion-border bg-aion-surface px-3 text-sm text-aion-ink " +
  "focus:outline-none focus:border-aion-accent focus:ring-1 focus:ring-aion-accent/30";

function StepHeader({ step }: { step: Step }) {
  return (
    <div className="mb-8 flex items-center justify-center gap-2">
      {STEPS.map((s, i) => {
        const Icon = s.icon;
        const isActive = i === step;
        const isDone = i < step;
        return (
          <div key={s.label} className="flex items-center">
            <div
              className={cn(
                "flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold transition-colors duration-200",
                isActive && "border-aion-accent/40 bg-aion-accent-tint text-aion-accent",
                isDone && !isActive && "border-health-green-border bg-health-green-tint text-health-green",
                !isActive && !isDone && "border-aion-border bg-aion-surface text-aion-ink-muted",
              )}
            >
              {isDone && !isActive ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
              {s.label}
            </div>
            {i < STEPS.length - 1 && (
              <ChevronRight className="mx-1 h-4 w-4 text-aion-ink-faint" />
            )}
          </div>
        );
      })}
    </div>
  );
}

function DepartmentsStep({ onNext }: { onNext: () => void }) {
  const { data, isLoading } = useDepartments();
  const createDept = useCreateDepartment();
  const [drafts, setDrafts] = useState<string[]>([""]);

  const updateDraft = (i: number, value: string) =>
    setDrafts((d) => d.map((v, idx) => (idx === i ? value : v)));
  const addRow = () => setDrafts((d) => [...d, ""]);
  const removeRow = (i: number) => setDrafts((d) => d.filter((_, idx) => idx !== i));

  const submit = async () => {
    const names = drafts.map((d) => d.trim()).filter(Boolean);
    for (const name of names) {
      await createDept.mutateAsync(name);
    }
    setDrafts([""]);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-aion-accent" />
            Existing Departments
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-aion-ink-muted">Loading...</p>
          ) : data?.departments.length ? (
            <div className="flex flex-wrap gap-2">
              {data.departments.map((d) => (
                <Badge key={d.id} variant="secondary" className="px-3 py-1.5">
                  {d.name} <span className="ml-1.5 text-aion-ink-muted">· {d.headcount} people</span>
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-aion-ink-muted">No departments yet — add your first one below.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-4 w-4 text-aion-accent" />
            Add Departments
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {drafts.map((value, i) => (
            <div key={i} className="flex items-center gap-2">
              <Input
                value={value}
                onChange={(e) => updateDraft(i, e.target.value)}
                placeholder="e.g. Finance, Human Resources, Legal & Compliance"
              />
              {drafts.length > 1 && (
                <Button variant="ghost" size="icon" onClick={() => removeRow(i)} aria-label="Remove">
                  <Trash2 className="h-4 w-4 text-aion-ink-muted" />
                </Button>
              )}
            </div>
          ))}
          <div className="flex items-center justify-between pt-2">
            <Button variant="outline" size="sm" onClick={addRow}>
              <Plus className="h-3.5 w-3.5" /> Add another
            </Button>
            <Button
              onClick={submit}
              loading={createDept.isPending}
              disabled={!drafts.some((d) => d.trim())}
            >
              Save Departments
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button variant="outline" onClick={onNext}>
          Next: Add People <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

type PersonDraft = { name: string; email: string; role: string };

function PeopleStep({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { data } = useDepartments();
  const bulkCreate = useBulkCreatePeople();
  const [department, setDepartment] = useState("");
  const [rows, setRows] = useState<PersonDraft[]>([{ name: "", email: "", role: "" }]);

  const updateRow = (i: number, field: keyof PersonDraft, value: string) =>
    setRows((r) => r.map((row, idx) => (idx === i ? { ...row, [field]: value } : row)));
  const addRow = () => setRows((r) => [...r, { name: "", email: "", role: "" }]);
  const removeRow = (i: number) => setRows((r) => r.filter((_, idx) => idx !== i));

  const submit = async () => {
    const people = rows
      .filter((r) => r.name.trim() && r.email.trim())
      .map((r) => ({ name: r.name.trim(), email: r.email.trim(), role: r.role.trim() || undefined, department: department || undefined }));
    if (!people.length) return;
    await bulkCreate.mutateAsync(people);
    setRows([{ name: "", email: "", role: "" }]);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-4 w-4 text-aion-accent" />
            Add People
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-aion-ink-muted">Department</label>
            <select value={department} onChange={(e) => setDepartment(e.target.value)} className={selectClass}>
              <option value="">Unassigned</option>
              {data?.departments.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            {rows.map((row, i) => (
              <div key={i} className="grid grid-cols-[1fr_1fr_1fr_auto] gap-2">
                <Input placeholder="Full name" value={row.name} onChange={(e) => updateRow(i, "name", e.target.value)} />
                <Input placeholder="Email" type="email" value={row.email} onChange={(e) => updateRow(i, "email", e.target.value)} />
                <Input placeholder="Role / Title" value={row.role} onChange={(e) => updateRow(i, "role", e.target.value)} />
                {rows.length > 1 && (
                  <Button variant="ghost" size="icon" onClick={() => removeRow(i)} aria-label="Remove">
                    <Trash2 className="h-4 w-4 text-aion-ink-muted" />
                  </Button>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-2">
            <Button variant="outline" size="sm" onClick={addRow}>
              <Plus className="h-3.5 w-3.5" /> Add another
            </Button>
            <Button
              onClick={submit}
              loading={bulkCreate.isPending}
              disabled={!rows.some((r) => r.name.trim() && r.email.trim())}
            >
              Save People
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>Back</Button>
        <Button variant="outline" onClick={onNext}>
          Next: Add Policies <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

type PolicyDraft = { title: string; summary: string };

function PoliciesStep({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { data } = useDepartments();
  const bulkCreate = useBulkCreatePolicies();
  const [department, setDepartment] = useState("");
  const [rows, setRows] = useState<PolicyDraft[]>([{ title: "", summary: "" }]);

  const updateRow = (i: number, field: keyof PolicyDraft, value: string) =>
    setRows((r) => r.map((row, idx) => (idx === i ? { ...row, [field]: value } : row)));
  const addRow = () => setRows((r) => [...r, { title: "", summary: "" }]);
  const removeRow = (i: number) => setRows((r) => r.filter((_, idx) => idx !== i));

  const submit = async () => {
    const policies = rows
      .filter((r) => r.title.trim())
      .map((r) => ({ title: r.title.trim(), summary: r.summary.trim() || undefined, department: department || undefined }));
    if (!policies.length) return;
    await bulkCreate.mutateAsync(policies);
    setRows([{ title: "", summary: "" }]);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-aion-accent" />
            Add Policies
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-aion-ink-muted">Department</label>
            <select value={department} onChange={(e) => setDepartment(e.target.value)} className={selectClass}>
              <option value="">Organization-wide</option>
              {data?.departments.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            {rows.map((row, i) => (
              <div key={i} className="grid grid-cols-[1fr_2fr_auto] gap-2">
                <Input placeholder="Policy title" value={row.title} onChange={(e) => updateRow(i, "title", e.target.value)} />
                <Input placeholder="Short summary (optional)" value={row.summary} onChange={(e) => updateRow(i, "summary", e.target.value)} />
                {rows.length > 1 && (
                  <Button variant="ghost" size="icon" onClick={() => removeRow(i)} aria-label="Remove">
                    <Trash2 className="h-4 w-4 text-aion-ink-muted" />
                  </Button>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-2">
            <Button variant="outline" size="sm" onClick={addRow}>
              <Plus className="h-3.5 w-3.5" /> Add another
            </Button>
            <Button
              onClick={submit}
              loading={bulkCreate.isPending}
              disabled={!rows.some((r) => r.title.trim())}
            >
              Save Policies
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>Back</Button>
        <Button variant="outline" onClick={onNext}>
          Next: Review <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function ReviewStep({ onBack }: { onBack: () => void }) {
  const { data } = useDepartments();
  const totalPeople = data?.departments.reduce((sum, d) => sum + d.headcount, 0) ?? 0;
  const totalPolicies = data?.departments.reduce((sum, d) => sum + d.policy_count, 0) ?? 0;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Check className="h-4 w-4 text-health-green" />
            Organization Snapshot
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="metric-card text-center">
              <p className="text-2xl font-bold text-aion-ink tabular-nums">{data?.departments.length ?? 0}</p>
              <p className="text-2xs text-aion-ink-muted uppercase tracking-wider mt-1">Departments</p>
            </div>
            <div className="metric-card text-center">
              <p className="text-2xl font-bold text-aion-ink tabular-nums">{totalPeople}</p>
              <p className="text-2xs text-aion-ink-muted uppercase tracking-wider mt-1">People</p>
            </div>
            <div className="metric-card text-center">
              <p className="text-2xl font-bold text-aion-ink tabular-nums">{totalPolicies}</p>
              <p className="text-2xs text-aion-ink-muted uppercase tracking-wider mt-1">Policies</p>
            </div>
          </div>

          <div className="space-y-2">
            {data?.departments.map((d) => (
              <div key={d.id} className="flex items-center justify-between rounded-lg border border-aion-border bg-aion-surface2 px-4 py-3">
                <div className="flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-aion-accent" />
                  <span className="text-sm font-medium text-aion-ink">{d.name}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-aion-ink-muted">
                  <span className="flex items-center gap-1"><Users className="h-3 w-3" /> {d.headcount}</span>
                  <span className="flex items-center gap-1"><FileText className="h-3 w-3" /> {d.policy_count}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>Back</Button>
        <Button onClick={() => (window.location.href = "/dashboard/advisor")}>
          Ask AI Advisor about your org <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export default function OrganizationSetupPage() {
  return (
    <Suspense fallback={null}>
      <OrganizationSetupWizard />
    </Suspense>
  );
}

function OrganizationSetupWizard() {
  const searchParams = useSearchParams();
  const initialStep = (() => {
    const raw = Number(searchParams.get("step"));
    return raw >= 0 && raw <= 3 ? (raw as Step) : 0;
  })();
  const [step, setStep] = useState<Step>(initialStep);

  return (
    <div className="mx-auto max-w-3xl">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8 text-center">
        <h1 className="page-title flex items-center justify-center gap-2">
          <Building2 className="h-6 w-6 text-aion-accent" />
          Organization Setup
        </h1>
        <p className="page-subtitle mt-1">
          Model your company&apos;s real structure — departments, people, and policies — so AION can reason about it.
        </p>
      </motion.div>

      <StepHeader step={step} />

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -12 }}
          transition={{ duration: 0.2 }}
        >
          {step === 0 && <DepartmentsStep onNext={() => setStep(1)} />}
          {step === 1 && <PeopleStep onNext={() => setStep(2)} onBack={() => setStep(0)} />}
          {step === 2 && <PoliciesStep onNext={() => setStep(3)} onBack={() => setStep(1)} />}
          {step === 3 && <ReviewStep onBack={() => setStep(2)} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
