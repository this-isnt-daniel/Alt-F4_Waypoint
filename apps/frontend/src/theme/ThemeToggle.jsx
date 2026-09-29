import React from 'react';
import { useTheme } from './useTheme';
import { Sun, Moon } from 'lucide-react';

export function ThemeToggle({ className = '' }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      className={`flex items-center gap-2 px-3 py-2 rounded-full border border-slate-700/60 bg-slate-900/90 hover:bg-slate-800 text-slate-200 shadow-xl backdrop-blur-md transition-all active:scale-95 cursor-pointer text-xs font-semibold select-none group ${className}`}
    >
      <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 group-hover:text-emerald-300">
        {isDark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
      </span>
      <span>{isDark ? 'Dark Mode' : 'Light Mode'}</span>
    </button>
  );
}
