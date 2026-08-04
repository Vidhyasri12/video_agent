import React from 'react';
import { 
  Video, 
  History, 
  Bookmark, 
  Settings, 
  Crown, 
  User,
  HelpCircle,
  Moon
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { id: 'summarizer', label: 'Summarizer', icon: Video, active: true },
    { id: 'history', label: 'History', icon: History, active: false },
    { id: 'saved', label: 'Saved Summaries', icon: Bookmark, active: false },
    { id: 'settings', label: 'Settings', icon: Settings, active: false },
  ];

  return (
    <div className="w-64 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col h-screen overflow-hidden">
      {/* Navigation */}
      <div className="flex-1 p-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
              item.active
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </div>

      {/* Upgrade to Pro */}
      <div className="p-4 border-t border-slate-800 flex-shrink-0">
        <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 rounded-xl p-4 space-y-3">
          <div className="flex items-center space-x-2">
            <Crown className="w-5 h-5 text-indigo-400" />
            <span className="text-sm font-semibold text-white">Upgrade to Pro</span>
          </div>
          <p className="text-xs text-slate-400">Unlock unlimited summaries and advanced features</p>
          <button className="w-full py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold rounded-lg transition">
            Upgrade Now
          </button>
        </div>
      </div>

      {/* User Section */}
      <div className="p-4 border-t border-slate-800 flex-shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">User</p>
            <p className="text-xs text-slate-400">Free Plan</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
