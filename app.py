import streamlit as st
import pandas as pd
import random
import streamlit.components.v1 as components

# 페이지 기본 설정
st.set_page_config(page_title="더울림 마더텅 어휘테스트", page_icon="📝", layout="centered")

st.title("📝 더울림 마더텅 어휘테스트")
st.write("날짜별 단어를 선택하여 테스트를 진행합니다.")

# 1. 구글 시트 URL 기본값 고정
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSTm5sTsaIjFDD77-SxjlNnp01CvW0ZyEKnDBrqEM830P7q5iwsXwvumTXHgM4-a-csHXtIxqu9oZRn/pub?gid=0&single=true&output=csv"

st.sidebar.header("⚙️ 설정")
sheet_url = st.sidebar.text_input(
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSTm5sTsaIjFDD77-SxjlNnp01CvW0ZyEKnDBrqEM830P7q5iwsXwvumTXHgM4-a-csHXtIxqu9oZRn/pub?gid=0&single=true&output=csv",
    value=DEFAULT_SHEET_URL
)

# 세션 상태 초기화 (문제 상태 유지용)
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "test_started" not in st.session_state:
    st.session_state.test_started = False

# 개선된 브라우저 음성 재생(TTS) 함수
def speak_text(text):
    # 특수문자 및 따옴표 에러 방지
    clean_text = text.replace("'", "").replace('"', '').replace("\n", " ")
    js_code = f"""
    <script>
        function speak() {{
            window.speechSynthesis.cancel(); // 이전 음성 중단
            var msg = new SpeechSynthesisUtterance('{clean_text}');
            msg.lang = 'ko-KR';
            msg.rate = 0.9; // 속도 조절
            window.speechSynthesis.speak(msg);
        }}
        // 브라우저 로딩 완료 후 실행
        setTimeout(speak, 200);
    </script>
    """
    components.html(js_code, height=0)

# 데이터 불러오기 및 날짜 선택
if sheet_url:
    try:
        df = pd.read_csv(sheet_url)
        
        if '날짜' in df.columns:
            date_list = sorted(df['날짜'].dropna().astype(str).unique().tolist(), reverse=True)
            selected_date = st.selectbox("📅 테스트할 날짜를 선택하세요:", date_list)
            filtered_df = df[df['날짜'].astype(str) == selected_date]
        else:
            st.warning("⚠️ 구글 시트에 '날짜' 열이 없습니다. 전체 단어로 진행합니다.")
            filtered_df = df

        if not st.session_state.test_started:
            st.write(f"선택된 단어 수: **{len(filtered_df)}개**")
            if st.button("🚀 테스트 시작하기", use_container_width=True):
                data = filtered_df[['단어', '뜻']].dropna().to_dict('records')
                random.shuffle(data)
                st.session_state.quiz_data = data
                st.session_state.current_idx = 0
                st.session_state.score = 0
                st.session_state.user_answers = []
                st.session_state.test_started = True
                st.rerun()

    except Exception as e:
        st.error("구글 시트를 불러오지 못했습니다. CSV URL 주소를 확인해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에 구글 시트 '웹에 게시' CSV URL을 입력해 주세요.")

# 테스트 진행 화면
if st.session_state.test_started and st.session_state.quiz_data:
    total = len(st.session_state.quiz_data)
    idx = st.session_state.current_idx

    # 테스트 종료
    if idx >= total:
        st.balloons()
        st.success(f"🎉 테스트가 종료되었습니다! 점수: {st.session_state.score} / {total}점")
        
        wrong_list = [ans for ans in st.session_state.user_answers if not ans['is_correct']]
        if wrong_list:
            st.subheader("❌ 오답 노트")
            for w in wrong_list:
                st.write(f"- **뜻:** {w['meaning']} | **정답:** `{w['correct']}` | **내가 쓴 답:** `{w['user']}`")
        else:
            st.write("👏 만점입니다! 오답이 없습니다.")

        if st.button("🔄 다른 날짜/다시 테스트하기", use_container_width=True):
            st.session_state.test_started = False
            st.rerun()

    # 문제 진행
    else:
        current_quiz = st.session_state.quiz_data[idx]
        meaning = current_quiz['뜻']
        correct_word = current_quiz['단어']

        st.progress((idx) / total)
        st.caption(f"문제 {idx + 1} / {total}")
        
        st.markdown(f"### **뜻:** {meaning}")

        # 수동으로 다시 듣는 버튼 제공 (클릭 시 소리 보장)
        if st.button("🔊 뜻 다시 듣기"):
            speak_text(meaning)

        # 문제 진입 시 음성 재생
        speak_text(meaning)

        with st.form(key=f"quiz_form_{idx}"):
            user_input = st.text_input("단어를 입력하세요:", key=f"input_{idx}").strip()
            submit_button = st.form_submit_button(label="정답 제출 ➡️")

            if submit_button:
                is_correct = (user_input == correct_word)
                if is_correct:
                    st.session_state.score += 1
                
                st.session_state.user_answers.append({
                    'meaning': meaning,
                    'correct': correct_word,
                    'user': user_input,
                    'is_correct': is_correct
                })
                
                st.session_state.current_idx += 1
                st.rerun()
                
                st.session_state.current_idx += 1
                st.rerun()
