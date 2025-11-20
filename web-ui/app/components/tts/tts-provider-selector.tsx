"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Cloud,
  Wifi,
  Zap,
  Globe,
  HardDrive,
  DollarSign,
  CheckCircle2,
  XCircle,
  AlertTriangle
} from "lucide-react";
import { toast } from "sonner";

interface TTSProviderSelectorProps {
  selectedProvider: string;
  onProviderChange: (provider: string) => void;
}

interface ProviderInfo {
  id: string;
  name: string;
  description: string;
  type: "local" | "cloud";
  quality: "high" | "medium" | "premium";
  cost: "free" | "paid";
  latency: "low" | "medium" | "high";
  languages: string[];
  features: string[];
  status: "available" | "unavailable" | "checking";
  icon: React.ReactNode;
  color: string;
}

export default function TTSProviderSelector({
  selectedProvider,
  onProviderChange,
}: TTSProviderSelectorProps) {
  const [providerStatus, setProviderStatus] = useState<Record<string, "available" | "unavailable" | "checking">>({});

  const providers: ProviderInfo[] = [
    {
      id: "kokoro",
      name: "Kokoro TTS",
      description: "Free, fast, and privacy-focused local TTS with excellent quality",
      type: "local",
      quality: "high",
      cost: "free",
      latency: "low",
      languages: ["English", "Japanese"],
      features: [
        "Real-time synthesis",
        "No internet required",
        "Voice cloning",
        "Emotion control",
        "Pitch/Speed adjustment"
      ],
      status: "checking",
      icon: <HardDrive className="w-6 h-6" />,
      color: "from-blue-500 to-cyan-500"
    },
    {
      id: "deepgram",
      name: "Deepgram TTS",
      description: "Cloud-based TTS with ultra-fast synthesis and natural-sounding voices",
      type: "cloud",
      quality: "high",
      cost: "paid",
      latency: "low",
      languages: ["English", "Spanish", "French", "German"],
      features: [
        "Streaming synthesis",
        "Emotion control",
        "SSML support",
        "Real-time API",
        "Batch processing"
      ],
      status: "checking",
      icon: <Zap className="w-6 h-6" />,
      color: "from-purple-500 to-indigo-500"
    },
    {
      id: "elevenlabs",
      name: "ElevenLabs",
      description: "Premium AI voice cloning with studio-quality output",
      type: "cloud",
      quality: "premium",
      cost: "paid",
      latency: "medium",
      languages: ["English", "Spanish", "French", "German", "Italian"],
      features: [
        "Voice cloning",
        "Emotion control",
        "Style control",
        "SSML support",
        "High-quality output"
      ],
      status: "checking",
      icon: <Globe className="w-6 h-6" />,
      color: "from-orange-500 to-red-500"
    }
  ];

  useEffect(() => {
    checkProviderStatus();
  }, []);

  const checkProviderStatus = async () => {
    for (const provider of providers) {
      try {
        setProviderStatus(prev => ({ ...prev, [provider.id]: "checking" }));

        const response = await fetch(`http://localhost:8934/api/tts/provider/${provider.id}/status`, {
          method: "GET",
        });

        if (response.ok) {
          setProviderStatus(prev => ({ ...prev, [provider.id]: "available" }));
        } else {
          setProviderStatus(prev => ({ ...prev, [provider.id]: "unavailable" }));
        }
      } catch (error) {
        setProviderStatus(prev => ({ ...prev, [provider.id]: "unavailable" }));
      }
    }
  };

  const handleProviderSelect = (providerId: string) => {
    if (providerStatus[providerId] === "available") {
      onProviderChange(providerId);
      toast.success(`Switched to ${providers.find(p => p.id === providerId)?.name}`);
    } else {
      toast.error("Provider is currently unavailable");
    }
  };

  const getStatusIcon = (status: "available" | "unavailable" | "checking") => {
    switch (status) {
      case "available":
        return <CheckCircle2 className="w-5 h-5 text-green-400" />;
      case "unavailable":
        return <XCircle className="w-5 h-5 text-red-400" />;
      case "checking":
        return <AlertTriangle className="w-5 h-5 text-yellow-400 animate-pulse" />;
    }
  };

  const getCostBadge = (cost: "free" | "paid") => {
    return cost === "free" ? (
      <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
        <HardDrive className="w-3 h-3 mr-1" />
        Free
      </Badge>
    ) : (
      <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/50">
        <DollarSign className="w-3 h-3 mr-1" />
        Paid
      </Badge>
    );
  };

  const getLatencyBadge = (latency: "low" | "medium" | "high") => {
    const colors = {
      low: "bg-green-500/20 text-green-400 border-green-500/50",
      medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
      high: "bg-red-500/20 text-red-400 border-red-500/50"
    };

    return (
      <Badge className={colors[latency]}>
        <Wifi className="w-3 h-3 mr-1" />
        {latency.charAt(0).toUpperCase() + latency.slice(1)} Latency
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      {/* Provider Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {providers.map((provider) => {
          const isSelected = selectedProvider === provider.id;
          const status = providerStatus[provider.id] || "checking";

          return (
            <Card
              key={provider.id}
              className={`cursor-pointer transition-all duration-300 glass-hover ${
                isSelected
                  ? "ring-2 ring-primary border-primary"
                  : "border-border/50 hover:border-border"
              } ${
                status === "unavailable" ? "opacity-60" : ""
              }`}
              onClick={() => handleProviderSelect(provider.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-lg bg-gradient-to-br ${provider.color} bg-opacity-20`}
                    >
                      <div className={provider.color.includes("blue") ? "text-blue-400" :
                                     provider.color.includes("purple") ? "text-purple-400" :
                                     "text-orange-400"}>
                        {provider.icon}
                      </div>
                    </div>
                    <div>
                      <CardTitle className="text-lg">{provider.name}</CardTitle>
                      <CardDescription className="text-sm">
                        {provider.description}
                      </CardDescription>
                    </div>
                  </div>
                  {getStatusIcon(status)}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Badges */}
                <div className="flex flex-wrap gap-2">
                  {provider.type === "local" ? (
                    <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">
                      <HardDrive className="w-3 h-3 mr-1" />
                      Local
                    </Badge>
                  ) : (
                    <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50">
                      <Cloud className="w-3 h-3 mr-1" />
                      Cloud
                    </Badge>
                  )}
                  {getCostBadge(provider.cost)}
                  {getLatencyBadge(provider.latency)}
                </div>

                {/* Languages */}
                <div>
                  <div className="text-sm font-medium mb-1">Languages</div>
                  <div className="flex flex-wrap gap-1">
                    {provider.languages.map((lang) => (
                      <Badge key={lang} variant="outline" className="text-xs">
                        {lang}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Features */}
                <div>
                  <div className="text-sm font-medium mb-1">Features</div>
                  <div className="flex flex-wrap gap-1">
                    {provider.features.slice(0, 3).map((feature) => (
                      <Badge key={feature} variant="outline" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                    {provider.features.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{provider.features.length - 3} more
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Select Button */}
                <Button
                  className="w-full"
                  variant={isSelected ? "default" : "outline"}
                  disabled={status !== "available"}
                >
                  {isSelected ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 mr-2" />
                      Selected
                    </>
                  ) : status === "available" ? (
                    "Select Provider"
                  ) : status === "checking" ? (
                    "Checking..."
                  ) : (
                    "Unavailable"
                  )}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Separator />

      {/* Provider Comparison */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="text-lg">Provider Comparison</CardTitle>
          <CardDescription>
            Detailed comparison of available TTS providers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/50">
                  <th className="text-left py-2">Feature</th>
                  <th className="text-center py-2">Kokoro</th>
                  <th className="text-center py-2">Deepgram</th>
                  <th className="text-center py-2">ElevenLabs</th>
                </tr>
              </thead>
              <tbody className="text-muted-foreground">
                <tr className="border-b border-border/30">
                  <td className="py-2 font-medium">Type</td>
                  <td className="text-center py-2">Local</td>
                  <td className="text-center py-2">Cloud</td>
                  <td className="text-center py-2">Cloud</td>
                </tr>
                <tr className="border-b border-border/30">
                  <td className="py-2 font-medium">Latency</td>
                  <td className="text-center py-2">Very Low</td>
                  <td className="text-center py-2">Low</td>
                  <td className="text-center py-2">Medium</td>
                </tr>
                <tr className="border-b border-border/30">
                  <td className="py-2 font-medium">Voice Cloning</td>
                  <td className="text-center py-2">✓</td>
                  <td className="text-center py-2">✗</td>
                  <td className="text-center py-2">✓</td>
                </tr>
                <tr className="border-b border-border/30">
                  <td className="py-2 font-medium">Emotion Control</td>
                  <td className="text-center py-2">✓</td>
                  <td className="text-center py-2">✓</td>
                  <td className="text-center py-2">✓</td>
                </tr>
                <tr>
                  <td className="py-2 font-medium">Cost</td>
                  <td className="text-center py-2">Free</td>
                  <td className="text-center py-2">Paid</td>
                  <td className="text-center py-2">Paid</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
