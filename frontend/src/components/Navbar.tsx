import React from 'react';
import { Truck, FileSpreadsheet, Calculator, BookOpen, Layers } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'deliveries', label: 'Delivery Entry & Live Preview', icon: Truck },
    { id: 'payouts', label: 'Weekly Payout Statements', icon: Calculator },
    { id: 'pricelists', label: 'Price List History', icon: FileSpreadsheet },
    { id: 'ledger', label: 'Farmer Financial Ledger', icon: BookOpen },
  ];

  return (
    <header className="bg-emerald-900 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-800 rounded-lg">
              <Layers className="w-6 h-6 text-emerald-300" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                KJBN Buying Centre
                <span className="text-xs font-normal px-2 py-0.5 rounded bg-emerald-800 text-emerald-200 border border-emerald-700">
                  Problem 4
                </span>
              </h1>
              <p className="text-xs text-emerald-300">Produce Procurement & Explainable Payout Engine</p>
            </div>
          </div>

          <nav className="hidden md:flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive
                      ? 'bg-emerald-800 text-white shadow-inner'
                      : 'text-emerald-100 hover:bg-emerald-800/60 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4 text-emerald-300" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="md:hidden border-t border-emerald-800 px-2 py-1 flex overflow-x-auto gap-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium whitespace-nowrap transition ${
                isActive
                  ? 'bg-emerald-800 text-white'
                  : 'text-emerald-200 hover:bg-emerald-800/60'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>
    </header>
  );
};
