import asyncio
import inspect
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

try:
    from app.db.session import engine
    from app.modules.user import service
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Runtime Error during import: {e}")
    sys.exit(1)

async def verify():
    print("=" * 50)
    print("🚀 Safefood Platform - Async Architecture Verification")
    print("=" * 50)
    
    errors = []

    # 1. Check Engine Type
    print(f"\n[1/3] Checking Database Engine...")
    if isinstance(engine, AsyncEngine):
        print(f"✅ PASS: Engine is AsyncEngine ({type(engine).__name__})")
        print(f"   Driver: {engine.driver}")
    else:
        msg = f"❌ FAIL: Engine is NOT AsyncEngine. Got: {type(engine)}"
        print(msg)
        errors.append(msg)

    # 2. Check Service Functions
    print(f"\n[2/3] Checking Service Layer (User Module)...")
    funcs_to_check = [
        "create_user_from_external",
        "ensure_default_tenant_and_org",
        "link_external_identity",
        "rotate_refresh_token"
    ]
    
    for name in funcs_to_check:
        if not hasattr(service, name):
            print(f"⚠️  SKIP: Function {name} not found in service module")
            continue
            
        func = getattr(service, name)
        if inspect.iscoroutinefunction(func):
            print(f"✅ PASS: {name} is async")
        else:
            msg = f"❌ FAIL: {name} is SYNC (blocking)!"
            print(msg)
            errors.append(msg)

    # 3. Connectivity Test
    print(f"\n[3/3] Testing Database Connectivity (SELECT 1)...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            print(f"✅ PASS: Successfully executed async query. Result: {val}")
    except Exception as e:
        msg = f"❌ FAIL: Database connection failed: {str(e)}"
        print(msg)
        errors.append(msg)

    print("\n" + "=" * 50)
    if not errors:
        print("🎉 SUCCESS: All async architecture checks passed!")
    else:
        print(f"⚠️  FOUND {len(errors)} ISSUES:")
        for err in errors:
            print(f"   - {err}")
    print("=" * 50)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())