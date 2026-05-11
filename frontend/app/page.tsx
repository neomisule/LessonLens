"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight, Brain, Zap, BarChart3, Map, Search, BookOpen,
  Youtube, GitBranch, Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoIcon } from "@/components/shared/LogoIcon";

// ── Data ──────────────────────────────────────────────────────────────────────

const FEATURES = [
  {
    icon: Brain,
    title: "AI-Powered Summaries",
    description:
      "Three detail levels — brief, standard, detailed — all timestamped to the original lecture.",
    color: "text-lens-purple-light bg-lens-purple/15",
  },
  {
    icon: Zap,
    title: "Auto Flashcards",
    description:
      "LangGraph agents extract key concepts and generate active-recall cards automatically.",
    color: "text-lens-blue-light bg-lens-blue/15",
  },
  {
    icon: BarChart3,
    title: "Mastery Tracking",
    description:
      "SM-2 spaced-repetition scheduling keeps you reviewing what you need, when you need it.",
    color: "text-emerald-400 bg-emerald-500/15",
  },
  {
    icon: GitBranch,
    title: "Visual Mind Maps",
    description:
      "Concept relationships rendered as an interactive graph — see how ideas connect across lectures.",
    color: "text-amber-400 bg-amber-500/15",
  },
  {
    icon: Search,
    title: "Semantic Search",
    description:
      "Find any moment in any lecture with natural language, powered by pgvector embeddings.",
    color: "text-pink-400 bg-pink-500/15",
  },
  {
    icon: BookOpen,
    title: "Subject Library",
    description:
      "Organize lectures by subject. Cross-lecture concepts surface automatically.",
    color: "text-lens-teal-light bg-lens-teal/15",
  },
];

const MODES = [
  { label: "Learn",         color: "from-lens-purple to-lens-blue"  },
  { label: "Break It Down", color: "from-lens-blue to-lens-teal"    },
  { label: "Revise",        color: "from-lens-teal to-emerald-500"  },
  { label: "Search",        color: "from-amber-500 to-lens-purple"  },
  { label: "Mind Map",      color: "from-pink-500 to-lens-purple"   },
];

const HOW_IT_WORKS = [
  { step: "01", icon: Youtube,   title: "Paste a YouTube URL",       body: "Any lecture — no account needed. We support any public video with captions." },
  { step: "02", icon: Sparkles,  title: "AI agents go to work",      body: "8 LangGraph agents transcribe, segment, summarize, extract concepts, and build your study assets in parallel." },
  { step: "03", icon: BookOpen,  title: "Open your study system",    body: "Flashcards, quiz, oral exam, mind map, semantic search — ready in under 2 minutes." },
];

// ── Animation variants ────────────────────────────────────────────────────────

const stagger = {
  hidden: { opacity: 0 },
  show:   { opacity: 1, transition: { staggerChildren: 0.09 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show:   { opacity: 1, y: 0,   transition: { duration: 0.45, ease: [0.4, 0, 0.2, 1] } },
};

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col" id="main-content">
      {/* ── Nav ──────────────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-40 border-b border-lens-glass-border glass px-6 py-3">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <LogoIcon size="sm" className="h-8 w-8" />
            <span className="font-semibold text-foreground">LectureLens</span>
          </div>
          <Link href="/dashboard" aria-label="Open app dashboard">
            <Button size="sm">
              Get Started <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────────────── */}
      <section className="relative flex flex-col items-center justify-center px-6 py-32 text-center overflow-hidden">
        {/* Ambient glow */}
        <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.2 }}
          >
            <div className="absolute left-1/4 top-1/4 h-96 w-96 rounded-full bg-lens-purple/10 blur-3xl" />
            <div className="absolute right-1/4 bottom-1/4 h-80 w-80 rounded-full bg-lens-blue/10 blur-3xl" />
            <div className="absolute left-1/2 bottom-0 h-64 w-64 -translate-x-1/2 rounded-full bg-lens-teal/5 blur-3xl" />
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65, ease: [0.4, 0, 0.2, 1] }}
          className="flex flex-col items-center gap-6 max-w-3xl"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-2 rounded-full border border-lens-purple/30 bg-lens-purple/10 px-4 py-1.5 text-sm text-lens-purple-light"
          >
            <Zap className="h-3.5 w-3.5" />
            Powered by LangGraph multi-agent orchestration
          </motion.div>

          {/* Headline */}
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl text-balance">
            Turn lectures into{" "}
            <span className="gradient-text">study systems</span>
          </h1>

          {/* Subheading */}
          <p className="text-lg text-muted-foreground max-w-xl text-balance">
            Paste a YouTube lecture URL. AI agents transcribe, segment, summarize,
            and build flashcards — so you can focus on learning, not note-taking.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap justify-center gap-3">
            <Link href="/dashboard">
              <Button size="lg" className="glow-purple">
                Start Learning <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Button size="lg" variant="glass" asChild>
              <a href="#how-it-works">How it works</a>
            </Button>
          </div>
        </motion.div>
      </section>

      {/* ── Mode pills ────────────────────────────────────────────────────────── */}
      <section className="px-6 py-10 border-y border-lens-glass-border" aria-label="Study modes">
        <div className="mx-auto max-w-4xl">
          <p className="mb-6 text-center text-xs uppercase tracking-widest text-muted-foreground">
            Five study modes, one lecture
          </p>
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="flex flex-wrap justify-center gap-3"
          >
            {MODES.map((mode) => (
              <motion.div
                key={mode.label}
                variants={fadeUp}
                className={`rounded-full bg-gradient-to-r ${mode.color} p-px`}
              >
                <div className="rounded-full bg-background px-5 py-2 text-sm font-medium text-foreground">
                  {mode.label}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="px-6 py-24 scroll-mt-16" aria-labelledby="how-title">
        <div className="mx-auto max-w-4xl">
          <motion.h2
            id="how-title"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mb-16 text-center text-3xl font-bold"
          >
            Up and running in <span className="gradient-text">under 2 minutes</span>
          </motion.h2>

          <motion.ol
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="relative flex flex-col gap-0"
          >
            {HOW_IT_WORKS.map((step, i) => (
              <motion.li
                key={step.step}
                variants={fadeUp}
                className="flex gap-6 pb-12 last:pb-0"
              >
                {/* Timeline spine */}
                <div className="flex flex-col items-center shrink-0">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-lens-gradient text-white shadow-md shadow-lens-purple/20">
                    <step.icon className="h-5 w-5" />
                  </div>
                  {i < HOW_IT_WORKS.length - 1 && (
                    <div className="mt-2 flex-1 w-px bg-gradient-to-b from-lens-purple/30 to-transparent" />
                  )}
                </div>
                {/* Content */}
                <div className="flex-1 pt-1.5">
                  <span className="text-[10px] font-mono text-lens-purple-light uppercase tracking-widest">
                    Step {step.step}
                  </span>
                  <h3 className="mt-0.5 text-base font-semibold text-foreground">{step.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground leading-relaxed">{step.body}</p>
                </div>
              </motion.li>
            ))}
          </motion.ol>
        </div>
      </section>

      {/* ── Feature grid ─────────────────────────────────────────────────────── */}
      <section className="px-6 py-24 bg-white/[0.01]" aria-labelledby="features-title">
        <div className="mx-auto max-w-6xl">
          <motion.h2
            id="features-title"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mb-16 text-center text-3xl font-bold"
          >
            Everything you need to{" "}
            <span className="gradient-text">actually learn</span>
          </motion.h2>
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {FEATURES.map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                className="glass-card card-hover p-6"
              >
                <div className={`mb-3 flex h-10 w-10 items-center justify-center rounded-xl ${feature.color}`}>
                  <feature.icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <h3 className="mb-1.5 font-semibold text-foreground">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────────── */}
      <section className="px-6 py-28 text-center" aria-labelledby="cta-title">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-xl flex flex-col gap-5"
        >
          <div className="mx-auto flex h-16 w-16 items-center justify-center">
            <LogoIcon size="lg" className="animate-float shadow-lg shadow-lens-purple/25" />
          </div>
          <h2 id="cta-title" className="text-3xl font-bold">Ready to study smarter?</h2>
          <p className="text-muted-foreground text-balance">
            No signup required. Paste any YouTube lecture and get a full study system in minutes.
          </p>
          <Link href="/dashboard" className="mx-auto">
            <Button size="lg" className="glow-purple">
              Open Dashboard <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────────── */}
      <footer className="border-t border-lens-glass-border px-6 py-6 text-center text-xs text-muted-foreground">
        LectureLens — built for students, powered by AI
      </footer>
    </div>
  );
}
