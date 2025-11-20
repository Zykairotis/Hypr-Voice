"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Search,
  Filter,
  Download,
  Star,
  Shield,
  GitFork,
  ExternalLink,
  Clock,
  User,
  Tag,
  TrendingUp,
  Store,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useMCPStore } from "@/lib/mcp-store";
import type { MCPServerStore, MCPServerCategory } from "@/types/mcp";
import { toast } from "sonner";

export default function ServerStore() {
  const { availableServers, loadAvailableServers, installServer, servers } = useMCPStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<MCPServerCategory | "all">("all");
  const [sortBy, setSortBy] = useState<"popular" | "rating" | "newest">("popular");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadAvailableServers();
  }, []);

  const filteredAndSortedServers = availableServers
    .filter((server) => {
      const matchesSearch =
        server.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        server.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        server.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesCategory = categoryFilter === "all" || server.category === categoryFilter;
      return matchesSearch && matchesCategory;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "popular":
          return b.downloads - a.downloads;
        case "rating":
          return b.rating - a.rating;
        case "newest":
          return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
        default:
          return 0;
      }
    });

  const handleInstall = async (serverId: string) => {
    setIsLoading(true);
    try {
      await installServer(serverId);
      toast.success("Server installed successfully");
    } catch (error) {
      toast.error("Failed to install server");
    } finally {
      setIsLoading(false);
    }
  };

  const isInstalled = (serverId: string) => {
    return serverId in servers;
  };

  const categories = [
    { value: "all", label: "All Categories" },
    { value: "filesystem", label: "Filesystem" },
    { value: "github", label: "GitHub" },
    { value: "git", label: "Git" },
    { value: "web", label: "Web" },
    { value: "database", label: "Database" },
    { value: "memory", label: "Memory" },
    { value: "ai", label: "AI" },
    { value: "custom", label: "Custom" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">MCP Server Store</h2>
          <p className="text-muted-foreground">
            Discover and install community-maintained MCP servers
          </p>
        </div>
        <Button variant="outline" onClick={loadAvailableServers}>
          <Download className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search servers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <select
              className="px-3 py-2 bg-background border rounded-md text-sm"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as any)}
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>

            <select
              className="px-3 py-2 bg-background border rounded-md text-sm"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
            >
              <option value="popular">Most Popular</option>
              <option value="rating">Highest Rated</option>
              <option value="newest">Newest</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Featured Servers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-500" />
            Featured Servers
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {availableServers
              .filter((s) => s.verified)
              .slice(0, 3)
              .map((server) => (
                <ServerCard key={server.serverId} server={server} onInstall={handleInstall} isInstalled={isInstalled(server.serverId)} featured />
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Server Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {filteredAndSortedServers.map((server) => (
            <ServerCard
              key={server.serverId}
              server={server}
              onInstall={handleInstall}
              isInstalled={isInstalled(server.serverId)}
              isLoading={isLoading}
            />
          ))}
        </AnimatePresence>
      </div>

      {filteredAndSortedServers.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Store className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No servers found</h3>
            <p className="text-muted-foreground">
              Try adjusting your search or filters
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ServerCard({
  server,
  onInstall,
  isInstalled,
  isLoading = false,
  featured = false,
}: {
  server: MCPServerStore;
  onInstall: (serverId: string) => void;
  isInstalled: boolean;
  isLoading?: boolean;
  featured?: boolean;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <Card className={`cursor-pointer transition-all hover:shadow-lg ${featured ? "ring-2 ring-yellow-500/50" : ""}`}>
        {featured && (
          <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-b border-yellow-500/30 px-4 py-2">
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-yellow-500" />
              <span className="text-sm font-medium text-yellow-500">Featured</span>
            </div>
          </div>
        )}
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {server.verified && (
                <Badge variant="outline" className="text-xs text-blue-500 border-blue-500/30">
                  <Shield className="w-3 h-3 mr-1" />
                  Verified
                </Badge>
              )}
            </div>
            <Badge variant="outline" className="text-xs">
              {server.category}
            </Badge>
          </div>
          <CardTitle className="text-lg">{server.name}</CardTitle>
          <CardDescription className="line-clamp-2">{server.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex flex-wrap gap-1">
              {server.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {server.tags.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{server.tags.length - 3}
                </Badge>
              )}
            </div>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-500" />
                  <span>{server.rating.toFixed(1)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Download className="w-4 h-4 text-blue-500" />
                  <span>{server.downloads.toLocaleString()}</span>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <User className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs">{server.author}</span>
              </div>
            </div>

            <div className="pt-2 border-t">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>Updated {new Date(server.lastUpdated).toLocaleDateString()}</span>
                </div>
                <span>v{server.version}</span>
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              {isInstalled ? (
                <Button size="sm" variant="outline" className="flex-1" disabled>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Installed
                </Button>
              ) : (
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={() => onInstall(server.serverId)}
                  disabled={isLoading}
                >
                  <Download className="w-4 h-4 mr-2" />
                  {isLoading ? "Installing..." : "Install"}
                </Button>
              )}
              <Button size="sm" variant="outline">
                <ExternalLink className="w-4 h-4" />
              </Button>
            </div>

            {server.readme && (
              <div className="pt-2">
                <p className="text-xs text-muted-foreground line-clamp-3">
                  {server.readme}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
