"use client";

import { useState } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Mic, Bot, Sparkles, Mic2, Server, Monitor, BarChart3, Network } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface DockProps {
  activeView?: "whisper" | "agent" | "orchestrator" | "skills" | "tts" | "vocabulary" | "mcp" | "analytics";
  onViewChange?: (view: "whisper" | "agent" | "orchestrator" | "skills" | "tts" | "vocabulary" | "mcp" | "analytics") => void;
}

const DOCK_SIZE = 56;
const DOCK_MAGNIFICATION = 1.4;
const DOCK_DISTANCE = 120;

export default function Dock({ activeView, onViewChange }: DockProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const mouseX = useMotionValue(Infinity);
  const pathname = usePathname();

  const dockItems = [
    {
      id: "whisper",
      icon: Mic,
      label: "Hypr-Whisper",
      gradient: "from-blue-400 via-cyan-400 to-teal-400",
      href: "/"
    },
    {
      id: "agent",
      icon: Bot,
      label: "Hypr-Voice Agent",
      gradient: "from-purple-400 via-pink-400 to-rose-400",
      href: "/"
    },
    {
      id: "orchestrator",
      icon: Network,
      label: "Agent Orchestrator",
      gradient: "from-violet-400 via-purple-400 to-indigo-400",
      href: "/"
    },
    {
      id: "tts",
      icon: Mic2,
      label: "TTS Control",
      gradient: "from-indigo-400 via-violet-400 to-purple-400",
      href: "/"
    },
    {
      id: "skills",
      icon: Sparkles,
      label: "Skills Marketplace",
      gradient: "from-orange-400 via-amber-400 to-yellow-400",
      href: "/skills"
    },
    {
      id: "mcp",
      icon: Server,
      label: "MCP Servers",
      gradient: "from-emerald-400 via-teal-400 to-cyan-400",
      href: "/mcp"
    },
    {
      id: "vocabulary",
      icon: Monitor,
      label: "Vocabulary",
      gradient: "from-red-400 via-pink-400 to-rose-400",
      href: "/"
    },
    {
      id: "analytics",
      icon: BarChart3,
      label: "Analytics",
      gradient: "from-yellow-400 via-orange-400 to-amber-400",
      href: "/"
    },
  ];

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
      <motion.div
        onMouseMove={(e) => mouseX.set(e.pageX)}
        onMouseLeave={() => mouseX.set(Infinity)}
        className="relative flex items-end gap-2 px-3 py-2.5 rounded-[22px] backdrop-blur-[40px] saturate-[180%] bg-[rgba(15,15,15,0.65)] border border-[rgba(255,255,255,0.18)] shadow-[0_0_0_0.5px_rgba(255,255,255,0.1)_inset,_0_8px_32px_rgba(0,0,0,0.6),_0_2px_8px_rgba(0,0,0,0.4),_0_0_80px_-20px_rgba(138,80,255,0.4),_0_0_40px_-10px_rgba(59,130,246,0.3)]"
        suppressHydrationWarning
        initial={{ y: 100, opacity: 0, scale: 0.8 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 25,
          mass: 0.5
        }}
      >
        {dockItems.map((item, index) => {
          const isActive = pathname === item.href || activeView === item.id;
          const isExternal = item.external;

          return (
            <DockIcon
              key={item.id}
              mouseX={mouseX}
              item={item}
              index={index}
              isActive={isActive}
              onClick={() => {
                if (isExternal) {
                  window.location.href = item.href!;
                } else {
                  onViewChange?.(item.id as any);
                }
              }}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
              isHovered={hoveredIndex === index}
            />
          );
        })}

        {/* Ambient glow effect */}
        <div className="absolute -inset-[1px] bg-gradient-to-b from-white/[0.12] to-white/[0.03] rounded-[22px] pointer-events-none" />
        
        {/* Frosted glass layer */}
        <div className="absolute inset-0 rounded-[22px] pointer-events-none bg-gradient-to-b from-white/[0.08] to-white/[0.02]" />
      </motion.div>

      {/* Realistic dock reflection */}
      <div className="absolute top-full left-0 right-0 h-12 pointer-events-none opacity-25 bg-gradient-to-b from-white/[0.04] to-transparent transform scale-y-[-1] translate-y-[2px] blur-[3px]" style={{
        maskImage: "linear-gradient(to bottom, black 0%, transparent 80%)",
        WebkitMaskImage: "linear-gradient(to bottom, black 0%, transparent 80%)"
      }} />
    </div>
  );
}

function DockIcon({ 
  mouseX, 
  item, 
  index, 
  isActive, 
  onClick, 
  onMouseEnter, 
  onMouseLeave,
  isHovered 
}: any) {
  const ref = useState<HTMLButtonElement | null>(null);
  const distance = useTransform(mouseX, (val: number) => {
    const bounds = ref[0]?.getBoundingClientRect() ?? { x: 0, width: 0 };
    return val - bounds.x - bounds.width / 2;
  });

  const widthSync = useTransform(distance, [-DOCK_DISTANCE, 0, DOCK_DISTANCE], [DOCK_SIZE, DOCK_SIZE * DOCK_MAGNIFICATION, DOCK_SIZE]);
  const width = useSpring(widthSync, { mass: 0.1, stiffness: 300, damping: 20 });

  const Icon = item.icon;

  return (
    <div className="relative">
      <motion.button
        ref={(el) => ref[1](el)}
        style={{ width }}
        onClick={onClick}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        className="relative aspect-square rounded-[16px] flex items-center justify-center group cursor-pointer"
        whileTap={{ scale: 0.88 }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
      >
        {/* Icon background with realistic liquid glass */}
        <div className="absolute inset-0 rounded-[16px] overflow-hidden">
          {/* Base gradient */}
          <div className={`absolute inset-0 bg-gradient-to-br ${item.gradient} ${isActive ? 'opacity-95' : 'opacity-85'} ${isActive ? 'blur-0' : 'blur-[2px]'} saturate-[120%]`} />

          {/* Frosted glass blur layer */}
          <div className="absolute inset-0 backdrop-blur-[20px] saturate-[150%]" />

          {/* Multi-layer glass reflections */}
          <div className="absolute inset-0 bg-[conic-gradient(at_30%_30%,rgba(255,255,255,0.4)_0%,rgba(255,255,255,0.1)_30%,transparent_60%),linear-gradient(225deg,rgba(255,255,255,0.25)_0%,transparent_50%),radial-gradient(circle_at_30%_30%,rgba(255,255,255,0.3),transparent_50%)]" />

          {/* Inner luminous glow */}
          <div className="absolute inset-[1px] rounded-[15px] shadow-[0_0_25px_rgba(255,255,255,0.4)_inset,_0_0_50px_rgba(255,255,255,0.15)_inset,_0_2px_4px_rgba(255,255,255,0.2)_inset]" />

          {/* Outer glow border */}
          <div className="absolute inset-0 rounded-[16px] border border-[rgba(255,255,255,0.5)] shadow-[0_0_0_1px_rgba(255,255,255,0.15)_inset,_0_4px_12px_rgba(0,0,0,0.3),0_0_20px_${isActive ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.1)'}]" />
        </div>

        {/* Icon */}
        <motion.div
          className="relative z-10"
          animate={{
            scale: isActive ? 1.08 : 1,
            rotate: isActive ? [0, -4, 4, -4, 0] : 0,
          }}
          transition={{
            scale: { type: "spring", stiffness: 400, damping: 17 },
            rotate: { duration: 0.5 }
          }}
        >
          <Icon
            className="w-7 h-7 text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.3)] drop-shadow-[0_0_4px_rgba(255,255,255,0.2)]"
            strokeWidth={2.5}
          />
        </motion.div>

        {/* Multi-layer active glow */}
        {isActive && (
          <>
            <motion.div
              className="absolute -inset-3 rounded-[20px] blur-2xl"
              style={{
                background: `radial-gradient(circle, ${item.gradient.includes('blue') ? 'rgba(59, 130, 246, 0.7)' : 'rgba(168, 85, 247, 0.7)'}, transparent 65%)`,
              }}
              animate={{
                opacity: [0.5, 0.8, 0.5],
                scale: [1, 1.08, 1],
              }}
              transition={{
                duration: 2.5,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
            <motion.div
              className="absolute -inset-4 rounded-[24px] blur-3xl"
              style={{
                background: `radial-gradient(circle, ${item.gradient.includes('blue') ? 'rgba(59, 130, 246, 0.4)' : 'rgba(168, 85, 247, 0.4)'}, transparent 70%)`,
              }}
              animate={{
                opacity: [0.3, 0.5, 0.3],
                scale: [1, 1.1, 1],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.5
              }}
            />
          </>
        )}

        {/* Hover highlight */}
        {isHovered && (
          <motion.div
            className="absolute inset-0 rounded-[20px] bg-white/10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
        )}
      </motion.button>

      {/* Label tooltip with realistic glass */}
      <motion.div
        className="absolute -top-14 left-1/2 -translate-x-1/2 pointer-events-none"
        initial={{ opacity: 0, y: 10, scale: 0.9 }}
        animate={{
          opacity: isHovered ? 1 : 0,
          y: isHovered ? 0 : 10,
          scale: isHovered ? 1 : 0.9,
        }}
        transition={{ type: "spring", stiffness: 400, damping: 20 }}
      >
        <div className="px-3 py-1.5 rounded-lg whitespace-nowrap backdrop-blur-[30px] saturate-[180%] bg-[rgba(25,25,25,0.85)] border border-[rgba(255,255,255,0.2)] shadow-[0_0_0_0.5px_rgba(255,255,255,0.12)_inset,_0_8px_24px_-4px_rgba(0,0,0,0.6),_0_0_40px_-8px_rgba(138,80,255,0.25),_0_2px_6px_rgba(0,0,0,0.4)]">
          <span className="text-xs font-medium text-white/95">{item.label}</span>
        </div>

        {/* Glass tooltip arrow */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 -translate-y-[1px] w-0 h-0 border-l-[5px] border-r-[5px] border-t-[5px] border-l-transparent border-r-transparent border-t-[rgba(25,25,25,0.85)] drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]" />
      </motion.div>

      {/* Active indicator */}
      {isActive && (
        <motion.div
          className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-[radial-gradient(circle,rgba(255,255,255,0.9),rgba(255,255,255,0.4))] shadow-[0_0_8px_rgba(255,255,255,0.6)]"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          transition={{ type: "spring", stiffness: 500, damping: 25 }}
        />
      )}
    </div>
  );
}

