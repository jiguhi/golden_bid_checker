황금이네 순위체커 - Streamlit 버전

[최초 1회 설치]
1. 00_install_streamlit.bat 실행

[실행]
1. 04_run_streamlit.bat 실행
2. 브라우저에 Streamlit 화면이 열리면 왼쪽의 '전용 Chrome 열기' 클릭
3. 새로 열린 전용 Chrome에서 네이버 로그인
4. Streamlit 화면에서 조회할 키워드 선택
5. '순위 조회 시작' 클릭
6. 조회 결과 확인
7. 입찰 변경이 필요하면 '현재 입찰가 조회 및 변경 계획 생성' 클릭
8. 계획표 확인 후 실제 적용하려면 '변경' 입력 → '입찰가 실제 변경' 클릭

[기존 로직 유지]
- PC 전체 조회 후 Mobile 전체 조회
- 1위: 입찰가 -5%
- 2위: 유지
- 3위 이하: +5%
- 미노출 인상은 체크박스로 별도 허용
- 10원 단위 반올림
- 쇼핑 최소 50원 / 파워링크 최소 70원
- 최대 20,000원
- 동일 ID 10분 이내 재입찰 방지
- 오래된 조회 결과 변경 방지
- 실제 변경 직전 광고 설정 fingerprint 재검증
- 변경 후 API 재조회로 적용값 확인
- CAPTCHA/보안확인/보호조치 우회 안 함

[필수 파일]
- streamlit_app.py: Streamlit 화면
- golden_integrated_checker.py: 기존 순위조회/API 핵심 로직
- material_ids.xlsx: 키워드/광고그룹/키워드 ID 매핑
- naver_searchad_config.json: Search AD API 인증 설정
- requirements_streamlit.txt: 설치 패키지

[주의]
- Streamlit을 실행한 PC와 Chrome이 같은 PC여야 합니다.
- 전용 Chrome은 순위 조회 중 닫지 마세요.
- naver_searchad_config.json에는 API 인증정보가 있으므로 외부에 공유하지 마세요.
- 쇼핑 입찰 변경은 그룹 기본입찰가에 영향을 줄 수 있습니다.
