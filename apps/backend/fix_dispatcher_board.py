import os

FILE_PATH = r"c:\Users\shami\OneDrive\Documents\GitHub\Alt-F4_Waypoint\apps\frontend\src\pages\dispatcher\RouteAllocationBoard.jsx"

with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Add import if missing
if "import { apiFetch }" not in content:
    content = content.replace("import React, { useState, useCallback } from 'react';", "import React, { useState, useCallback } from 'react';\nimport { apiFetch } from '../../lib/api';")

old_func = """  const handleFinalConfirm = (_note) => {
    setShowConfirmModal(false);
    if (onConfirmAllocations) {
      onConfirmAllocations();
    } else {
      setConfirmed(true);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 4000);
    }
  };"""

new_func = """  const handleFinalConfirm = async (_note) => {
    setShowConfirmModal(false);
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await apiFetch('/dispatcher/plans/draft', {
        method: 'POST',
        body: JSON.stringify({ target_date: today })
      });
      await apiFetch(`/dispatcher/plans/${res.plan_id || res.run_id}/approve`, {
        method: 'POST',
        body: JSON.stringify({})
      });
      setConfirmed(true);
      setShowToast(true);
      setTimeout(() => {
        setShowToast(false);
        if (onConfirmAllocations) {
          onConfirmAllocations();
        }
      }, 2000);
    } catch (e) {
      console.error(e);
      alert('Failed to plan: ' + e.message);
    }
  };"""

content = content.replace(old_func, new_func)

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched RouteAllocationBoard.jsx")
