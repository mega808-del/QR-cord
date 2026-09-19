# 🚀 GitHub Pages 배포 안내

앱은 **서버 없이 브라우저에서만 동작**하며 GitHub Pages에서 24시간 무료로 운영됩니다.

- **앱 주소**: https://mega808-del.github.io/QR-cord/
- **공유 링크 형식**: `https://mega808-del.github.io/QR-cord/share.html?p=1.<vCard>.<이름>.<번호>`
  - `?p=` 쿼리스트링 방식을 쓰는 이유: 카카오톡 모바일 등 일부 앱은 URL의 `#` 뒤 조각을 잘라내거나
    이스케이프해 해시 방식 링크를 유실할 수 있음 (쿼리스트링은 유지됨)
  - share.html은 `#` 방식과 `?p=` 방식을 모두 지원

---

## 배포 구조 (현재 상태)

Pages가 **"Deploy from a branch" 모드(저장소 루트 = 사이트)** 로 활성화되어 있으므로
앱 파일(`index.html`, `share.html`, `qrcode.min.js`)이 **저장소 루트에** 있습니다.

- push하면 GitHub이 자동으로 사이트를 재배포합니다 (별도 설정 불필요)
- ⚠️ 저장소의 모든 파일이 웹에 노출됩니다 — 개인정보 파일을 올리지 마세요

## 배포 흐름

```bash
git add -A
git commit -m "update"
git push
```

1~2분 후 자동 반영. 확인: https://mega808-del.github.io/QR-cord/

## 로컬 실행

- 더블클릭: `start.bat` → 로컬 `index.html`을 브라우저로 열기 (오프라인 OK)
- 또는 브라우저에 `https://mega808-del.github.io/QR-cord/` 직접 접속

## 문제 해결

| 증상 | 원인/해결 |
|---|---|
| 사이트 404 | push 후 1~2분 대기, 또는 Settings → Pages에서 배포 상태 확인 |
| 공유 링크 404 | 링크 주소가 `mega808-del.github.io/QR-cord/share.html`로 시작하는지 확인 (구 버전 링크는 만료) |
| 카톡에서 열면 "잘못된 링크" | 링크 뒷부분이 잘린 것 — 길게 눌러 복사 후 브라우저 주소창에 붙여넣기 |
| 모바일에서 저장 안 됨 | QR 이미지를 길게 눌러 "이미지 저장/사진에 추가" |
