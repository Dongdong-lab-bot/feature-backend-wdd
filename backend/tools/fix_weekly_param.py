"""Fix: add canteen_id param to list_weekly_tasks signature"""
import pathlib

p = pathlib.Path(__file__).parent.parent / "app/modules/inspection/api.py"
src = p.read_text(encoding="utf-8-sig", errors="replace")

old = (
    "    page_size: int = Query(20, ge=1, le=1000),\n"
    "    db: AsyncSession = Depends(get_db),\n"
    "):\n"
    "    filters = [InspectionTask.inspection_type == InspectionType.WEEKLY]"
)
new = (
    "    page_size: int = Query(20, ge=1, le=1000),\n"
    "    canteen_id: Optional[int] = Query(None, description=\"按食堂ID过滤\"),\n"
    "    db: AsyncSession = Depends(get_db),\n"
    "):\n"
    "    filters = [InspectionTask.inspection_type == InspectionType.WEEKLY]"
)

count = src.count(old)
print("occurrences:", count)
if count == 1:
    src = src.replace(old, new)
    p.write_text(src, encoding="utf-8")
    print("Done")
elif count > 1:
    print("multiple matches")
else:
    print("not found")
    idx = src.find("async def list_weekly_tasks")
    print(repr(src[idx:idx+600]))
