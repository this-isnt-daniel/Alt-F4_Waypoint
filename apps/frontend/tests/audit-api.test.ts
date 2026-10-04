import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchLoaderQueue, fetchLoaderWorkbench } from '../src/pages/loader/loaderApi';
import { postDriverEvent } from '../src/driver/api';
import { safeStorage } from '../src/lib/security';

afterEach(() => { vi.unstubAllGlobals(); safeStorage.remove('token'); });
it('loader uses one API prefix and passes authorization', async () => {
  const fetchMock=vi.fn().mockResolvedValue({ok:true,text:async()=> '[]'});
  vi.stubGlobal('fetch',fetchMock);
  await fetchLoaderQueue('test-token');
  await fetchLoaderWorkbench('test-token','trip with spaces');
  expect(fetchMock.mock.calls[0]![0]).toBe('http://localhost:8000/api/v1/loader/queue');
  expect(fetchMock.mock.calls[0]![1].headers.Authorization).toBe('Bearer test-token');
  expect(fetchMock.mock.calls[1]![0]).toContain('/trips/trip%20with%20spaces/workbench');
});
for (const status of ['failed','conflict','applied','already_applied']) {
  it(`driver recognizes ${status} inside HTTP 200`, async () => {
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({results:[{client_event_id:'E1',status,error:'rejected'}]})}));
    const result=postDriverEvent('stop.arrived','STOP1',{base_row_version:3},'E1');
    if (['applied','already_applied'].includes(status)) await expect(result).resolves.toMatchObject({status});
    else await expect(result).rejects.toThrow('rejected');
  });
}
