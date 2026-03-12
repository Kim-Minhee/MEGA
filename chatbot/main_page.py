import io, os
from dotenv import load_dotenv
from PIL import Image

import streamlit as st
import tensorflow as tf
import google.generativeai as genai
# import google import genai

import image_model as im
import assistant_mega as am



## Session
def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'container_visible' not in st.session_state: # 토글 기본값 -> 접기
        st.session_state.container_visible = True

    if 'form_data' not in st.session_state: # 문진표 기본값
        st.session_state['form_data'] = {
            'gender': '남',
            'age': 40,
            'height': 180.0,
            'weight': 80.0,
            'conditions_self': [],
            'conditions_family': [],
            'smoking': {
                'status': '안 함',
                'details': {
                    'current': '현재도 흡연 중',
                    'years': 3,
                    'amount': 10
                }
            },
            'drinking': {
                'status': '안 함',
                'details': {
                    'frequency': 3,
                    'type': '소주',
                    'amount': 3
                }
            },
            'exercise': {
                'status': '안 함',
                'details': {
                    'frequency': 3,
                    'amount': 30
                }
            }
        }
    
    if 'diagnosis_type' not in st.session_state:
        st.session_state.diagnosis_type = 0 # 0: 갑상선 초음파, 1: 뇌 MRI


## 문진표
def toggle_container():
    st.session_state.container_visible = not st.session_state.container_visible

def create_section_title(title):
    col1, col2 = st.columns([1, 9])
    with col1:
        st.write(title)
    with col2:
        st.markdown('<hr style="margin: 12px 0px">', unsafe_allow_html=True)

def create_medical_form():
    st.markdown('#### 문진표')
    if not st.session_state.container_visible:
        if st.button('펼치기', key='open_button', on_click=toggle_container):
            st.rerun()
    else:
        if st.button('접기', key='close_button', on_click=toggle_container):
            st.rerun()

    if st.session_state.container_visible:
        with st.container(border=False):
            col_basic, col_history = st.columns(2)
            # 기본
            with col_basic:
                create_section_title('기본')
                col_gender_age, col_height_weight = st.columns(2)
                with col_gender_age:
                    st.session_state['form_data']['gender'] = st.radio('**성별**', key='gender',
                        options=['남', '여'], index=['남', '여'].index(st.session_state['form_data']['gender']), horizontal=True)
                    st.session_state['form_data']['age'] = st.number_input('**나이 (만)**', key='age',
                        value=st.session_state['form_data']['age'], min_value=0, max_value=150, step=1)
                with col_height_weight:
                    st.session_state['form_data']['height'] = st.number_input('**신장 (cm)**', key='height',
                        value=st.session_state['form_data']['height'], min_value=0.0, max_value=300.0, step=0.1, format='%.1f')
                    st.session_state['form_data']['weight'] = st.number_input('**체중 (kg)**', key='weight',
                        value=st.session_state['form_data']['weight'], min_value=0.0, max_value=500.0, step=0.1, format='%.1f')

            # 질환력  
            with col_history:
                create_section_title('질환력')
                st.session_state['form_data']['conditions_self'] = st.multiselect(label='**본인**', key='conditions_self',
                    options=['뇌졸중', '심근경색', '고혈압', '당뇨병', '폐질환', '기타(암 포함)'], default=st.session_state['form_data']['conditions_self'])
                st.session_state['form_data']['conditions_family'] = st.multiselect(label='**가족** (부모, 형제, 자매)', key='conditions_family',
                    options=['뇌졸중', '심근경색', '고혈압', '당뇨병', '기타(암 포함)'], default=st.session_state['form_data']['conditions_family'])
            
            # 생활
            create_section_title('생활')
            col_smoking, col_drinking, col_exercise = st.columns(3)
            with col_smoking: # 흡연
                with st.container(border=True):
                    st.session_state['form_data']['smoking']['status'] = st.radio('**흡연**', key='smoking_status',
                        options=['안 함', '함'], index=['안 함', '함'].index(st.session_state['form_data']['smoking']['status']), horizontal=True)
                    if st.session_state['form_data']['smoking']['status']=='함':
                        st.markdown('<hr style="margin: -5px 0px">', unsafe_allow_html=True)
                        st.session_state['form_data']['smoking']['details']['current'] = st.radio('현재 흡연 여부', key='smoking_current',
                            options=['현재도 흡연 중', '현재는 끊음'], index=['현재도 흡연 중', '현재는 끊음'].index(st.session_state['form_data']['smoking']['details']['current']))
                        st.session_state['form_data']['smoking']['details']['years'] = st.number_input('흡연 기간 (년)', key='smoking_years',
                            value=st.session_state['form_data']['smoking']['details']['years'], min_value=0, max_value=150, step=1)
                        st.session_state['form_data']['smoking']['details']['amount'] = st.number_input('1일 흡연량 (개비)', key='smoking_amount',
                            value=st.session_state['form_data']['smoking']['details']['amount'], min_value=0, max_value=100, step=1)
            
            with col_drinking: # 음주
                with st.container(border=True):
                    st.session_state['form_data']['drinking']['status'] = st.radio('**음주**', key='drinking_status',
                        options=['안 함', '함'], index=['안 함', '함'].index(st.session_state['form_data']['drinking']['status']), horizontal=True)
                    if st.session_state['form_data']['drinking']['status']=='함':
                        st.markdown('<hr style="margin: -5px 0px">', unsafe_allow_html=True)
                        st.session_state['form_data']['drinking']['details']['frequency'] = st.number_input('한 달 평균 (회)', key='drinking_freq',
                            value=st.session_state['form_data']['drinking']['details']['frequency'], min_value=0, max_value=100, step=1)
                        st.session_state['form_data']['drinking']['details']['type'] = st.selectbox('주종을 선택하세요.', key='drinking_type',
                            options=['소주', '맥주', '양주', '막걸리', '와인'])
                        st.session_state['form_data']['drinking']['details']['amount'] = st.number_input('1회 음주량 (잔)', key='drinking_amount',
                            value=3, min_value=0, max_value=100, step=1)
            
            with col_exercise: # 운동
                with st.container(border=True):
                    st.session_state['form_data']['exercise']['status'] = st.radio('**운동**', key='exercise',
                        options=['안 함', '함'], index=['안 함', '함'].index(st.session_state['form_data']['exercise']['status']), horizontal=True)
                    if st.session_state['form_data']['exercise']['status']=='함':
                        st.markdown('<hr style="margin: -5px 0px">', unsafe_allow_html=True)
                        st.session_state['form_data']['exercise']['details']['frequency'] = st.number_input('일주일 평균 (회)', key='exercise_freq',
                            value=st.session_state['form_data']['exercise']['details']['frequency'], min_value=0, max_value=20, step=1)
                        st.session_state['form_data']['exercise']['details']['amount'] = st.number_input('1일 운동량 (분)', key='exercise_amount',
                            value=st.session_state['form_data']['exercise']['details']['amount'], min_value=0, max_value=1000, step=1)
        
        form_data = st.session_state['form_data']
    
    return st.session_state['form_data']


## 메인
def main():
    st.set_page_config(
        layout = 'wide',
        page_title='MEGA',
        #page_icon='', # 윈도우 창의 탭 아이콘 설정
    )

    init_session_state()
    # model = im.load_model()
    gemini = am.load_gemini()

    # 사이드바
    with st.sidebar:
        st.header('이미지 파일 업로드')
        # 이미지 종류 선택
        image_type = st.radio(
            '**1) 진단 종류 선택**',
            options=['갑상선 초음파', '뇌 MRI'],
            index=0  # 기본 선택값: '갑상선'
        )
        uploaded_file = st.file_uploader('**2) 이미지 업로드**', type=['jpg', 'bmp'])

    
    # 소개/설명
    st.header('의료 진단 보조 챗봇', divider='gray') # divider 옵션: blue, green, orange, red, violet, gray, grey, rainbow
    st.title('MEGA')
    with st.container(border=False):
        col_intro, col_guide = st.columns(2)
        with col_intro:
            st.write('''
            👋 안녕하세요! 의료 진단 보조 챗봇 **메가**입니다.

            문진표 작성과 이미지 파일을 업로드해주시면 초진기록지 작성을 도와드리겠습니다!
            ''')
        with col_guide:
            st.write('''
            💡 **사용 방법**
            1. 하단의 **문진표**를 작성해주세요.
            2. 진단이 필요한 **의료 이미지 파일**을 사이드바에서 업로드해주세요.
            3. 업로드가 완료되면 **초진기록지 초안**을 작성해드립니다.
            ''')

    # 문진표
    with st.container(border=True):
        medical_form_data = create_medical_form()

    # 이미지 업로드 시
    if uploaded_file:
        image = Image.open(uploaded_file)
        # st.image(image, caption='업로드된 원본 이미지', use_column_width=True) # (선택) 분석 전 원본 이미지만 먼저 보여주기
    
        if st.sidebar.button("진단 분석 시작하기 🚀"):
            with st.spinner("AI가 이미지를 분석하고 초진기록지를 작성 중입니다..."): # (선택) 로딩 애니메이션

                # 모델 예측
                st.session_state['diagnosis_type'] = 0 if image_type=='갑상선 초음파' else 1
                model = im.load_model(st.session_state.diagnosis_type)
                if st.session_state['diagnosis_type'] == 0:
                    prob, label = im.predict_image(image, model, st.session_state.diagnosis_type)
                else:
                    prob, label, visualized_image = im.predict_image(image, model, st.session_state.diagnosis_type)

                # 초진기록지 초안
                medical_record = am.generate_medical_record(gemini, st.session_state.form_data, st.session_state.diagnosis_type, prob, label)

                col_image, col_result = st.columns([1, 2])
                with col_image:
                    if st.session_state['diagnosis_type'] == 0:
                        st.image(image, caption='분석된 갑상선 초음파 이미지', use_column_width=True)
                    else:
                        st.image(visualized_image, caption='분석된 뇌 MRI 이미지', use_column_width=True)
                with col_result:
                    with st.container(border=True):
                        st.subheader(f'{prob}%의 확률로 {label}입니다.')
                        st.write(medical_record)

    
    ## 챗봇 ##
    
    # 메시지 기록
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    
    # 채팅
    if prompt:=st.chat_input('메시지를 입력하세요.'):
        st.chat_message('user').markdown(prompt) # 사용자 메시지 출력
        try: # gemini 응답
            response = gemini.generate_content([prompt])
            with st.chat_message('assistant'):
                st.markdown(response.text) # gemini 답변 출력
            st.session_state.messages.append({'role':'user', 'content':prompt}) # 대화 기록 저장
            st.session_state.messages.append({'role':'assistant', 'content':response.text}) # 대화 기록 저장
        except Exception as e:
            st.error(f'Gemini 응답 오류 발생: {str(e)}')


if __name__=='__main__':
    main()