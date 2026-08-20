import apiClient from './client';
import type { AuditRecord, AuditVerifyResult, ChainVerifyResult } from '../types';

export async function listAuditRecords(skip = 0, limit = 50): Promise<AuditRecord[]> {
  const res = await apiClient.get<AuditRecord[]>('/api/v1/audit/records', { params: { skip, limit } });
  return res.data;
}

export async function verifyRecord(id: string): Promise<AuditVerifyResult> {
  const res = await apiClient.get<AuditVerifyResult>(`/api/v1/audit/verify/${id}`);
  return res.data;
}

export async function verifyChain(limit = 500): Promise<ChainVerifyResult> {
  const res = await apiClient.get<ChainVerifyResult>('/api/v1/audit/verify-chain', { params: { limit } });
  return res.data;
}
