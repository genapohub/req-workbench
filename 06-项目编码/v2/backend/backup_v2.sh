#!/usr/bin/env bash
# v2 数据备份脚本（AC-25）
# 备份 v2 独立数据目录（SQLite 文件），与 v1.4（8011）完全隔离。
# 支持冷/热备份；热备建议在低峰期执行，生产环境推荐停止服务后用 sqlite .backup。
set -euo pipefail
cd "$(dirname "$0")"

DATA_DIR="${WORKBENCH_DATA_DIR:-$(pwd)/运行数据}"
BACKUP_ROOT="${WORKBENCH_BACKUP_DIR:-$(pwd)/backups}"
mkdir -p "$BACKUP_ROOT"

if [ ! -d "$DATA_DIR" ]; then
  echo "数据目录不存在：$DATA_DIR（请先启动一次后端以生成种子数据）" >&2
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
NAME="wb_v2_data_${TS}.tar.gz"
DEST="$BACKUP_ROOT/$NAME"

tar -czf "$DEST" -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")"
SHA="$(shasum -a 256 "$DEST" | awk '{print $1}')"
echo "$SHA  $NAME" > "$BACKUP_ROOT/wb_v2_data_${TS}.sha256"
ln -sf "$DEST" "$BACKUP_ROOT/latest.tar.gz"

echo "备份完成：$DEST"
echo "SHA256：$SHA"
echo "大小：$(du -h "$DEST" | awk '{print $1}')"
echo "校验清单：$BACKUP_ROOT/wb_v2_data_${TS}.sha256"
