import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { ReviewerClockBanner } from './components/ReviewerClockBanner';

import { DeliveryForm } from './components/DeliveryForm';
import { PayoutStatement } from './components/PayoutStatement';
import { PriceListTable } from './components/PriceListTable';
import { FarmerLedger } from './components/FarmerLedger';

export default function App() {
  const [activeTab, setActiveTab] = useState('deliveries');

  return (
    <div className="min-h-screen flex flex-col bg-slate-100">
      {/* Reviewer Clock Override Banner */}
      <ReviewerClockBanner />

      {/* Main Navbar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'deliveries' && <DeliveryForm />}
        {activeTab === 'payouts' && <PayoutStatement />}
        {activeTab === 'pricelists' && <PriceListTable />}
        {activeTab === 'ledger' && <FarmerLedger />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          <p className="font-medium text-slate-700">KJBN Labs Software Engineering Take-Home Assignment</p>
          <p className="mt-1">
            Problem 4: Produce Procurement & Payout · Built by <span className="font-semibold text-emerald-800">Nandini</span> (Candidate)
          </p>
        </div>
      </footer>
    </div>
  );
}
