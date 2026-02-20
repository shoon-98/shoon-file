#!/usr/bin/env python3
"""네이버에서 '블로그 체험단' 검색 결과를 순회 확인하는 자동화 스크립트.

기능:
1) 네이버 검색창에서 키워드를 검색
2) 검색 결과 페이지에서 결과 링크들을 수집
3) 결과를 하나씩 새 탭으로 열고 제목/URL 출력

주의:
- 자동화 탐지, 캡차, 로그인 정책에 따라 동작이 제한될 수 있습니다.
- 사이트 이용약관 및 robots 정책을 준수하세요.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from typing import Iterable

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class SearchResult:
    title: str
    url: str


def build_driver(headless: bool) -> webdriver.Chrome:
    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(2)
    return driver


def normalize_url(url: str) -> str:
    return re.sub(r"#.*$", "", url.strip())


def unique_by_url(items: Iterable[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    output: list[SearchResult] = []
    for item in items:
        key = normalize_url(item.url)
        if key and key not in seen:
            seen.add(key)
            output.append(item)
    return output


def collect_results(driver: webdriver.Chrome, limit: int) -> list[SearchResult]:
    candidates = driver.find_elements(By.CSS_SELECTOR, "a.title_link, a.api_txt_lines.total_tit")
    results: list[SearchResult] = []

    for anchor in candidates:
        title = anchor.text.strip()
        url = anchor.get_attribute("href") or ""
        if not title or not url:
            continue
        if "naver.com" not in url and "blog" not in url.lower():
            continue
        results.append(SearchResult(title=title, url=url))

    deduped = unique_by_url(results)
    return deduped[:limit]


def run(args: argparse.Namespace) -> int:
    driver = build_driver(headless=args.headless)
    wait = WebDriverWait(driver, args.wait_seconds)

    try:
        print(f"[1/4] 네이버 접속: {args.base_url}")
        driver.get(args.base_url)

        print(f"[2/4] 검색어 입력: {args.keyword}")
        search_input = wait.until(EC.presence_of_element_located((By.NAME, "query")))
        search_input.clear()
        search_input.send_keys(args.keyword)
        search_input.submit()

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.title_link, a.api_txt_lines.total_tit")))
        except TimeoutException:
            print("검색 결과를 찾지 못했습니다. 캡차/로그인/레이아웃 변경을 확인하세요.")
            return 1

        print(f"[3/4] 결과 수집 (최대 {args.limit}개)")
        results = collect_results(driver, args.limit)
        if not results:
            print("수집된 결과가 없습니다.")
            return 1

        print(f"총 {len(results)}개 결과를 확인합니다.\n")

        print("[4/4] 결과 페이지 하나씩 확인")
        main_window = driver.current_window_handle
        for index, item in enumerate(results, start=1):
            print(f"\n[{index}] {item.title}")
            print(f"    URL: {item.url}")

            driver.switch_to.new_window("tab")
            driver.get(item.url)
            time.sleep(args.per_page_delay)

            page_title = driver.title.strip()
            print(f"    페이지 타이틀: {page_title or '(없음)'}")

            driver.close()
            driver.switch_to.window(main_window)

        print("\n완료: 모든 결과 순회 확인이 끝났습니다.")
        return 0
    finally:
        driver.quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="네이버 블로그 체험단 검색 결과 확인 자동화")
    parser.add_argument("--keyword", default="블로그 체험단", help="검색 키워드")
    parser.add_argument("--limit", type=int, default=10, help="확인할 최대 결과 수")
    parser.add_argument("--wait-seconds", type=int, default=15, help="요소 대기 시간(초)")
    parser.add_argument("--per-page-delay", type=float, default=1.5, help="각 페이지 확인 대기 시간(초)")
    parser.add_argument("--base-url", default="https://www.naver.com", help="네이버 시작 URL")
    parser.add_argument("--headless", action="store_true", help="헤드리스 모드 실행")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        raise SystemExit(run(parse_args()))
    except KeyboardInterrupt:
        print("\n사용자 중단")
        raise SystemExit(130) from None
    except Exception as exc:  # noqa: BLE001
        print(f"오류 발생: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
