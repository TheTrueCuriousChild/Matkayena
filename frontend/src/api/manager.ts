import apiClient from './client';
import type { ManagerAlert } from '../types';

export async function getManagerAlerts(period = '2026-Q1'): Promise<ManagerAlert[]> {
  const res = await apiClient.get<ManagerAlert[]>('/api/v1/manager/alerts', { params: { period } });
  return res.data;
}
