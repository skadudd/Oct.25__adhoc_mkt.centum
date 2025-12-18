## 로그인

- 계정: /Users/nam-yeong/git/Oct.25__adhoc_mkt.centum/data/info_naver.csv
- 로그인 페이지 : https://nid.naver.com/nidlogin.login?svctype=1&locale=ko_KR&url=https%3A%2F%2Fnew.smartplace.naver.com%2F&area=bbt
- ID 입력 Selector : input_item_id
- PW 입력 Selector : input_item_pw
- IP 보안 토글 : #login_keep_wrap > div.ip_check > span > label
  - IP 보안토글은 Off 가 되어야 함.
- 제출 버튼 : #log\.login

## 베이스 url

- base : https://new.smartplace.naver.com/bizes/place/5921383?bookingBusinessId=603738

## 통계 페이지

#### 페이지

- 플레이스 : https://new.smartplace.naver.com/bizes/place/5921383/statistics?bookingBusinessId=603738&endDate=2025-11-15&menu=place&placeTab=inflow&startDate=2025-11-10&term=daily

  - 유입수
    - Class : Statistics_number__kPHuM
    -
- 스마트콜 : https://smartcall.smartplace.naver.com/statistics/1191881927?bookingBusinessId=603738&endDate=2025-11-16&startDate=2025-11-16
- 예약주문 : https://new.smartplace.naver.com/bizes/place/5921383/statistics?bookingBusinessId=603738&endDate=2025-11-16&menu=booking&startDate=2025-11-10&term=weekly

  - 예약 지표 : https://partner.booking.naver.com/bizes/603738/statistics/booking?endDate=2025-11-16&period=2&startDate=2025-11-10
  - 유입 경로 : https://partner.booking.naver.com/bizes/603738/statistics/funnel?endDate=2025-11-16&period=2&startDate=2025-11-10
  - 고객 분석 : https://partner.booking.naver.com/bizes/603738/statistics/customer?endDate=2025-11-16&period=2&startDate=2025-11-10
- 리뷰 : https://new.smartplace.naver.com/bizes/place/5921383/statistics?bookingBusinessId=603738&endDate=2025-11-15&menu=review&startDate=2025-11-10&term=weekly

## 스마트콜

### 통화 통계

- 통화 통계 : https://smartcall.smartplace.naver.com/statistics/1191881927?startDate=2025-12-09&endDate=2025-12-15&bookingBusinessId=603738
- 일별 통화 : #__next > div > div:nth-child(3) > div > div.call_section > div.styles_call_info__qa5Bn > div.styles_info_tab__E4QqY > ul > li:nth-child(2) > a
- 수집 테이블 : #call-daily > div > div.styles_table_scroll__or3Yy
  #call-daily > div > div.styles_table_scroll__or3Yy > table

### 전화가 많이 오는 매체
#__next > div > div:nth-child(3) > div > div.call_section > div:nth-child(3)

- #__next > div > div:nth-child(3) > div > div.call_section > div:nth-child(3) > div > ul > li:nth-child(1) > strong.styles_rank_num__Pkqpj
- #__next > div > div:nth-child(3) > div > div.call_section > div:nth-child(3) > div > ul > li:nth-child(1) > strong.styles_rank_name__usvhI
- #__next > div > div:nth-child(3) > div > div.call_section > div:nth-child(3) > div > ul > li:nth-child(1)


### 전화가 많이 오는키워드
#__next > div > div:nth-child(3) > div > div.call_section > div:nth-child(4) > div > ul
- 하위 li

## 예약 주문
### 예약 지표 : https://partner.booking.naver.com/bizes/603738/statistics/booking?endDate=2025-12-21&period=1&startDate=2025-12-15
#### 예약 트렌드 차트 : #app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-body > div > div > div.StatisticsIndicators__chart-wrap__4UCu\+.StatisticsIndicators__chart-wrap-m__b8qFo

- 체크박스 그룹 : #app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div
  - 하위 체크박스 클래스들 : custom-radio-checkbox light-green StatisticsIndicators__checkbox__FwYei
    - 하위 체크박스 클래스 : #app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child(1) > input
      - 체크 활성화 <input class="check-radio" type="checkbox" data-tst_input="checkbox" checked="true">
      - 각 체크박스 피쳐 명칭 : #app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child(1) > span > span
        - 각 체크박스를 하나씩 True로 체크하여 데이터를 각기 수집 후, 개별 피쳐로 join 필수
## 리뷰
- 방문자리뷰 : https://new.smartplace.naver.com/bizes/place/5921383/reviews?bookingBusinessId=603738&menu=visitor
- 블로그 : https://new.smartplace.naver.com/bizes/place/5921383/reviews?bookingBusinessId=603738&menu=blog

## 고객
