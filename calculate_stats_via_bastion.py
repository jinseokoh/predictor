"""
Bastion Host SSH 터널을 통해 RDS에서 통계 계산
"""
import json

try:
    import pymysql
    print("✓ pymysql 모듈 로드 성공")
except ImportError:
    print("✗ pymysql 모듈이 설치되어 있지 않습니다.")
    print("  설치 방법: pip install pymysql")
    exit(1)

# SSH 터널을 통한 MySQL 접속 정보
# SSH 터널: ssh -i key.pem -N -L 3307:fleaauction.clhth1vxav6k.ap-northeast-2.rds.amazonaws.com:3306 ec2-user@bastion-ip
DB_CONFIG = {
    'host': 'localhost',        # SSH 터널을 사용하므로 localhost
    'port': 3307,               # 로컬 포워딩 포트 (위의 -L 3307에서 지정한 포트)
    'user': '',                 # ← RDS 사용자명 입력 필요
    'password': '',             # ← RDS 비밀번호 입력 필요
    'database': '',             # ← 데이터베이스명 입력 필요
    'charset': 'utf8mb4',
    'connect_timeout': 5
}

# 테이블 및 컬럼 정보
TABLE_NAME = ''  # ← 학습 데이터가 있는 테이블명 입력 필요

# 컬럼명 매핑 (실제 DB 컬럼명으로 변경)
COLUMN_MAPPING = {
    'e1': 'e1',  # ← 실제 컬럼명 (예: 'engagement_index_1')
    'b1': 'b1',  # ← 실제 컬럼명 (예: 'behavior_index_1')
    'p1': 'p1',  # ← 실제 컬럼명 (예: 'popularity_index_1')
    'e2': 'e2',  # ← 실제 컬럼명 (예: 'engagement_index_2')
    'b2': 'b2',  # ← 실제 컬럼명 (예: 'behavior_index_2')
    'p2': 'p2'   # ← 실제 컬럼명 (예: 'popularity_index_2')
}


def calculate_statistics():
    """
    DB에서 6개 지수의 평균과 표준편차를 계산
    """
    print('=' * 70)
    print('MySQL RDS에서 통계값 계산 시작 (via Bastion Host)')
    print('=' * 70)
    print(f'\n접속 정보:')
    print(f'  Host: {DB_CONFIG["host"]}:{DB_CONFIG["port"]} (SSH 터널)')
    print(f'  Database: {DB_CONFIG["database"]}')
    print(f'  User: {DB_CONFIG["user"]}')
    print(f'  Table: {TABLE_NAME}')
    
    try:
        # MySQL 연결
        print('\n데이터베이스 연결 중...')
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print('✓ 연결 성공!')
        
        # 테이블 존재 확인
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f'\n사용 가능한 테이블 목록 ({len(tables)}개):')
        for i, table in enumerate(tables[:10], 1):
            print(f'  {i}. {table}')
        if len(tables) > 10:
            print(f'  ... 외 {len(tables) - 10}개')
        
        if TABLE_NAME not in tables:
            print(f'\n⚠️  경고: 테이블 "{TABLE_NAME}"을 찾을 수 없습니다.')
            print('   위 목록에서 올바른 테이블명을 확인하고 스크립트를 수정하세요.')
            cursor.close()
            connection.close()
            return None
        
        # 컬럼 정보 확인
        cursor.execute(f"DESCRIBE {TABLE_NAME}")
        columns = [col[0] for col in cursor.fetchall()]
        print(f'\n"{TABLE_NAME}" 테이블의 컬럼 목록 ({len(columns)}개):')
        for i, col in enumerate(columns[:20], 1):
            print(f'  {i}. {col}')
        if len(columns) > 20:
            print(f'  ... 외 {len(columns) - 20}개')
        
        # 각 컬럼별로 평균과 표준편차 계산
        mean_std = {}
        
        print('\n' + '=' * 70)
        print('통계값 계산 중...')
        print('=' * 70)
        
        api_column_name_map = {
            'e1': 'In_Engagement',
            'b1': 'In_History',
            'p1': 'In_Popularity',
            'e2': 'Ex_Engagement',
            'b2': 'Ex_History',
            'p2': 'Ex_Popularity'
        }
        
        for key, column_name in COLUMN_MAPPING.items():
            if column_name not in columns:
                print(f'\n⚠️  경고: 컬럼 "{column_name}"을 찾을 수 없습니다.')
                print(f'   COLUMN_MAPPING["{key}"]를 올바른 컬럼명으로 수정하세요.')
                continue
            
            query = f"""
                SELECT 
                    AVG({column_name}) as mean,
                    STDDEV({column_name}) as std,
                    COUNT({column_name}) as count,
                    MIN({column_name}) as min,
                    MAX({column_name}) as max
                FROM {TABLE_NAME}
                WHERE {column_name} IS NOT NULL
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            mean_value = float(result[0]) if result[0] is not None else 0.0
            std_value = float(result[1]) if result[1] is not None else 1.0
            count_value = int(result[2]) if result[2] is not None else 0
            min_value = float(result[3]) if result[3] is not None else 0.0
            max_value = float(result[4]) if result[4] is not None else 0.0
            
            api_column_name = api_column_name_map[key]
            mean_std[api_column_name] = {
                'mean': mean_value,
                'std': std_value
            }
            
            print(f'\n[{key} → {api_column_name}]')
            print(f'  DB 컬럼: {column_name}')
            print(f'  평균(mean): {mean_value:,.4f}')
            print(f'  표준편차(std): {std_value:,.4f}')
            print(f'  데이터 개수: {count_value:,}')
            print(f'  최소값: {min_value:,.2f}')
            print(f'  최대값: {max_value:,.2f}')
        
        cursor.close()
        connection.close()
        
        if not mean_std:
            print('\n✗ 통계값을 계산할 수 없습니다.')
            print('   테이블명과 컬럼명을 확인하세요.')
            return None
        
        print('\n' + '=' * 70)
        print('계산 완료!')
        print('=' * 70)
        
        # JSON 형식으로 출력
        print('\n코드에 사용할 mean_std 딕셔너리 (JSON):')
        print('=' * 70)
        print(json.dumps(mean_std, indent=4, ensure_ascii=False))
        
        # Python 코드 형식으로도 출력
        print('\n\nPython 코드 형식:')
        print('=' * 70)
        print('mean_std = {')
        for key, value in mean_std.items():
            print(f"    '{key}': {{'mean': {value['mean']}, 'std': {value['std']}}},")
        print('}')
        
        # 파일로 저장
        output_file = 'mean_std_config.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mean_std, f, indent=4, ensure_ascii=False)
        print(f'\n✓ 결과를 {output_file} 파일로 저장했습니다.')
        
        return mean_std
        
    except pymysql.Error as e:
        print(f'\n✗ MySQL 오류 발생: {e}')
        print('\n연결 실패 시 확인사항:')
        print('  1. SSH 터널이 실행 중인가요?')
        print('  2. 포트 번호가 일치하나요? (기본: 3307)')
        print('  3. DB 사용자명/비밀번호가 정확한가요?')
        return None
    except Exception as e:
        print(f'\n✗ 오류 발생: {e}')
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    print('=' * 70)
    print('Bastion Host를 통한 RDS 통계 계산')
    print('=' * 70)
    print('\n📋 실행 전 체크리스트:')
    print('  1. ✅ SSH 터널 실행:')
    print('     ssh -i your-key.pem -N -L 3307:fleaauction.clhth1vxav6k.ap-northeast-2.rds.amazonaws.com:3306 ec2-user@bastion-ip')
    print('  2. ⚙️  스크립트 설정 확인:')
    print('     - DB_CONFIG: user, password, database')
    print('     - TABLE_NAME: 학습 데이터 테이블명')
    print('     - COLUMN_MAPPING: 6개 지수의 실제 컬럼명')
    print()
    
    response = input('SSH 터널이 실행 중이고 설정을 완료했나요? (y/n): ')
    if response.lower() != 'y':
        print('\n준비 후 다시 실행해주세요.')
        exit(0)
    
    calculate_statistics()

