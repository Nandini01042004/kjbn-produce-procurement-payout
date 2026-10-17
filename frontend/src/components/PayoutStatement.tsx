import React, { useState, useEffect } from 'react';
import {
  Calculator,
  Lock,
  CheckCircle,
  AlertCircle,
  Printer,
} from 'lucide-react';
import { api } from '../api/client';

import { Farmer, Payout } from '../types';

export const PayoutStatement: React.FC = () => {
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [selectedFarmerId, setSelectedFarmerId] = useState<number | ''>('');
  const [targetDate, setTargetDate] = useState<string>(() => {
    return new Date().toISOString().slice(0, 10);
  });
  const [currentPayout, setCurrentPayout] = useState<Payout | null>(null);
  const [payoutHistory, setPayoutHistory] = useState<Payout[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadFarmers = async () => {
    try {
      const fData = await api.getFarmers();
      setFarmers(fData);
      if (fData.length > 0 && selectedFarmerId === '') {
        setSelectedFarmerId(fData[0].id);
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const loadPayouts = async () => {
    if (!selectedFarmerId) return;
    setLoading(true);
    try {
      const history = await api.getPayouts(Number(selectedFarmerId));
      setPayoutHistory(history);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFarmers();
  }, []);

  useEffect(() => {
    loadPayouts();
    setCurrentPayout(null);
  }, [selectedFarmerId]);

  const handleGenerateDraft = async () => {
    if (!selectedFarmerId) return;
    setActionError(null);
    setActionSuccess(null);
    setLoading(true);
    try {
      const draft = await api.generatePayout(Number(selectedFarmerId), targetDate);
      setCurrentPayout(draft);
      setActionSuccess(`Draft Payout #${draft.id} generated for week ${draft.week_start} to ${draft.week_end}!`);
      loadPayouts();
    } catch (err: any) {
      setActionError(err.message || 'Failed to generate payout draft');
    } finally {
      setLoading(false);
    }
  };

  const handleFinalise = async (payoutId: number) => {
    if (!confirm('Finalising will permanently lock this payout and deduct the recovered advance from the farmer balance. Continue?')) {
      return;
    }
    setActionError(null);
    setActionSuccess(null);
    setLoading(true);
    try {
      const finalised = await api.finalisePayout(payoutId);
      setCurrentPayout(finalised);
      setActionSuccess(`Payout #${finalised.id} successfully Finalised! Advance deduction applied.`);
      loadPayouts();
      loadFarmers(); // Refresh farmer outstanding advances
    } catch (err: any) {
      setActionError(err.message || 'Failed to finalise payout');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkPaid = async (payoutId: number) => {
    setActionError(null);
    setActionSuccess(null);
    setLoading(true);
    try {
      const paid = await api.markPayoutPaid(payoutId);
      setCurrentPayout(paid);
      setActionSuccess(`Payout #${paid.id} marked as Paid!`);
      loadPayouts();
    } catch (err: any) {
      setActionError(err.message || 'Failed to mark payout as paid');
    } finally {
      setLoading(false);
    }
  };

  const selectedFarmer = farmers.find((f) => f.id === Number(selectedFarmerId));

  return (
    <div className="space-y-8">
      {/* Selector & Generator Card */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Calculator className="w-5 h-5 text-emerald-600" />
              Weekly Settlement & Payout Statement Generator
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Aggregates all unassigned deliveries in a Monday–Sunday cycle and applies 30% advance recovery capping (Rules 4 & 5).
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-5">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Select Farmer
            </label>
            <select
              value={selectedFarmerId}
              onChange={(e) => setSelectedFarmerId(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 text-sm"
            >
              {farmers.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name} ({f.village}) — Adv: ₹{f.outstanding_advance}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-4">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Target Week Date (any date in cycle)
            </label>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 text-sm"
            />
          </div>

          <div className="md:col-span-3">
            <button
              onClick={handleGenerateDraft}
              disabled={loading || !selectedFarmerId}
              className="w-full py-2 px-4 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg font-semibold text-xs shadow transition disabled:opacity-50"
            >
              Generate Weekly Draft
            </button>
          </div>
        </div>

        {/* Feedback messages */}
        {actionError && (
          <div className="p-3 bg-rose-50 border border-rose-300 rounded-lg text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            {actionError}
          </div>
        )}
        {actionSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600" />
            {actionSuccess}
          </div>
        )}
      </div>

      {/* Active Payout Statement Card */}
      {currentPayout && (
        <div className="bg-white rounded-xl shadow-lg border-2 border-emerald-600 p-6 space-y-6">
          {/* Statement Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-100 text-emerald-900">
                  Payout #{currentPayout.id}
                </span>
                <span
                  className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                    currentPayout.status === 'Finalised'
                      ? 'bg-blue-100 text-blue-900 border border-blue-300'
                      : currentPayout.status === 'Paid'
                      ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                      : 'bg-amber-100 text-amber-900 border border-amber-300'
                  }`}
                >
                  Status: {currentPayout.status}
                </span>
              </div>
              <h3 className="text-lg font-black text-slate-900 mt-2">
                Produce Procurement Weekly Statement
              </h3>
              <p className="text-xs text-slate-500">
                Cycle: <span className="font-semibold text-slate-800">{currentPayout.week_start}</span> (Mon) to{' '}
                <span className="font-semibold text-slate-800">{currentPayout.week_end}</span> (Sun)
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 text-xs font-medium"
              >
                <Printer className="w-3.5 h-3.5" />
                Print Statement
              </button>

              {currentPayout.status === 'Draft' && (
                <button
                  onClick={() => handleFinalise(currentPayout.id)}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold shadow transition"
                >
                  <Lock className="w-3.5 h-3.5" />
                  Finalise & Lock Payout
                </button>
              )}

              {currentPayout.status === 'Finalised' && (
                <button
                  onClick={() => handleMarkPaid(currentPayout.id)}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-xs font-bold shadow transition"
                >
                  <CheckCircle className="w-3.5 h-3.5" />
                  Mark as Paid
                </button>
              )}
            </div>
          </div>

          {/* Farmer Info Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-xl text-xs border border-slate-200">
            <div>
              <span className="text-slate-500 block">Farmer Name:</span>
              <span className="font-bold text-slate-900 text-sm">{currentPayout.farmer_name}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Village & Phone:</span>
              <span className="font-medium text-slate-900">{currentPayout.farmer_village} · {currentPayout.farmer_phone}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Bank Account / Reference:</span>
              <span className="font-mono text-slate-900 font-semibold">{currentPayout.farmer_bank_ref}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Current Outstanding Advance:</span>
              <span className="font-bold text-emerald-800">
                ₹{selectedFarmer?.outstanding_advance}
              </span>
            </div>
          </div>

          {/* Deliveries Breakdown Table */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Weekly Deliveries Included in Statement ({currentPayout.deliveries.length})
            </h4>

            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-100 font-semibold text-slate-700 uppercase text-[10px] tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="px-3 py-2">ID</th>
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Crop / Grade</th>
                    <th className="px-3 py-2 text-right">Gross kg</th>
                    <th className="px-3 py-2 text-right">Moisture %</th>
                    <th className="px-3 py-2 text-right">Ded. % (kg)</th>
                    <th className="px-3 py-2 text-right">Net kg</th>
                    <th className="px-3 py-2 text-right">Rate (₹/kg)</th>
                    <th className="px-3 py-2 text-right">Amount (₹)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {currentPayout.deliveries.map((d) => (
                    <tr key={d.id}>
                      <td className="px-3 py-2 font-mono">#{d.id}</td>
                      <td className="px-3 py-2">{new Date(d.delivered_on).toLocaleDateString()}</td>
                      <td className="px-3 py-2 font-medium">{d.crop_name} ({d.grade})</td>
                      <td className="px-3 py-2 text-right font-mono">{d.gross_kg}</td>
                      <td className="px-3 py-2 text-right font-mono">{d.moisture}%</td>
                      <td className="px-3 py-2 text-right font-mono text-amber-700">
                        {d.deduction_pct}% ({d.deduction_kg} kg)
                      </td>
                      <td className="px-3 py-2 text-right font-mono font-semibold">{d.net_kg}</td>
                      <td className="px-3 py-2 text-right font-mono">₹{d.applied_price}</td>
                      <td className="px-3 py-2 text-right font-mono font-bold text-slate-900">₹{d.amount}</td>
                    </tr>
                  ))}
                  {currentPayout.deliveries.length === 0 && (
                    <tr>
                      <td colSpan={9} className="px-3 py-6 text-center text-slate-400">
                        No deliveries recorded for this farmer in this week. Gross amount is ₹0.00.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Explainable Net Arithmetic Card */}
          <div className="bg-slate-900 text-white rounded-xl p-5 border border-slate-800 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
              Explainable Payout Arithmetic (Every Rupee Accounted For)
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs pt-2">
              <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700">
                <span className="text-slate-400 block text-[11px]">1. Total Gross Amount</span>
                <span className="text-xl font-black text-white mt-1 block">
                  ₹{currentPayout.gross_amount}
                </span>
                <span className="text-[10px] text-slate-400">Sum of net delivery amounts</span>
              </div>

              <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700">
                <span className="text-slate-400 block text-[11px]">2. Advance Recovery Deduction</span>
                <span className="text-xl font-black text-amber-400 mt-1 block">
                  - ₹{currentPayout.advance_deduction}
                </span>
                <span className="text-[10px] text-slate-400">
                  Lesser of Advance vs 30% of Gross (₹{(Number(currentPayout.gross_amount) * 0.3).toFixed(2)})
                </span>
              </div>

              <div className="bg-emerald-950/80 p-3 rounded-lg border border-emerald-700">
                <span className="text-emerald-300 block text-[11px]">3. Net Amount Payable</span>
                <span className="text-2xl font-black text-emerald-300 mt-1 block">
                  ₹{currentPayout.net_amount}
                </span>
                <span className="text-[10px] text-emerald-400/80">Net = Gross - Advance Deduction</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Historical Payouts Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-bold text-slate-900 text-sm">
            Farmer Payout History ({selectedFarmer?.name || 'All'})
          </h3>
          <span className="text-xs text-slate-500">{payoutHistory.length} statements on file</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 font-semibold text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Payout ID</th>
                <th className="px-4 py-3">Week Cycle</th>
                <th className="px-4 py-3">Farmer</th>
                <th className="px-4 py-3 text-right">Gross (₹)</th>
                <th className="px-4 py-3 text-right">Advance Ded. (₹)</th>
                <th className="px-4 py-3 text-right">Net Paid (₹)</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {payoutHistory.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50/80 transition">
                  <td className="px-4 py-3 font-mono font-medium text-slate-900">#{p.id}</td>
                  <td className="px-4 py-3 font-medium">
                    {p.week_start} to {p.week_end}
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-900">{p.farmer_name}</td>
                  <td className="px-4 py-3 text-right font-mono">₹{p.gross_amount}</td>
                  <td className="px-4 py-3 text-right font-mono text-amber-700">-₹{p.advance_deduction}</td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-emerald-800 text-sm">
                    ₹{p.net_amount}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        p.status === 'Paid'
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : p.status === 'Finalised'
                          ? 'bg-blue-100 text-blue-800 border border-blue-300'
                          : 'bg-amber-100 text-amber-800 border border-amber-300'
                      }`}
                    >
                      {p.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setCurrentPayout(p)}
                      className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-800 font-medium text-xs transition"
                    >
                      View Statement
                    </button>
                  </td>
                </tr>
              ))}
              {payoutHistory.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                    No payouts on file for this farmer.
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
