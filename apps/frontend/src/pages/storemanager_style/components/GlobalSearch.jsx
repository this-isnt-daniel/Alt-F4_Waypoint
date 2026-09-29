import React, { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';
import { searchProducts } from '../data/catalogue';
import QuantityStepper from './QuantityStepper';

/**
 * Global Product Search
 * Can be placed on the Overview page (or anywhere).
 * Gives immediate add/edit access to the basket.
 */
export default function GlobalSearch({ basket, onSetQty, placeholder = "Search by product code or name..." }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef(null);

  useEffect(() => {
    if (query.trim().length > 0) {
      setResults(searchProducts(query));
      setIsOpen(true);
    } else {
      setResults([]);
      setIsOpen(false);
    }
  }, [query]);

  // Click outside to close results
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative w-full z-20" ref={wrapperRef}>
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (query.trim()) setIsOpen(true); }}
          placeholder={placeholder}
          className="w-full h-10 pl-10 pr-10 text-[14px] font-medium text-slate-900 bg-white border border-slate-300 rounded-md placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all shadow-sm"
        />
        {query && (
          <button
            type="button"
            onClick={() => { setQuery(''); setIsOpen(false); }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1.5"
          >
            <X size={15} />
          </button>
        )}
      </div>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 shadow-xl rounded-md overflow-hidden max-h-[60vh] flex flex-col">
          {results.length === 0 ? (
            <div className="py-8 text-center px-4">
              <p className="text-[14px] font-medium text-slate-600">No products found for "{query}"</p>
              <p className="text-[12px] text-slate-400 mt-1">Try searching for generic terms like "oil" or "rice"</p>
            </div>
          ) : (
            <div className="overflow-y-auto p-2 space-y-1">
              <div className="px-3 py-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                {results.length} result{results.length !== 1 ? 's' : ''}
              </div>
              {results.map((product) => {
                const key = `${product.id}-${product.variant ?? ''}`;
                const basketItem = basket.find((b) => b.key === key);
                const qty = basketItem?.qty ?? 0;
                const step = product.quantityType === 'weight' ? 0.5 : 1;
                
                return (
                  <div
                    key={key}
                    className="flex items-center justify-between p-3 border-b last:border-b-0 border-slate-100 hover:bg-slate-50 transition-colors group"
                  >
                    <div className="flex-1 min-w-0 pr-4">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{product.id}</span>
                        <span className="text-[11px] font-medium text-brand-600 tracking-wide">
                          {product.categoryName}
                        </span>
                      </div>
                      <p className="text-[14px] font-bold text-slate-900 truncate">
                        {product.name} {product.variant ? ` · ${product.variant}` : ''}
                      </p>
                    </div>
                    <div className="shrink-0">
                      <QuantityStepper
                        qty={qty}
                        quantityType={product.quantityType}
                        unit={product.unit}
                        onChange={(newQty) => onSetQty(product, product.variant, newQty)}
                        onDecrement={() => onSetQty(product, product.variant, Math.max(0, qty - step))}
                        onIncrement={() => onSetQty(product, product.variant, qty + step)}
                        size="md"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
