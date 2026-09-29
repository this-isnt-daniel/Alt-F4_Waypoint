import React, { useState, useEffect, useRef } from 'react';
import { Minus, Plus } from 'lucide-react';
import { formatQuantity } from '../data/catalogue';

export default function QuantityStepper({ 
  qty, 
  quantityType, 
  unit, 
  onChange, 
  onDecrement, 
  onIncrement, 
  min = 0, 
  size = 'md' 
}) {
  const isZero = qty === 0;
  const [editing, setEditing] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef(null);

  const btnBase =
    'flex items-center justify-center rounded-md border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 select-none shrink-0';

  const sizeMap = {
    sm: { btn: 'w-7 h-7', textWidth: 'min-w-[3rem]', textSize: 'text-[13px]', icon: 12 },
    md: { btn: 'w-8 h-8', textWidth: 'min-w-[4rem]', textSize: 'text-[14px]', icon: 14 },
    lg: { btn: 'w-10 h-10', textWidth: 'min-w-[5rem]', textSize: 'text-base', icon: 16 },
  };
  const s = sizeMap[size] || sizeMap.md;

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const handleDisplayClick = () => {
    setInputValue(formatQuantity(qty, quantityType, unit).replace(/s$/, ''));
    setEditing(true);
  };

  const handleBlurOrSubmit = () => {
    setEditing(false);
    const parsed = parseInput(inputValue, quantityType);
    if (parsed !== null && parsed >= min) {
      if (onChange) onChange(parsed);
    }
  };

  const parseInput = (val, type) => {
    const str = val.toLowerCase().replace(/\s+/g, '');
    if (type === 'weight') {
      if (str.endsWith('kg')) {
        const num = parseFloat(str.replace('kg', ''));
        return !isNaN(num) ? num : null;
      }
      if (str.endsWith('g')) {
        const num = parseFloat(str.replace('g', ''));
        return !isNaN(num) ? num / 1000 : null; // store as kg
      }
      // No unit provided
      const num = parseFloat(str);
      if (isNaN(num)) return null;
      // Infer unit: if they type >= 10, it's almost certainly grams.
      if (num >= 10) return num / 1000;
      return num; // otherwise assume kg
    } else {
      // Count type
      const num = parseInt(str, 10);
      return !isNaN(num) ? num : null;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleBlurOrSubmit();
    } else if (e.key === 'Escape') {
      setEditing(false);
    }
  };

  if (isZero) {
    return (
      <button
        type="button"
        onClick={onIncrement}
        aria-label="Add to order"
        className={`${btnBase} ${s.btn} border-brand-600 dark:border-emerald-500 text-brand-600 dark:text-emerald-400 hover:bg-brand-50 dark:hover:bg-emerald-950/40 active:bg-brand-100 cursor-pointer`}
      >
        <Plus size={s.icon} strokeWidth={2.2} />
      </button>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      <button
        type="button"
        onClick={onDecrement}
        disabled={qty <= min}
        aria-label="Decrease quantity"
        className={`${btnBase} ${s.btn} border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-slate-400 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer`}
      >
        <Minus size={s.icon} strokeWidth={2.2} />
      </button>

      {editing ? (
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onBlur={handleBlurOrSubmit}
          onKeyDown={handleKeyDown}
          className={`${s.textWidth} ${s.textSize} h-8 px-1 text-center font-bold text-brand-700 dark:text-emerald-300 bg-brand-50 dark:bg-emerald-950/50 border border-brand-300 dark:border-emerald-700 rounded-md outline-none focus:ring-2 focus:ring-brand-500 dark:focus:ring-emerald-500`}
        />
      ) : (
        <span
          onClick={handleDisplayClick}
          className={`${s.textWidth} ${s.textSize} text-center font-bold text-slate-900 dark:text-[#F8FAFC] tabular-nums cursor-text hover:bg-slate-100 dark:hover:bg-slate-800 rounded px-1 transition-colors`}
          aria-label={`Quantity: ${formatQuantity(qty, quantityType, unit)}`}
        >
          {formatQuantity(qty, quantityType, unit)}
        </span>
      )}

      <button
        type="button"
        onClick={onIncrement}
        aria-label="Increase quantity"
        className={`${btnBase} ${s.btn} border-brand-600 dark:border-emerald-500 text-brand-600 dark:text-emerald-400 hover:bg-brand-50 dark:hover:bg-emerald-950/40 active:bg-brand-100 cursor-pointer`}
      >
        <Plus size={s.icon} strokeWidth={2.2} />
      </button>
    </div>
  );
}
