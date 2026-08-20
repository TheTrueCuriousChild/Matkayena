import apiClient from './client';
import type { LoginRequest, LoginResponse, User } from '../types';

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const res = await apiClient.post<LoginResponse>('/api/v1/auth/login', data);
  return res.data;
}

export async function getCurrentUser(): Promise<User> {
  const res = await apiClient.get<User>('/api/v1/auth/me');
  return res.data;
}
