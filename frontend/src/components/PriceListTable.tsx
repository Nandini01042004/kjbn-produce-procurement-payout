import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, PlusCircle, AlertCircle, CheckCircle2, Calendar } from 'lucide-react';
import { api } from '../api/client';
import { Crop, PriceListEntry } from '../types';

export const PriceListTable: React.FC = () => {
  const [crops, setCrops] = useState<Crop[]>([]);
  const [entries, setEntries] = useState<PriceListEntry[]>([]);
  const [selectedCropId, setSelectedCropId] = useState<number | ''>('');
  const [selectedGrade, setSelectedGrade] = useState<string>('');
  const [loading, setLoading] = useState(false);


  // New price entry form
  const [showAddModal, setShowAddModal] = useState(false);
  const [formCropId, setFormCropId] = useState<number | ''>('');
  const [formGrade, setFormGrade] = useState<string>('A');
  const [formPrice, setFormPrice] = useState<string>('25.00');
  const [formEffectiveFrom, setFormEffectiveFrom] = useState<string>(() => {
    return new Date().toISOString().slice(0, 10);
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cData, pData] = await Promise.all([
        api.getCrops(),
        api.getPriceLists(
          selectedCropId !== '' ? Number(selectedCropId) : undefined,
          selectedGrade ? selectedGrade : undefined
        ),
      ]);
      setCrops(cData);
      setEntries(pData);
      if (cData.length > 0 && formCropId === '') {
        setFormCropId(cData[0].id);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCropId, selectedGrade]);

  const handleAddPrice = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);
    try {
      const res = await api.createPriceList({
        crop_id: Number(formCropId),
        grade: formGrade,
        price_per_kg: formPrice,
        effective_from: formEffectiveFrom,
      });
      setFormSuccess(`New price entry added! Effective from ${res.effective_from} at ₹${res.price_per_kg}/kg.`);
      loadData();
      setTimeout(() => {
        setShowAddModal(false);
        setFormSuccess(null);
      }, 1500);
    } catch (err: any) {
      setFormError(err.message || 'Failed to add price entry');
    }
  };

  const selectedCropForForm = crops.find((c) => c.id === Number(formCropId));

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-emerald-600" />
            Effective-Dated Price Lists & Rate History
            {loading && <span className="text-xs text-slate-400 font-normal animate-pulse">(updating...)</span>}
          </h2>
          <p className="text-xs text-slate-500 mt-1">

            Prices are effective-dated over time and never overwritten (Rule 1). Historical deliveries preserve frozen rates.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-2 px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold shadow transition"
        >
          <PlusCircle className="w-4 h-4" />
          Add Effective Price Entry
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-wrap items-center gap-4 text-xs">
        <span className="font-semibold text-slate-700 uppercase tracking-wider">Filter History:</span>
        <div className="flex items-center gap-2">
          <label className="text-slate-500">Crop:</label>
          <select
            value={selectedCropId}
            onChange={(e) => setSelectedCropId(e.target.value ? Number(e.target.value) : '')}
            className="px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white text-slate-900"
          >
            <option value="">All Crops</option>
            {crops.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-slate-500">Grade:</label>
          <select
            value={selectedGrade}
            onChange={(e) => setSelectedGrade(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white text-slate-900"
          >
            <option value="">All Grades</option>
            <option value="A">Grade A</option>
            <option value="B">Grade B</option>
            <option value="C">Grade C</option>
          </select>
        </div>

        {(selectedCropId !== '' || selectedGrade !== '') && (
          <button
            onClick={() => {
              setSelectedCropId('');
              setSelectedGrade('');
            }}
            className="text-emerald-700 hover:underline font-medium ml-auto"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Price List Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-600 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-3">Entry ID</th>
                <th className="px-4 py-3">Crop Name</th>
                <th className="px-4 py-3">Grade</th>
                <th className="px-4 py-3 text-right">Price per kg (₹)</th>
                <th className="px-4 py-3">Effective From Date</th>
                <th className="px-4 py-3">Audit Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {entries.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50/80 transition">
                  <td className="px-4 py-3 font-mono font-medium text-slate-900">#{p.id}</td>
                  <td className="px-4 py-3 font-semibold text-emerald-900">{p.crop_name}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded font-medium bg-slate-100 text-slate-800 border border-slate-200">
                      Grade {p.grade}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-slate-900 text-sm">
                    ₹{p.price_per_kg}
                  </td>
                  <td className="px-4 py-3 font-medium text-emerald-800">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-emerald-600" />
                      {p.effective_from}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                    {new Date(p.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {entries.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    No price list entries matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Price Entry Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-emerald-600" />
                Add Effective Price Entry
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleAddPrice} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Crop</label>
                <select
                  value={formCropId}
                  onChange={(e) => setFormCropId(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
                  required
                >
                  {crops.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Grade</label>
                <select
                  value={formGrade}
                  onChange={(e) => setFormGrade(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
                  required
                >
                  {selectedCropForForm?.allowed_grades.map((g) => (
                    <option key={g} value={g}>
                      Grade {g}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Price per kg (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={formPrice}
                  onChange={(e) => setFormPrice(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white font-mono"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Effective From Date</label>
                <input
                  type="date"
                  value={formEffectiveFrom}
                  onChange={(e) => setFormEffectiveFrom(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
                  required
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Takes effect for all deliveries on or after this date.
                </span>
              </div>

              {formError && (
                <div className="p-2.5 bg-rose-50 border border-rose-300 rounded text-rose-800 text-[11px] flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  {formError}
                </div>
              )}

              {formSuccess && (
                <div className="p-2.5 bg-emerald-50 border border-emerald-300 rounded text-emerald-800 text-[11px] flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                  {formSuccess}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-semibold"
                >
                  Save Price Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
