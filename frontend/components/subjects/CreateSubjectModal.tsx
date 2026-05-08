"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateSubject } from "@/lib/hooks/useSubjects";

const PRESET_COLORS = [
  "#7C3AED", "#3B82F6", "#14B8A6", "#F59E0B",
  "#EF4444", "#10B981", "#8B5CF6", "#EC4899",
];
const PRESET_ICONS = ["📚", "🔬", "💻", "🎨", "🧮", "🌍", "⚗️", "🎵", "📐", "🏛️"];

interface CreateSubjectModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateSubjectModal({ open, onOpenChange }: CreateSubjectModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState(PRESET_COLORS[0]);
  const [icon, setIcon] = useState(PRESET_ICONS[0]);

  const { mutateAsync, isPending } = useCreateSubject();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await mutateAsync({ name: name.trim(), description: description.trim() || undefined, color, icon });
    setName("");
    setDescription("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Subject</DialogTitle>
          <DialogDescription>Organize your lectures by subject area.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-2xl border border-lens-glass-border"
              style={{ backgroundColor: `${color}20` }}
            >
              {icon}
            </div>
            <Input
              placeholder="Subject name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <Input
            placeholder="Short description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div>
            <p className="mb-2 text-xs text-muted-foreground">Icon</p>
            <div className="flex flex-wrap gap-2">
              {PRESET_ICONS.map((ic) => (
                <button
                  key={ic}
                  type="button"
                  onClick={() => setIcon(ic)}
                  className={`flex h-9 w-9 items-center justify-center rounded-lg border text-lg transition-all ${
                    icon === ic
                      ? "border-lens-purple/60 bg-lens-purple/15"
                      : "border-lens-glass-border bg-white/5 hover:bg-white/10"
                  }`}
                >
                  {ic}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs text-muted-foreground">Color</p>
            <div className="flex gap-2">
              {PRESET_COLORS.map((c) => (
                <motion.button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  className="h-6 w-6 rounded-full transition-all"
                  style={{
                    backgroundColor: c,
                    boxShadow: color === c ? `0 0 0 3px ${c}40, 0 0 0 5px ${c}20` : "none",
                  }}
                />
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!name.trim() || isPending}>
              {isPending ? "Creating…" : "Create Subject"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
