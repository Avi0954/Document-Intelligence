import React from 'react';

export const Navbar = ({ user, onSignOut }) => {
  return (
    <header className="w-full bg-[#0B0B0B] border-b border-[#242424]">
      <div className="max-w-7xl w-full mx-auto px-4 sm:px-8 py-4 flex items-center justify-between">

        {/* Brand Header */}
        <div className="flex items-center gap-3 font-mono text-xs uppercase tracking-widest">
          <span className="font-semibold text-white">PRAGATI BHARATI</span>
          <span className="text-[#404040]">/</span>
          <span className="text-[#A0A0A0]">DOCUMENT INTELLIGENCE</span>
        </div>

        {/* User Info & Sign Out */}
        {user && (
          <div className="flex items-center gap-5 text-xs">
            <span className="font-mono text-[#A0A0A0] text-[11px] hidden sm:inline">
              {user.email}
            </span>
            <button
              onClick={onSignOut}
              className="font-mono text-[11px] uppercase tracking-wider text-[#F5F5F5] hover:text-[#707070] transition-colors"
            >
              Sign out
            </button>
          </div>
        )}

      </div>
    </header>
  );
};


