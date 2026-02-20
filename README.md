# shoon-file

네이버에서 `블로그 체험단` 검색 후 결과를 **하나씩 열어 확인**하는 Selenium 자동화 스크립트입니다.

## 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install selenium
```

> Chrome 브라우저와 호환되는 ChromeDriver가 필요합니다.

## 실행

```bash
python3 naver_blog_experience_checker.py --keyword "블로그 체험단" --limit 10
```

옵션 예시:

- `--headless`: 창 없이 실행
- `--per-page-delay 2`: 결과 페이지당 2초 대기
- `--wait-seconds 20`: 요소 로딩 대기 시간 증가

## 주의사항

- 네이버 정책/캡차/로그인 상태에 따라 자동화가 제한될 수 있습니다.
- 본 스크립트는 조회 자동화를 돕는 예시이며, 서비스 이용약관을 준수해 사용하세요.
