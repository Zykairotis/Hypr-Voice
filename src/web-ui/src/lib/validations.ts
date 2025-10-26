import * as yaml from 'js-yaml';

export interface ValidationResult {
  valid: boolean;
  error?: string;
  line?: number;
  column?: number;
}

export function validateYAML(content: string): ValidationResult {
  try {
    yaml.load(content);
    return { valid: true };
  } catch (error) {
    if (error instanceof Error) {
      // Try to extract line and column information from YAML error
      const match = error.message.match(/at line (\d+)(?:, column (\d+))?/);
      if (match) {
        return {
          valid: false,
          error: error.message,
          line: parseInt(match[1]),
          column: match[2] ? parseInt(match[2]) : undefined,
        };
      }
      return { valid: false, error: error.message };
    }
    return { valid: false, error: 'Invalid YAML syntax' };
  }
}

export function validateApiKey(key: string): ValidationResult {
  if (!key || key.trim().length === 0) {
    return { valid: false, error: 'API key cannot be empty' };
  }

  if (key.length < 10) {
    return { valid: false, error: 'API key appears to be too short' };
  }

  // Basic pattern validation for common API key formats
  const validPatterns = [
    /^[a-zA-Z0-9_-]+$/,  // Alphanumeric with underscores and dashes
    /^sk-[a-zA-Z0-9_-]+$/,  // OpenAI format
    /^xai-[a-zA-Z0-9_-]+$/,  // xAI format
  ];

  const isValidFormat = validPatterns.some(pattern => pattern.test(key));

  if (!isValidFormat) {
    return { valid: false, error: 'API key format appears invalid' };
  }

  return { valid: true };
}

export function validatePort(port: number): ValidationResult {
  if (isNaN(port) || port < 1 || port > 65535) {
    return { valid: false, error: 'Port must be between 1 and 65535' };
  }

  if (port < 1024) {
    return { valid: false, error: 'Ports below 1024 may require administrative privileges' };
  }

  return { valid: true };
}

export function validateTimeout(timeout: number): ValidationResult {
  if (isNaN(timeout) || timeout < 1 || timeout > 300) {
    return { valid: false, error: 'Timeout must be between 1 and 300 seconds' };
  }

  return { valid: true };
}

export function validateSampleRate(sampleRate: number): ValidationResult {
  const validSampleRates = [8000, 16000, 22050, 44100, 48000];

  if (!validSampleRates.includes(sampleRate)) {
    return {
      valid: false,
      error: `Sample rate must be one of: ${validSampleRates.join(', ')} Hz`
    };
  }

  return { valid: true };
}

export function validateLogLevel(level: string): ValidationResult {
  const validLevels = ['debug', 'info', 'warn', 'error'];

  if (!validLevels.includes(level.toLowerCase())) {
    return {
      valid: false,
      error: `Log level must be one of: ${validLevels.join(', ')}`
    };
  }

  return { valid: true };
}