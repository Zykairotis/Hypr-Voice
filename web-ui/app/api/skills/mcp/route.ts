import { NextResponse } from 'next/server';

export async function GET() {
  const mcpServers = [
    {
      id: 'filesystem',
      name: 'Filesystem',
      description: 'File system operations',
      category: 'system',
      enabled: true,
      installed: true,
      config: {
        allowed_directories: ['/workspace', '/tmp']
      },
      auth_required: false,
      version: '1.0.0'
    },
    {
      id: 'github',
      name: 'GitHub',
      description: 'GitHub operations',
      category: 'development',
      enabled: true,
      installed: true,
      config: {
        base_url: 'https://api.github.com'
      },
      auth_required: true,
      auth_config: {
        token: 'GITHUB_TOKEN'
      },
      version: '1.0.0',
      maintainer: 'GitHub',
      homepage: 'https://github.com'
    },
    {
      id: 'git',
      name: 'Git',
      description: 'Git operations',
      category: 'development',
      enabled: false,
      installed: true,
      config: {},
      auth_required: false,
      version: '1.0.0'
    },
    {
      id: 'brave_search',
      name: 'Brave Search',
      description: 'Brave search API',
      category: 'search',
      enabled: false,
      installed: false,
      config: {
        api_version: 'v1'
      },
      auth_required: true,
      auth_config: {
        api_key: 'BRAVE_API_KEY'
      },
      version: '1.0.0',
      maintainer: 'Brave',
      homepage: 'https://search.brave.com'
    },
    {
      id: 'postgres',
      name: 'PostgreSQL',
      description: 'PostgreSQL database operations',
      category: 'database',
      enabled: false,
      installed: false,
      config: {
        connection_string: 'postgresql://user:pass@localhost/db'
      },
      auth_required: true,
      auth_config: {
        connection_string: 'DB_CONNECTION_STRING'
      },
      version: '1.0.0',
      maintainer: 'PostgreSQL Community'
    },
    {
      id: 'mongodb',
      name: 'MongoDB',
      description: 'MongoDB database operations',
      category: 'database',
      enabled: false,
      installed: false,
      config: {
        connection_string: 'mongodb://localhost:27017'
      },
      auth_required: true,
      auth_config: {
        connection_string: 'MONGO_CONNECTION_STRING'
      },
      version: '1.0.0',
      maintainer: 'MongoDB Community'
    }
  ];

  return NextResponse.json({ servers: mcpServers });
}
