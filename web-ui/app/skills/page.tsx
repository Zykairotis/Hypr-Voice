"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Mic, Bot, Activity, Sparkles } from "lucide-react";
import SkillsLibrary from "@/components/skills/SkillsLibrary";

export default function SkillsPage() {
  return (
    <div className="min-h-screen w-full bg-background overflow-hidden">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-pink-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative container mx-auto px-6 py-8">
        <SkillsLibrary />
      </div>
    </div>
  );
}
