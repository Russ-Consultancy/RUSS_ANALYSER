import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
CATALOGS = BASE.parent / "vm_catalogs"

def recommend_vm_shape(cloud: str, vcpus: float, memory_gb: float):
    cloud = cloud.lower()
    if cloud == "azure":
        files = [CATALOGS / "azure_shapes_e.json", CATALOGS / "azure_shapes_m.json"]
    else:
        files = [CATALOGS / f"{cloud}_shapes.json"]

    catalog = []
    for f in files:
        if f.exists():
            catalog.extend(json.loads(f.read_text()))
    if not catalog:
        return {"name":"No catalog found","vcpus":"-","memory":"-","category":"-","price_per_hour":"-","monthly_cost":"-"}

    # choose the smallest VM that meets vcpu & memory
    best=None; min_diff=float("inf")
    for vm in catalog:
        if vm["vcpus"]>=vcpus and vm["memory"]>=memory_gb:
            diff = (vm["vcpus"]-vcpus) + ((vm["memory"]-memory_gb)/4.0)
            if diff < min_diff:
                min_diff = diff
                best = vm

    if not best:
        return {"name":"Custom VM Required","vcpus":"-","memory":"-","category":"-","price_per_hour":"-","monthly_cost":"-"}

    price_per_hour = best.get("price_per_hour",0) or 0
    monthly_cost = round(price_per_hour * 730, 2)   # 730 hours/month baseline
    out = best.copy()
    out["monthly_cost"] = monthly_cost
    return out
