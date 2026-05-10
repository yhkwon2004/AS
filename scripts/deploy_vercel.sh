#!/usr/bin/env bash
set -euo pipefail

if ! command -v npx >/dev/null 2>&1; then
  echo "[오류] npx(Node.js)가 필요합니다."
  exit 1
fi

: "${VERCEL_TOKEN:?VERCEL_TOKEN 환경변수가 필요합니다.}"
: "${VERCEL_ORG_ID:?VERCEL_ORG_ID 환경변수가 필요합니다.}"
: "${VERCEL_PROJECT_ID:?VERCEL_PROJECT_ID 환경변수가 필요합니다.}"

npx vercel pull --yes --environment=production --token "$VERCEL_TOKEN"
npx vercel build --prod --token "$VERCEL_TOKEN"
npx vercel deploy --prebuilt --prod --token "$VERCEL_TOKEN"
