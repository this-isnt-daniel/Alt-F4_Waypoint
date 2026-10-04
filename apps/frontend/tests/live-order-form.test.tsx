import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import LiveOrderForm from '../src/pages/storemanager/components/LiveOrderForm';
import { apiFetch } from '../src/lib/api';
vi.mock('../src/lib/api',()=>({apiFetch:vi.fn()}));
afterEach(()=>vi.clearAllMocks());
it('orders canonical catalogue IDs and only reports success after confirmation',async()=>{
 vi.mocked(apiFetch).mockResolvedValueOnce({outlet_id:'OUT015',brand:'style',name:'Style'})
 .mockResolvedValueOnce([{product_id:'PROD-S',name:'Shirt',temp_req:'ambient',unit:'piece',unit_wt_kg:0.2}])
 .mockResolvedValueOnce({order_id:'ORD-LIVE'}).mockResolvedValueOnce({order_id:'ORD-LIVE'});
 render(<LiveOrderForm />);
 await screen.findByLabelText('Quantity for Shirt');
 fireEvent.change(screen.getByLabelText('Delivery date'),{target:{value:'2026-10-06'}});
 fireEvent.change(screen.getByLabelText('Quantity for Shirt'),{target:{value:'2'}});
 fireEvent.click(screen.getByRole('button',{name:'Confirm order'}));
 await screen.findByText('Order ORD-LIVE confirmed. Awaiting allocation.');
 expect(apiFetch).toHaveBeenNthCalledWith(3,'/store-manager/orders',expect.objectContaining({body:JSON.stringify({outlet_id:'OUT015',brand:'style',temp_req:'ambient',order_date:'2026-10-06',items:[{product_id:'PROD-S',quantity:2}]})}));
});
