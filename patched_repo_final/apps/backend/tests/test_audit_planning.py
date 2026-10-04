from test_planning_security_and_alembic import plan_security_db, client
from app.models.vehicle import Vehicle
from app.models.trip import Trip


def make_plan(client):
    login = client.post('/api/v1/auth/login',json={'username':'dispatcher_sec','password':'pass123'})
    headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
    res = client.post('/api/v1/dispatcher/plans/draft',headers=headers,json={'target_date':'2026-10-02'})
    assert res.status_code==200, res.text
    return res.json(), headers


def test_approval_preserves_driver_and_plan_metadata(client, plan_security_db):
    for vehicle in plan_security_db.query(Vehicle):
        vehicle.driver_id='U-DRV-SEC'
    plan_security_db.commit()
    plan, headers=make_plan(client)
    assert plan['trips']
    res=client.post(f'/api/v1/dispatcher/plans/{plan["plan_id"]}/approve',headers=headers,json={})
    assert res.status_code==200, res.text
    trips=plan_security_db.query(Trip).all()
    assert trips and all(t.driver_id=='U-DRV-SEC' for t in trips)
    assert all(t.dist_km is not None and t.est_fuel_l is not None and t.plan_return for t in trips)
    res=client.post(f'/api/v1/dispatcher/plans/{plan["plan_id"]}/edit',headers=headers,json={'actions':[]})
    assert res.status_code==409


def test_two_drafts_cannot_reassign_the_same_order(client, plan_security_db):
    first, headers=make_plan(client)
    second, _=make_plan(client)
    res=client.post(f'/api/v1/dispatcher/plans/{first["plan_id"]}/approve',headers=headers,json={})
    assert res.status_code==200
    before=[(t.trip_id,t.status) for t in plan_security_db.query(Trip)]
    res=client.post(f'/api/v1/dispatcher/plans/{second["plan_id"]}/approve',headers=headers,json={})
    assert res.status_code==409, res.text
    assert [(t.trip_id,t.status) for t in plan_security_db.query(Trip)]==before


def test_fleet_runtime_includes_capacities(client, plan_security_db):
    _, headers=make_plan(client)
    response=client.get('/api/v1/dispatcher/vehicles',headers=headers)
    assert response.status_code==200
    assert response.json() and all(v['weight_cap_kg']>0 and v['vol_cap_m3']>0 for v in response.json())
