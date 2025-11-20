'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import {
  Brain,
  Terminal,
  Clipboard,
  Monitor,
  TrendingUp,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useContextData } from '../hooks/useContextData';

export function ContextWidget() {
  const { data, loading, lastUpdate } = useContextData();

  const getContextStrength = (): number => {
    if (!data) return 0;

    let score = 0;
    score += Math.min(data.shell.commands.length / 50, 1) * 30;
    score += Math.min(data.clipboard.entries.length / 30, 1) * 20;
    score += data.applications.activeWindow ? 25 : 0;
    score += Math.min(data.applications.history.length / 20, 1) * 25;

    return Math.min(score, 100);
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Live Context
          </CardTitle>
          <Link href="/context">
            <Button variant="ghost" size="sm">
              <ExternalLink className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Context Strength */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Context Strength</span>
            <Badge variant={getContextStrength() > 70 ? 'default' : 'secondary'}>
              {getContextStrength().toFixed(0)}%
            </Badge>
          </div>
          <Progress value={getContextStrength()} className="h-2" />
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-2">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 p-2 bg-muted/50 rounded"
          >
            <Terminal className="w-4 h-4 text-blue-400" />
            <div>
              <div className="text-xs text-muted-foreground">Commands</div>
              <div className="font-semibold text-sm">{data?.shell.commands.length || 0}</div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="flex items-center gap-2 p-2 bg-muted/50 rounded"
          >
            <Clipboard className="w-4 h-4 text-green-400" />
            <div>
              <div className="text-xs text-muted-foreground">Clipboard</div>
              <div className="font-semibold text-sm">{data?.clipboard.entries.length || 0}</div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex items-center gap-2 p-2 bg-muted/50 rounded col-span-2"
          >
            <Monitor className="w-4 h-4 text-purple-400" />
            <div className="flex-1 min-w-0">
              <div className="text-xs text-muted-foreground">Active Window</div>
              <div className="font-semibold text-sm truncate">
                {data?.applications.activeWindow?.class || 'None detected'}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Recent Activity */}
        {data && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">Recent Activity</span>
              <Badge variant="outline" className="text-xs">
                Live
              </Badge>
            </div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {data.shell.commands.slice(0, 3).map((cmd, i) => (
                <div key={cmd.id} className="text-xs font-mono bg-muted/20 rounded px-2 py-1 truncate">
                  {cmd.command}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Last Update */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
          <span>Updated {new Date(lastUpdate).toLocaleTimeString()}</span>
        </div>
      </CardContent>
    </Card>
  );
}
