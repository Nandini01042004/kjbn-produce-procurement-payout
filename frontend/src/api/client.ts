import {
  Farmer,
  Crop,
  PriceListEntry,
  Delivery,
  DeliveryPreviewResponse,
  Payout,
  FarmerLedger,
  Advance,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Memory / localStorage key for reviewer test clock override
const CLOCK_KEY = 'kjbn_test_clock_override';

export function getStoredTestClock(): string | null {
  return localStorage.getItem(CLOCK_KEY);
}

export function setStoredTestClock(val: string | null) {
  if (val) {
    localStorage.setItem(CLOCK_KEY, val);
  } else {
    localStorage.removeItem(CLOCK_KEY);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');

  const testClock = getStoredTestClock();
  if (testClock) {
    headers.set('X-Test-Clock', testClock);
  }

  const response = await fetch(url, { ...options, headers });
  const data = await response.json();

  if (!response.ok) {
    const errorInfo = data?.error || {
      code: 'HTTP_ERROR',
      message: response.statusText || 'Request failed',
    };
    const err = new Error(errorInfo.message) as Error & { code?: string; details?: any; requestId?: string };
    err.code = errorInfo.code;
    err.details = errorInfo.details;
    err.requestId = errorInfo.request_id;
    throw err;
  }

  return data as T;
}

export const api = {
  // Health & Admin
  getHealth: () => request<{ status: string; database: string; clock: { utc: string; ist: string } }>('/health'),
  resetSeed: () => request<{ status: string; message: string }>('/admin/reset-seed', { method: 'POST' }),

  // Farmers
  getFarmers: (search?: string) => request<Farmer[]>(`/farmers${search ? `?search=${encodeURIComponent(search)}` : ''}`),
  getFarmer: (id: number) => request<Farmer>(`/farmers/${id}`),
  createFarmer: (data: Partial<Farmer>) => request<Farmer>('/farmers', { method: 'POST', body: JSON.stringify(data) }),
  getFarmerLedger: (id: number) => request<FarmerLedger>(`/farmers/${id}/ledger`),

  // Crops
  getCrops: () => request<Crop[]>('/crops'),
  createCrop: (data: Partial<Crop>) => request<Crop>('/crops', { method: 'POST', body: JSON.stringify(data) }),

  // Price Lists
  getPriceLists: (cropId?: number, grade?: string) => {
    const params = new URLSearchParams();
    if (cropId) params.set('crop_id', cropId.toString());
    if (grade) params.set('grade', grade);
    const qs = params.toString();
    return request<PriceListEntry[]>(`/price-lists${qs ? `?${qs}` : ''}`);
  },
  createPriceList: (data: { crop_id: number; grade: string; price_per_kg: string; effective_from: string }) =>
    request<PriceListEntry>('/price-lists', { method: 'POST', body: JSON.stringify(data) }),
  getPriceHistory: (cropId: number, grade: string) =>
    request<PriceListEntry[]>(`/price-lists/history?crop_id=${cropId}&grade=${encodeURIComponent(grade)}`),

  // Deliveries
  previewDelivery: (data: { crop_id: number; grade: string; gross_weight_kg: string; moisture: string; delivered_on: string }) =>
    request<DeliveryPreviewResponse>('/deliveries/preview', { method: 'POST', body: JSON.stringify(data) }),
  createDelivery: (data: any) =>
    request<Delivery>('/deliveries', { method: 'POST', body: JSON.stringify(data) }),
  getDeliveries: (farmerId?: number, unassignedOnly?: boolean) => {
    const params = new URLSearchParams();
    if (farmerId) params.set('farmer_id', farmerId.toString());
    if (unassignedOnly) params.set('unassigned_only', 'true');
    const qs = params.toString();
    return request<Delivery[]>(`/deliveries${qs ? `?${qs}` : ''}`);
  },

  // Advances
  getAdvances: (farmerId?: number) =>
    request<Advance[]>(`/advances${farmerId ? `?farmer_id=${farmerId}` : ''}`),
  issueAdvance: (data: { farmer_id: number; amount: string; given_on: string; notes?: string }) =>
    request<Advance>('/advances', { method: 'POST', body: JSON.stringify(data) }),

  // Payouts
  getPayouts: (farmerId?: number, status?: string) => {
    const params = new URLSearchParams();
    if (farmerId) params.set('farmer_id', farmerId.toString());
    if (status) params.set('status', status);
    const qs = params.toString();
    return request<Payout[]>(`/payouts${qs ? `?${qs}` : ''}`);
  },
  getPayout: (id: number) => request<Payout>(`/payouts/${id}`),
  generatePayout: (farmer_id: number, for_date: string) =>
    request<Payout>('/payouts/generate', { method: 'POST', body: JSON.stringify({ farmer_id, for_date }) }),
  finalisePayout: (id: number) =>
    request<Payout>(`/payouts/${id}/finalise`, { method: 'POST' }),
  markPayoutPaid: (id: number) =>
    request<Payout>(`/payouts/${id}/mark-paid`, { method: 'POST' }),
};
