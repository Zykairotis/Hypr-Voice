"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Activity,
  Clock,
  TrendingUp,
  User,
  Settings,
  Download,
  Star,
  Tag,
  PlayCircle,
  CheckCircle,
  XCircle,
} from "lucide-react";
import type { Skill } from "@/types/skills";

interface SkillCardProps {
  skill: Skill;
  onToggle?: (skillId: string, enabled: boolean) => void;
  onConfigure?: (skill: Skill) => void;
  onExecute?: (skill: Skill) => void;
}

export default function SkillCard({
  skill,
  onToggle,
  onConfigure,
  onExecute,
}: SkillCardProps) {
  const [isEnabled, setIsEnabled] = useState(skill.enabled);

  const handleToggle = (checked: boolean) => {
    setIsEnabled(checked);
    onToggle?.(skill.id, checked);
  };

  const getStatusColor = (rate: number) => {
    if (rate >= 98) return "text-green-400";
    if (rate >= 95) return "text-yellow-400";
    return "text-red-400";
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      core: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      custom: "bg-purple-500/20 text-purple-400 border-purple-500/30",
      mcp: "bg-orange-500/20 text-orange-400 border-orange-500/30",
      community: "bg-pink-500/20 text-pink-400 border-pink-500/30",
    };
    return colors[category as keyof typeof colors] || colors.core;
  };

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ y: -4 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        <Card className="overflow-hidden h-full">
          <div
            className={`absolute inset-0 bg-gradient-to-br ${
              isEnabled
                ? "from-white/5 to-white/0"
                : "from-gray-500/5 to-gray-500/0"
            } to-transparent opacity-50`}
          />

          <CardHeader className="relative">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <CardTitle className="text-lg">{skill.name}</CardTitle>
                  <Badge
                    variant="outline"
                    className={getCategoryColor(skill.category)}
                  >
                    {skill.category}
                  </Badge>
                </div>
                <CardDescription className="text-sm text-white/60">
                  {skill.description}
                </CardDescription>
              </div>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={isEnabled}
                      onCheckedChange={handleToggle}
                    />
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{isEnabled ? "Disable skill" : "Enable skill"}</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </CardHeader>

          <CardContent className="relative space-y-4">
            {skill.author && (
              <div className="flex items-center gap-2 text-sm text-white/60">
                <User className="w-4 h-4" />
                <span>{skill.author}</span>
              </div>
            )}

            <div className="grid grid-cols-3 gap-3">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="bg-white/5 rounded-lg p-3 text-center">
                    <Activity className="w-4 h-4 mx-auto mb-1 text-blue-400" />
                    <div className="text-xs text-white/60">Usage</div>
                    <div className="text-sm font-semibold text-white">
                      {skill.usage_count.toLocaleString()}
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Total executions</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="bg-white/5 rounded-lg p-3 text-center">
                    <TrendingUp
                      className={`w-4 h-4 mx-auto mb-1 ${getStatusColor(
                        skill.success_rate
                      )}`}
                    />
                    <div className="text-xs text-white/60">Success</div>
                    <div
                      className={`text-sm font-semibold ${getStatusColor(
                        skill.success_rate
                      )}`}
                    >
                      {skill.success_rate.toFixed(1)}%
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Success rate</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="bg-white/5 rounded-lg p-3 text-center">
                    <Clock className="w-4 h-4 mx-auto mb-1 text-purple-400" />
                    <div className="text-xs text-white/60">Avg Time</div>
                    <div className="text-sm font-semibold text-white">
                      {skill.average_execution_time}ms
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Average execution time</p>
                </TooltipContent>
              </Tooltip>
            </div>

            {skill.tags && skill.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {skill.tags.map((tag) => (
                  <Badge
                    key={tag}
                    variant="outline"
                    className="text-xs bg-white/5 border-white/10 text-white/70"
                  >
                    <Tag className="w-3 h-3 mr-1" />
                    {tag}
                  </Badge>
                ))}
              </div>
            )}

            {skill.is_public && skill.rating && (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  <span className="text-sm font-semibold text-white">
                    {skill.rating.toFixed(1)}
                  </span>
                </div>
                {skill.download_count && (
                  <div className="flex items-center gap-1 text-sm text-white/60">
                    <Download className="w-4 h-4" />
                    <span>{skill.download_count}</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>

          <CardFooter className="relative flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onConfigure?.(skill)}
            >
              <Settings className="w-4 h-4 mr-2" />
              Configure
            </Button>
            <Button
              size="sm"
              className="flex-1"
              onClick={() => onExecute?.(skill)}
              disabled={!isEnabled}
            >
              <PlayCircle className="w-4 h-4 mr-2" />
              Test
            </Button>
          </CardFooter>
        </Card>
      </motion.div>
    </TooltipProvider>
  );
}
