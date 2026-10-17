export interface Farmer {
  id: number;
  name: string;
  phone: string;
  village: string;
  bank_reference: string;
  outstanding_advance: string;
  created_at: string;
}

export interface Crop {
  id: number;
  name: string;
  allowed_grades: string[];
  base_moisture_threshold: string;
  max_moisture_accepted: string;
  created_at: string;
}

export interface PriceListEntry {
  id: number;
  crop_id: number;
  crop_name?: string;
  grade: string;
  price_per_kg: string;
  effective_from: string;
  created_at: string;
}

export interface DeliveryBreakdown {
  gross_kg: string;
  deduction_pct: string;
  deduction_kg: string;
  net_kg: string;
  applied_price: string;
  applied_price_list_id: number;
  amount: string;
}

export interface DeliveryPreviewResponse {
  crop_id: number;
  crop_name: string;
  grade: string;
  gross_weight_kg: string;
  moisture: string;
  delivered_on: string;
  breakdown: DeliveryBreakdown;
}

export interface Delivery {
  id: number;
  farmer_id: number;
  farmer_name?: string;
  crop_id: number;
  crop_name?: string;
  grade: string;
  gross_weight_kg: string;
  moisture: string;
  delivered_on: string;
  gross_kg: string;
  deduction_pct: string;
  deduction_kg: string;
  net_kg: string;
  applied_price: string;
  applied_price_list_id: number;
  amount: string;
  payout_id?: number | null;
  reference_delivery_id?: number | null;
  is_credit_debit_note: boolean;
  note_reason?: string | null;
  created_at: string;
}

export interface Advance {
  id: number;
  farmer_id: number;
  farmer_name?: string;
  amount: string;
  given_on: string;
  notes?: string | null;
  created_at: string;
}

export interface Payout {
  id: number;
  farmer_id: number;
  farmer_name?: string;
  farmer_phone?: string;
  farmer_village?: string;
  farmer_bank_ref?: string;
  week_start: string;
  week_end: string;
  gross_amount: string;
  advance_deduction: string;
  net_amount: string;
  status: 'Draft' | 'Finalised' | 'Paid';
  finalised_at?: string | null;
  paid_at?: string | null;
  created_at: string;
  deliveries: Delivery[];
}

export interface FarmerLedger {
  farmer_id: number;
  name: string;
  phone: string;
  village: string;
  bank_reference: string;
  outstanding_advance: string;
  total_deliveries_count: number;
  total_delivered_gross_kg: string;
  total_delivered_net_kg: string;
  total_gross_earnings: string;
  total_advance_deducted: string;
  total_net_paid: string;
  deliveries: Delivery[];
  advances: Advance[];
  payouts: Payout[];
}

export interface ApiError {
  code: string;
  message: string;
  request_id?: string;
  details?: Array<{ field: string; issue: string }> | null;
}
