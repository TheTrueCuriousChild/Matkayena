import apiClient from './client';
import type { Customer, Customer360Response } from '../types';

export async function listCustomers(limit = 50): Promise<Customer[]> {
  const res = await apiClient.get<Customer[]>('/api/v1/customers', { params: { limit } });
  return res.data;
}

export async function getCustomer360(customerId: string): Promise<Customer360Response> {
  const res = await apiClient.get<Customer360Response>(`/api/v1/customers/${customerId}`);
  return res.data;
}
