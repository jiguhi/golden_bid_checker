황금이네 순위체커 + Search AD API 입찰관리 안정화본 v2

[권장 실행 순서]
1. 최초 1회: 00_install.bat
2. 01_start_login_chrome.bat 실행
3. 열린 전용 Chrome에서 네이버에 직접 로그인
4. Chrome을 닫지 않은 상태에서 02_run_connected.bat 실행

[조회 구조]
- 동일 로그인 세션 유지
- PC 키워드 전체 조회
- PC/Mobile 사이 30초 휴식
- Mobile 키워드 전체 조회
- 키워드 검색 사이 5초
- 보호조치/보안확인/자동입력방지 또는 HTTP 401/403/429 감지 시 즉시 중단
- 입찰 변경은 기존과 동일하게 NAVER Search AD API 사용

[파일 설명]
00_install.bat: Python 패키지 설치
01_start_login_chrome.bat: 로그인 상태를 보존하는 전용 Chrome 실행
02_run_connected.bat: 열린 전용 Chrome에 연결하여 실행 (권장)
03_run_managed.bat: 프로그램이 전용 Chrome 프로필을 직접 실행하는 예비 방식
material_ids.xlsx: 소재/그룹/키워드 ID 매핑
naver_searchad_config.json: Search AD API 설정
golden_integrated_checker.py: 본 프로그램

[중요]
- CAPTCHA나 보호조치를 자동으로 우회하지 않습니다. 감지되면 중단합니다.
- 01_start_login_chrome.bat으로 연 Chrome은 프로그램 실행 중 닫지 마세요.
- 평소 사용 중인 일반 Chrome에 사후 연결하는 방식이 아니라, 전용 프로필 Chrome을 먼저 열어 로그인해 둔 뒤 연결하는 방식입니다.
