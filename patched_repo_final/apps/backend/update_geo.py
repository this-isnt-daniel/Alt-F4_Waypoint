import sys
import re

with open('app/services/geo_service.py', 'r') as f:
    content = f.read()

# 1. Imports
content = content.replace('import sqlite3', 'from sqlalchemy.orm import Session\nfrom app.models.road_geometry import RoadGeometry\nfrom app.models.trip import TripStop\nfrom app.models.outlet import Outlet')
content = content.replace('sqlite3.Connection', 'Session')

# 2. get_outlet_coordinates query
old_outlet_query = '''        try:
            row = db.execute(
                "SELECT lat, lng FROM stops WHERE outlet_id = ? AND lat IS NOT NULL LIMIT 1",
                (clean_id,),
            ).fetchone()
            if row and row["lat"] is not None and row["lng"] is not None:
                return float(row["lat"]), float(row["lng"])
        except Exception:
            pass'''

new_outlet_query = '''        try:
            outlet = db.query(Outlet.lat, Outlet.lng).filter(Outlet.outlet_id == clean_id, Outlet.lat.isnot(None)).first()
            if outlet and outlet.lat is not None and outlet.lng is not None:
                return float(outlet.lat), float(outlet.lng)
        except Exception:
            pass'''
content = content.replace(old_outlet_query, new_outlet_query)

# 3. lookup_or_fetch_edge queries
old_edge_query_1 = '''    row = db.execute(
        "SELECT from_id, to_id, coords, coord_version, distance_meters, duration_seconds "
        "FROM road_geometry WHERE from_id = ? AND to_id = ? AND coord_version = ?",
        (from_id, to_id, coord_version),
    ).fetchone()
    if row:
        coords = json.loads(row["coords"]) if isinstance(row["coords"], str) else row["coords"]
        return {
            "from_id": row["from_id"],
            "to_id": row["to_id"],
            "coords": coords,
            "coord_version": row["coord_version"],
            "distance_meters": row["distance_meters"],
            "duration_seconds": row["duration_seconds"],
        }'''

new_edge_query_1 = '''    row = db.query(RoadGeometry).filter_by(from_id=from_id, to_id=to_id, coord_version=coord_version).first()
    if row:
        coords = json.loads(row.coords) if isinstance(row.coords, str) else row.coords
        return {
            "from_id": row.from_id,
            "to_id": row.to_id,
            "coords": coords,
            "coord_version": row.coord_version,
            "distance_meters": row.distance_meters,
            "duration_seconds": row.duration_seconds,
        }'''
content = content.replace(old_edge_query_1, new_edge_query_1)

old_edge_query_2 = '''    rev_row = db.execute(
        "SELECT from_id, to_id, coords, coord_version, distance_meters, duration_seconds "
        "FROM road_geometry WHERE from_id = ? AND to_id = ? AND coord_version = ?",
        (to_id, from_id, coord_version),
    ).fetchone()
    if rev_row:
        rev_coords = json.loads(rev_row["coords"]) if isinstance(rev_row["coords"], str) else rev_row["coords"]
        reversed_coords = list(reversed(rev_coords))
        db.execute(
            "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                from_id,
                to_id,
                json.dumps(reversed_coords),
                coord_version,
                rev_row["distance_meters"],
                rev_row["duration_seconds"],
            ),
        )
        db.commit()
        return {
            "from_id": from_id,
            "to_id": to_id,
            "coords": reversed_coords,
            "coord_version": coord_version,
            "distance_meters": rev_row["distance_meters"],
            "duration_seconds": rev_row["duration_seconds"],
        }'''

new_edge_query_2 = '''    rev_row = db.query(RoadGeometry).filter_by(from_id=to_id, to_id=from_id, coord_version=coord_version).first()
    if rev_row:
        rev_coords = json.loads(rev_row.coords) if isinstance(rev_row.coords, str) else rev_row.coords
        reversed_coords = list(reversed(rev_coords))
        new_geom = RoadGeometry(
            from_id=from_id,
            to_id=to_id,
            coords=json.dumps(reversed_coords),
            coord_version=coord_version,
            distance_meters=rev_row.distance_meters,
            duration_seconds=rev_row.duration_seconds
        )
        db.merge(new_geom)
        db.commit()
        return {
            "from_id": from_id,
            "to_id": to_id,
            "coords": reversed_coords,
            "coord_version": coord_version,
            "distance_meters": rev_row.distance_meters,
            "duration_seconds": rev_row.duration_seconds,
        }'''
content = content.replace(old_edge_query_2, new_edge_query_2)

old_edge_insert = '''    db.execute(
        "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            from_id,
            to_id,
            json.dumps(route_data["coords"]),
            coord_version,
            route_data.get("distance_meters"),
            route_data.get("duration_seconds"),
        ),
    )
    # Also save reverse
    db.execute(
        "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            to_id,
            from_id,
            json.dumps(list(reversed(route_data["coords"]))),
            coord_version,
            route_data.get("distance_meters"),
            route_data.get("duration_seconds"),
        ),
    )
    db.commit()'''

new_edge_insert = '''    db.merge(RoadGeometry(
        from_id=from_id,
        to_id=to_id,
        coords=json.dumps(route_data["coords"]),
        coord_version=coord_version,
        distance_meters=route_data.get("distance_meters"),
        duration_seconds=route_data.get("duration_seconds")
    ))
    db.merge(RoadGeometry(
        from_id=to_id,
        to_id=from_id,
        coords=json.dumps(list(reversed(route_data["coords"]))),
        coord_version=coord_version,
        distance_meters=route_data.get("distance_meters"),
        duration_seconds=route_data.get("duration_seconds")
    ))
    db.commit()'''
content = content.replace(old_edge_insert, new_edge_insert)


old_resolve_seq = '''        row = db.execute(
            "SELECT from_id, to_id, coords, coord_version, distance_meters, duration_seconds "
            "FROM road_geometry WHERE from_id = ? AND to_id = ? AND coord_version = ?",
            (f, t, coord_version),
        ).fetchone()
        if row:
            resolved[f"{f}|{t}"] = {
                "from_id": f,
                "to_id": t,
                "coords": json.loads(row["coords"]) if isinstance(row["coords"], str) else row["coords"],
                "coord_version": row["coord_version"],
                "distance_meters": row["distance_meters"],
                "duration_seconds": row["duration_seconds"],
            }
        else:
            # Check reverse
            rev_row = db.execute(
                "SELECT from_id, to_id, coords, coord_version, distance_meters, duration_seconds "
                "FROM road_geometry WHERE from_id = ? AND to_id = ? AND coord_version = ?",
                (t, f, coord_version),
            ).fetchone()
            if rev_row:
                rev_coords = json.loads(rev_row["coords"]) if isinstance(rev_row["coords"], str) else rev_row["coords"]
                rev_list = list(reversed(rev_coords))
                db.execute(
                    "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (f, t, json.dumps(rev_list), coord_version, rev_row["distance_meters"], rev_row["duration_seconds"]),
                )
                resolved[f"{f}|{t}"] = {
                    "from_id": f,
                    "to_id": t,
                    "coords": rev_list,
                    "coord_version": coord_version,
                    "distance_meters": rev_row["distance_meters"],
                    "duration_seconds": rev_row["duration_seconds"],
                }
            else:
                missing_indices.append(i)'''

new_resolve_seq = '''        row = db.query(RoadGeometry).filter_by(from_id=f, to_id=t, coord_version=coord_version).first()
        if row:
            resolved[f"{f}|{t}"] = {
                "from_id": f,
                "to_id": t,
                "coords": json.loads(row.coords) if isinstance(row.coords, str) else row.coords,
                "coord_version": row.coord_version,
                "distance_meters": row.distance_meters,
                "duration_seconds": row.duration_seconds,
            }
        else:
            rev_row = db.query(RoadGeometry).filter_by(from_id=t, to_id=f, coord_version=coord_version).first()
            if rev_row:
                rev_coords = json.loads(rev_row.coords) if isinstance(rev_row.coords, str) else rev_row.coords
                rev_list = list(reversed(rev_coords))
                db.merge(RoadGeometry(
                    from_id=f, to_id=t, coords=json.dumps(rev_list),
                    coord_version=coord_version, distance_meters=rev_row.distance_meters,
                    duration_seconds=rev_row.duration_seconds
                ))
                resolved[f"{f}|{t}"] = {
                    "from_id": f,
                    "to_id": t,
                    "coords": rev_list,
                    "coord_version": coord_version,
                    "distance_meters": rev_row.distance_meters,
                    "duration_seconds": rev_row.duration_seconds,
                }
            else:
                missing_indices.append(i)'''
content = content.replace(old_resolve_seq, new_resolve_seq)


old_batch_insert = '''        for i, leg_data in enumerate(batch_legs):
            f, t = edges[i]
            # Save directed
            db.execute(
                "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (f, t, json.dumps(leg_data["coords"]), coord_version, leg_data["distance_meters"], leg_data["duration_seconds"]),
            )
            # Save reverse
            db.execute(
                "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (t, f, json.dumps(list(reversed(leg_data["coords"]))), coord_version, leg_data["distance_meters"], leg_data["duration_seconds"]),
            )
            resolved[f"{f}|{t}"] = {
                "from_id": f,
                "to_id": t,
                "coords": leg_data["coords"],
                "coord_version": coord_version,
                "distance_meters": leg_data["distance_meters"],
                "duration_seconds": leg_data["duration_seconds"],
            }
        db.commit()'''

new_batch_insert = '''        for i, leg_data in enumerate(batch_legs):
            f, t = edges[i]
            db.merge(RoadGeometry(
                from_id=f, to_id=t, coords=json.dumps(leg_data["coords"]),
                coord_version=coord_version, distance_meters=leg_data["distance_meters"],
                duration_seconds=leg_data["duration_seconds"]
            ))
            db.merge(RoadGeometry(
                from_id=t, to_id=f, coords=json.dumps(list(reversed(leg_data["coords"]))),
                coord_version=coord_version, distance_meters=leg_data["distance_meters"],
                duration_seconds=leg_data["duration_seconds"]
            ))
            resolved[f"{f}|{t}"] = {
                "from_id": f,
                "to_id": t,
                "coords": leg_data["coords"],
                "coord_version": coord_version,
                "distance_meters": leg_data["distance_meters"],
                "duration_seconds": leg_data["duration_seconds"],
            }
        db.commit()'''
content = content.replace(old_batch_insert, new_batch_insert)

with open('app/services/geo_service.py', 'w') as fh:
    fh.write(content)
