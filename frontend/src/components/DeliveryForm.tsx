import React, { useState, useEffect } from 'react';
import {
  Truck,
  Calculator,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Scale,
  Droplets,
  FileText,
  Clock,
} from 'lucide-react';
import { api } from '../api/client';
import { Farmer, Crop, DeliveryPreviewResponse, Delivery } from '../types';

export const DeliveryForm: React.FC = () => {
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [crops, setCrops] = useState<Crop[]>([]);
  const [recentDeliveries, setRecentDeliveries] = useState<Delivery[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);



  // Form inputs
  const [farmerId, setFarmerId] = useState<number | ''>('');
  const [cropId, setCropId] = useState<number | ''>('');
  const [grade, setGrade] = useState<string>('');
  const [grossWeight, setGrossWeight] = useState<string>('1000');
  const [moisture, setMoisture] = useState<string>('17.6');
  const [deliveredOn, setDeliveredOn] = useState<string>(() => {
    const now = new Date();
    return now.toISOString().slice(0, 16);
  });

  // Credit / Debit Note correction mode
  const [isNote, setIsNote] = useState<boolean>(false);
  const [refDeliveryId, setRefDeliveryId] = useState<number | ''>('');
  const [noteReason, setNoteReason] = useState<string>('');

  // Live preview state
  const [preview, setPreview] = useState<DeliveryPreviewResponse | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [fData, cData, dData] = await Promise.all([
        api.getFarmers(),
        api.getCrops(),
        api.getDeliveries(),
      ]);
      setFarmers(fData);
      setCrops(cData);
      setRecentDeliveries(dData);
      if (fData.length > 0 && farmerId === '') setFarmerId(fData[0].id);
      if (cData.length > 0 && cropId === '') {
        setCropId(cData[0].id);
        if (cData[0].allowed_grades.length > 0) {
          setGrade(cData[0].allowed_grades[0]);
        }
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const selectedCrop = crops.find((c) => c.id === Number(cropId));

  // Sync grade when crop changes
  useEffect(() => {
    if (selectedCrop && selectedCrop.allowed_grades.length > 0) {
      if (!selectedCrop.allowed_grades.includes(grade)) {
        setGrade(selectedCrop.allowed_grades[0]);
      }
    }
  }, [cropId, selectedCrop]);

  // Trigger live calculation preview whenever input fields change
  useEffect(() => {
    if (!cropId || !grade || !grossWeight || !moisture || !deliveredOn) {
      setPreview(null);
      setPreviewError(null);
      return;
    }

    const grossNum = parseFloat(grossWeight);
    const moistNum = parseFloat(moisture);
    if (isNaN(grossNum) || isNaN(moistNum) || grossNum <= 0 || moistNum <= 0) {
      setPreview(null);
      setPreviewError('Gross weight and moisture must be positive numbers');
      return;
    }

    const debounceTimer = setTimeout(async () => {
      setPreviewLoading(true);
      setPreviewError(null);
      try {
        const isoDate = new Date(deliveredOn).toISOString();
        const res = await api.previewDelivery({
          crop_id: Number(cropId),
          grade,
          gross_weight_kg: grossWeight,
          moisture,
          delivered_on: isoDate,
        });
        setPreview(res);
      } catch (err: any) {
        setPreview(null);
        setPreviewError(err.message || 'Failed to calculate delivery preview');
      } finally {
        setPreviewLoading(false);
      }
    }, 200);

    return () => clearTimeout(debounceTimer);
  }, [cropId, grade, grossWeight, moisture, deliveredOn]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!farmerId || !cropId || !grade || !grossWeight || !moisture) {
      alert('Please fill out all required fields');
      return;
    }

    setSubmitting(true);
    setSubmitSuccess(null);
    try {
      const payload: any = {
        farmer_id: Number(farmerId),
        crop_id: Number(cropId),
        grade,
        gross_weight_kg: grossWeight,
        moisture,
        delivered_on: new Date(deliveredOn).toISOString(),
        is_credit_debit_note: isNote,
        reference_delivery_id: isNote && refDeliveryId ? Number(refDeliveryId) : null,
        note_reason: isNote ? noteReason : null,
      };

      const result = await api.createDelivery(payload);
      setSubmitSuccess(`Delivery #${result.id} successfully recorded! Net Amount: ₹${result.amount}`);
      loadData();
    } catch (err: any) {
      alert(`Submission Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const selectedFarmer = farmers.find((f) => f.id === Number(farmerId));

  return (
    <div className="space-y-8">
      {/* Top Banner / Edge-case Guidance */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-sm text-emerald-900 shadow-sm flex items-start gap-3">
        <HelpCircle className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
        <div>
          <span className="font-semibold text-emerald-950">Explainable Procurement Rules Engine:</span>
          <p className="text-xs text-emerald-800 mt-0.5">
            Prices are resolved against effective dates on or before delivery date. Moisture above base threshold incurs
            a 1% weight penalty per full 1% excess (capped at 10%). Produce above max moisture is rejected.
            Try edge cases like <code className="bg-emerald-100 px-1 rounded font-mono">14.99%</code> (0% deduction) vs <code className="bg-emerald-100 px-1 rounded font-mono">17.6%</code> (3% deduction).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Form: Delivery Inputs */}
        <div className="lg:col-span-7 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Truck className="w-5 h-5 text-emerald-600" />
              Produce Delivery Entry Form
            </h2>
            <span className="text-xs font-medium text-slate-500">Live Breakdown Calculation</span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Farmer selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Farmer <span className="text-rose-500">*</span>
              </label>
              <select
                value={farmerId}
                onChange={(e) => setFarmerId(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
                required
              >
                <option value="">Select Farmer...</option>
                {farmers.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name} — {f.village} ({f.phone}) | Advance: ₹{f.outstanding_advance}
                  </option>
                ))}
              </select>
              {selectedFarmer && (
                <div className="mt-1.5 flex items-center justify-between text-xs text-slate-500 bg-slate-50 px-2.5 py-1 rounded border border-slate-100">
                  <span>Bank: {selectedFarmer.bank_reference}</span>
                  <span className="font-medium text-emerald-800">
                    Outstanding Advance: ₹{selectedFarmer.outstanding_advance}
                  </span>
                </div>
              )}
            </div>

            {/* Crop & Grade */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Crop <span className="text-rose-500">*</span>
                </label>
                <select
                  value={cropId}
                  onChange={(e) => setCropId(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
                  required
                >
                  <option value="">Select Crop...</option>
                  {crops.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} (Base: {c.base_moisture_threshold}%, Max: {c.max_moisture_accepted}%)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Grade <span className="text-rose-500">*</span>
                </label>
                <select
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
                  required
                >
                  {selectedCrop?.allowed_grades.map((g) => (
                    <option key={g} value={g}>
                      Grade {g}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Gross Weight & Moisture */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Gross Weight (kg) <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={grossWeight}
                    onChange={(e) => setGrossWeight(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
                    required
                  />
                  <Scale className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Moisture Content (%) <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max="100"
                    value={moisture}
                    onChange={(e) => setMoisture(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
                    required
                  />
                  <Droplets className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                </div>
                {selectedCrop && (
                  <p className="text-[11px] text-slate-500 mt-1">
                    Threshold: {selectedCrop.base_moisture_threshold}% · Max Allowed: {selectedCrop.max_moisture_accepted}%
                  </p>
                )}
              </div>
            </div>

            {/* Delivered On Timestamp */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Delivered On (Date & Time) <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <input
                  type="datetime-local"
                  value={deliveredOn}
                  onChange={(e) => setDeliveredOn(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
                  required
                />
                <Clock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            {/* Credit / Debit note toggle */}
            <div className="pt-2 border-t border-slate-100">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={isNote}
                  onChange={(e) => setIsNote(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500 h-4 w-4"
                />
                Is Credit / Debit Note Correction (Rule 6)
              </label>

              {isNote && (
                <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-200 space-y-3 text-xs">
                  <div>
                    <label className="block font-semibold text-amber-900 mb-1">
                      Referenced Original Delivery ID
                    </label>
                    <input
                      type="number"
                      placeholder="e.g. 1"
                      value={refDeliveryId}
                      onChange={(e) => setRefDeliveryId(e.target.value ? Number(e.target.value) : '')}
                      className="w-full px-2.5 py-1.5 rounded border border-amber-300 bg-white"
                      required={isNote}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-amber-900 mb-1">Reason for Adjustment</label>
                    <input
                      type="text"
                      placeholder="e.g. Weighbridge calibration shortfall"
                      value={noteReason}
                      onChange={(e) => setNoteReason(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded border border-amber-300 bg-white"
                      required={isNote}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Submission feedback */}
            {submitSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-lg text-xs font-medium text-emerald-900 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                {submitSuccess}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting || !preview || Boolean(previewError)}
              className="w-full py-2.5 px-4 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg font-semibold text-sm shadow transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <FileText className="w-4 h-4" />
              {submitting ? 'Recording Delivery...' : 'Save & Freeze Delivery'}
            </button>
          </form>
        </div>

        {/* Right Card: Live Calculated Preview (Core Feature) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900 text-white rounded-xl shadow-lg p-6 border border-slate-800">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <Calculator className="w-4 h-4" />
                Live Calculated Preview
              </span>
              {previewLoading && (
                <span className="text-xs text-slate-400 animate-pulse">Calculating...</span>
              )}
            </div>

            {previewError ? (
              <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-rose-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Calculation Rejected:</span>
                  {previewError}
                </div>
              </div>
            ) : preview ? (
              <div className="space-y-4 text-xs">
                <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60 flex justify-between items-center">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Applied Price-List Rate</span>
                    <span className="text-sm font-bold text-white">
                      ₹{preview.breakdown.applied_price} / kg
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-900 text-emerald-300 text-[10px] border border-emerald-700">
                    Price Entry #{preview.breakdown.applied_price_list_id}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-800/40 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-400 text-[11px] block">Gross Weight</span>
                    <span className="text-sm font-semibold text-white">{preview.breakdown.gross_kg} kg</span>
                  </div>
                  <div className="bg-slate-800/40 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-400 text-[11px] block">Moisture Penalty</span>
                    <span className={`text-sm font-semibold ${Number(preview.breakdown.deduction_pct) > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {preview.breakdown.deduction_pct}% ({preview.breakdown.deduction_kg} kg)
                    </span>
                  </div>
                </div>

                <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-800">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Net Billable Weight:</span>
                    <span className="font-bold text-emerald-400 text-sm">
                      {preview.breakdown.net_kg} kg
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Arithmetic Invariant: {preview.breakdown.net_kg} kg + {preview.breakdown.deduction_kg} kg = {preview.breakdown.gross_kg} kg
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800">
                  <span className="text-slate-400 text-xs block">Calculated Total Amount:</span>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-2xl font-black text-emerald-400">
                      ₹{preview.breakdown.amount}
                    </span>
                    <span className="text-slate-500 text-[11px] font-mono">
                      ({preview.breakdown.net_kg} kg × ₹{preview.breakdown.applied_price})
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 text-xs">
                Fill in the delivery parameters to view live breakdown calculations.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Table: Recent Recorded Deliveries */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-bold text-slate-900 text-sm">Recorded Deliveries Ledger (Frozen Breakdown)</h3>
          <span className="text-xs text-slate-500">{loading ? 'Loading deliveries...' : `${recentDeliveries.length} total entries`}</span>
        </div>


        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-600 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Delivered On</th>
                <th className="px-4 py-3">Farmer</th>
                <th className="px-4 py-3">Crop / Grade</th>
                <th className="px-4 py-3 text-right">Gross (kg)</th>
                <th className="px-4 py-3 text-right">Moisture / Ded.</th>
                <th className="px-4 py-3 text-right">Net (kg)</th>
                <th className="px-4 py-3 text-right">Applied Rate</th>
                <th className="px-4 py-3 text-right">Amount (₹)</th>
                <th className="px-4 py-3 text-center">Payout</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recentDeliveries.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50/80 transition">
                  <td className="px-4 py-3 font-mono font-medium text-slate-900">
                    #{d.id}
                    {d.is_credit_debit_note && (
                      <span className="ml-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-[10px]">
                        Adj #{d.reference_delivery_id}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {new Date(d.delivered_on).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900">{d.farmer_name || `Farmer #${d.farmer_id}`}</td>
                  <td className="px-4 py-3">
                    <span className="font-semibold text-emerald-800">{d.crop_name}</span> ({d.grade})
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{d.gross_kg}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    <span className={Number(d.deduction_pct) > 0 ? 'text-amber-700 font-medium' : 'text-slate-500'}>
                      {d.moisture}% (-{d.deduction_pct}%)
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-semibold text-slate-900">{d.net_kg}</td>
                  <td className="px-4 py-3 text-right font-mono">₹{d.applied_price}</td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-emerald-700">₹{d.amount}</td>
                  <td className="px-4 py-3 text-center">
                    {d.payout_id ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-800 border border-emerald-200">
                        Payout #{d.payout_id}
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
                        Unsettled
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {recentDeliveries.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-4 py-8 text-center text-slate-400">
                    No deliveries recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
