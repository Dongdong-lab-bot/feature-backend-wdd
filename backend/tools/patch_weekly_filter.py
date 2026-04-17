"""Patch: add canteen_id filter to list_weekly_tasks in api.py"""
import re, pathlib

path = pathlib.Path(__file__).parent.parent / "app/modules/inspection/api.py"
content = path.read_text(encoding="utf-8", errors="replace")

# Find the list_weekly_tasks function and insert canteen_id param + filter
# Strategy: find the page_size query param line before `db: AsyncSession = Depends(get_db)`
# and insert canteen_id after it, then add the filter inside the function body.

old_sig = '    page_size: int = Query(20, ge=1, le=1000),\n    db: AsyncSession = Depends(get_db),'
new_sig = '    page_size: int = Query(20, ge=1, le=1000),\n    canteen_id: Optional[int] = Query(None, description="按食堂ID过滤"),\n    db: AsyncSession = Depends(get_db),'

if old_sig not in content:
    print("SIGNATURE NOT FOUND")
else:
    content = content.replace(old_sig, new_sig, 1)
    print("Signature patched OK")

# Now add the canteen_id filter after the status filter
old_filter = '    if status:\n        filters.append(InspectionTask.status == status)\n    if keyword:'
new_filter = '    if status:\n        filters.append(InspectionTask.status == status)\n    if canteen_id:\n        filters.append(InspectionTask.canteen_id == canteen_id)\n    if keyword:'

if old_filter not in content:
    print("FILTER BLOCK NOT FOUND")
else:
    content = content.replace(old_filter, new_filter, 1)
    print("Filter block patched OK")

path.write_text(content, encoding="utf-8")
print("Done")
