"use client";
import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Check, Copy, Database, Send, Sparkles, User } from "lucide-react";
import { useAdvisorChat } from "@/lib/hooks/use-board";
import { useAuthStore } from "@/lib/stores/auth.store";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

type ChatTurn = { role: "user" | "assistant"; content: string };

const SUGGESTED_PROMPTS = [
  "What is our biggest organizational risk right now?",
  "How healthy is our knowledge base overall?",
  "Which knowledge is at risk if someone leaves?",
  "What should we do this week to improve?",
];

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-2">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-aion-insight/60"
          animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }}
          transition={{ duration: 1, repeat: Infinity, delay: i * 0.15, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}

// Lazy-loaded — the markdown parser (and its dependency tree) has no reason
// to be in this page's initial bundle just to land on an empty chat screen;
// it's only needed once an assistant message with formatting actually
// arrives. Cuts /dashboard/advisor's first-load JS noticeably.
const ReactMarkdown = dynamic(() => import("react-markdown"), { ssr: false });

const markdownComponents = {
  p: ({ children }: { children?: React.ReactNode }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }: { children?: React.ReactNode }) => (
    <ul className="mb-2 ml-4 list-disc space-y-1 last:mb-0">{children}</ul>
  ),
  ol: ({ children }: { children?: React.ReactNode }) => (
    <ol className="mb-2 ml-4 list-decimal space-y-1 last:mb-0">{children}</ol>
  ),
  strong: ({ children }: { children?: React.ReactNode }) => (
    <strong className="font-semibold text-aion-accent">{children}</strong>
  ),
  code: ({ children }: { children?: React.ReactNode }) => (
    <code className="rounded bg-aion-surface2 px-1.5 py-0.5 font-mono text-2xs text-aion-insight">{children}</code>
  ),
  a: ({ children, href }: { children?: React.ReactNode; href?: string }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-aion-accent underline underline-offset-2">
      {children}
    </a>
  ),
};

function ChatBubble({ turn, i }: { turn: ChatTurn; i: number }) {
  const isUser = turn.role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(turn.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i === 0 ? 0 : 0.02, duration: 0.25 }}
      className={cn("group flex items-start gap-3", isUser && "flex-row-reverse")}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          isUser
            ? "bg-aion-surface2 ring-1 ring-aion-border text-aion-ink-muted"
            : "bg-brand-gradient text-white shadow-glow-violet",
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className={cn("max-w-[75%]", isUser && "flex flex-col items-end")}>
        {!isUser && (
          <span className="mb-1 block text-2xs font-semibold text-aion-insight">Axon</span>
        )}
        <div
          className={cn(
            "rounded-lg px-4 py-3 text-sm leading-relaxed transition-shadow duration-200",
            isUser
              ? "whitespace-pre-wrap bg-aion-accent-tint border border-aion-accent-border text-aion-ink"
              : "bg-aion-surface border-l-2 border-l-aion-violet border-y border-r border-y-aion-border border-r-aion-border text-aion-ink shadow-card hover:shadow-glow-violet",
          )}
        >
          {isUser ? (
            turn.content
          ) : (
            <ReactMarkdown components={markdownComponents}>
              {turn.content}
            </ReactMarkdown>
          )}
        </div>
        {!isUser && (
          <button
            onClick={handleCopy}
            className="mt-1 flex cursor-pointer items-center gap-1 text-2xs text-aion-ink-faint opacity-0 transition-opacity duration-150 hover:text-aion-ink-muted group-hover:opacity-100"
          >
            {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            {copied ? "Copied" : "Copy"}
          </button>
        )}
      </div>
    </motion.div>
  );
}

export default function AdvisorChatPage() {
  const user = useAuthStore((s) => s.user);
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const chatMutation = useAdvisorChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [history, chatMutation.isPending]);

  const send = (message: string) => {
    const text = message.trim();
    if (!text || chatMutation.isPending) return;

    const nextHistory: ChatTurn[] = [...history, { role: "user", content: text }];
    setHistory(nextHistory);
    setInput("");

    chatMutation.mutate(
      { message: text, history },
      {
        onSuccess: (data) => {
          setHistory((h) => [...h, { role: "assistant", content: data.answer }]);
        },
        onError: () => {
          setHistory((h) => [
            ...h,
            { role: "assistant", content: "I couldn't reach the AI model just now. Please try again in a moment." },
          ]);
        },
      },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  return (
    <div className="flex h-[calc(100vh-6rem)] flex-col">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-4 shrink-0">
        <h1 className="page-title flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-white shadow-glow-violet">
            <Sparkles className="h-4 w-4" />
          </span>
          Axon
        </h1>
        <p className="page-subtitle mt-1">
          Your AI organizational advisor — ask anything, grounded in AION&apos;s real, live intelligence data.
        </p>
      </motion.div>

      <div className="card-surface flex flex-1 flex-col overflow-hidden">
        <div className="flex shrink-0 items-center justify-between border-b border-aion-border bg-gradient-to-r from-aion-insight-tint via-aion-violet-tint to-aion-surface2 px-5 py-3">
          <span className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-gradient text-white shadow-glow-violet">
              <Bot className="h-3.5 w-3.5" />
            </span>
            <span className="text-xs font-semibold text-aion-ink">Axon</span>
            <span className="hidden text-2xs text-aion-ink-muted sm:flex sm:items-center sm:gap-1">
              <Database className="h-3 w-3" />
              Grounded in your live organizational data
            </span>
          </span>
          <span className="flex items-center gap-1.5 text-2xs text-aion-ink-faint">
            <span className="h-1.5 w-1.5 rounded-full bg-health-green live-pulse" />
            Connected
          </span>
        </div>
        <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-6 py-6 no-scrollbar">
          {history.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-brand-gradient shadow-glow-violet">
                <Bot className="h-7 w-7 text-white" />
              </div>
              <p className="text-sm font-semibold text-aion-ink">
                Hi{user?.email ? `, ${user.email.split("@")[0]}` : ""}. I&apos;m Axon.
              </p>
              <p className="mt-1 max-w-md text-xs text-aion-ink-muted">
                I can see your organization&apos;s knowledge graph, intelligence index, disease scans,
                and bottlenecks in real time. Ask me anything.
              </p>
              <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => send(prompt)}
                    className="cursor-pointer rounded-lg border border-aion-border bg-aion-surface px-4 py-2.5 text-left text-xs text-aion-ink-muted transition-colors duration-200 hover:border-aion-accent/40 hover:bg-aion-accent-tint hover:text-aion-ink"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {history.map((turn, i) => (
                <ChatBubble key={i} turn={turn} i={i} />
              ))}
              <AnimatePresence>
                {chatMutation.isPending && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-start gap-3"
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-aion-insight-tint ring-1 ring-aion-insight/25 text-aion-insight">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="rounded-lg border border-aion-border bg-aion-surface px-2 shadow-card">
                      <TypingIndicator />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </>
          )}
        </div>

        <div className="shrink-0 border-t border-aion-border p-4">
          <div className="flex items-end gap-2 rounded-lg border border-aion-border bg-aion-surface2 p-2 focus-within:border-aion-accent transition-colors duration-200">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Axon about the organization..."
              rows={1}
              className="max-h-32 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-aion-ink placeholder:text-aion-ink-faint focus:outline-none"
            />
            <Button
              size="icon"
              onClick={() => send(input)}
              disabled={!input.trim() || chatMutation.isPending}
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
