from datetime import date, timedelta, datetime, timezone
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.shared import TripStopItemResponse
from app.api.v1.dispatcher.operations import VehicleOperationalResponse
from app.services.order_service import order_cutoff
from test_store_manager import store_manager_db, client, get_auth_header
from receipt_fixture import record_delivery
from app.models.delivery import Discrepancy


def draft(client, **changes):
    body = dict(outlet_id='OUT100', brand='fresh', temp_req='ambient',
                order_date=str(date.today() + timedelta(days=7)), items=[dict(product_id='P200', quantity=4)])
    body.update(changes)
    headers = get_auth_header(client, 'sm1')
    return client.post('/api/v1/store-manager/orders', headers=headers, json=body), headers


def test_expired_cutoff_cannot_confirm(client):
    result, headers = draft(client, order_date=str(date.today()))
    assert result.status_code == 200
    response = client.post(f'/api/v1/store-manager/orders/{result.json()["order_id"]}/confirm', headers=headers)
    assert response.status_code == 409
    assert '16:00' in response.json()['detail']


def test_colombo_cutoff_exact_utc_instant():
    assert order_cutoff(date(2026,10,6)).astimezone(timezone.utc) == datetime(2026,10,5,10,30,tzinfo=timezone.utc)


@pytest.mark.parametrize('changes', [dict(brand='tech'), dict(items=[dict(product_id='P100',quantity=1)]), dict(items=[dict(product_id='P300',quantity=1)])])
def test_brand_and_cold_chain_not_client_controlled(client, changes):
    result, _ = draft(client, **changes)
    assert result.status_code == 400


def test_receipt_cannot_deliver_a_draft(client):
    result, headers = draft(client)
    response = client.post(f'/api/v1/store-manager/orders/{result.json()["order_id"]}/receipt', headers=headers,
                           json=dict(client_op_id='early',pod_id='made-up',items_ok=True))
    assert response.status_code == 409


def test_receipt_requires_matching_pod_and_keeps_zero_actual(client, store_manager_db):
    result, headers = draft(client)
    order_id = result.json()['order_id']
    record_delivery(store_manager_db, order_id, 'POD-REAL')
    path=f'/api/v1/store-manager/orders/{order_id}/receipt'
    response=client.post(path,headers=headers,json=dict(client_op_id='bad',pod_id='POD-FAKE',items_ok=True))
    assert response.status_code==400
    response=client.post(path,headers=headers,json=dict(client_op_id='ok',pod_id='POD-REAL',items_ok=False,
        discrepancies=[dict(product_id='P200', expected_qty=4,actual_qty=0,reason_code='missing')]))
    assert response.status_code==200, response.text
    assert store_manager_db.query(Discrepancy).one().reported_qty==4


def test_trip_item_orm_fields_match_response_contract():
    item=TripStopItemResponse.model_validate(SimpleNamespace(item_id='I',sku='P',qty_assigned=4,
        qty_loaded=3,qty_delivered=2,qty_returned=1))
    assert item.model_dump()==dict(item_id='I',product_id='P',quantity=4,loaded_qty=3,delivered_qty=2,returned_qty=1)


def test_fleet_response_has_capacity_fields():
    item=VehicleOperationalResponse.model_validate(dict(vehicle_id='V',depot_id='D',type='van',temp='reefer',
        status='available',weight_cap_kg=1000,vol_cap_m3=10,fuel_quota_l=200))
    assert item.weight_cap_kg==1000 and item.vol_cap_m3==10 and item.fuel_quota_l==200


def test_fleet_openapi_matches_runtime_contract():
    spec = TestClient(app).get('/openapi.json').json()
    response = spec['paths']['/api/v1/dispatcher/vehicles']['get']['responses']['200']['content']['application/json']['schema']
    name = response['items']['$ref'].split('/')[-1]
    assert 'weight_cap_kg' in spec['components']['schemas'][name]['properties']
