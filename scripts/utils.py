"""
분석 유틸 함수
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_api_credentials(csv_path: str = './data/info.csv') -> Dict[str, str]:
    """
    CSV 파일에서 API 크레덴셜 로드
    
    Args:
        csv_path: API 정보 CSV 파일 경로
        
    Returns:
        {'nsa': {'key': '...', 'scr': '...'}} 형태의 딕셔너리
    """
    df = pd.read_csv(csv_path)
    
    credentials = {}
    for _, row in df.iterrows():
        media = row['media']
        credentials[media] = {
            'key': row['key'],
            'scr': row['scr']
        }
    
    return credentials


def save_json(data: Any, filepath: str, ensure_ascii: bool = False) -> None:
    """
    데이터를 JSON 파일로 저장
    
    Args:
        data: 저장할 데이터
        filepath: 저장 경로
        ensure_ascii: ASCII 문자만 사용할지 여부
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=2)
    
    print(f"✓ 저장 완료: {filepath}")


def load_json(filepath: str) -> Any:
    """
    JSON 파일에서 데이터 로드
    
    Args:
        filepath: 로드할 JSON 파일 경로
        
    Returns:
        로드된 데이터
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    DataFrame 검증
    
    Args:
        df: 검증할 DataFrame
        required_columns: 필수 컬럼 리스트
        
    Returns:
        검증 결과 (True/False)
    """
    missing_cols = set(required_columns) - set(df.columns)
    
    if missing_cols:
        print(f"❌ 필수 컬럼 누락: {missing_cols}")
        return False
    
    if df.empty:
        print("❌ DataFrame이 비어있습니다")
        return False
    
    return True


def check_missing_values(df: pd.DataFrame, threshold: float = 0.05) -> Dict[str, float]:
    """
    결측치 확인
    
    Args:
        df: 검사할 DataFrame
        threshold: 결측치 비율 임계값 (기본값: 5%)
        
    Returns:
        컬럼별 결측치 비율
    """
    missing_rates = {}
    
    for col in df.columns:
        missing_rate = df[col].isnull().sum() / len(df)
        missing_rates[col] = missing_rate
        
        if missing_rate > threshold:
            print(f"⚠️  {col}: {missing_rate:.2%} (임계값 {threshold:.2%} 초과)")
    
    return missing_rates


def detect_outliers(df: pd.DataFrame, column: str, method: str = 'iqr') -> List[int]:
    """
    이상치 탐지
    
    Args:
        df: DataFrame
        column: 검사할 컬럼명
        method: 탐지 방법 ('iqr' 또는 'zscore')
        
    Returns:
        이상치 인덱스 리스트
    """
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)].index.tolist()
    
    elif method == 'zscore':
        from scipy import stats
        z_scores = abs(stats.zscore(df[column].dropna()))
        outliers = df[abs(stats.zscore(df[column])) > 3].index.tolist()
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return outliers


def calculate_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    광고 성과 지표 계산
    
    Args:
        df: 광고 데이터 DataFrame
               필수 컬럼: impressions, clicks, cost, conversions
        
    Returns:
        지표 딕셔너리: CTR, CVR, CPC, CPA, ROAS 등
    """
    metrics = {}
    
    try:
        # CTR (Click-Through Rate)
        if 'impressions' in df.columns and df['impressions'].sum() > 0:
            metrics['CTR'] = (df['clicks'].sum() / df['impressions'].sum()) * 100
        
        # CVR (Conversion Rate)
        if 'clicks' in df.columns and df['clicks'].sum() > 0:
            metrics['CVR'] = (df['conversions'].sum() / df['clicks'].sum()) * 100
        
        # CPC (Cost Per Click)
        if 'clicks' in df.columns and df['clicks'].sum() > 0:
            metrics['CPC'] = df['cost'].sum() / df['clicks'].sum()
        
        # CPA (Cost Per Acquisition)
        if 'conversions' in df.columns and df['conversions'].sum() > 0:
            metrics['CPA'] = df['cost'].sum() / df['conversions'].sum()
        
        # ROAS (Return on Ad Spend)
        if 'cost' in df.columns and df['cost'].sum() > 0 and 'conversion_value' in df.columns:
            metrics['ROAS'] = df['conversion_value'].sum() / df['cost'].sum()
        
        # 총 지출, 클릭, 전환
        metrics['Total_Cost'] = df['cost'].sum()
        metrics['Total_Clicks'] = df['clicks'].sum()
        metrics['Total_Conversions'] = df['conversions'].sum()
        metrics['Total_Impressions'] = df['impressions'].sum()
    
    except Exception as e:
        print(f"❌ 지표 계산 중 오류: {e}")
    
    return metrics


def print_data_summary(df: pd.DataFrame, title: str = "데이터 요약") -> None:
    """
    DataFrame 요약 정보 출력
    
    Args:
        df: DataFrame
        title: 제목
    """
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    print(f"행 수: {len(df):,}")
    print(f"열 수: {len(df.columns)}")
    print(f"\n컬럼 정보:")
    print(df.info())
    print(f"\n기초 통계:")
    print(df.describe())
    print(f"\n결측치:")
    print(df.isnull().sum())
    print(f"{'='*60}\n")


# 사용 예시
if __name__ == "__main__":
    # API 크레덴셜 로드
    credentials = load_api_credentials()
    print(f"로드된 크레덴셜: {list(credentials.keys())}")
    
    # 샘플 데이터 생성
    sample_data = {
        'date': ['2025-10-01', '2025-10-02', '2025-10-03'],
        'impressions': [1000, 1100, 900],
        'clicks': [50, 55, 45],
        'cost': [10000, 12000, 9000],
        'conversions': [5, 6, 4],
        'conversion_value': [150000, 180000, 120000]
    }
    
    df = pd.DataFrame(sample_data)
    
    # 데이터 요약 출력
    print_data_summary(df)
    
    # 지표 계산
    metrics = calculate_metrics(df)
    print("계산된 지표:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.2f}")
