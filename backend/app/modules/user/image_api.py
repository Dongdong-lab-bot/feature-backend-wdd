import base64
import hashlib
import hmac
import os
import shutil
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db import get_db
from app.modules.user.models import Image, User as UserModel
from app.modules.user.schemas import GenericResponse

router = APIRouter()

# 营业执照专用静态目录（使用绝对路径，避免工作目录影响）
# __file__ = backend/app/modules/user/image_api.py → 向上四级为 backend/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LICENSE_IMAGE_DIR = os.path.join(_BACKEND_DIR, "image_license")

os.makedirs(settings.image_upload_dir, exist_ok=True)
os.makedirs(LICENSE_IMAGE_DIR, exist_ok=True)


def _get_base_url(request: Request) -> str:
    configured = (settings.public_base_url or "").strip()
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


def _encode_public_file_token(image_id: int, expires_at: int) -> str:
    payload = f"{image_id}:{expires_at}"
    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    raw = f"{payload}:{digest}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _decode_public_file_token(token: str) -> tuple[int, int]:
    padding = "=" * ((4 - len(token) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode((token + padding).encode("utf-8")).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌")
    parts = decoded.split(":")
    if len(parts) != 3:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌")
    image_id_raw, expires_at_raw, digest = parts
    payload = f"{image_id_raw}:{expires_at_raw}"
    expected = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(digest, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌")
    try:
        image_id = int(image_id_raw)
        expires_at = int(expires_at_raw)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌")
    if int(datetime.now().timestamp()) > expires_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="访问令牌已过期")
    return image_id, expires_at


def _build_signed_public_url(base_url: str, image_id: int, expires_in_seconds: int) -> tuple[str, int]:
    expires_at = int(datetime.now().timestamp()) + expires_in_seconds
    token = _encode_public_file_token(image_id, expires_at)
    return f"{base_url}/files/public/{token}", expires_at


@router.post("/api/images/upload", response_model=GenericResponse)
@router.post("/images/upload", response_model=GenericResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持图片文件"
        )

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    original_name = os.path.basename(file.filename or "image")
    filename = f"{timestamp}_{original_name}"
    filepath = os.path.join(settings.image_upload_dir, filename)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )

    db_image = Image(
        filename=filename,
        filepath=filepath,
        description=description,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)

    base_url = _get_base_url(request)
    public_url, expires_at = _build_signed_public_url(
        base_url, db_image.id, settings.file_public_token_expire_seconds
    )
    return GenericResponse(
        success=True,
        message="图片上传成功",
        data={
            "image_id": db_image.id,
            "filename": db_image.filename,
            "url": f"/api/images/{db_image.id}",
            "public_url": public_url,
            "expires_at": expires_at,
        }
    )


@router.post("/images/license/upload", response_model=GenericResponse)
async def upload_license_image(
    request: Request,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
):
    _ = description
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持图片文件"
        )

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    original_name = os.path.basename(file.filename or "file")
    _, ext = os.path.splitext(original_name)
    filename = f"license_{current_user.tenant_id}_{timestamp}{ext}"
    filepath = os.path.join(LICENSE_IMAGE_DIR, filename)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )

    relative_url = f"/image_license/{filename}"
    public_url = f"{_get_base_url(request)}{relative_url}"
    return GenericResponse(
        success=True,
        message="营业执照上传成功",
        data={
            "filename": filename,
            "url": relative_url,
            "public_url": public_url,
        }
    )


@router.get("/api/images/{image_id}")
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    db_image = (await db.execute(select(Image).where(Image.id == image_id))).scalar_one_or_none()
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    if db_image.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    if not os.path.exists(db_image.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片文件不存在"
        )

    return FileResponse(
        db_image.filepath,
        media_type="image/*",
        filename=db_image.filename
    )


@router.get("/images/{image_id}")
async def get_image_without_prefix(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    db_image = (await db.execute(select(Image).where(Image.id == image_id))).scalar_one_or_none()
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    if db_image.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    if not os.path.exists(db_image.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片文件不存在"
        )

    return FileResponse(
        db_image.filepath,
        media_type="image/*",
        filename=db_image.filename
    )


@router.get("/files/{image_id}/signed-url", response_model=GenericResponse)
async def get_signed_image_url(
    request: Request,
    image_id: int,
    expires_in: int = Query(default=settings.file_public_token_expire_seconds, ge=60, le=604800),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    db_image = (await db.execute(select(Image).where(Image.id == image_id))).scalar_one_or_none()
    if not db_image or db_image.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    if not os.path.exists(db_image.filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片文件不存在")
    public_url, expires_at = _build_signed_public_url(_get_base_url(request), image_id, expires_in)
    return GenericResponse(
        success=True,
        message="success",
        data={
            "image_id": image_id,
            "public_url": public_url,
            "expires_at": expires_at,
        },
    )


@router.get("/files/public/{token}")
async def get_public_image_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    image_id, _ = _decode_public_file_token(token)
    db_image = (await db.execute(select(Image).where(Image.id == image_id))).scalar_one_or_none()
    if not db_image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    if not os.path.exists(db_image.filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片文件不存在")
    return FileResponse(
        db_image.filepath,
        media_type="image/*",
        filename=db_image.filename,
    )


@router.delete("/api/images/{image_id}", response_model=GenericResponse)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    db_image = (await db.execute(select(Image).where(Image.id == image_id))).scalar_one_or_none()
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    if db_image.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    if os.path.exists(db_image.filepath):
        try:
            os.remove(db_image.filepath)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件删除失败: {str(e)}"
            )

    await db.delete(db_image)
    await db.commit()

    return GenericResponse(
        success=True,
        message="图片删除成功"
    )


@router.get("/api/images")
async def get_images(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    images = (
        await db.execute(
            select(Image)
            .where(Image.tenant_id == current_user.tenant_id)
            .offset(skip)
            .limit(limit)
        )
    ).scalars().all()

    base_url = _get_base_url(request)
    image_list = []
    for image in images:
        public_url, expires_at = _build_signed_public_url(
            base_url, image.id, settings.file_public_token_expire_seconds
        )
        image_list.append({
            "id": image.id,
            "filename": image.filename,
            "description": image.description,
            "url": f"/api/images/{image.id}",
            "public_url": public_url,
            "expires_at": expires_at,
            "created_at": image.created_at
        })

    return {
        "images": image_list,
        "skip": skip,
        "limit": limit
    }
