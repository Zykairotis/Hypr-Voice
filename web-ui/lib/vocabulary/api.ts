// Vocabulary Management API
import {
  VocabularyConfig,
  VocabularyStatistics,
  ApplicationContext,
  ContextData,
  VocabularyPreset,
  VocabularyWord
} from './types';

export class VocabularyAPI {
  private baseUrl = '/api/vocabulary';

  async getVocabularies(): Promise<VocabularyConfig[]> {
    const response = await fetch(`${this.baseUrl}`);
    if (!response.ok) throw new Error('Failed to fetch vocabularies');
    return response.json();
  }

  async getVocabulary(id: string): Promise<VocabularyConfig> {
    const response = await fetch(`${this.baseUrl}/${id}`);
    if (!response.ok) throw new Error(`Failed to fetch vocabulary: ${id}`);
    return response.json();
  }

  async createVocabulary(vocab: Omit<VocabularyConfig, 'name'> & { name: string }): Promise<VocabularyConfig> {
    const response = await fetch(`${this.baseUrl}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(vocab),
    });
    if (!response.ok) throw new Error('Failed to create vocabulary');
    return response.json();
  }

  async updateVocabulary(id: string, vocab: Partial<VocabularyConfig>): Promise<VocabularyConfig> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(vocab),
    });
    if (!response.ok) throw new Error('Failed to update vocabulary');
    return response.json();
  }

  async deleteVocabulary(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete vocabulary');
  }

  async getStatistics(): Promise<VocabularyStatistics> {
    const response = await fetch(`${this.baseUrl}/statistics`);
    if (!response.ok) throw new Error('Failed to fetch statistics');
    return response.json();
  }

  async getCurrentContext(): Promise<ContextData> {
    const response = await fetch(`${this.baseUrl}/context`);
    if (!response.ok) throw new Error('Failed to fetch context');
    return response.json();
  }

  async getApplicationContext(): Promise<ApplicationContext> {
    const response = await fetch(`${this.baseUrl}/application`);
    if (!response.ok) throw new Error('Failed to fetch application context');
    return response.json();
  }

  async forceVocabularyUpdate(appName?: string, appTitle?: string): Promise<void> {
    await fetch(`${this.baseUrl}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appName, appTitle }),
    });
  }

  async addWords(vocabularyId: string, words: VocabularyWord[]): Promise<void> {
    await fetch(`${this.baseUrl}/${vocabularyId}/words`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ words }),
    });
  }

  async removeWords(vocabularyId: string, wordIds: string[]): Promise<void> {
    await fetch(`${this.baseUrl}/${vocabularyId}/words`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ wordIds }),
    });
  }

  async bulkImport(vocabularyId: string, data: string, format: 'csv' | 'json' | 'yaml'): Promise<{ imported: number; errors: string[] }> {
    const response = await fetch(`${this.baseUrl}/${vocabularyId}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data, format }),
    });
    if (!response.ok) throw new Error('Failed to import vocabulary');
    return response.json();
  }

  async exportVocabulary(vocabularyId: string, format: 'csv' | 'json' | 'yaml'): Promise<string> {
    const response = await fetch(`${this.baseUrl}/${vocabularyId}/export?format=${format}`);
    if (!response.ok) throw new Error('Failed to export vocabulary');
    return response.text();
  }

  async getPresets(): Promise<VocabularyPreset[]> {
    const response = await fetch(`${this.baseUrl}/presets`);
    if (!response.ok) throw new Error('Failed to fetch presets');
    return response.json();
  }

  async createPreset(name: string, vocabularyId: string, description?: string): Promise<VocabularyPreset> {
    const response = await fetch(`${this.baseUrl}/presets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, vocabularyId, description }),
    });
    if (!response.ok) throw new Error('Failed to create preset');
    return response.json();
  }

  async applyPreset(presetId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/presets/${presetId}/apply`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to apply preset');
  }

  async getKeywordMatches(text: string): Promise<Array<{ word: string; match: string; confidence: number }>> {
    const response = await fetch(`${this.baseUrl}/matches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) throw new Error('Failed to get matches');
    return response.json();
  }

  async validateVocabulary(vocabularyId: string): Promise<{ isValid: boolean; errors: string[]; warnings: string[] }> {
    const response = await fetch(`${this.baseUrl}/${vocabularyId}/validate`);
    if (!response.ok) throw new Error('Failed to validate vocabulary');
    return response.json();
  }
}

export const vocabularyAPI = new VocabularyAPI();
