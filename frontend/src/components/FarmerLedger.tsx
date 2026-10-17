import React, { useState, useEffect } from 'react';
import {
  PlusCircle,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../api/client';
import { Farmer, FarmerLedger as LedgerType } from '../types';

export const FarmerLedger: React.FC = () => {
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [selectedFarmerId, setSelectedFarmerId] = useState<number | ''>('');
  const [ledger, setLedger] = useState<LedgerType | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeLedgerTab, setActiveLedgerTab] = useState<'deliveries' | 'advances' | 'payouts'>('deliveries');



  // Issue advance modal
  const [showAdvanceModal, setShowAdvanceModal] = useState(false);
  const [advanceAmount, setAdvanceAmount] = useState<string>('5000');
  const [advanceNotes, setAdvanceNotes] = useState<string>('');
  const [advanceDate, setAdvanceDate] = useState<string>(() => {
    return new Date().toISOString().slice(0, 16);
  });
  const [advanceError, setAdvanceError] = useState<string | null>(null);
  const [advanceSuccess, setAdvanceSuccess] = useState<string | null>(null);

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

  const loadLedger = async () => {
    if (!selectedFarmerId) return;
    setLoading(true);
    try {
      const data = await api.getFarmerLedger(Number(selectedFarmerId));
      setLedger(data);
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
    loadLedger();
  }, [selectedFarmerId]);

  const handleIssueAdvance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFarmerId) return;
    setAdvanceError(null);
    setAdvanceSuccess(null);
    try {
      const adv = await api.issueAdvance({
        farmer_id: Number(selectedFarmerId),
        amount: advanceAmount,
        given_on: new Date(advanceDate).toISOString(),
        notes: advanceNotes,
      });
      setAdvanceSuccess(`₹${adv.amount} advance issued to ${adv.farmer_name}!`);
      loadLedger();
      loadFarmers();
      setTimeout(() => {
        setShowAdvanceModal(false);
        setAdvanceSuccess(null);
      }, 1500);
    } catch (err: any) {
      setAdvanceError(err.message || 'Failed to issue advance');
    }
  };

  return (
    <div className="space-y-6">
      {/* Farmer Selection & Summary Header */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Select Farmer Account {loading && <span className="text-slate-400 font-normal animate-pulse">(syncing...)</span>}
            </label>
            <select

              value={selectedFarmerId}
              onChange={(e) => setSelectedFarmerId(Number(e.target.value))}
              className="px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 text-sm min-w-[280px]"
            >
              {farmers.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name} — {f.village} ({f.phone})
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={() => setShowAdvanceModal(true)}
          className="inline-flex items-center gap-2 px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold shadow transition"
        >
          <PlusCircle className="w-4 h-4" />
          Issue Cash Advance
        </button>
      </div>

      {ledger && (
        <div className="space-y-6">
          {/* Metrics Overview Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Current Outstanding Advance
              </span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-2xl font-black text-amber-700">
                  ₹{ledger.outstanding_advance}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Deducted from payouts (up to 30% cap)</p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Total Produce Delivered
              </span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-2xl font-black text-slate-900">
                  {ledger.total_delivered_net_kg}
                </span>
                <span className="text-xs text-slate-500">net kg ({ledger.total_deliveries_count} trips)</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Gross: {ledger.total_delivered_gross_kg} kg</p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Lifetime Gross Earnings
              </span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-2xl font-black text-slate-900">
                  ₹{ledger.total_gross_earnings}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Before advance recoveries</p>
            </div>

            <div className="bg-emerald-900 text-white p-5 rounded-xl shadow-sm">
              <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wider">
                Total Net Paid to Bank
              </span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-2xl font-black text-emerald-300">
                  ₹{ledger.total_net_paid}
                </span>
              </div>
              <p className="text-[11px] text-emerald-400 mt-1">Recovered advance: ₹{ledger.total_advance_deducted}</p>
            </div>
          </div>

          {/* Ledger Tabs */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="border-b border-slate-200 flex space-x-1 p-2 bg-slate-50">
              <button
                onClick={() => setActiveLedgerTab('deliveries')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition ${
                  activeLedgerTab === 'deliveries'
                    ? 'bg-white text-emerald-800 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Produce Deliveries ({ledger.deliveries.length})
              </button>
              <button
                onClick={() => setActiveLedgerTab('advances')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition ${
                  activeLedgerTab === 'advances'
                    ? 'bg-white text-emerald-800 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Cash Advances History ({ledger.advances.length})
              </button>
              <button
                onClick={() => setActiveLedgerTab('payouts')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition ${
                  activeLedgerTab === 'payouts'
                    ? 'bg-white text-emerald-800 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Weekly Settlements ({ledger.payouts.length})
              </button>
            </div>

            <div className="p-4">
              {activeLedgerTab === 'deliveries' && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-slate-50 font-semibold text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-200">
                      <tr>
                        <th className="px-3 py-2">ID</th>
                        <th className="px-3 py-2">Date</th>
                        <th className="px-3 py-2">Crop / Grade</th>
                        <th className="px-3 py-2 text-right">Gross (kg)</th>
                        <th className="px-3 py-2 text-right">Moisture %</th>
                        <th className="px-3 py-2 text-right">Deduction</th>
                        <th className="px-3 py-2 text-right">Net (kg)</th>
                        <th className="px-3 py-2 text-right">Applied Rate</th>
                        <th className="px-3 py-2 text-right">Amount (₹)</th>
                        <th className="px-3 py-2 text-center">Settlement</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {ledger.deliveries.map((d) => (
                        <tr key={d.id} className="hover:bg-slate-50/80">
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
                          <td className="px-3 py-2 text-center">
                            {d.payout_id ? (
                              <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-800">
                                Payout #{d.payout_id}
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-500">
                                Pending
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {activeLedgerTab === 'advances' && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-slate-50 font-semibold text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-200">
                      <tr>
                        <th className="px-3 py-2">ID</th>
                        <th className="px-3 py-2">Date Given</th>
                        <th className="px-3 py-2 text-right">Advance Amount (₹)</th>
                        <th className="px-3 py-2">Notes & Reference</th>
                        <th className="px-3 py-2">Audit Timestamp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {ledger.advances.map((a) => (
                        <tr key={a.id} className="hover:bg-slate-50/80">
                          <td className="px-3 py-2 font-mono">#{a.id}</td>
                          <td className="px-3 py-2">{new Date(a.given_on).toLocaleDateString()}</td>
                          <td className="px-3 py-2 text-right font-mono font-bold text-amber-800">₹{a.amount}</td>
                          <td className="px-3 py-2 text-slate-600">{a.notes || '—'}</td>
                          <td className="px-3 py-2 text-slate-400 font-mono text-[11px]">
                            {new Date(a.created_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {activeLedgerTab === 'payouts' && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-slate-50 font-semibold text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-200">
                      <tr>
                        <th className="px-3 py-2">Payout ID</th>
                        <th className="px-3 py-2">Cycle</th>
                        <th className="px-3 py-2 text-right">Gross (₹)</th>
                        <th className="px-3 py-2 text-right">Advance Deduction (₹)</th>
                        <th className="px-3 py-2 text-right">Net Disbursed (₹)</th>
                        <th className="px-3 py-2 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {ledger.payouts.map((p) => (
                        <tr key={p.id} className="hover:bg-slate-50/80">
                          <td className="px-3 py-2 font-mono">#{p.id}</td>
                          <td className="px-3 py-2 font-medium">{p.week_start} to {p.week_end}</td>
                          <td className="px-3 py-2 text-right font-mono">₹{p.gross_amount}</td>
                          <td className="px-3 py-2 text-right font-mono text-amber-700">-₹{p.advance_deduction}</td>
                          <td className="px-3 py-2 text-right font-mono font-bold text-emerald-800">₹{p.net_amount}</td>
                          <td className="px-3 py-2 text-center">
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                              {p.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Issue Advance Modal */}
      {showAdvanceModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-emerald-600" />
                Issue Cash Advance to Farmer
              </h3>
              <button
                onClick={() => setShowAdvanceModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleIssueAdvance} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Advance Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={advanceAmount}
                  onChange={(e) => setAdvanceAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white font-mono"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Date & Time Given</label>
                <input
                  type="datetime-local"
                  value={advanceDate}
                  onChange={(e) => setAdvanceDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Notes / Purpose (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Fertilizer purchase support"
                  value={advanceNotes}
                  onChange={(e) => setAdvanceNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
                />
              </div>

              {advanceError && (
                <div className="p-2.5 bg-rose-50 border border-rose-300 rounded text-rose-800 text-[11px] flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  {advanceError}
                </div>
              )}

              {advanceSuccess && (
                <div className="p-2.5 bg-emerald-50 border border-emerald-300 rounded text-emerald-800 text-[11px] flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                  {advanceSuccess}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAdvanceModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-semibold"
                >
                  Confirm Advance
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
