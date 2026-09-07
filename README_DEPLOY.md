# 황금이네 순위체커 - Streamlit 배포

## 1. 로컬에서 최초 네이버 로그인 상태 만들기

```bash
pip install -r requirements.txt
python -m playwright install chromium
python local_naver_login.py
```

열린 Chrome에서 네이버에 로그인한 뒤 터미널에서 Enter를 누르면 `naver_auth_state.json`이 생성됩니다.
이 파일에는 로그인 세션이 있으므로 GitHub에 올리거나 타인에게 공유하지 마세요.

## 2. GitHub 업로드

이 폴더 전체를 Git 저장소에 올리면 됩니다. `.gitignore`가 인증 파일과 API 키 파일을 제외합니다.

```bash
git init
git add .
git commit -m "Deploy golden bid checker"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## 3. Supabase 영구 저장소 만들기

Supabase 프로젝트의 SQL Editor에서 `SUPABASE_SETUP.sql`을 실행합니다.
그 후 Project URL과 **service_role key**를 준비합니다. service_role key는 GitHub에 절대 올리지 마세요.

Supabase를 설정하지 않으면 앱의 로컬 파일에 세션을 저장합니다. 로컬 실행에서는 괜찮지만 Streamlit Cloud는 재부팅/재배포 시 파일이 사라질 수 있습니다.

## 4. Streamlit Community Cloud Secrets 설정

앱 Settings > Secrets에 아래 형식으로 입력합니다.

```toml
[naver_searchad]
customer_id = "..."
api_key = "..."
secret_key = "..."

[supabase]
url = "https://YOUR_PROJECT.supabase.co"
service_key = "YOUR_SERVICE_ROLE_KEY"
table = "naver_sessions"
session_key = "golden-default"
```

## 5. 앱에서 최초 1회 로그인 상태 등록

배포된 앱의 왼쪽 사이드바 `네이버 로그인 상태 등록`에서 로컬에서 만든 `naver_auth_state.json`을 선택하고 `업로드한 로그인 상태 저장`을 누릅니다.

Supabase가 설정되어 있으면 이후 브라우저를 닫거나 Streamlit 앱이 재시작되어도 저장된 세션을 다시 가져옵니다.

## 6. 이후 사용

1. 앱 접속
2. 저장된 로그인 정보 있음 확인
3. 필요하면 `저장된 세션 연결 확인`
4. `전체 키워드` 또는 원하는 키워드 선택
5. `순위 조회 시작`
6. 입찰 변경 계획 확인 후 승인

네이버가 보안상 NID_AUT/NID_SES 세션을 만료시키면 로컬에서 `local_naver_login.py`를 다시 실행하여 새 JSON을 한 번 업로드해야 합니다.

## 보안 주의

- `naver_auth_state.json`, `naver_searchad_config.json`, `.streamlit/secrets.toml`은 GitHub에 올리지 않습니다.
- Supabase `service_role` 키는 Streamlit Secrets에만 저장합니다.
- 공개 앱이라면 Streamlit 앱 자체에도 접근 제한을 두는 것을 권장합니다.
