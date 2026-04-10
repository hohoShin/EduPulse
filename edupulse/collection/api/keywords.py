"""분야별 검색 키워드 매핑.

Naver DataLab과 Google Trends에서 사용할 키워드 그룹 정의.
각 분야(coding, security, game, art)에 대해 한국어/영어 키워드를 관리한다.
"""

# 네이버 DataLab용 한국어 키워드 (파이프라인 출력에 사용)
FIELD_KEYWORDS: dict[str, list[str]] = {
    "coding": ["코딩학원", "프로그래밍학원", "개발자부트캠프"],
    "security": ["보안학원", "정보보안교육", "사이버보안자격증"],
    "game": ["게임개발학원", "유니티학원", "게임프로그래밍"],
    "art": ["디자인학원", "그래픽디자인교육", "웹디자인학원"],
}

# Google Trends용 영어 키워드 (캐시 전용, 파이프라인 출력에 사용하지 않음)
FIELD_KEYWORDS_EN: dict[str, list[str]] = {
    "coding": ["coding bootcamp", "programming course", "developer bootcamp"],
    "security": ["cybersecurity course", "security certification", "infosec training"],
    "game": ["game development course", "unity course", "game programming"],
    "art": ["design course", "graphic design school", "web design course"],
}

# 집계 방법: 분야 내 키워드별 검색량을 합산
AGGREGATION_METHOD = "sum"

FIELDS = list(FIELD_KEYWORDS.keys())
