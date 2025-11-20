'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Activity,
  Database,
  Settings,
  Download,
  Upload,
  RefreshCw,
  Search,
  TestTube,
  BarChart3,
  FileText,
  Terminal,
  Clipboard,
  CheckCircle,
  XCircle,
  AlertCircle,
  Star,
  TrendingUp,
  TrendingDown,
  Minus,
  Eye,
  EyeOff,
  Copy,
  Trash2,
  Edit,
  Save,
  X,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  VocabularyStatistics,
  VocabularyConfig,
  ContextData,
  ApplicationContext,
  KeywordEffectiveness,
  VocabularyMatch,
} from '@/lib/vocabulary/types';

interface VocabularyDashboardProps {
  initialStats?: VocabularyStatistics;
  onConfigChange?: (config: VocabularyConfig) => void;
}

interface IntegrationSettings {
  shellHistory: {
    enabled: boolean;
    maxEntries: number;
    extractKeywords: boolean;
  };
  clipboardHistory: {
    enabled: boolean;
    maxEntries: number;
    extractKeywords: boolean;
  };
  windowDetection: {
    enabled: boolean;
    autoSwitch: boolean;
    sensitivity: number;
  };
}

interface TestResult {
  word: string;
  matched: boolean;
  confidence: number;
  suggestions: string[];
  timestamp: number;
}

interface PerformanceMetrics {
  totalMatches: number;
  accuracyRate: number;
  falsePositives: number;
  recentlyUsed: string[];
  topCategories: Array<{
    name: string;
    count: number;
    trend: 'up' | 'down' | 'stable';
  }>;
}

export default function VocabularyDashboard({
  initialStats,
  onConfigChange,
}: VocabularyDashboardProps) {
  const [stats, setStats] = useState<VocabularyStatistics | null>(initialStats || null);
  const [contextData, setContextData] = useState<ContextData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());

  // State for various features
  const [integrationSettings, setIntegrationSettings] = useState<IntegrationSettings>({
    shellHistory: {
      enabled: true,
      maxEntries: 40,
      extractKeywords: true,
    },
    clipboardHistory: {
      enabled: true,
      maxEntries: 5,
      extractKeywords: true,
    },
    windowDetection: {
      enabled: true,
      autoSwitch: true,
      sensitivity: 0.8,
    },
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVocabulary, setSelectedVocabulary] = useState<string>('global');
  const [isEditing, setIsEditing] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [showInactive, setShowInactive] = useState(false);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>({
    totalMatches: 0,
    accuracyRate: 0.95,
    falsePositives: 2,
    recentlyUsed: [],
    topCategories: [],
  });

  const [effectivenessData, setEffectivenessData] = useState<KeywordEffectiveness[]>([]);

  // Load initial data
  useEffect(() => {
    loadDashboardData();

    // Set up periodic refresh
    const interval = setInterval(() => {
      if (!refreshing) {
        loadDashboardData(false);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setRefreshing(true);

    try {
      // In a real implementation, these would be API calls
      await Promise.all([
        loadStatistics(),
        loadContextData(),
        loadPerformanceMetrics(),
        loadEffectivenessData(),
      ]);

      setLastUpdate(Date.now());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast.error('Failed to load vocabulary data');
    } finally {
      setRefreshing(false);
      if (showLoader) setLoading(false);
    }
  };

  const loadStatistics = async () => {
    // Mock data - replace with actual API call
    const mockStats: VocabularyStatistics = {
      totalVocabularies: 5,
      currentVocabulary: 'global',
      currentApplication: 'VSCode',
      activeKeywords: 247,
      vocabularies: {
        global: {
          name: 'Global',
          description: 'Global vocabulary for all applications',
          totalKeywords: 89,
        },
        vscode: {
          name: 'Visual Studio Code',
          description: 'Development vocabulary for VSCode',
          totalKeywords: 156,
        },
        terminal: {
          name: 'Terminal',
          description: 'Shell and command-line vocabulary',
          totalKeywords: 78,
        },
        browser: {
          name: 'Web Browser',
          description: 'Web development vocabulary',
          totalKeywords: 92,
        },
      },
      usageStats: {
        mostUsed: [
          { word: 'TypeScript', count: 45 },
          { word: 'React', count: 38 },
          { word: 'Kubernetes', count: 32 },
          { word: 'Docker', count: 28 },
          { word: 'API', count: 25 },
        ],
        accuracyRate: 0.94,
        totalCorrections: 156,
      },
    };

    setStats(mockStats);
  };

  const loadContextData = async () => {
    // Mock data - replace with actual API call
    const mockContext: ContextData = {
      vocabulary: ['TypeScript', 'React', 'Component', 'Docker', 'Kubernetes'],
      context: {
        shell: {
          recent_commands: [
            'git status',
            'npm run build',
            'docker-compose up',
            'kubectl get pods',
            'npm test',
          ],
          command_count: 5,
          unique_commands: 5,
          timestamp: Date.now(),
        },
        clipboard: {
          recent_entries: [
            'React.Component',
            'useState hook',
            'TypeScript interface',
          ],
          entry_count: 3,
          timestamp: Date.now(),
        },
        window: {
          application: 'VSCode',
          title: 'App.tsx - MyProject',
          metadata: {
            class: 'code',
            workspace: 'MyProject',
          },
          timestamp: Date.now(),
        },
      },
    };

    setContextData(mockContext);
  };

  const loadPerformanceMetrics = async () => {
    // Mock data - replace with actual API call
    setPerformanceMetrics({
      totalMatches: 1847,
      accuracyRate: 0.94,
      falsePositives: 12,
      recentlyUsed: ['TypeScript', 'React', 'Docker'],
      topCategories: [
        { name: 'Technical Terms', count: 156, trend: 'up' },
        { name: 'Programming', count: 142, trend: 'stable' },
        { name: 'System Admin', count: 89, trend: 'down' },
        { name: 'Development', count: 201, trend: 'up' },
      ],
    });
  };

  const loadEffectivenessData = async () => {
    // Mock data - replace with actual API call
    const mockData: KeywordEffectiveness[] = [
      {
        word: 'TypeScript',
        category: 'Programming',
        matches: 45,
        corrections: 2,
        accuracy: 0.96,
        lastUsed: Date.now(),
        trend: 'up',
      },
      {
        word: 'Kubernetes',
        category: 'DevOps',
        matches: 32,
        corrections: 1,
        accuracy: 0.97,
        lastUsed: Date.now() - 1000,
        trend: 'up',
      },
      {
        word: 'Docker',
        category: 'DevOps',
        matches: 28,
        corrections: 3,
        accuracy: 0.89,
        lastUsed: Date.now() - 2000,
        trend: 'stable',
      },
    ];

    setEffectivenessData(mockData);
  };

  const handleRefresh = useCallback(() => {
    loadDashboardData();
    toast.success('Dashboard refreshed');
  }, []);

  const handleExportVocabulary = useCallback(async () => {
    try {
      const exportData = {
        vocabularies: stats?.vocabularies,
        settings: integrationSettings,
        timestamp: Date.now(),
        version: '1.0.0',
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `hypr-voice-vocabulary-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success('Vocabulary exported successfully');
    } catch (error) {
      toast.error('Failed to export vocabulary');
      console.error(error);
    }
  }, [stats, integrationSettings]);

  const handleImportVocabulary = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text);

      // Validate import data
      if (!data.vocabularies) {
        throw new Error('Invalid vocabulary file format');
      }

      toast.success('Vocabulary imported successfully');
      loadDashboardData();
    } catch (error) {
      toast.error('Failed to import vocabulary');
      console.error(error);
    } finally {
      event.target.value = '';
    }
  }, []);

  const handleTestVocabulary = useCallback(() => {
    if (!testInput.trim()) {
      toast.error('Please enter text to test');
      return;
    }

    const words = testInput.split(/\s+/);
    const results: TestResult[] = words.map((word) => {
      const cleanWord = word.replace(/[^\w]/g, '');
      const isMatch = stats?.usageStats?.mostUsed.some((w) =>
        w.word.toLowerCase() === cleanWord.toLowerCase()
      );

      return {
        word: cleanWord,
        matched: !!isMatch,
        confidence: isMatch ? 0.95 : 0.3,
        suggestions: isMatch ? [] : ['Check spelling', 'Add to vocabulary'],
        timestamp: Date.now(),
      };
    });

    setTestResults(results);
    toast.success(`Tested ${results.length} words`);
  }, [testInput, stats]);

  const handleCopyVocabulary = useCallback(async () => {
    if (!stats?.currentVocabulary) return;

    try {
      const vocabList = Object.entries(stats.vocabularies)
        .filter(([id, vocab]) => showInactive || id === stats.currentVocabulary)
        .map(([id, vocab]) => `${id}: ${vocab.name} (${vocab.totalKeywords} words)`)
        .join('\n');

      await navigator.clipboard.writeText(vocabList);
      toast.success('Vocabulary list copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  }, [stats, showInactive]);

  const getAccuracyColor = (rate: number) => {
    if (rate >= 0.9) return 'text-green-500';
    if (rate >= 0.7) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const filteredVocabularies = stats?.vocabularies
    ? Object.entries(stats.vocabularies).filter(([id, vocab]) => {
        if (!showInactive && id !== stats.currentVocabulary) return false;
        if (searchQuery && !vocab.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
      })
    : [];

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-96 glass rounded-xl">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading vocabulary dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Vocabulary Dashboard</h2>
            <p className="text-muted-foreground mt-1">
              Comprehensive vocabulary management and analytics
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleExportVocabulary}
                  className="glass-hover"
                >
                  <Download className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Export vocabulary</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <label htmlFor="import-vocab" className="cursor-pointer">
                  <Button
                    variant="outline"
                    size="icon"
                    className="glass-hover"
                    asChild
                  >
                    <span>
                      <Upload className="h-4 w-4" />
                    </span>
                  </Button>
                  <input
                    id="import-vocab"
                    type="file"
                    accept=".json"
                    onChange={handleImportVocabulary}
                    className="hidden"
                  />
                </label>
              </TooltipTrigger>
              <TooltipContent>Import vocabulary</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="glass-hover"
                >
                  <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Refresh data</TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="glass glass-hover border-border/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Vocabularies</CardTitle>
              <Database className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.totalVocabularies || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {Object.keys(stats?.vocabularies || {}).length} loaded configurations
              </p>
            </CardContent>
          </Card>

          <Card className="glass glass-hover border-border/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Keywords</CardTitle>
              <Activity className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.activeKeywords || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Currently in use
              </p>
            </CardContent>
          </Card>

          <Card className="glass glass-hover border-border/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Accuracy Rate</CardTitle>
              <BarChart3 className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getAccuracyColor(performanceMetrics.accuracyRate)}`}>
                {(performanceMetrics.accuracyRate * 100).toFixed(1)}%
              </div>
              <Progress
                value={performanceMetrics.accuracyRate * 100}
                className="mt-2 h-2"
              />
            </CardContent>
          </Card>

          <Card className="glass glass-hover border-border/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current App</CardTitle>
              <Settings className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold truncate">
                {stats?.currentApplication || 'None'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats?.currentVocabulary || 'Global'} vocabulary
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="glass p-1">
            <TabsTrigger value="overview" className="data-[state=active]:glass">
              Overview
            </TabsTrigger>
            <TabsTrigger value="context" className="data-[state=active]:glass">
              Context-Aware
            </TabsTrigger>
            <TabsTrigger value="applications" className="data-[state=active]:glass">
              Applications
            </TabsTrigger>
            <TabsTrigger value="testing" className="data-[state=active]:glass">
              Testing
            </TabsTrigger>
            <TabsTrigger value="performance" className="data-[state=active]:glass">
              Performance
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:glass">
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <Card className="glass border-border/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Vocabulary Overview</CardTitle>
                    <CardDescription>
                      Manage and configure your vocabulary configurations
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowInactive(!showInactive)}
                      className="glass-hover"
                    >
                      {showInactive ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
                      {showInactive ? 'Hide Inactive' : 'Show All'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCopyVocabulary}
                      className="glass-hover"
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Copy List
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredVocabularies.length > 0 ? (
                    filteredVocabularies.map(([id, vocab]) => (
                      <div
                        key={id}
                        className="flex items-center justify-between p-4 rounded-lg glass-hover border border-border/30"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold">{vocab.name}</h4>
                            <Badge variant={id === stats?.currentVocabulary ? 'default' : 'secondary'}>
                              {vocab.totalKeywords} words
                            </Badge>
                            {id === stats?.currentVocabulary && (
                              <Badge variant="outline" className="text-green-500">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Active
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{vocab.description}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Select value={selectedVocabulary} onValueChange={setSelectedVocabulary}>
                            <SelectTrigger className="w-32 glass">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="global">Global</SelectItem>
                              <SelectItem value="vscode">VSCode</SelectItem>
                              <SelectItem value="terminal">Terminal</SelectItem>
                              <SelectItem value="browser">Browser</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No vocabularies found
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Most Used Keywords */}
            {stats?.usageStats?.mostUsed && stats.usageStats.mostUsed.length > 0 && (
              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle>Most Used Keywords</CardTitle>
                  <CardDescription>
                    Top keywords by usage frequency
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {stats.usageStats.mostUsed.slice(0, 10).map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-3 rounded-lg glass-hover border border-border/30">
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className="w-8 justify-center">
                            {index + 1}
                          </Badge>
                          <span className="font-mono text-sm">{item.word}</span>
                        </div>
                        <Badge variant="secondary" className="glass">
                          {item.count} uses
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Context-Aware Tab */}
          <TabsContent value="context" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Terminal className="h-5 w-5 text-primary" />
                    Shell History
                  </CardTitle>
                  <CardDescription>
                    Keywords from recent shell commands
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Recent Commands</span>
                    <Badge variant="secondary" className="glass">
                      {contextData?.context.shell.command_count || 0}
                    </Badge>
                  </div>
                  <Separator className="bg-border/50" />
                  <ScrollArea className="h-[200px] pr-4">
                    <div className="space-y-2">
                      {contextData?.context.shell.recent_commands.map((command, index) => (
                        <div
                          key={index}
                          className="p-2 bg-muted/20 rounded text-sm font-mono border border-border/30"
                        >
                          {command}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                  <div className="flex items-center gap-2 pt-2">
                    <Switch
                      checked={integrationSettings.shellHistory.enabled}
                      onCheckedChange={(checked) =>
                        setIntegrationSettings((prev) => ({
                          ...prev,
                          shellHistory: { ...prev.shellHistory, enabled: checked },
                        }))
                      }
                    />
                    <Label className="text-sm">Enable shell history extraction</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clipboard className="h-5 w-5 text-primary" />
                    Clipboard History
                  </CardTitle>
                  <CardDescription>
                    Keywords from clipboard entries
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Recent Entries</span>
                    <Badge variant="secondary" className="glass">
                      {contextData?.context.clipboard.entry_count || 0}
                    </Badge>
                  </div>
                  <Separator className="bg-border/50" />
                  <ScrollArea className="h-[200px] pr-4">
                    <div className="space-y-2">
                      {contextData?.context.clipboard.recent_entries.map((entry, index) => (
                        <div
                          key={index}
                          className="p-2 bg-muted/20 rounded text-sm border border-border/30 break-all"
                        >
                          {entry}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                  <div className="flex items-center gap-2 pt-2">
                    <Switch
                      checked={integrationSettings.clipboardHistory.enabled}
                      onCheckedChange={(checked) =>
                        setIntegrationSettings((prev) => ({
                          ...prev,
                          clipboardHistory: { ...prev.clipboardHistory, enabled: checked },
                        }))
                      }
                    />
                    <Label className="text-sm">Enable clipboard extraction</Label>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Extracted Vocabulary */}
            <Card className="glass border-border/50">
              <CardHeader>
                <CardTitle>Extracted Vocabulary</CardTitle>
                <CardDescription>
                  Technical terms extracted from context sources
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {contextData?.vocabulary && contextData.vocabulary.length > 0 ? (
                    contextData.vocabulary.map((word, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="font-mono glass-hover px-3 py-1"
                      >
                        {word}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No vocabulary extracted yet. Try using different applications or commands.
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Applications Tab */}
          <TabsContent value="applications" className="space-y-4">
            <Card className="glass border-border/50">
              <CardHeader>
                <CardTitle>Application Detection</CardTitle>
                <CardDescription>
                  Current active application and matched vocabulary
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Current Application</Label>
                    <div className="p-3 rounded-lg glass border border-border/30">
                      <div className="font-semibold">{stats?.currentApplication || 'Not detected'}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Window class detection
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Active Vocabulary</Label>
                    <div className="p-3 rounded-lg glass border border-border/30">
                      <div className="font-semibold">{stats?.currentVocabulary || 'Global'}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Auto-matched vocabulary
                      </div>
                    </div>
                  </div>
                </div>

                <Separator className="bg-border/50" />

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Window Detection</Label>
                    <Switch
                      checked={integrationSettings.windowDetection.enabled}
                      onCheckedChange={(checked) =>
                        setIntegrationSettings((prev) => ({
                          ...prev,
                          windowDetection: { ...prev.windowDetection, enabled: checked },
                        }))
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Auto-switch vocabularies</Label>
                    <Switch
                      checked={integrationSettings.windowDetection.autoSwitch}
                      onCheckedChange={(checked) =>
                        setIntegrationSettings((prev) => ({
                          ...prev,
                          windowDetection: { ...prev.windowDetection, autoSwitch: checked },
                        }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Detection Sensitivity</Label>
                    <div className="flex items-center gap-4">
                      <Slider
                        value={[integrationSettings.windowDetection.sensitivity]}
                        onValueChange={([value]) =>
                          setIntegrationSettings((prev) => ({
                            ...prev,
                            windowDetection: { ...prev.windowDetection, sensitivity: value },
                          }))
                        }
                        max={1}
                        min={0.1}
                        step={0.1}
                        className="flex-1"
                      />
                      <span className="text-sm font-mono w-12 text-right">
                        {(integrationSettings.windowDetection.sensitivity * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pt-2 text-xs text-muted-foreground">
                  Last update: {new Date(lastUpdate).toLocaleTimeString()}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Testing Tab */}
          <TabsContent value="testing" className="space-y-4">
            <Card className="glass border-border/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TestTube className="h-5 w-5 text-primary" />
                  Real-time Vocabulary Testing
                </CardTitle>
                <CardDescription>
                  Test how well vocabulary recognizes technical terms
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter text to test vocabulary recognition..."
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    className="flex-1 glass"
                    onKeyDown={(e) => e.key === 'Enter' && handleTestVocabulary()}
                  />
                  <Button onClick={handleTestVocabulary} className="glow-hover">
                    <TestTube className="h-4 w-4 mr-2" />
                    Test
                  </Button>
                </div>

                {testResults.length > 0 && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Test Results</Label>
                    <div className="space-y-2">
                      {testResults.map((result, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border ${
                            result.matched
                              ? 'bg-green-500/10 border-green-500/30'
                              : 'bg-muted/20 border-border/30'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-mono text-sm">{result.word}</span>
                            <div className="flex items-center gap-2">
                              <Badge
                                variant={result.matched ? 'default' : 'secondary'}
                                className="glass"
                              >
                                {result.matched ? (
                                  <>
                                    <CheckCircle className="h-3 w-3 mr-1" />
                                    Matched
                                  </>
                                ) : (
                                  <>
                                    <XCircle className="h-3 w-3 mr-1" />
                                    Not Found
                                  </>
                                )}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {Math.round(result.confidence * 100)}%
                              </span>
                            </div>
                          </div>
                          {result.suggestions.length > 0 && (
                            <div className="text-xs text-muted-foreground">
                              {result.suggestions.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-4">
            {/* Metrics Overview */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle className="text-lg">Total Matches</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{performanceMetrics.totalMatches}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Successful keyword matches
                  </p>
                </CardContent>
              </Card>

              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle className="text-lg">Accuracy</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-3xl font-bold ${getAccuracyColor(performanceMetrics.accuracyRate)}`}>
                    {(performanceMetrics.accuracyRate * 100).toFixed(1)}%
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Recognition accuracy rate
                  </p>
                </CardContent>
              </Card>

              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle className="text-lg">False Positives</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{performanceMetrics.falsePositives}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Incorrect matches
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Category Performance */}
            <Card className="glass border-border/50">
              <CardHeader>
                <CardTitle>Category Performance</CardTitle>
                <CardDescription>
                  Keyword usage by category with trends
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {performanceMetrics.topCategories.map((category, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{category.name}</span>
                          {getTrendIcon(category.trend)}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">{category.count} matches</span>
                          <Badge variant="outline" className="glass">
                            {category.trend}
                          </Badge>
                        </div>
                      </div>
                      <Progress
                        value={(category.count / performanceMetrics.totalMatches) * 100}
                        className="h-2"
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Keyword Effectiveness */}
            <Card className="glass border-border/50">
              <CardHeader>
                <CardTitle>Keyword Effectiveness</CardTitle>
                <CardDescription>
                  Individual keyword performance metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px] pr-4">
                  <div className="space-y-3">
                    {effectivenessData.map((item, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 rounded-lg glass-hover border border-border/30"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-sm">{item.word}</span>
                            <Badge variant="outline" className="glass">
                              {item.category}
                            </Badge>
                            {getTrendIcon(item.trend)}
                          </div>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{item.matches} matches</span>
                            <span>{item.corrections} corrections</span>
                            <span className={getAccuracyColor(item.accuracy)}>
                              {Math.round(item.accuracy * 100)}% accuracy
                            </span>
                          </div>
                        </div>
                        <div className="w-24">
                          <Progress value={item.accuracy * 100} className="h-2" />
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-4">
            <Card className="glass border-border/50">
              <CardHeader>
                <CardTitle>Integration Settings</CardTitle>
                <CardDescription>
                  Configure how vocabulary interacts with system data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Shell History Settings */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-base font-semibold">Shell History Integration</Label>
                      <p className="text-sm text-muted-foreground">
                        Extract keywords from shell command history
                      </p>
                    </div>
                    <Switch
                      checked={integrationSettings.shellHistory.enabled}
                      onCheckedChange={(checked) =>
                        setIntegrationSettings((prev) => ({
                          ...prev,
                          shellHistory: { ...prev.shellHistory, enabled: checked },
                        }))
                      }
                    />
                  </div>

                  {integrationSettings.shellHistory.enabled && (
                    <div className="ml-6 space-y-3 pl-4 border-l border-border/50">
                      <div className="space-y-2">
                        <Label className="text-sm">Max History Entries</Label>
                        <Input
                          type="number"
                          value={integrationSettings.shellHistory.maxEntries}
                          onChange={(e) =>
                            setIntegrationSettings((prev) => ({
                              ...prev,
                              shellHistory: {
                                ...prev.shellHistory,
                                maxEntries: parseInt(e.target.value),
                              },
                            }))
                          }
                          className="w-32 glass"
                          min={10}
                          max={1000}
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={integrationSettings.shellHistory.extractKeywords}
                          onCheckedChange={(checked) =>
                            setIntegrationSettings((prev) => ({
                              ...prev,
                              shellHistory: { ...prev.shellHistory, extractKeywords: checked },
                            }))
                          }
                        />
                        <Label className="text-sm">Extract technical keywords</Label>
                      </div>
                    </div>
                  )}
                </div>

                <Separator className="bg-border/50" />

                {/* Clipboard Settings */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-base font-semibold">Clipboard Integration</Label>
                      <p className="text-sm text-muted-foreground">
                        Extract keywords from clipboard history
                      </p>
                    </div>
                    <Switch
                      checked={integrationSettings.clipboardHistory.enabled}
                      onCheckedChange={(checked) =>
                        setIntegrationSettings((prev) => ({
                          ...prev,
                          clipboardHistory: { ...prev.clipboardHistory, enabled: checked },
                        }))
                      }
                    />
                  </div>

                  {integrationSettings.clipboardHistory.enabled && (
                    <div className="ml-6 space-y-3 pl-4 border-l border-border/50">
                      <div className="space-y-2">
                        <Label className="text-sm">Max Clipboard Entries</Label>
                        <Input
                          type="number"
                          value={integrationSettings.clipboardHistory.maxEntries}
                          onChange={(e) =>
                            setIntegrationSettings((prev) => ({
                              ...prev,
                              clipboardHistory: {
                                ...prev.clipboardHistory,
                                maxEntries: parseInt(e.target.value),
                              },
                            }))
                          }
                          className="w-32 glass"
                          min={1}
                          max={50}
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={integrationSettings.clipboardHistory.extractKeywords}
                          onCheckedChange={(checked) =>
                            setIntegrationSettings((prev) => ({
                              ...prev,
                              clipboardHistory: {
                                ...prev.clipboardHistory,
                                extractKeywords: checked,
                              },
                            }))
                          }
                        />
                        <Label className="text-sm">Extract technical keywords</Label>
                      </div>
                    </div>
                  )}
                </div>

                <Separator className="bg-border/50" />

                {/* Window Detection Settings */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-base font-semibold">Window Detection</Label>
                      <p className="text-sm text-muted-foreground">
                        Automatically switch vocabularies based on active window
                      </p>
                    </div>
                    <Switch
                      checked={integrationSettings.windowDetection.enabled}
                      onCheckedChange={(checked) =>
                        setIntegrationSettings((prev) => ({
                          ...prev,
                          windowDetection: { ...prev.windowDetection, enabled: checked },
                        }))
                      }
                    />
                  </div>

                  {integrationSettings.windowDetection.enabled && (
                    <div className="ml-6 space-y-3 pl-4 border-l border-border/50">
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={integrationSettings.windowDetection.autoSwitch}
                          onCheckedChange={(checked) =>
                            setIntegrationSettings((prev) => ({
                              ...prev,
                              windowDetection: { ...prev.windowDetection, autoSwitch: checked },
                            }))
                          }
                        />
                        <Label className="text-sm">Auto-switch vocabularies</Label>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm">Detection Sensitivity</Label>
                        <div className="flex items-center gap-4">
                          <Slider
                            value={[integrationSettings.windowDetection.sensitivity]}
                            onValueChange={([value]) =>
                              setIntegrationSettings((prev) => ({
                                ...prev,
                                windowDetection: { ...prev.windowDetection, sensitivity: value },
                              }))
                            }
                            max={1}
                            min={0.1}
                            step={0.1}
                            className="flex-1"
                          />
                          <span className="text-sm font-mono w-12 text-right">
                            {(integrationSettings.windowDetection.sensitivity * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Save Settings Button */}
            <Button
              onClick={() => {
                onConfigChange?.(integrationSettings as any);
                toast.success('Settings saved successfully');
              }}
              className="w-full glow-hover"
              size="lg"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Settings
            </Button>
          </TabsContent>
        </Tabs>
      </div>
    </TooltipProvider>
  );
}
