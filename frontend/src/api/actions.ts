import apiClient from './client';
import type {
  Action,
  ActionDetailResponse,
  CompleteActionRequest,
  CompleteActionResponse,
  SnoozeActionRequest,
  ReassignActionRequest,
} from '../types';

export async function listActions(params?: {
  rm_id?: string;
  customer_id?: string;
  status?: string;
  limit?: number;
}): Promise<Action[]> {
  const res = await apiClient.get<Action[]>('/api/v1/actions', { params });
  return res.data;
}

export async function getAction(id: string): Promise<ActionDetailResponse> {
  const res = await apiClient.get<ActionDetailResponse>(`/api/v1/actions/${id}`);
  return res.data;
}

export async function completeAction(id: string, data: CompleteActionRequest): Promise<CompleteActionResponse> {
  const res = await apiClient.post<CompleteActionResponse>(`/api/v1/actions/${id}/complete`, data);
  return res.data;
}

export async function snoozeAction(id: string, data: SnoozeActionRequest): Promise<Action> {
  const res = await apiClient.post<Action>(`/api/v1/actions/${id}/snooze`, data);
  return res.data;
}

export async function reassignAction(id: string, data: ReassignActionRequest): Promise<Action> {
  const res = await apiClient.post<Action>(`/api/v1/actions/${id}/reassign`, data);
  return res.data;
}
