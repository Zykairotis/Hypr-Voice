import { NextResponse } from 'next/server';

export async function GET() {
  const skills = [
    {
      id: 'file_operations',
      name: 'File Operations',
      description: 'Read, write, and manipulate files in the working directory',
      category: 'core',
      version: '1.0.0',
      enabled: true,
      parameters: [
        {
          name: 'operation',
          type: 'string',
          description: 'Operation to perform',
          required: true,
          options: ['read', 'write', 'list', 'delete']
        },
        {
          name: 'path',
          type: 'string',
          description: 'File or directory path',
          required: true
        },
        {
          name: 'content',
          type: 'string',
          description: 'Content to write (for write operation)',
          required: false
        }
      ],
      usage_count: 1245,
      success_rate: 98.5,
      average_execution_time: 120,
      tags: ['filesystem', 'io'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      documentation: 'Comprehensive file operations for reading, writing, listing, and deleting files.',
      examples: [
        {
          title: 'Read a file',
          description: 'Read the contents of a specific file',
          code: 'skill.execute({ operation: "read", path: "/path/to/file.txt" })'
        },
        {
          title: 'Write to a file',
          description: 'Write content to a file',
          code: 'skill.execute({ operation: "write", path: "/path/to/file.txt", content: "Hello World" })'
        }
      ]
    },
    {
      id: 'bash_execution',
      name: 'Bash Execution',
      description: 'Execute bash commands in the agent\'s working directory',
      category: 'core',
      version: '1.0.0',
      enabled: true,
      parameters: [
        {
          name: 'command',
          type: 'string',
          description: 'Bash command to execute',
          required: true
        },
        {
          name: 'timeout',
          type: 'number',
          description: 'Command timeout in seconds',
          required: false,
          default_value: 30
        }
      ],
      usage_count: 892,
      success_rate: 96.8,
      average_execution_time: 450,
      tags: ['shell', 'system', 'process'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      documentation: 'Execute arbitrary bash commands safely within the agent workspace.',
      examples: [
        {
          title: 'List directory contents',
          description: 'List files in current directory',
          code: 'skill.execute({ command: "ls -la" })'
        },
        {
          title: 'Run Python script',
          description: 'Execute a Python script',
          code: 'skill.execute({ command: "python script.py", timeout: 60 })'
        }
      ]
    },
    {
      id: 'voice_synthesis',
      name: 'Voice Synthesis',
      description: 'Convert text to speech using Kokoro TTS',
      category: 'core',
      version: '1.0.0',
      enabled: true,
      parameters: [
        {
          name: 'text',
          type: 'string',
          description: 'Text to synthesize',
          required: true
        },
        {
          name: 'voice',
          type: 'string',
          description: 'Voice to use',
          required: false,
          default_value: 'af_bella',
          options: ['af_bella', 'af_adam', 'af_sarah', 'am_adam', 'am_michael']
        },
        {
          name: 'output_path',
          type: 'string',
          description: 'Output file path',
          required: false
        }
      ],
      usage_count: 543,
      success_rate: 99.2,
      average_execution_time: 2100,
      tags: ['tts', 'audio', 'kokoro'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      documentation: 'High-quality text-to-speech synthesis using Kokoro TTS model.',
      examples: [
        {
          title: 'Basic synthesis',
          description: 'Convert text to speech',
          code: 'skill.execute({ text: "Hello, how are you today?" })'
        },
        {
          title: 'Custom voice',
          description: 'Use a specific voice',
          code: 'skill.execute({ text: "Hello", voice: "af_sarah" })'
        }
      ]
    },
    {
      id: 'web_scraper',
      name: 'Web Scraper',
      description: 'Scrape content from websites',
      category: 'community',
      version: '2.1.0',
      author: 'SkillCraft Community',
      enabled: false,
      parameters: [
        {
          name: 'url',
          type: 'string',
          description: 'URL to scrape',
          required: true
        },
        {
          name: 'selector',
          type: 'string',
          description: 'CSS selector for content',
          required: true
        }
      ],
      usage_count: 2341,
      success_rate: 94.5,
      average_execution_time: 850,
      tags: ['web', 'scrape', 'html'],
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-03-10T00:00:00Z',
      documentation: 'Powerful web scraping tool with CSS selector support.',
      examples: [
        {
          title: 'Scrape article title',
          description: 'Extract article title from news site',
          code: 'skill.execute({ url: "https://example.com/article", selector: "h1.title" })'
        }
      ],
      is_public: true,
      rating: 4.8,
      download_count: 567
    },
    {
      id: 'data_analyzer',
      name: 'Data Analyzer',
      description: 'Analyze and visualize data sets',
      category: 'community',
      version: '1.5.0',
      author: 'DataTools Inc',
      enabled: true,
      parameters: [
        {
          name: 'data',
          type: 'object',
          description: 'Data to analyze',
          required: true
        },
        {
          name: 'analysis_type',
          type: 'string',
          description: 'Type of analysis',
          required: true,
          options: ['statistics', 'correlation', 'regression', 'clustering']
        }
      ],
      usage_count: 678,
      success_rate: 97.3,
      average_execution_time: 1200,
      tags: ['data', 'analysis', 'ml'],
      created_at: '2024-02-01T00:00:00Z',
      updated_at: '2024-03-15T00:00:00Z',
      documentation: 'Comprehensive data analysis with statistical insights and visualizations.',
      examples: [],
      is_public: true,
      rating: 4.6,
      download_count: 234
    }
  ];

  return NextResponse.json({ skills });
}
