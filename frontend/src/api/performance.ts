import apiClient from './client';
import type { PerformanceSnapshot, Achievement } from '../types';

export async function getRMPerformance(rmId: string, period = '2026-Q3'): Promise<PerformanceSnapshot> {
  const res = await apiClient.get<PerformanceSnapshot>(`/api/v1/performance/${rmId}`, { params: { period } });
  return res.data;
}

export async function listAchievements(rmId?: string): Promise<Achievement[]> {
  const res = await apiClient.get<Achievement[]>('/api/v1/performance/achievements/all', {
    params: rmId ? { rm_id: rmId } : undefined,
  });
  return res.data;
}
