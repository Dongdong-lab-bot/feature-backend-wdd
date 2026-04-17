"""Insert reset-password endpoint before the 执行端 CRUD section"""
import pathlib, re

p = pathlib.Path(__file__).parent.parent / "app/modules/user/api.py"
src = p.read_text(encoding="utf-8-sig", errors="replace")

insert_before = '@router.get("/users")\nasync def list_users('

new_endpoint = '''@router.post("/admin/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: int,
    req: AdminPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """监管端管理员重置指定用户密码。"""
    denied = _ensure_regulator(current_user)
    if denied is not None:
        return denied

    from sqlalchemy import select, update as sql_update
    from app.core.security import hash_password as _hash_pw

    user = (await db.execute(
        select(UserModel).where(
            UserModel.id == user_id,
            UserModel.tenant_id == current_user.tenant_id,
        )
    )).scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="用户不存在", code=404))

    await db.execute(
        sql_update(UserModel)
        .where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
        .values(
            password_hash=_hash_pw(req.new_password),
            token_version=UserModel.token_version + 1,
        )
    )
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": user_id}))


'''

if insert_before in src:
    src = src.replace(insert_before, new_endpoint + insert_before, 1)
    p.write_text(src, encoding="utf-8")
    print("Done")
else:
    print("NOT FOUND")
    idx = src.find("list_users")
    print(repr(src[max(0, idx-200):idx+50]))
