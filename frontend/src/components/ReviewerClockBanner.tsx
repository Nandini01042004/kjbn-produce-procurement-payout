import React, { useState, useEffect } from 'react';
import { Clock, RotateCcw, AlertTriangle, CheckCircle } from 'lucide-react';
import { api, getStoredTestClock, setStoredTestClock } from '../api/client';

export const ReviewerClockBanner: React.FC = () => {
  const [testClock, setTestClock] = useState<string>(getStoredTestClock() || '');
  const [currentIst, setCurrentIst] = useState<string>('');
  const [isResetting, setIsResetting] = useState(false);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      const res = await api.getHealth();
      setCurrentIst(res.clock.ist);
    } catch {
      // Backend might be starting
    }
  };


  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleApplyClock = () => {
    if (testClock.trim()) {
      setStoredTestClock(testClock.trim());
    } else {
      setStoredTestClock(null);
    }
    fetchHealth();
    window.location.reload();
  };

  const handleResetClock = () => {
    setTestClock('');
    setStoredTestClock(null);
    fetchHealth();
    window.location.reload();
  };

  const handleResetSeed = async () => {
    if (!confirm('Are you sure you want to reset all data to initial sample seed?')) return;
    setIsResetting(true);
    setSeedMessage(null);
    try {
      const res = await api.resetSeed();
      setSeedMessage(res.message);
      setTimeout(() => {
        setSeedMessage(null);
        window.location.reload();
      }, 1500);
    } catch (e: any) {
      alert(`Seed reset failed: ${e.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  const isOverrideActive = Boolean(getStoredTestClock());

  return (
    <div className={`border-b text-xs px-4 py-2 flex flex-wrap items-center justify-between gap-3 ${
      isOverrideActive ? 'bg-amber-50 border-amber-300 text-amber-950' : 'bg-slate-100 border-slate-300 text-slate-800'
    }`}>
      <div className="flex items-center gap-2 flex-wrap">
        <span className="inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-800">
          <Clock className="w-3.5 h-3.5" />
          Reviewer Clock:
        </span>
        <span className="font-mono">{currentIst || 'Syncing clock...'}</span>
        {isOverrideActive && (
          <span className="inline-flex items-center gap-1 text-amber-800 bg-amber-200/80 px-2 py-0.5 rounded font-medium">
            <AlertTriangle className="w-3 h-3 text-amber-700" />
            Override Active (X-Test-Clock)
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1">
          <input
            type="text"
            placeholder="YYYY-MM-DD or ISO (e.g. 2026-10-15)"
            value={testClock}
            onChange={(e) => setTestClock(e.target.value)}
            className="px-2 py-1 rounded border border-slate-300 bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-emerald-500 w-52 text-xs"
          />
          <button
            onClick={handleApplyClock}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded font-medium transition"
          >
            Set Clock
          </button>
          {isOverrideActive && (
            <button
              onClick={handleResetClock}
              title="Reset to live system clock"
              className="px-2 py-1 bg-amber-200 hover:bg-amber-300 text-amber-900 rounded font-medium transition"
            >
              Reset
            </button>
          )}
        </div>

        <div className="h-4 w-px bg-slate-300 mx-1 hidden sm:block" />

        <button
          onClick={handleResetSeed}
          disabled={isResetting}
          className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-700 hover:bg-emerald-800 text-white rounded font-medium transition disabled:opacity-50"
        >
          <RotateCcw className={`w-3 h-3 ${isResetting ? 'animate-spin' : ''}`} />
          {isResetting ? 'Resetting...' : 'Re-seed Data'}
        </button>

        {seedMessage && (
          <span className="inline-flex items-center gap-1 text-emerald-800 font-medium">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
            {seedMessage}
          </span>
        )}
      </div>
    </div>
  );
};
