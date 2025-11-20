import { NextResponse } from 'next/server';

export async function GET() {
  const analytics = {
    overview: {
      total_skills: 24,
      enabled_skills: 18,
      total_executions: 12453,
      successful_executions: 11876,
      average_success_rate: 95.4
    },
    skills: [
      {
        skill_id: 'file_operations',
        name: 'File Operations',
        executions: 1245,
        success_rate: 98.5,
        avg_time: 120
      },
      {
        skill_id: 'bash_execution',
        name: 'Bash Execution',
        executions: 892,
        success_rate: 96.8,
        avg_time: 450
      },
      {
        skill_id: 'voice_synthesis',
        name: 'Voice Synthesis',
        executions: 543,
        success_rate: 99.2,
        avg_time: 2100
      }
    ],
    most_used_skills: [
      { name: 'file_operations', count: 1245 },
      { name: 'bash_execution', count: 892 },
      { name: 'voice_synthesis', count: 543 },
      { name: 'web_scraper', count: 234 }
    ],
    recent_activity: [
      {
        timestamp: new Date().toISOString(),
        skill: 'file_operations',
        status: 'completed',
        duration: 95
      },
      {
        timestamp: new Date(Date.now() - 30000).toISOString(),
        skill: 'bash_execution',
        status: 'completed',
        duration: 420
      },
      {
        timestamp: new Date(Date.now() - 60000).toISOString(),
        skill: 'voice_synthesis',
        status: 'failed',
        duration: 50,
        error: 'Invalid voice parameter'
      }
    ]
  };

  return NextResponse.json(analytics);
}
