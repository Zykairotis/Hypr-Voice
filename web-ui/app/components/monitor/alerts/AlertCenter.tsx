"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Input } from "components/ui/input";
import { Button } from "components/ui/button";
import { Badge } from "components/ui/badge";
import { ScrollArea } from "components/ui/scroll-area";
import {
  AlertTriangle,
  AlertCircle,
  XCircle,
  Bell,
  BellOff,
  CheckCircle2,
  Clock,
  Settings,
  Volume2
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket, AlertRule } from "lib/websocket";

const DEFAULT_RULES: AlertRule[] = [
  {
    id: "1",
    name: "High CPU Usage",
    condition: "cpu > 80",
    threshold: 80,
    severity: "warning",
    enabled: true,
    cooldown: 300,
  },
  {
    id: "2",
    name: "Critical CPU Usage",
    condition: "cpu > 95",
    threshold: 95,
    severity: "critical",
    enabled: true,
    cooldown: 60,
  },
  {
    id: "3",
    name: "High Memory Usage",
    condition: "memory > 85",
    threshold: 85,
    severity: "warning",
    enabled: true,
    cooldown: 300,
  },
  {
    id: "4",
    name: "Error Rate Spike",
    condition: "errorRate > 10",
    threshold: 10,
    severity: "critical",
    enabled: true,
    cooldown: 120,
  },
];

export default function AlertCenter() {
  const { alerts, metrics } = useWebSocket();
  const [rules, setRules] = useState<AlertRule[]>(DEFAULT_RULES);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [newRuleName, setNewRuleName] = useState("");

  const activeAlerts = useMemo(() => {
    return alerts.filter(alert => {
      const rule = rules.find(r => r.id === alert.ruleId);
      return rule?.enabled !== false;
    });
  }, [alerts, rules]);

  const alertStats = useMemo(() => {
    return {
      total: alerts.length,
      critical: alerts.filter(a => a.severity === "critical").length,
      error: alerts.filter(a => a.severity === "error").length,
      warning: alerts.filter(a => a.severity === "warning").length,
      active: activeAlerts.length,
    };
  }, [alerts, activeAlerts]);

  const addRule = () => {
    if (!newRuleName.trim()) return;

    const newRule: AlertRule = {
      id: `rule_${Date.now()}`,
      name: newRuleName,
      condition: "custom",
      threshold: 0,
      severity: "info",
      enabled: true,
      cooldown: 300,
    };

    setRules([...rules, newRule]);
    setNewRuleName("");
  };

  const toggleRule = (ruleId: string) => {
    setRules(rules.map(rule =>
      rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule
    ));
  };

  const testAlert = (severity: string) => {
    const testAlert = {
      ruleId: "test",
      message: `Test ${severity} alert`,
      severity,
      timestamp: Date.now(),
    };
    console.log("Test alert:", testAlert);
  };

  return (
    <div className="space-y-6">
      {/* Alert Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <AlertStatCard
          title="Total Alerts"
          value={alertStats.total}
          icon={Bell}
          color="text-blue-400"
        />
        <AlertStatCard
          title="Critical"
          value={alertStats.critical}
          icon={XCircle}
          color="text-red-400"
        />
        <AlertStatCard
          title="Errors"
          value={alertStats.error}
          icon={AlertCircle}
          color="text-orange-400"
        />
        <AlertStatCard
          title="Warnings"
          value={alertStats.warning}
          icon={AlertTriangle}
          color="text-yellow-400"
        />
        <AlertStatCard
          title="Active"
          value={alertStats.active}
          icon={Bell}
          color="text-purple-400"
        />
      </div>

      {/* Controls */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex items-center gap-3 flex-wrap">
            <Button
              variant={soundEnabled ? "default" : "outline"}
              size="sm"
              onClick={() => setSoundEnabled(!soundEnabled)}
            >
              {soundEnabled ? <Volume2 className="w-4 h-4 mr-2" /> : <BellOff className="w-4 h-4 mr-2" />}
              {soundEnabled ? "Sound On" : "Sound Off"}
            </Button>

            <Button variant="outline" size="sm" onClick={() => testAlert("critical")}>
              Test Critical
            </Button>

            <Button variant="outline" size="sm" onClick={() => testAlert("warning")}>
              Test Warning
            </Button>

            <div className="flex-1" />

            <div className="flex items-center gap-2">
              <Input
                placeholder="New rule name..."
                value={newRuleName}
                onChange={(e) => setNewRuleName(e.target.value)}
                className="bg-black/30 border-white/10 w-48"
              />
              <Button size="sm" onClick={addRule}>
                Add Rule
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alert Rules */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Alert Rules
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {rules.map((rule) => (
              <motion.div
                key={rule.id}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  rule.enabled
                    ? "bg-white/5 border-white/10 hover:bg-white/10"
                    : "bg-white/5 border-white/10 opacity-50"
                }`}
                onClick={() => toggleRule(rule.id)}
                whileHover={{ scale: 1.01 }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      rule.severity === "critical" ? "bg-red-500/20" :
                      rule.severity === "error" ? "bg-orange-500/20" :
                      rule.severity === "warning" ? "bg-yellow-500/20" :
                      "bg-blue-500/20"
                    }`}>
                      {rule.severity === "critical" && <XCircle className="w-4 h-4 text-red-400" />}
                      {rule.severity === "error" && <AlertCircle className="w-4 h-4 text-orange-400" />}
                      {rule.severity === "warning" && <AlertTriangle className="w-4 h-4 text-yellow-400" />}
                      {rule.severity === "info" && <Bell className="w-4 h-4 text-blue-400" />}
                    </div>
                    <div>
                      <h3 className="font-medium text-white">{rule.name}</h3>
                      <p className="text-sm text-white/60">
                        {rule.condition} • Cooldown: {rule.cooldown}s
                      </p>
                    </div>
                  </div>
                  <Badge variant={rule.enabled ? "default" : "outline"}>
                    {rule.enabled ? "Enabled" : "Disabled"}
                  </Badge>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Active Alerts */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Active Alerts</span>
            <Badge variant="outline">{activeAlerts.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-2">
              {activeAlerts.length === 0 ? (
                <div className="text-center py-12 text-white/50">
                  <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-green-400" />
                  <p>No active alerts</p>
                  <p className="text-sm">System is running normally</p>
                </div>
              ) : (
                <AnimatePresence>
                  {activeAlerts.slice().reverse().map((alert, index) => (
                    <motion.div
                      key={`${alert.ruleId}-${alert.timestamp}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.2, delay: index * 0.01 }}
                    >
                      <AlertItem alert={alert} />
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

function AlertStatCard({
  title,
  value,
  icon: Icon,
  color
}: {
  title: string;
  value: number;
  icon: any;
  color: string;
}) {
  return (
    <motion.div whileHover={{ scale: 1.02 }}>
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white/60">{title}</p>
              <p className="text-2xl font-bold text-white mt-1">{value}</p>
            </div>
            <Icon className={`w-6 h-6 ${color}`} />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function AlertItem({ alert }: { alert: any }) {
  const severityConfig = {
    critical: { color: "text-red-400", bg: "bg-red-500/20 border-red-500/30", icon: XCircle },
    error: { color: "text-orange-400", bg: "bg-orange-500/20 border-orange-500/30", icon: AlertCircle },
    warning: { color: "text-yellow-400", bg: "bg-yellow-500/20 border-yellow-500/30", icon: AlertTriangle },
    info: { color: "text-blue-400", bg: "bg-blue-500/20 border-blue-500/30", icon: Bell },
  };

  const config = severityConfig[alert.severity as keyof typeof severityConfig] || severityConfig.info;
  const SeverityIcon = config.icon;

  return (
    <motion.div
      className={`p-4 rounded-lg border backdrop-blur-xl ${config.bg}`}
      whileHover={{ x: 4 }}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-black/30">
          <SeverityIcon className={`w-5 h-5 ${config.color}`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge className={`${config.bg} ${config.color} border-0 text-xs`}>
              {alert.severity.toUpperCase()}
            </Badge>
            <span className="text-xs text-white/40">
              {new Date(alert.timestamp).toLocaleString()}
            </span>
          </div>

          <p className="text-white font-medium mb-1">{alert.message}</p>

          <div className="flex items-center gap-2 text-sm text-white/60">
            <Clock className="w-3 h-3" />
            {getTimeAgo(alert.timestamp)}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function getTimeAgo(timestamp: number): string {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
