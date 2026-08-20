import apiClient from './client';
import type { Opportunity } from '../types';

export async function listOpportunities(params?: {
  rm_id?: string;
  customer_id?: string;
  status?: string;
  limit?: number;
}): Promise<Opportunity[]> {
  const res = await apiClient.get<Opportunity[]>('/api/v1/opportunities', { params });
  return res.data;
}

export async function getOpportunity(id: string): Promise<Opportunity> {
  const res = await apiClient.get<Opportunity>(`/api/v1/opportunities/${id}`);
  return res.data;
}

export async function evaluateCustomer(customerId: string): Promise<unknown> {
  const res = await apiClient.post('/api/v1/opportunities/evaluate', { customer_id: customerId });
  return res.data;
}
