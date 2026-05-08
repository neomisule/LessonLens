"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Brain, Zap, BarChart3, Map, Search, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

const FEATURES = [
  { icon: Brain, title: "AI-Powered Summaries", description: "Three detail levels — brief, standard, detailed — all timestamped to the original lecture." },
  { icon: Zap, title: "Auto Flashcards", description: "LangGraph agents extract key concepts and generate active-recall cards automatically." },
  { icon: BarChart3, title: "Mastery Tracking", description: "Spaced-repetition scheduling keeps you reviewing what you don't know, when you need it." },
  { icon: Map, title: "Visual Mind Maps", description: "Concept relationships rendered as an interactive graph — see how ideas connect." },
  { icon: Search, title: "Semantic Search", description: "Find any moment in any lecture with natural language, powered by pgvector." },
  { icon: BookOpen, title: "Subject Library", description: "Organize lectures by subject. Every course becomes its own knowledge base." },
];

const MODES = [
  { id: "learn", label: "Learn", color: "from-lens-purple to-lens-blue" },
  { id: "break_it_down", label: "Break It Down", color: "from-lens-blue to-lens-teal" },
  { id: "revise", label: "Revise", color: "from-lens-teal to-green-500" },
  { id: "search", label: "Search", color: "from-amber-500 to-lens-purple" },
  { id: "mind_map", label: "Mind Map", color: "from-pink-500 to-lens-purple" },
];

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <nav className="sticky top-0 z-40 border-b border-lens-glass-border glass px-6 py-3">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-lens-gradient text-white text-sm font-bold">L</div>
            <span className="font-semibold text-foreground">LectureLens</span>
          </div>
          <Link href="/dashboard"><Button size="sm">Get Started <ArrowRight className="h-3.5 w-3.5" /></Button></Link>
        </div>
      </nav>

      <section className="relative flex flex-col items-center justify-center px-6 py-32 text-center">
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }} className="absolute inset-0 -z-10">
          <div className="absolute left-1/4 top-1/4 h-96 w-96 rounded-full bg-lens-purple/10 blur-3xl" />
          <div className="absolute right-1/4 bottom-1/4 h-80 w-80 rounded-full bg-lens-blue/10 blur-3xl" />
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="flex flex-col items-center gap-6 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-lens-purple/30 bg-lens-purple/10 px-4 py-1.5 text-sm text-lens-purple-light">
            <Zap className="h-3.5 w-3.5" />
            Powered by LangGraph multi-agent orchestration
          </div>
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
            Turn lectures into{" "}
            <span className="gradient-text">study systems</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl">
            Paste a YouTube lecture URL. LectureLens&apos; AI agents transcribe, segment, summarize,
            and build flashcards — so you can focus on learning, not note-taking.
          </p>
          <div className="flex gap-3">
            <Link href="/dashboard"><Button size="lg" className="glow-purple">Start Learning <ArrowRight className="h-4 w-4" /></Button></Link>
            <Button size="lg" variant="glass">See Demo</Button>
          </div>
        </motion.div>
      </section>

      <section className="px-6 py-10 border-y border-lens-glass-border">
        <div className="mx-auto max-w-4xl">
          <p className="mb-6 text-center text-xs uppercase tracking-widest text-muted-foreground">Five study modes, one lecture</p>
          <motion.div variants={container} initial="hidden" whileInView="show" viewport={{ once: true }} className="flex flex-wrap justify-center gap-3">
            {MODES.map((mode) => (
              <motion.div key={mode.id} variants={item} className={`rounded-full bg-gradient-to-r ${mode.color} p-px`}>
                <div className="rounded-full bg-background px-4 py-1.5 text-sm font-medium text-foreground">{mode.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <motion.h2 initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16 text-center text-3xl font-bold">
            Everything you need to <span className="gradient-text">actually learn</span>
          </motion.h2>
          <motion.div variants={container} initial="hidden" whileInView="show" viewport={{ once: true }} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <motion.div key={feature.title} variants={item} className="glass-card p-6">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-lens-purple/15 text-lens-purple-light">
                  <feature.icon className="h-5 w-5" />
                </div>
                <h3 className="mb-1.5 font-semibold text-foreground">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="px-6 py-24 text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="mx-auto max-w-xl flex flex-col gap-5">
          <h2 className="text-3xl font-bold">Ready to study smarter?</h2>
          <p className="text-muted-foreground">No signup required. Just paste a YouTube URL and go.</p>
          <Link href="/dashboard" className="mx-auto"><Button size="lg" className="glow-purple">Open Dashboard <ArrowRight className="h-4 w-4" /></Button></Link>
        </motion.div>
      </section>

      <footer className="border-t border-lens-glass-border px-6 py-6 text-center text-xs text-muted-foreground">
        LectureLens — built for students, powered by AI
      </footer>
    </div>
  );
}
