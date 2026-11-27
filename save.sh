#!/usr/bin/env bash
# 전체 변경분을 현재 브랜치에 커밋하고 푸시한다.
# 사용법: ./save.sh ["커밋 메시지"]
set -euo pipefail
cd "$(dirname "$0")"

msg="${1:-자료 업데이트 $(date '+%Y-%m-%d %H:%M')}"
branch="$(git rev-parse --abbrev-ref HEAD)"

# 문서가 바뀌었으면 열람 페이지도 다시 빌드
if command -v python3 >/dev/null && python3 -c "import markdown" 2>/dev/null; then
  python3 tools/build.py >/dev/null
fi

git add -A
if git diff --cached --quiet; then
  echo "변경 없음 ($branch)"
  exit 0
fi
git commit -q -m "$msg"
git push -q -u origin "$branch"
echo "커밋·푸시 완료: $branch $(git rev-parse --short HEAD) — $msg"
