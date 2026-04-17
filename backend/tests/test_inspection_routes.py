from collections import Counter

from app.core.constants.permissions import MONTHLY_DELETE_REPORT, PERMISSIONS_BY_MODULE
from app.modules.inspection.api import router


def test_inspection_router_no_duplicate_paths():
    pairs = []
    for route in router.routes:
        methods = sorted(method for method in route.methods or [] if method in {"GET", "POST", "PUT", "PATCH", "DELETE"})
        for method in methods:
            pairs.append((method, route.path))

    counter = Counter(pairs)
    duplicates = [f"{method} {path}" for (method, path), count in counter.items() if count > 1]
    assert not duplicates


def test_monthly_delete_permission_in_inspection_module():
    assert MONTHLY_DELETE_REPORT in PERMISSIONS_BY_MODULE["inspection"]
