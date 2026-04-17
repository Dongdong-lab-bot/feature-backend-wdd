"""merge all heads

版本 ID: 56c170054082
上一个版本: 20260224_merge_heads_only, 74f8aad4bd97
创建时间: 2026-02-24 22:26:38.971831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# 迁移脚本标识信息，供 Alembic 使用
revision: str = '56c170054082'
down_revision: Union[str, Sequence[str], None] = ('20260224_merge_heads_only', '74f8aad4bd97')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库结构。"""
    pass


def downgrade() -> None:
    """回退数据库结构。"""
    pass
