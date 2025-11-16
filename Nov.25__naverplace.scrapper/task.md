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
- 플레이스 : https://new.smartplace.naver.com/bizes/place/5921383/statistics?bookingBusinessId=603738&endDate=2025-11-15&menu=place&placeTab=inflow&startDate=2025-11-10&term=weekly
- 스마트콜 : https://smartcall.smartplace.naver.com/statistics/1191881927?bookingBusinessId=603738&endDate=2025-11-16&startDate=2025-11-16
- 예약주문 : https://new.smartplace.naver.com/bizes/place/5921383/statistics?bookingBusinessId=603738&endDate=2025-11-16&menu=booking&startDate=2025-11-10&term=weekly
    - 예약 지표 : https://partner.booking.naver.com/bizes/603738/statistics/booking?endDate=2025-11-16&period=2&startDate=2025-11-10
    - 유입 경로 : https://partner.booking.naver.com/bizes/603738/statistics/funnel?endDate=2025-11-16&period=2&startDate=2025-11-10
    - 고객 분석 : https://partner.booking.naver.com/bizes/603738/statistics/customer?endDate=2025-11-16&period=2&startDate=2025-11-10
- 리뷰 : https://new.smartplace.naver.com/bizes/place/5921383/statistics?bookingBusinessId=603738&endDate=2025-11-15&menu=review&startDate=2025-11-10&term=weekly
