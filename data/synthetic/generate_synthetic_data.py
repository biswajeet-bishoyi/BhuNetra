import os
import json
import random
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
from PIL import Image, ImageDraw, ImageFont

def ensure_dirs():
    os.makedirs("data/synthetic/registry_scans", exist_ok=True)
    os.makedirs("data/satellite", exist_ok=True)
    os.makedirs("models", exist_ok=True)

def generate_parcels():
    print("Generating synthetic cadastral parcels for Telangana (Shamshabad Mandal)...")
    np.random.seed(42)
    random.seed(42)

    # Base coordinates around Shamshabad Mandal, Rangareddy District, Telangana (lat: 17.254, lon: 78.431)
    base_lon, base_lat = 78.431, 17.254
    scale = 0.001 # ~110m scale

    parcels = []
    ground_truth = {}
    
    rows, cols = 6, 7
    parcel_count = 0

    grid_polys = []

    for i in range(rows):
        for j in range(cols):
            parcel_count += 1
            pid = f"P-{100 + parcel_count}"
            
            x0 = base_lon + j * scale
            y0 = base_lat + i * scale
            x1 = x0 + scale * 0.95
            y1 = y0 + scale * 0.95

            # Random slight polygon perturbation
            poly = Polygon([
                (x0 + random.uniform(-0.0001, 0.0001), y0 + random.uniform(-0.0001, 0.0001)),
                (x1 + random.uniform(-0.0001, 0.0001), y0 + random.uniform(-0.0001, 0.0001)),
                (x1 + random.uniform(-0.0001, 0.0001), y1 + random.uniform(-0.0001, 0.0001)),
                (x0 + random.uniform(-0.0001, 0.0001), y1 + random.uniform(-0.0001, 0.0001)),
            ])
            grid_polys.append((pid, poly, i, j))

    # Convert lat/lon approx area in sqm (1 deg lat ~ 111,000m)
    deg_to_m = 111000.0

    # Inject deliberate anomalies into canonical parcels
    anomalous_ids = {
        "P-105": ("OVERLAP", "Severe boundary overlap (>12.4%) with neighboring parcel P-106"),
        "P-112": ("AREA_DEVIATION", "Claimed area in Dharani RoR deed (4500 sqm) exceeds calculated GIS geometry area (2800 sqm) by 60%"),
        "P-118": ("BOUNDARY_GAP", "Unmapped spatial gap (>8m width) along western parcel boundary"),
        "P-124": ("OVERLAP", "Boundary overlap with government road reserve / adjacent parcel P-125"),
        "P-130": ("AREA_DEVIATION", "Claimed area (8200 sqm) significantly deviates from GIS polygon area (5100 sqm)"),
        "P-135": ("LAND_USE_MISMATCH", "Registry claims Agricultural land, satellite scene confirms Commercial/Built-up construction")
    }

    features = []
    
    first_names = ["Kalyan", "Venkat", "Srinivas", "Ravi", "Ananya", "Prasad", "Sujatha", "Anand", "Nagaraju", "Kavitha", "Suresh", "Praveen", "Swapna", "Mahesh"]
    last_names = ["Reddy", "Rao", "Goud", "Chary", "Yadav", "Naidu", "Varma", "Kumar", "Sharma", "Babu"]
    land_uses = ["Agricultural", "Agricultural", "Agricultural", "Residential", "Commercial"]

    for idx_num, (pid, poly, r, c) in enumerate(grid_polys):
        geom = poly
        
        # Inject boundary overlap anomaly if P-105
        if pid == "P-105":
            # Expand P-105 into P-106 space
            coords = list(poly.exterior.coords)
            new_coords = [(pt[0] + 0.0004, pt[1]) if idx in [1, 2] else pt for idx, pt in enumerate(coords)]
            geom = Polygon(new_coords)
        
        # Calculate polygon area in approx sqm
        area_sqm = round(geom.area * (deg_to_m ** 2), 2)
        claimed_area = area_sqm

        if pid in ["P-112", "P-130"]:
            claimed_area = round(area_sqm * 1.6, 2) # Inflated deed claim

        land_use_claim = "Agricultural" if pid == "P-135" else random.choice(land_uses)
        court_status = "Court Case" if pid == "P-105" else ("Stay Order" if pid == "P-118" else random.choice(["Clean", "Clean", "Clean", "Clean", "Mutation Pending"]))
        
        # Assign 3 canonical Telangana demo villages
        if idx_num < 15:
            village = "Shamshabad"
        elif idx_num < 30:
            village = "Mamidipally"
        else:
            village = "Kothwalguda"

        owner = f"{random.choice(first_names)} {random.choice(last_names)}"
        survey_no = f"{100 + r * 10 + c}/A"
        khatian_no = f"KH-{200 + r * 5 + c}"
        ulpin = f"36-78431-{pid.replace('P-', '')}-2026"

        is_anomalous = pid in anomalous_ids
        anom_info = anomalous_ids.get(pid, ("CLEAN", "No anomaly detected"))

        ground_truth[pid] = {
            "is_anomalous": is_anomalous,
            "anomaly_type": anom_info[0],
            "description": anom_info[1],
            "village": village
        }

        prop = {
            "parcel_id": pid,
            "survey_no": survey_no,
            "khatian_no": khatian_no,
            "ulpin": ulpin,
            "owner_name": owner,
            "village": village,
            "mandal": "Shamshabad",
            "district": "Rangareddy",
            "state": "Telangana",
            "claimed_area_sqm": claimed_area,
            "actual_area_sqm": area_sqm,
            "land_use_claim": land_use_claim,
            "revenue_court_status": court_status,
            "is_anomalous": is_anomalous,
            "anomaly_type": anom_info[0]
        }

        features.append({
            "type": "Feature",
            "properties": prop,
            "geometry": geom.__geo_interface__
        })

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    with open("data/synthetic/parcels.geojson", "w") as f:
        json.dump(geojson_data, f, indent=2)

    with open("data/synthetic/ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Generated {len(features)} parcels in data/synthetic/parcels.geojson across Shamshabad, Mamidipally, Kothwalguda")
    print(f"Ground truth saved to data/synthetic/ground_truth.json ({len(anomalous_ids)} anomalous parcels labeled)")

def generate_ownership_history():
    print("Generating synthetic ownership transfer history...")
    with open("data/synthetic/ground_truth.json", "r") as f:
        gt = json.load(f)

    records = []
    parcels = list(gt.keys())
    
    first_names = ["Kalyan", "Venkat", "Srinivas", "Ravi", "Ananya", "Prasad", "Sujatha", "Anand", "Nagaraju", "Kavitha", "Suresh", "Praveen", "Swapna", "Mahesh"]
    last_names = ["Reddy", "Rao", "Goud", "Chary", "Yadav", "Naidu", "Varma", "Kumar", "Sharma", "Babu"]

    for pid in parcels:
        # Standard parcel: 1 to 2 transfers over 10 years
        if pid not in ["P-108", "P-114", "P-122"]:
            owner1 = f"{random.choice(first_names)} {random.choice(last_names)}"
            records.append({
                "parcel_id": pid,
                "owner_name": owner1,
                "transfer_date": "2016-04-12",
                "transfer_type": "Pattadar Passbook / Legacy RoR",
                "deed_number": f"DHARANI-2016-{pid}",
                "price_inr": 2500000,
                "flag_rapid_resale": False
            })
            if random.random() > 0.5:
                owner2 = f"{random.choice(first_names)} {random.choice(last_names)}"
                records.append({
                    "parcel_id": pid,
                    "owner_name": owner2,
                    "transfer_date": "2022-09-18",
                    "transfer_type": "Registered Sale Deed",
                    "deed_number": f"TS-DHARANI-2022-{pid}",
                    "price_inr": 4200000,
                    "flag_rapid_resale": False
                })
        else:
            # Inject Rapid Resale Anomaly (>3 transfers in 30 days)
            o1, o2, o3, o4 = "Venkat Reddy", "Srinivas Goud", "Praveen Rao", "Suresh Chary"
            records.append({"parcel_id": pid, "owner_name": o1, "transfer_date": "2026-05-01", "transfer_type": "Pattadar Allotment", "deed_number": f"TS-DHARANI-2026-A1-{pid}", "price_inr": 5000000, "flag_rapid_resale": False})
            records.append({"parcel_id": pid, "owner_name": o2, "transfer_date": "2026-05-08", "transfer_type": "Registered Sale Deed", "deed_number": f"TS-DHARANI-2026-A2-{pid}", "price_inr": 6800000, "flag_rapid_resale": True})
            records.append({"parcel_id": pid, "owner_name": o3, "transfer_date": "2026-05-15", "transfer_type": "Registered Sale Deed", "deed_number": f"TS-DHARANI-2026-A3-{pid}", "price_inr": 8200000, "flag_rapid_resale": True})
            records.append({"parcel_id": pid, "owner_name": o4, "transfer_date": "2026-05-24", "transfer_type": "Registered Sale Deed", "deed_number": f"TS-DHARANI-2026-A4-{pid}", "price_inr": 9900000, "flag_rapid_resale": True})
            
            # Add to ground truth anomaly records
            gt[pid]["is_anomalous"] = True
            gt[pid]["anomaly_type"] = "RAPID_RESALE"
            gt[pid]["description"] = "Suspicious transaction velocity: 4 transfers recorded within 24 days with steep price escalation."

    with open("data/synthetic/ground_truth.json", "w") as f:
        json.dump(gt, f, indent=2)

    df = pd.DataFrame(records)
    df.to_csv("data/synthetic/ownership_history.csv", index=False)
    print(f"Generated {len(records)} ownership records in data/synthetic/ownership_history.csv")

def generate_registry_scans():
    """Delegate to the browser-render Dharani scan pipeline (generate_scans.py).

    PIL cannot shape Telugu (no libraqm on Windows), so realistic bilingual deed
    scans + field-level extraction ground truth are produced by generate_scans.py,
    which renders each deed as HTML and screenshots it with headless Chrome/Edge.
    """
    
    from generate_scans import generate_scans
    generate_scans()

def generate_satellite_data():
    print("Generating pre-downloaded Sentinel-2 satellite scene for Shamshabad...")
    
    sat_scene = {
        "village": "Mamidipally & Shamshabad",
        "mandal": "Shamshabad",
        "district": "Rangareddy",
        "state": "Telangana",
        "satellite_source": "Sentinel-2 L2A",
        "acquisition_date": "2026-06-15",
        "bands": ["B02_Blue", "B03_Green", "B04_Red", "B08_NIR"],
        "ndvi_mean": 0.64,
        "land_use_classified": {
            "P-135": {
                "claimed_use": "Agricultural",
                "satellite_detected_use": "Commercial/Built-up",
                "built_up_coverage_pct": 78.5,
                "vegetation_ndvi": 0.12,
                "confidence_score": 0.94,
                "mismatch_flag": True,
                "explanation": "High reflectance concrete structure detected (78.5% built-up surface area) conflicting with RoR Agricultural claim."
            },
            "P-101": {
                "claimed_use": "Agricultural",
                "satellite_detected_use": "Agricultural",
                "built_up_coverage_pct": 2.1,
                "vegetation_ndvi": 0.68,
                "confidence_score": 0.98,
                "mismatch_flag": False,
                "explanation": "High NDVI (0.68) active crop canopy matches RoR Agricultural claim."
            },
            "P-112": {
                "claimed_use": "Agricultural",
                "satellite_detected_use": "Agricultural",
                "built_up_coverage_pct": 5.0,
                "vegetation_ndvi": 0.55,
                "confidence_score": 0.92,
                "mismatch_flag": False,
                "explanation": "Vegetation index matches agricultural classification."
            }
        }
    }

    with open("data/satellite/rampur_sentinel2_precomputed.json", "w") as f:
        json.dump(sat_scene, f, indent=2)

    # Preview image
    img = Image.new('RGB', (600, 600), color=(30, 80, 40))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(50, 50), (250, 250)], fill=(40, 140, 50))
    draw.rectangle([(270, 50), (550, 250)], fill=(35, 120, 45))
    draw.rectangle([(50, 270), (250, 550)], fill=(45, 150, 60))
    draw.rectangle([(270, 270), (550, 550)], fill=(160, 140, 120))

    draw.line([(0, 260), (600, 260)], fill=(200, 190, 170), width=12)

    draw.text((20, 20), "SENTINEL-2 L2A - SHAMSHABAD / MAMIDIPALLY (NDVI FALSE COLOR)", fill=(255, 255, 255))
    draw.text((270, 300), "[ANOMALY: P-135 COMMERCIAL WAREHOUSE DETECTED]", fill=(255, 60, 60))

    img.save("data/satellite/rampur_satellite_preview.png")
    print("Pre-downloaded satellite scene saved to data/satellite/")

if __name__ == "__main__":
    ensure_dirs()
    generate_parcels()
    generate_ownership_history()
    generate_registry_scans()
    generate_satellite_data()
    print("All synthetic data generated successfully for Telangana (Shamshabad / Mamidipally / Kothwalguda)!")
