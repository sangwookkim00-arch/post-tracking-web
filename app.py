import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import time
from io import BytesIO

# [cite_start][설정] 성공이 확인된 API 정보 [cite: 15, 29]
ENCODING_KEY = 'MxyfxFQNwxFj93tQTC0CA3f0ETSG8TawCq8F2u2Bd4JPB9iQSfOuPAPnWNyCv4eUuzEWPhaCiekSarpwWqeiKg%3D%3D'
BASE_URL = 'http://openapi.epost.go.kr/trace/retrieveLongitudinalCombinedService/retrieveLongitudinalCombinedService/getLongitudinalCombinedList'

st.set_page_config(page_title="우체국 통합 조회기", layout="wide", page_icon="📮")

# 커스텀 CSS 스타일
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* 메인 타이틀 스타일 */
    .main-title {
        background: linear-gradient(135deg, #E63946 0%, #F77F00 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        box-shadow: 0 8px 16px rgba(230, 57, 70, 0.3);
    }
    
    /* 카드 스타일 컨테이너 */
    .upload-card, .result-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    
    /* 버튼 스타일 개선 */
    .stButton>button {
        background: linear-gradient(135deg, #E63946 0%, #F77F00 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(230, 57, 70, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(230, 57, 70, 0.4);
    }
    
    /* 다운로드 버튼 스타일 */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #06D6A0 0%, #1B9AAA 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(6, 214, 160, 0.3);
    }
    
    .stDownloadButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(6, 214, 160, 0.4);
    }
    
    /* 프로그레스 바 스타일 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #E63946 0%, #F77F00 100%);
    }
    
    /* 파일 업로더 스타일 */
    .stFileUploader {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px dashed #E63946;
    }
    
    /* 성공 메시지 스타일 */
    .stSuccess {
        background: linear-gradient(135deg, #06D6A0 0%, #1B9AAA 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* 테이블 스타일 */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* 선택 박스 스타일 */
    .stSelectbox {
        background: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown('<div class="main-title">📮 우체국 등기 배송 통합 조회 서비스</div>', unsafe_allow_html=True)

# 안내 메시지
st.markdown("""
<div style='background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1.5rem; border-left: 4px solid #E63946;'>
    <h4 style='color: #2B2D42; margin: 0;'>📋 사용 방법</h4>
    <p style='color: #666; margin: 0.5rem 0 0 0;'>
        1️⃣ 등기번호가 포함된 엑셀 파일을 업로드하세요<br>
        2️⃣ 등기번호 컬럼을 선택하세요<br>
        3️⃣ 조회 시작 버튼을 클릭하세요
    </p>
</div>
""", unsafe_allow_html=True)

# 파일 업로드
uploaded_file = st.file_uploader("📁 조회할 엑셀 파일을 업로드하세요 (.xlsx)", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # 컬럼 선택 섹션
    st.markdown("### 🎯 등기번호 컬럼 선택")
    target_col = st.selectbox("등기번호가 포함된 컬럼을 선택하세요", df.columns, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 조회 시작 버튼을 중앙 정렬
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_button = st.button("🚀 조회 시작하기", use_container_width=True)
    
    if start_button:
        results = []
        
        # 진행 상황 표시 영역
        st.markdown("---")
        st.markdown("### 📊 조회 진행 상황")
        
        status_area = st.empty()
        progress_bar = st.progress(0)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📋 최근 조회 결과 (최근 5건)")
        table_area = st.empty()
        
        for i, num in enumerate(df[target_col]):
            full_url = f"{BASE_URL}?ServiceKey={ENCODING_KEY}&rgist={num}"
            
            try:
                resp = requests.get(full_url, timeout=15)
                root = ET.fromstring(resp.content)
                
                track_info = root.find('.//trackInfo')
                if track_info is not None:
                    recipient = track_info.findtext('receiveName') or "-"
                    status = track_info.findtext('trackState') or "-"
                    
                    details = root.findall('.//detaileTrackList')
                    last_step = details[-1] if details else None
                    date = last_step.findtext('date') if last_step is not None else "-"
                else:
                    recipient, status, date = "-", "조회불가", "-"
            except:
                recipient, status, date = "-", "오류", "-"
            
            results.append({'등기번호': num, '수령인': recipient, '배송상태': status, '날짜': date})
            
            # 실시간 업데이트
            progress = (i + 1) / len(df)
            progress_bar.progress(progress)
            
            # 진행 상황 메시지를 더 시각적으로
            status_area.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                <h4 style='color: #E63946; margin: 0;'>⏳ 처리 중: {i+1} / {len(df)} 건</h4>
                <p style='color: #666; margin: 0.5rem 0 0 0;'>진행률: {int(progress * 100)}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 최근 결과를 컬럼으로 표시
            if results:
                recent_df = pd.DataFrame(results).tail(5)
                table_area.dataframe(recent_df, use_container_width=True, hide_index=True)
            
            time.sleep(0.3)

        # 완료 후 다운로드 버튼 생성
        st.markdown("---")
        st.markdown("### ✅ 조회 완료!")
        st.success(f"🎉 총 {len(results)}건의 조회가 성공적으로 완료되었습니다!")
        
        # 전체 결과 표시
        st.markdown("### 📊 전체 조회 결과")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        
        # 다운로드 버튼
        st.markdown("<br>", unsafe_allow_html=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame(results).to_excel(writer, index=False, sheet_name='조회결과')
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="📥 결과 엑셀 파일 다운로드",
                data=output.getvalue(),
                file_name=f"우체국_조회결과_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )

