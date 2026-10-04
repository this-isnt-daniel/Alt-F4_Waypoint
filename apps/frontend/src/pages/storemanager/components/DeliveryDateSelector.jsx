import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';

// For this mock, we assume September 2026
// We will mock the calendar days
const DAYS_IN_MONTH = 30;
const START_DAY_OF_WEEK = 2; // Sept 1 2026 is a Tuesday (0=Sun, 1=Mon, 2=Tue)

// Helper to get day name
const getDayName = (dateStr) => {
  if (dateStr.includes('Sep')) return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][(parseInt(dateStr) + START_DAY_OF_WEEK - 1) % 7];
  if (dateStr.includes('Oct')) return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][(parseInt(dateStr) + START_DAY_OF_WEEK + 29) % 7];
  return '';
};

export default function DeliveryDateSelector({ orderDate, setOrderDate, onDateSelected, hideHeader = false }) {
  const [currentMonth, setCurrentMonth] = useState('September 2026'); // Mock state
  const [isOct, setIsOct] = useState(false);

  const handleNextMonth = () => {
    setCurrentMonth('October 2026');
    setIsOct(true);
  };
  const handlePrevMonth = () => {
    setCurrentMonth('September 2026');
    setIsOct(false);
  };

  const handleSelectDate = (day, isOctMonth) => {
    const month = isOctMonth ? 10 : 9;
    const dateStr = `2026-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    setOrderDate(dateStr);
    onDateSelected();
  };

  const renderCalendar = (isOctMonth) => {
    const daysInMonth = isOctMonth ? 31 : 30;
    const startDay = isOctMonth ? (START_DAY_OF_WEEK + 30) % 7 : START_DAY_OF_WEEK; // Oct 1 is Thursday (4)

    const weeks = [];
    let currentWeek = [];
    
    // Empty cells before start day
    for (let i = 0; i < startDay; i++) {
      currentWeek.push(null);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      currentWeek.push(day);
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
    }
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) currentWeek.push(null);
      weeks.push(currentWeek);
    }

    return (
      <div className="w-full">
        <div className="grid grid-cols-7 gap-1 mb-2 text-center">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d, i) => (
            <div key={d} className={`text-[12px] font-semibold py-1 ${i === 0 ? 'text-slate-300' : 'text-slate-500'}`}>
              {d}
            </div>
          ))}
        </div>
        <div className="flex flex-col gap-1">
          {weeks.map((week, wIdx) => (
            <div key={wIdx} className="grid grid-cols-7 gap-1 text-center">
              {week.map((day, dIdx) => {
                if (!day) return <div key={dIdx} className="p-2" />;
                
                const isSunday = dIdx === 0;
                
                // Mock: disable past dates in September
                const isPast = !isOctMonth && day < 29;
                const isToday = !isOctMonth && day === 29;

                const isDisabled = isSunday || isPast;

                const month = isOctMonth ? 10 : 9;
                const checkStr = `2026-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                
                const isSelected = orderDate === checkStr;

                return (
                  <button
                    key={dIdx}
                    disabled={isDisabled}
                    onClick={() => handleSelectDate(day, isOctMonth)}
                    className={`
                      h-10 rounded-lg text-[14px] font-medium transition-colors flex flex-col items-center justify-center cursor-pointer
                      ${isDisabled ? 'text-slate-300 cursor-not-allowed' : ''}
                      ${!isDisabled && !isSelected ? 'text-slate-700 hover:bg-slate-100' : ''}
                      ${isSelected ? 'bg-brand-600 text-white shadow-sm font-bold' : ''}
                      ${isToday ? 'border border-slate-200' : ''}
                    `}
                  >
                    <span>{day}</span>
                    {isToday && <span className="text-[9px] -mt-1 opacity-70">Today</span>}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-sm mx-auto px-1 w-full">
      {!hideHeader && (
        <div className="text-center mb-4">
          <h2 className="text-[18px] font-bold text-slate-900 mb-1">Delivery Date</h2>
          <p className="text-[13px] text-slate-500">When should this order be delivered?</p>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
          <button 
            type="button"
            disabled={!isOct}
            onClick={handlePrevMonth}
            className={`p-1.5 rounded-md transition-colors ${!isOct ? 'text-slate-300 cursor-not-allowed' : 'text-slate-600 hover:bg-slate-100'}`}
          >
            <ChevronLeft size={18} />
          </button>
          <p className="text-[14px] font-bold text-slate-900">{currentMonth}</p>
          <button 
            type="button"
            disabled={isOct}
            onClick={handleNextMonth}
            className={`p-1.5 rounded-md transition-colors ${isOct ? 'text-slate-300 cursor-not-allowed' : 'text-slate-600 hover:bg-slate-100'}`}
          >
            <ChevronRight size={18} />
          </button>
        </div>
        
        <div className="p-4">
          {renderCalendar(isOct)}
        </div>
      </div>
    </div>
  );
}
