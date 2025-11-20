export interface Skill {
  id: string;
  name: string;
  description: string;
  category: 'core' | 'custom' | 'mcp' | 'community';
  version: string;
  author?: string;
  enabled: boolean;
  parameters: SkillParameter[];
  dependencies?: string[];
  usage_count: number;
  success_rate: number;
  average_execution_time: number;
  tags: string[];
  created_at: string;
  updated_at: string;
  documentation?: string;
  examples?: SkillExample[];
  is_public?: boolean;
  rating?: number;
  download_count?: number;
}

export interface SkillParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description: string;
  required: boolean;
  default_value?: any;
  options?: string[];
}

export interface SkillExample {
  title: string;
  description: string;
  code: string;
}

export interface SkillExecution {
  id: string;
  skill_id: string;
  agent_id: string;
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  input: any;
  output?: any;
  error?: string;
  duration?: number;
}

export interface MCPServer {
  id: string;
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  installed: boolean;
  config: Record<string, any>;
  auth_required: boolean;
  auth_config?: Record<string, string>;
  version: string;
  maintainer?: string;
  homepage?: string;
}

export interface SkillAnalytics {
  skill_id: string;
  total_executions: number;
  success_count: number;
  failure_count: number;
  average_execution_time: number;
  most_used_parameters: Array<{
    parameter: string;
    value: any;
    count: number;
  }>;
  recent_executions: SkillExecution[];
}

export interface SkillVersion {
  version: string;
  released_at: string;
  changelog: string;
  breaking_changes?: boolean;
}

export interface CommunitySkill extends Skill {
  downloads: number;
  likes: number;
  reviews: CommunityReview[];
  verified: boolean;
}

export interface CommunityReview {
  id: string;
  author: string;
  rating: number;
  comment: string;
  created_at: string;
}

export interface SkillTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  code: string;
  parameters: SkillParameter[];
  estimated_time: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}
