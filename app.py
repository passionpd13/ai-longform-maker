import streamlit as st
import requests
import random
import json
import time
import os
import re
import shutil
import zipfile
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from google import genai
from google.genai import types

# [NEW] 오디오 처리를 위한 라이브러리 추가
try:
    from pydub import AudioSegment
    from pydub.silence import detect_silence
except ImportError:
    pass 

# [NEW] 동영상 생성을 위한 라이브러리 및 효과 추가
try:
    from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips
    import numpy as np 
except ImportError:
    st.error("⚠️ 'moviepy' 라이브러리가 없습니다. 터미널에 'pip install moviepy numpy'를 입력하세요.")
    st.stop()

# ==========================================
# [설정] 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="열정피디 AI 유튜브 대본 구조 분석기 (Pro)", 
    layout="wide", 
    page_icon="🎬",
    initial_sidebar_state="expanded"
)

# ==========================================
# [디자인] 다크모드 가독성 최종 수정 (CSS)
# ==========================================
st.markdown("""
    <style>
    /* [1] 앱 전체 강제 다크모드 */
    .stApp {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
        font-family: 'Pretendard', sans-serif;
    }

    /* [2] 사이드바 텍스트 하얗게 */
    section[data-testid="stSidebar"] {
        background-color: #12141C !important;
        border-right: 1px solid #2C2F38;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* [3] 파일 업로더 가독성 해결 */
    [data-testid="stFileUploader"] {
        background-color: #262730 !important;
        border-radius: 10px;
        padding: 15px;
    }
    [data-testid="stFileUploader"] section {
        background-color: #262730 !important; /* 드롭존 배경 어둡게 */
    }
    /* 업로더 내부 설명 글씨(Drag and drop items here) */
    [data-testid="stFileUploader"] div, 
    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] small {
        color: #FFFFFF !important;
    }
    /* 'Browse files' 버튼 */
    [data-testid="stFileUploader"] button {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
        border: 1px solid #555 !important;
    }

    /* [4] 드롭다운(Selectbox) 가독성 해결 */
    div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border-color: #4A4A4A !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #262730 !important;
    }
    div[data-baseweb="option"], li[role="option"] {
        color: #FFFFFF !important;
        background-color: #262730 !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #FF4B2B !important;
        color: #FFFFFF !important;
    }

    /* [5] 모든 버튼 스타일 (제목 추천 포함) - 여기가 문제였음 */
    .stButton > button {
        /* 배경색을 흰색이 아닌 그라데이션으로 강제 고정 */
        background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        transition: transform 0.2s;
        color: #FFFFFF !important;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(255, 75, 43, 0.4);
    }
    /* 버튼 내부 텍스트(p태그) 강제 흰색 */
    .stButton > button p {
        color: #FFFFFF !important;
    }

    /* [6] Expander (프롬프트 확인) 스타일 수정 - 여기가 문제였음 */
    div[data-testid="stExpander"] {
        background-color: #1F2128 !important; /* 배경 어둡게 */
        border: 1px solid #4A4A4A !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
    /* 헤더(클릭하는 부분) 글씨색 */
    div[data-testid="stExpander"] > details > summary {
        color: #FFFFFF !important; 
    }
    /* 헤더 내부의 p태그 */
    div[data-testid="stExpander"] > details > summary p {
        color: #FFFFFF !important;
    }
    /* 화살표 아이콘 */
    div[data-testid="stExpander"] > details > summary svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    /* 펼쳤을 때 나오는 내용 */
    div[data-testid="stExpander"] > details > div {
        color: #DDDDDD !important;
    }

    /* [7] 입력창 스타일 */
    .stTextInput input, .stTextArea textarea {
        background-color: #262730 !important; 
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid #4A4A4A !important;
        caret-color: #FF4B2B !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #B0B0B0 !important;
        -webkit-text-fill-color: #B0B0B0 !important;
    }

    /* [8] 다운로드 버튼 */
    [data-testid="stDownloadButton"] button {
        background-color: #2C2F38 !important;
        border: 1px solid #555 !important;
    }
    [data-testid="stDownloadButton"] button p {
        color: #FFFFFF !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        border-color: #FF4B2B !important;
    }
    [data-testid="stDownloadButton"] button:hover p {
        color: #FF4B2B !important;
    }

    /* [9] 기타 텍스트 */
    h1, h2, h3, h4, p, label, li {
        color: #FFFFFF !important;
    }
    .stCaption {
        color: #AAAAAA !important;
    }
    header[data-testid="stHeader"] {
        background-color: #0E1117 !important;
    }
    </style>
""", unsafe_allow_html=True)


# 파일 저장 경로 설정
BASE_PATH = "./web_result_files"
IMAGE_OUTPUT_DIR = os.path.join(BASE_PATH, "output_images")
AUDIO_OUTPUT_DIR = os.path.join(BASE_PATH, "output_audio")
VIDEO_OUTPUT_DIR = os.path.join(BASE_PATH, "output_video") 

# 텍스트 모델 설정
GEMINI_TEXT_MODEL_NAME = "gemini-2.5-pro" 

# [기본값] 문서에 명시된 정확한 호스트 주소
DEFAULT_SUPERTONE_URL = "https://supertoneapi.com"
DEFAULT_VOICE_ID = "ff700760946618e1dcf7bd" 

# ==========================================
# [함수] 0. TTS용 텍스트 정규화 (숫자/기호 -> 한글)
# ==========================================
def num_to_kor(num_str):
    """숫자 문자열을 한글 발음으로 변환 (예: 1,500 -> 천오백)"""
    try:
        num_str = num_str.replace(',', '')
        if not num_str.isdigit(): return num_str
        
        num = int(num_str)
        if num == 0: return "영"
        
        units = ['', '십', '백', '천']
        big_units = ['', '만', '억', '조', '경']
        num_chars = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
        
        result = []
        big_idx = 0
        
        while num > 0:
            small_part = num % 10000
            if small_part > 0:
                small_res = []
                small_idx = 0
                while small_part > 0:
                    digit = small_part % 10
                    if digit > 0:
                        unit = units[small_idx]
                        char = num_chars[digit]
                        if digit == 1 and small_idx > 0:
                            char = ""
                        small_res.append(char + unit)
                    small_part //= 10
                    small_idx += 1
                result.append("".join(reversed(small_res)) + big_units[big_idx])
            num //= 10000
            big_idx += 1
            
        return "".join(reversed(result))
    except:
        return num_str

def normalize_text_for_tts(text):
    """TTS 발음을 위해 특수문자와 숫자를 한글 발음으로 변환"""
    # [추가] 일본어 문자가 포함되어 있으면 정규화(숫자 한글 변환)를 건너뜀
    if any("\u3040" <= char <= "\u30ff" for char in text):
        return text

    text = text.replace("%", " 퍼센트")
    
    def replace_decimal(match):
        return f"{match.group(1)} 점 {match.group(2)}"
    text = re.sub(r'(\d+)\.(\d+)', replace_decimal, text)

    def replace_number(match):
        return num_to_kor(match.group())
    
    text = re.sub(r'\d+(?:,\d+)*', replace_number, text)
    
    return text

# ==========================================
# [함수] 1. 대본 구조화 로직
# ==========================================
def generate_structure(client, full_script):
    """Gemini를 이용해 대본 구조화"""
    prompt = f"""
    [Role]
    You are a professional YouTube Content Editor and Scriptwriter.

    [Task]
    Analyze the provided transcript (script).
    Restructure the content into a highly detailed, list-style format suitable for a blog post or a new video plan.
        
    [Output Format]
    1. **Video Theme/Title**: (Extract or suggest a catchy title based on the whole script)
    2. **Intro**: (Hook and background, no music) Approve specific channel names, The intro hooks the overall topic (안녕하십니까 같은 인사 금지)
    3. **Chapter 1** to **Chapter 8**: (Divide the main content into logical sections. Use detailed bullet points for each chapter.)
    4. **Epilogue**: (Conclusion and Subscribe Like Comments that make you anticipate the next specific content)

    [Constraint]
    - Analyze the entire context deeply.
    - Write the output in **Korean**.
    - Make the content rich and detailed.
    - If the original script has a channel name, remove it.

    [Transcript]
    {full_script}
    """
    
    try:
        response = client.models.generate_content(
            model=GEMINI_TEXT_MODEL_NAME,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

# ==========================================
# [함수] 2. 섹션별 대본 생성 (수정 버전)
# ==========================================
def generate_section(client, section_title, full_structure, duration_type="fixed", custom_instruction=""):
    # 1. 분량에 따른 글자수 및 지침 설정
    if duration_type == "2min":
        target_chars = "약 1,000자 (공백 포함)"
        detail_level = "핵심 내용 위주로 명확하게 전달하되, 너무 짧지 않게 서술하십시오."
    elif duration_type == "3min":
        target_chars = "약 1,500자 (공백 포함)"
        detail_level = "충분한 예시와 설명을 곁들여 상세하게 서술하십시오."
    elif duration_type == "4min":
        target_chars = "약 2,000자 이상 (공백 포함)"
        detail_level = "현미경으로 들여다보듯 아주 깊이 있고 디테일하게 묘사하십시오. 절대 요약하지 마십시오."
    else: # Intro / Epilogue (Fixed)
        target_chars = "약 400단어 (약 1,400자)"
        detail_level = "시청자를 사로잡는 강력한 후킹과 여운을 주는 마무리로 작성하십시오. 안녕 인사는 하지 않는다"

    user_guide_prompt = ""
    if custom_instruction:
        user_guide_prompt = f"""
    [User's Special Direction]
    The user has provided specific instructions for the tone/style. You MUST follow this:
    👉 "{custom_instruction}"
        """

    prompt = f"""
    [Role]
    당신은 대한민국 최고의 유튜브 다큐멘터리 작가입니다.

    [Task]
    전체 대본 구조 중 오직 **"{section_title}"** 부분만 작성하십시오.
        
    [Context (Overall Structure)]
    {full_structure}
    {user_guide_prompt}

    [Target Section]
    **{section_title}**

    [Length Constraints]
    - **목표 분량: {target_chars}** - **작성 지침:** {detail_level}
        
    [Style Guidelines - 매우 중요]
    1. '습니다' 체를 사용하고, 다큐멘터리 특유의 진지하고 몰입감 있는 어조를 유지하세요.
    2. 앞뒤 문맥(이전 챕터, 다음 챕터)을 고려하되, 이 파트의 내용에만 집중하세요.
    3. (지문), (효과음) 같은 연출 지시어는 제외하고 **오직 나레이션 대사만** 출력하세요.
    4. 서두에 "네, 알겠습니다" 같은 잡담을 하지 말고 바로 대본 내용을 시작하세요.
    5. 영문 병기(괄호)는 하지 마세요. 깔끔하게 한글만.
    6. 쉼표와 접속어 등을 사용하여, 리듬이 있지만 너무 끊기지 않는 흐름을 만들 것.
    
    # [수정됨] 흐름 끊김 방지 핵심 지침 --------------------------
    7. **[금지사항]** 글의 마지막에 "다음 장에서는...", "이어서...", "이제 ~를 알아보겠습니다" 같은 **예고성 멘트를 절대 쓰지 마십시오.**
    8. **[금지사항]** "지금까지 ~를 알아보았습니다" 같은 **중간 정리 멘트도 절대 쓰지 마십시오.**
    9. 이 텍스트들은 나중에 하나로 합쳐질 것입니다. 따라서 **그냥 설명하다가 자연스럽게 문장(마침표)으로 끝내십시오.** 뒷내용은 다음 텍스트가 자연스럽게 이어받습니다.
    10. 챕터 번호나 소제목을 본문에 다시 적지 마십시오. 오직 내용만 서술하십시오.
    ---------------------------------------------------------

    [Output]
    (지금 바로 {section_title}의 원고를 작성 시작하세요)
    """
    
    try:
        response = client.models.generate_content(
            model=GEMINI_TEXT_MODEL_NAME, 
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.75 
            )
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

# ==========================================
# [함수] 3. 이미지 생성 관련 로직
# ==========================================

def init_folders():
    for path in [IMAGE_OUTPUT_DIR, AUDIO_OUTPUT_DIR, VIDEO_OUTPUT_DIR]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

def split_script_by_time(script, chars_per_chunk=100):
    # [수정됨] 일본어 구두점 및 줄바꿈(\n)도 확실하게 분리하도록 개선
    temp_script = script.replace(".", ".|").replace("?", "?|").replace("!", "!|") \
                        .replace("。", "。|").replace("？", "？|").replace("！", "！|") \
                        .replace("\n", "\n|")  # 줄바꿈도 강제 분리 기준으로 추가

    temp_sentences = temp_script.split("|")
                             
    chunks = []
    current_chunk = ""
    
    for sentence in temp_sentences:
        sentence = sentence.strip()
        if not sentence: continue
        
        if len(current_chunk) + len(sentence) < chars_per_chunk:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk.strip(): 
                chunks.append(current_chunk.strip())
            
            current_chunk = sentence
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

def make_filename(scene_num, text_chunk):
    # 1. 줄바꿈을 공백으로 변경하고 양쪽 공백 제거
    clean_line = text_chunk.replace("\n", " ").strip()
    
    # 2. 파일명에 쓸 수 없는 특수문자 제거
    clean_line = re.sub(r'[\\/:*?"<>|]', "", clean_line)
    
    # [안전장치] 만약 정제 후 내용이 없다면 기본값 반환
    if not clean_line:
        return f"S{scene_num:03d}_Scene.png"
    
    # [수정됨] 일본어/긴 문자열 대응 로직
    words = clean_line.split()
    
    # 조건: 단어가 1개뿐이거나(일본어), 아시아권 문자(한글/일본어 등 유니코드 > 12000)가 포함된 경우
    if len(words) <= 1 or any(ord(c) > 12000 for c in clean_line[:10]): 
        if len(clean_line) > 16:
            # 앞 8자 ... 뒤 8자 (총 19자)
            summary = f"{clean_line[:10]}...{clean_line[-10:]}"
        else:
            summary = clean_line
    else:
        # 기존 로직 (영어 등 띄어쓰기가 명확한 경우)
        if len(words) <= 6:
            summary = " ".join(words)
        else:
            start_part = " ".join(words[:3])
            end_part = " ".join(words[-3:])
            summary = f"{start_part}...{end_part}"
            
            # [추가 안전장치] 영어라도 단어가 너무 길 경우를 대비해 50자로 강제 절삭
            if len(summary) > 50:
                summary = summary[:50]
    
    # 최종 파일명 생성
    filename = f"S{scene_num:03d}_{summary}.png"
    return filename

# ==========================================
# [함수 수정] 캐릭터 참조 이미지 분석 (DNA 추출 버전)
# ==========================================
def analyze_character_image(api_key, image_bytes):
    """업로드된 캐릭터 이미지를 분석하여 '이미지 생성 전용 프롬프트(DNA)'를 추출"""
    client = genai.Client(api_key=api_key)
    
    # [핵심 변경] 단순 묘사가 아니라, 이미지 생성 AI가 알아듣는 '키워드' 위주로 추출 요청
    prompt = """
    [Role]
    You are an expert 'Reverse Prompt Engineer' for AI Image Generation (like Midjourney, Stable Diffusion).

    [Task]
    Analyze the uploaded character image and extract its "Visual DNA".
    Your output must be a strict set of keywords and descriptions that will force another AI to generate 99% identical character.

    [Extraction Rules]
    1. **Art Style (Crucial):** Define the exact medium (e.g., '2D flat vector', '3D Unreal Engine render', 'Oil painting', 'Sketch'). Mention line weight, shading style, and texture.
    2. **Character Features:** Precise details (e.g., 'Silver messy hair', 'Sharp red cat-eyes', 'Scar on left cheek').
    3. **Outfit & Colors:** Describe clothes specifically (e.g., 'Navy blue hoodie with white strings', 'Gold armor plate'). Mention key colors.
    4. **Vibe & Lighting:** (e.g., 'Cyberpunk neon lighting', 'Soft pastel atmosphere').

    [Output Format]
    **Do not write sentences.** Output a structured Prompt Block like this:
    
    (Art Style Keywords), (Character Subject Description), (Outfit Details), (Color Palette & Lighting)
    
    Example:
    "Flat 2D vector art, thick black outlines, cell shading, A cute robot with round glowing blue eyes, white sleek metal body, rusty joints, orange mechanical wings, bright studio lighting, white background"
    """
    
    try:
        # PIL Image로 변환하여 전송
        image = Image.open(BytesIO(image_bytes))

        response = client.models.generate_content(
            model="gemini-2.5-pro", # 분석은 똑똑한 2.5 Pro 모델이 수행
            contents=[prompt, image]
        )
        return response.text.strip()
    except Exception as e:
        return f"Error analyzing image: {e}"

# ==========================================
# [함수] 프롬프트 생성 (수정됨: 캐릭터 일관성 + 비율 구도 추가)
# ==========================================
def generate_prompt(api_key, index, text_chunk, style_instruction, video_title, genre_mode="info", target_language="Korean", character_desc="", target_layout="16:9 와이드 시네마틱 비율"):
    scene_num = index + 1
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TEXT_MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}

    # [언어 설정 로직] 선택된 언어에 따라 지침 자동 변경
    if target_language == "Korean":
        lang_guide = "화면 속 글씨는 **무조건 '한글(Korean)'로 표기**하십시오. (다른 언어 절대 금지)"
        lang_example = "(예: '뉴욕', '도쿄')"
    elif target_language == "English":
        lang_guide = "화면 속 글씨는 **무조건 '영어(English)'로 표기**하십시오."
        lang_example = "(예: 'Seoul', 'Dokdo')"
    elif target_language == "Japanese":
        lang_guide = "화면 속 글씨는 **무조건 '일본어(Japanese)'로 표기**하십시오."
        lang_example = "(예: 'ソウル', 'ニューヨーク')"
    else:
        lang_guide = f"화면 속 글씨는 **무조건 '{target_language}'로 표기**하십시오."
        lang_example = ""

    # ------------------------------------------------------
    # [NEW] 캐릭터 일관성 유지 지침 블록 생성
    # ------------------------------------------------------
    character_consistency_block = ""
    if character_desc and "Error" not in character_desc:
        character_consistency_block = f"""
    [⭐⭐⭐ 비주얼 일관성 유지 핵심 지침 (최우선 순위) ⭐⭐⭐]
    모든 장면에 등장하는 주인공 캐릭터는 반드시 아래의 상세 묘사와 시각적으로 일치해야 합니다.
    절대로 이 캐릭터의 핵심적인 외형 특징을 바꾸지 마십시오.

    **[Reference Character Visual Blueprint]:**
    {character_desc}
    ---------------------------------------------------------
        """

    # ------------------------------------------------------
    # [NEW] 화면 구도(비율) 지침 블록 생성
    # ------------------------------------------------------
    layout_prompt_block = f"""
    [화면 구도(Composition) 지침 - 매우 중요]
    - **목표 비율:** {target_layout}
    - **배치:** 이 비율에 맞춰서 피사체를 배치하십시오. 
      (9:16인 경우: 위아래로 긴 구도이므로 캐릭터나 중요 사물이 중앙에 오되 잘리지 않게 묘사)
      (16:9인 경우: 좌우로 넓은 시네마틱 구도 활용)
    """

    # 공통 헤더 (모든 모드에 주입)
    common_header = f"""
    {character_consistency_block}
    {layout_prompt_block}
    """

    # ---------------------------------------------------------
    # [모드 1] 밝은 정보/이슈
    # ---------------------------------------------------------
    if genre_mode == "info":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 복잡한 상황을 아주 쉽고 직관적인 그림으로 표현하는 '비주얼 커뮤니케이션 전문가'이자 '교육용 일러스트레이터'입니다.

    [전체 영상 주제]
    "{video_title}"

    [그림 스타일 가이드 - 절대 준수]
    {style_instruction}
    
    [필수 연출 지침]
    1. **조명(Lighting):** 무조건 **'몰입감있는 조명(High Key Lighting)'**을 사용하십시오.
    2. **색감(Colors):** 선명한 색상을 사용하여 시인성을 높이십시오. (칙칙하거나 회색조 톤 금지)
    3. **구성(Composition):** 시청자가 상황을 한눈에 이해할 수 있도록 피사체를 화면 중앙에 명확하게 배치하십시오.
    4. **분위기(Mood):** 교육적이지만 사실적, 중립적이며, 몰입감있는 분위기여야 합니다. **(절대 우울하거나, 무섭거나, 기괴한 느낌 금지)**
    5. 분활화면으로 연출하지 말고 하나의 화면으로 연출한다.
    6. **[텍스트 언어]:** {lang_guide} {lang_example}
    - **[절대 금지]:** 화면의 네 모서리(Corners)나 가장자리(Edges)에 글자를 배치하지 마십시오. 글자는 반드시 중앙 피사체 주변에만 연출하십시오.
    7. 캐릭터의 감정도 느껴진다.
    8. 특정 국가에 대한 내용일시 배경에 국가 분위기가 연출 잘되게 한다.
    9. 배경 현실감(Background Realism): 배경은 단순한 평면이 아닌, **깊이감(Depth)**과 **질감(Texture)**이 살아있는 입체적인 공간으로 연출하십시오. 추상적이거나 흐릿한 배경 대신, 실제 장소에 있는 듯한 **구체적인 환경 디테일(건축 양식, 자연물, 소품 배치, 거리, 공간간 등)을 선명하게 묘사하여 2d이지만 현장감을 극대화하십시오.


    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 이미지 생성 AI가 그릴 수 있는 **구체적인 묘사 프롬프트**를 작성하십시오.
    
    [작성 요구사항]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - **포함 요소:**
        - **캐릭터 행동:** 대본의 상황을 연기하는 캐릭터의 구체적인 동작.
        - **배경:** 상황을 설명하는 소품이나 장소를 몰입감 있고 깊이감 있게 2d로 구성. 
        - **시각적 은유:** 추상적인 내용일 경우, 이를 설명할 수 있는 시각적 아이디어 (예: 돈이 날아가는 모습, 그래프가 하락하는 모습 등).
          한글 뒤에 (영어)를 넣어서 프롬프트에 쓰지 않는다. ex) 색감(Colors) x ,구성(Composition) x

    
    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오.
    - 부가적인 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """

    # ---------------------------------------------------------
    # [모드 NEW] 스틱맨 사실적 연출 (Realistic Stickman Drama)
    # ---------------------------------------------------------
    elif genre_mode == "realistic_stickman":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **'넷플릭스 2D 애니메이션 감독'**입니다. 
    **반드시 '2D 그림(Digital Art)' 스타일**이어야 하며, **실사(Photorealism)나 3D 렌더링 느낌이 나면 절대 안 됩니다.**
    단순한 얼굴이 둥근 스틱맨들을 주인공으로 사용하여, 배경과 조명만 영화처럼 분위기 있게 연출합니다.
    
    [전체 영상 주제] "{video_title}"
    [유저 스타일 선호] {style_instruction}

    [🚫 핵심 금지 사항 - 절대 어기지 마시오]
    - **실사 사진(Real Photo), 3D 렌더링(Unreal Engine), 사람 피부 질감(Skin texture) 절대 금지.**
    - 사람의 코, 입, 귀, 손톱 등을 리얼하게 묘사하지 마시오.
    - 무조건 **'그림(Illustration/Drawing/Manhwa)'** 느낌이 나야 합니다.

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **캐릭터(Character):** - **얼굴이 둥근 하얀색 스틱맨(Round-headed white stickman)**을 사용하십시오.
       - 하지만 선은 굵고 부드러우며, **그림자(Shading)**가 들어가 입체감이 느껴져야 합니다.
       - **의상:** 대본 상황에 맞는 현실적인 의상(정장, 군복, 잠옷, 작업복 등)을 스틱맨 위에 입혀 '캐릭터성'을 부여하십시오.
       - 얼굴이 크게 잘 보이게 연출. 장면도 잘 드러나게.
       
    2. **배경(Background) - 가장 중요:**
       - 단순한 그라데이션이나 단색 배경을 **절대 금지**합니다.
       - **고해상도 컨셉 아트(High-quality Concept Art)** 수준으로 배경을 그리십시오.
       - 예: 사무실이라면 책상의 서류 더미, 창밖의 풍경, 커피잔의 김, 벽의 질감까지 묘사해야 합니다.
       
    3. **조명(Lighting):**
       - 2D지만 **입체적인 조명(Volumetric Lighting)**과 그림자를 사용하여 깊이감을 만드십시오.
       - 상황에 따라 따뜻한 햇살, 차가운 네온사, 어두운 방의 스탠드 조명 등을 명확히 구분하십시오.
       
    4. **연기(Acting):**
       - 인포그래픽처럼 정보를 나열하지 말고, **캐릭터가 행동(Action)하는 장면**을 포착하십시오.
       - 감정 표현: 얼굴 표정은 단순하게 가되, **어깨의 처짐, 주먹 쥔 손, 다급한 달리기, 무릎 꿇기 등 '몸짓(Body Language)'**으로 감정을 전달하십시오.

    5. **언어(Text):** {lang_guide} {lang_example} (자막 연출보다는 배경 속 간판, 서류, 화면 등 자연스러운 텍스트 위주로)
    6. **구도:** 분할 화면(Split Screen) 금지. **{target_layout}** 꽉 찬 시네마틱 구도 사용.

    [임무]
    제공된 대본 조각(Script Segment)을 읽고, 그 상황을 가장 잘 보여주는 **한 장면의 영화 스틸컷** 같은 프롬프트를 작성하십시오.
    
    [작성 팁]
    - "A cinematic 2D shot of a round-headed stickman..." 으로 시작하는 느낌으로 작성.
    - 대본이 추상적(예: 경제 위기)이라면, 스틱맨이 텅 빈 지갑을 보며 좌절하는 구체적인 상황으로 치환하여 묘사하십시오.
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - 자막 같은 연출 하지 않는다. ("화면 하단 중앙에는 명조체로 **'필리핀, 1944년'**이라는 한글 텍스트가 선명하게 새겨져 있다" 이런 연출 하면 안된다) 

    
    [출력 형식]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - **무조건 한국어(한글)**로만 작성하십시오.
    - 부가 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """

    # ---------------------------------------------------------
    # [모드 2] 역사/다큐 (수정됨: else -> elif)
    # ---------------------------------------------------------
    elif genre_mode == "history":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **세계사의 결정적인 순간들(한국사, 서양사, 동양사 등)**을 한국 시청자에게 전달하는 '시대극 애니메이션 감독'입니다.
    역사적 비극을 다루지만, 절대로 잔인하거나 혐오스럽거나 고어틱하게 묘사를 하지 않습니다.

    [전체 영상 주제] "{video_title}"
    [그림 스타일 가이드 - 유저 지정 (최우선 준수)] {style_instruction}
    
    [필수 연출 지침]
    1. **[매우 중요] 매체(Medium):** 무조건 **평면적인 '2D 스틱맨 일러스트레이션'** 스타일로 표현하십시오. (3D, 실사, 모델링 느낌 절대 금지)
    2. **[매우 중요] 텍스트 현지화(Localization):** 배경이 서양, 중국, 일본 등 어디든 상관없이, {lang_guide}
        - **금지:** 지정된 언어 외의 문자 사용을 절대 금지합니다.
        - **예시:** {lang_example}
    3. **[매우 중요 - 순화된 표현] 비극의 상징화(Symbolization of Tragedy):** 전쟁, 죽음, 고통과 같은 비극적인 상황은 **절대로 직접적으로 묘사하지 마십시오.** 물리적 폭력 대신, **상실감, 허무함, 애도**의 정서에 집중하십시오.
        - **핵심:** 파괴된 신체나 직접적인 무기 사용 장면 대신, **남겨진 물건(주인 없는 신발, 깨진 안경), 드리우는 그림자, 시들어버린 자연물, 혹은 빛이 사라지는 연출** 등을 통해 간접적으로 슬픔을 표현하십시오.
    4. **[핵심] 다양한 장소와 시대 연출(Diverse Locations):** 대본에 나오는 **특정 시대와 장소의 특징(건축 양식, 의상, 자연환경)을 정확히 포착**하여 그리십시오.
    5. **[수정됨] 절제된 캐릭터 연기(Restrained Acting):** 2D 스틱맨 캐릭터는 시대에 맞는 의상을 입되, **과장된 표정보다는 '몸짓(Body Language)'과 '분위기'로 감정을 표현**해야 합니다. 비극적인 상황에서도 격렬한 분노나 공포보다는 **깊은 슬픔, 체념, 혹은 간절한 기도**와 같은 정적인 감정을 우선시하십시오.
    6. **조명(Lighting):** 2D 작화 내에서 극적인 분위기를 만드는 **'시네마틱 조명'**을 사용하십시오. (시대극 특유의 톤)
    7. **[수정됨] 색감(Colors):** **차분하고 애상적인 색감(Somber & Melancholic Tones)**을 사용하십시오. 깊이 있되 다양한 채도의 색조를 사용하여, 역사 다큐멘터리의 톤앤매너를 유지하십시오. (자극적인 붉은색 과다 사용 금지)
    8. **구성(Composition):** 시청자가 상황을 한눈에 이해할 수 있도록 핵심 피사체를 화면 중앙에 배치하십시오. 분활화면(Split screen)은 금지입니다.
    - **[절대 금지]:** 텍스트가 화면의 네 모서리(Corners)나 가장자리에 배치되는 것을 절대 금지합니다. (자막 공간 확보)
    9. **[매우 중요] 배경보다 **'인물(Character)'이 무조건 우선**입니다. 캐릭터가 화면을 장악해야 합니다.
    10. 상호작용하는 소품 (Interactive Props): 스틱맨 캐릭터가 대본 속 중요한 사물과 어떻게 상호작용하는지 명확히 그리십시오. 사물은 단순하지만 그 특징이 명확해야 합니다.
    11. 캐릭터 연출 : 스틱맨은 시대를 반영하는 의상과 헤어스타일을 연출한다.
    
    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 이미지 생성 AI가 그릴 수 있는 **구체적인 묘사 프롬프트**를 작성하십시오.
    
    [작성 요구사항]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - **포함 요소:**
        - **텍스트 지시:** (중요) 이미지에 들어갈 텍스트를 반드시 **'{target_language}'**로 명시하십시오.
            - 텍스트는 그래픽 연출이 아니라 화면의 사물에 자연스럽게 연출되게 한다.
        - **안전한 묘사:** 잔인한 장면은 은유적으로 표현하여 필터링을 피하십시오.
        - **시대적 배경:** 대본의 시대(고대/중세/근대)와 장소(동양/서양)를 명확히 반영한 배경 묘사.
        - **[수정됨] 절제된 캐릭터 연기 묘사:**
            - 스틱맨의 얼굴은 **단순한 선으로 표현된 슬픈 눈매, 굳게 다문 입매** 정도로 절제하여 묘사하십시오. (기괴한 표정 묘사 금지)
            - 스틱맨의 시대적 의상과 헤어스타일을 연출한다.
            - **감정은 몸짓으로 표현하십시오.** (예: 고개를 깊이 숙인 모습, 얼굴을 감싸 쥔 손, 힘없이 축 늘어진 어깨, 무릎 꿇고 기도하는 자세 등 정적인 동작 위주)
        - 배경 보다는 대본에 어울리는 인물들과 상황 연출에 더 초점을 맞춘다.
        - 자막 같은 연출 하지 않는다. ("화면 하단 중앙에는 명조체로 **'필리핀, 1944년'**이라는 한글 텍스트가 선명하게 새겨져 있다" 이런 연출 하면 안된다) 
    
    [🎭 캐릭터 감정 연기 지침 (Character Acting Guide) - 중요]
    **얼굴 표정이 단순한 스틱맨이므로, '몸짓(Body Language)'으로 감정을 표현하는 데 집중하십시오.**
    
    - 금지: 피(Blood), 출혈, 시체(Corpse, Dead body), 잘린 머리(Decapitation), 고문, 자살, 뼈/해골(Skeleton), 내장, 리얼한 총/칼(Weapon).
    - **추가 금지:** 과도하게 일그러진 얼굴 표정, 공포에 질려 비명 지르는 입 모양 등 자극적인 얼굴 묘사.
    - 금지: 나치(Nazi), 욱일기 등 정치적으로 극도로 민감한 심볼.
    
    [🛡️ 검열 회피를 위한 '시각적 은유(Visual Metaphors)' 가이드]
    대본 내용이 비극적이거나 폭력적일 경우, 반드시 아래의 **부드러운 상징물**로 대체하여 묘사하십시오.
    
    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오.
    - 부가적인 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
    - 프롬프트에 '얼굴이 둥근 2d 스틱맨' 무조건 들어간다.
        """

    # ---------------------------------------------------------
    # [모드 3] 3D 다큐멘터리 (현대/미스터리)
    # ---------------------------------------------------------
    elif genre_mode == "3d_docu":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 'Unreal Engine 5'를 사용하는 3D 시네마틱 아티스트입니다.
    현대 사회의 이슈나 미스터리한 현상을 고퀄리티 3D 그래픽으로 시각화합니다.

    [전체 영상 주제] "{video_title}"
    [유저 스타일 선호] {style_instruction}

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **화풍 (Art Style):** "A realistic 3D game cinematic screenshot", "Unreal Engine 5 render style", "8k resolution", "Highly detailed texture".
    2. **캐릭터 디자인 (Character Design):** - 등장인물의 머리는 반드시 **"매끈하고 하얀, 이목구비가 없는 마네킹 머리 (Smooth white featureless mannequin head)"**여야 합니다.
        - **얼굴 묘사 금지:** 눈, 코, 입이 절대 없어야 합니다 (Blank face, No eyes/nose/mouth).
        - **의상:** 하지만 몸에는 **현실적인 의상(정장, 가디건, 청바지, 유니폼 등)**을 입혀서 기묘하고 현대적인 느낌을 줍니다.
    3. **조명 및 분위기 (Lighting & Mood):** - "Cinematic lighting", "Dim lighting", "Volumetric fog".
        - 다소 어둡고, 밝기도 하며, 미스터리하며, 진지한 분위기를 연출하십시오.
    4. **언어 (Text):** {lang_guide} {lang_example} (가능한 텍스트 묘사는 줄이고 상황 묘사에 집중)

    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 위 스타일이 적용된 이미지 생성 프롬프트를 작성하십시오.
    
    [작성 팁]
    - 프롬프트 시작 부분에 반드시 **"언리얼 엔진 5 스타일, Realistic 3D game screenshot, Smooth white featureless mannequin head character"** 키워드가 포함되도록 문장을 구성하십시오.
    - 대본의 상황(좌절, 성공, 회의, 폭락 등)을 마네킹 캐릭터가 연기하도록 묘사하십시오.
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.

    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오. (단, Unreal Engine 5 같은 핵심 영단어는 혼용 가능)
    - 부가 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """
        
    # ---------------------------------------------------------
    # [모드 4] 과학/엔지니어링 (Clean Technical + Characters) - [NEW! 재수정됨]
    # ---------------------------------------------------------
    elif genre_mode == "scifi":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 'Fern', 'AiTelly', 'Blackfiles' 채널 스타일의 **깔끔하고 명확한 '3D 테크니컬 애니메이터'**입니다.
    복잡한 기계나 과학 원리를 설명하되, **엔지니어/과학자 캐릭터의 행동**을 통해 시청자의 이해를 돕습니다. (어둡고 과한 시네마틱 X, 밝고 명확한 교육용 O)

    [전체 영상 주제] "{video_title}"
    [유저 스타일 선호] {style_instruction}

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **화풍 (Art Style):** "3D Technical Animation", "Blender Cycles Render", "Clean rendering", "High detail".
    2. **분위기 및 조명 (Atmosphere & Lighting):**
        - **"Clean Studio Lighting", "Bright", "Educational"**.
        - 그림자가 너무 짙거나 어두워서는 안 됩니다. 모든 부품과 인물이 명확하게 보여야 합니다.
    3. **피사체 (Subject) - 기계와 인물의 조화:**
        - **기계/구조물:** 단면도(Cutaway), 투시도(X-ray view), 분해도(Exploded view)를 적극 활용하여 내부 작동 원리를 보여주십시오.
        - **[중요] 인물(Characters):** 대본 내용에 맞춰 엔지니어, 과학자, 작업자를 3d 게임 캐릭터 처럼 등장시키십시오.
            - **복장:** 안전모, 실험 가운, 작업복 등 전문적인 복장.
            - **행동:** 단순히 서 있는 것이 아니라, **기계를 조작하거나, 특정 부위를 가리키며 설명하거나, 단면을 관찰하는 등 '기능적인 행동'**을 취해야 합니다.
    4. **카메라 (Camera):** "Clear view", "Isometric view"(선택적), "Slight zoom"(디테일 강조). 과도한 아웃포커싱(심도)은 자제하고 전체적으로 쨍하게 보여주십시오.
    5. **언어 (Text):** {lang_guide} {lang_example} (화살표와 함께 부품 명칭을 지시할 때만 최소한으로 사용)

    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 마치 공학 교육 영상의 한 장면 같은 3D 프롬프트를 작성하십시오.
    
    [작성 팁]
    - 프롬프트 시작 부분에 반드시 **"3D technical animation, Blender Cycles render, Clean studio lighting, Cutaway view"** 키워드를 포함하십시오.
    - **인물 등장 시 행동 묘사 예시:** "안전모를 쓴 엔지니어가 거대한 터빈의 단면을 손으로 가리키고 있다", "과학자가 실험 장비를 조작하며 데이터를 확인하는 모습".
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.

    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오. (단, Cutaway, X-ray view 같은 핵심 영단어는 혼용 가능)
    - 부가 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """

    # ---------------------------------------------------------
    # [모드 5] The Paint Explainer (Modified: Clean Lines & Flat Color)
    # ---------------------------------------------------------
    elif genre_mode == "paint_explainer":
        # [NEW] The Paint Explainer 스타일 (깔끔한 선 + 스틱맨 + 단순함 + 명확한 사물 표현)
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 유튜브 'The Paint Explainer' 채널 스타일의 **'깔끔하고 직관적인 스틱맨 디지털 일러스트레이터'**입니다.
    복잡한 이야기를 **'정돈된 선과 다채로운 플랫 컬러'**를 사용하여 시청자가 직관적으로 이해할 수 있도록 그려야 합니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [필수 연출 지침]
    1. **[핵심 - 배경] '단순화된 2D 플랫 배경(Simple 2D Flat Background)'으로 채우십시오.**
        - 배경을 하얗게 비워두지 마십시오.
        - 대본 장소에 맞춰 하늘, 땅, 벽, 바닥 등을 단순한 면으로 분할하여 칠하십시오. (예: 파란 하늘과 초록 땅 / 베이지색 벽과 갈색 바닥)
        - 복잡한 질감이나 그라데이션 없이 **깔끔한 단색 채우기(Flat Color Fill)**로 표현하십시오.
         
    2. **[핵심 - 작화 스타일] '깔끔하고 매끄러운 선(Clean & Smooth Lines)':**
        - **절대 금지:** 마우스로 대충 그린 듯한 삐뚤빼뚤한 선, 거친 스케치 느낌을 배제하십시오.
        - **지향점:** 벡터 이미지처럼 **선이 매끄럽고 정돈되어 있어야 하며**, 두께가 일정하고 깔끔해야 합니다.
        - 그림자와 명암을 그리지 않는 **완전한 평면(Flat Design)** 스타일을 유지하십시오.

    3. **[핵심 - 캐릭터] '스틱맨':**
        - 머리는 하얀색 동그라미, 몸통과 팔다리는 선으로 이루어진 단순한 구조입니다.
        - 배경에 묻히지 않도록 **굵고 선명한 검은색 외곽선(Bold Black Outline)**을 사용하십시오.
        - 상황에 따라 캐릭터에게 색깔 있는 단순한 의상을 입혀 가시성을 높여도 좋습니다.
        - **행동(Body Language):** 정적인 자세를 피하십시오. **온몸을 사용한 역동적인 포즈**로 상황을 설명하십시오.
        - **가시성 확보:** 감정 표현이 중요한 장면에서는 캐릭터를 화면 중앙에 **크게 배치하거나 약간의 클로즈업**을 사용하여 표정이 잘 보이도록 구도를 잡으십시오.

    4. **[핵심 - 소품 및 시각적 은유 (Visual Metaphor) - 강화됨]:**
        - 대본의 핵심 사물을 아이콘처럼 단순하고 명확하게 과장하여 그리십시오.
        - 추상적인 개념을 시각화하는 **은유(Metaphor)**를 적극 활용하십시오.
            - (예: '압박감' -> 스틱맨 머리 위에 거대한 쇳덩이 추가)
        - 만화적 기호(화살표 →, 물음표 ?, 느낌표 !, 땀방울 💦, 반짝임 ✨, 스피드 선)를 그림 옆에 적극적으로 추가하여 상황 전달력을 극대화하십시오.
    
    5. **[색상 사용]:**
        - 전체적으로 밝고 선명한 플랫 컬러를 다양하게 사용하되, 복잡해 보이지 않게 정돈된 색감을 유지하십시오.
        - 핵심적인 사물이나 강조점에는 채도가 높은 원색(빨강, 노랑, 파랑)을 사용하여 시선을 집중시키십시오.

    6. **[텍스트 처리] - '굵고 다양한 손글씨(Bold & Varied Handwriting)':** {lang_guide} {lang_example}
        - 딱딱한 디지털 폰트 대신, **사람이 마카펜이나 붓으로 꾹꾹 눌러 쓴 듯한 '굵은 손글씨 느낌'**으로 연출하십시오.
        - 상황에 따라 **귀여운 글씨, 거친 글씨, 흘려 쓴 글씨** 등 다양한 스타일을 적용하여 단조로움을 피하십시오.
        - 텍스트는 배경 그림의 일부처럼 자연스럽게 어우러져야 합니다.
        - 텍스트 역시 깔끔한 디지털 폰트 느낌으로 그림 옆에 자연스럽게 배치하십시오.
        - **[절대 금지]:** 화면의 네 모서리(Corners)나 가장자리(Edges)에 글자를 배치하지 마십시오. 글자는 반드시 중앙 피사체 주변에만 연출하십시오.


    7. **[구도]:** 분할 화면 금지. **{target_layout}** 비율의 화면을 꽉 채우는 하나의 완결된 장면(Full Scene Illustration)으로 연출하십시오.

    [임무]
    대본을 분석하여 AI가 그릴 수 있는 **'깔끔한 The Paint Explainer 스타일'의 프롬프트**를 작성하십시오.
    - **필수 키워드 반영:** "Clean digital line art, smooth lines, minimal vector style, flat design aesthetic, colorful flat background, no shading, bold outlines, infographic elements (arrows, symbols), visual metaphor"
    - **금지 키워드:** "crude drawing, rough sketch, ms paint style, wobbly lines, sketchy"
    - **한글**로만 출력하십시오.
        """

    else: # Fallback
        full_instruction = f"스타일: {style_instruction}. 비율: {target_layout}. 대본 내용: {text_chunk}. 이미지 프롬프트 작성."

    # 공통 실행 로직
    payload = {
        "contents": [{"parts": [{"text": f"Instruction:\n{full_instruction}\n\nScript Segment:\n\"{text_chunk}\"\n\nImage Prompt (Korean Only, Safe for Work):"}]}]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            try:
                prompt = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                # 9:16일 경우 프롬프트 앞단에 강제 주입 (AI가 실수하지 않도록)
                if "9:16" in target_layout:
                      prompt = "Vertical 9:16 smartphone wallpaper composition, " + prompt
                      
                # 금지어 후처리
                banned_words = ["피가", "피를", "시체", "절단", "학살", "살해", "Blood", "Kill", "Dead"]
                for bad in banned_words:
                    prompt = prompt.replace(bad, "")
            except:
                prompt = text_chunk
            return (scene_num, prompt)
        elif response.status_code == 429:
            time.sleep(2)
            return (scene_num, f"일러스트 묘사: {text_chunk}")
        else:
            return (scene_num, f"Error generating prompt: {response.status_code}")
    except Exception as e:
        return (scene_num, f"Error: {e}")

# ==========================================
# [수정됨] generate_image: API 제한(429) 완벽 대응 + 재시도 강화 + 비율 설정
# ==========================================
def generate_image(client, prompt, filename, output_dir, selected_model_name, target_ratio="16:9"):
    full_path = os.path.join(output_dir, filename)
    
    # 재시도 설정 (최대 5회, 대기 시간 점증)
    max_retries = 5
    
    # [NEW] 마지막 에러를 기억할 변수
    last_error_msg = "알 수 없는 오류" 

    # 안전 필터 설정
    safety_settings = [
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="BLOCK_ONLY_HIGH"
        ),
    ]

    for attempt in range(1, max_retries + 1):
        try:
            # 이미지 생성 요청 (비율 동적 적용)
            response = client.models.generate_content(
                model=selected_model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(aspect_ratio=target_ratio), # 여기서 비율 결정
                    safety_settings=safety_settings 
                )
            )
            
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        img_data = part.inline_data.data
                        image = Image.open(BytesIO(img_data))
                        image.save(full_path)
                        return full_path
            
            # 응답은 왔으나 이미지가 없는 경우 (필터링 등)
            last_error_msg = "이미지 데이터 없음 (Blocked by Safety Filter?)"
            print(f"⚠️ [시도 {attempt}/{max_retries}] {last_error_msg} ({filename})")
            time.sleep(2)
            
        except Exception as e:
            error_msg = str(e)
            last_error_msg = error_msg # [NEW] 에러 메시지 저장
            
            # [핵심 수정] 429 에러(속도 제한) 발생 시 스마트 대기
            if "429" in error_msg or "ResourceExhausted" in error_msg:
                # 시도 횟수가 늘어날수록 대기 시간 증가 (예: 5초 -> 10초 -> 20초...)
                # 랜덤 시간을 섞어 스레드들이 동시에 재시도하는 것 방지 (Jitter)
                wait_time = (5 * attempt) + random.uniform(1, 3)
                print(f"🛑 [API 제한] {filename} - {wait_time:.1f}초 대기 후 재시도... (시도 {attempt})")
                time.sleep(wait_time)
            else:
                # 일반 에러는 짧게 대기
                print(f"⚠️ [에러] {error_msg} ({filename}) - 5초 대기")
                time.sleep(5)
            
    # [최종 실패] 에러 메시지 반환
    print(f"❌ [최종 실패] {filename}")
    return f"ERROR_DETAILS: {last_error_msg}"

def create_zip_buffer(source_dir):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.basename(file_path))
    buffer.seek(0)
    return buffer

# ==========================================
# [함수] 4. Supertone TTS 및 오디오 후처리 (Noise Cut - Micro Fade)
# ==========================================
def check_connection_and_get_voices(api_key, base_url):
    """연결 테스트 및 목소리 목록 가져오기"""
    base_url = base_url.rstrip('/')
    url = f"{base_url}/v1/voices"
    headers = {"x-sup-api-key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            voices = []
            if isinstance(data, dict) and "items" in data:
                voices = data["items"]
            elif isinstance(data, list):
                voices = data
            else:
                return False, [], f"응답 구조가 예상과 다릅니다. (items 키 없음: {list(data.keys())})"
            
            return True, voices, "✅ 연결 성공!"
            
        elif response.status_code == 401:
            return False, [], "❌ API Key가 틀렸습니다 (401)"
        elif response.status_code == 404:
            return False, [], f"❌ 주소(URL) 오류 (404). {base_url} 이 맞는지 확인하세요."
        else:
            return False, [], f"❌ 서버 오류 ({response.status_code}): {response.text}"
            
    except Exception as e:
        return False, [], f"❌ 네트워크 연결 오류: {str(e)}"

def generate_supertone_tts(api_key, voice_id, text, scene_num, base_url, speed=1.0, pitch=0):
    """Supertone API를 사용해 TTS 오디오 생성 및 저장"""
    
    # 1. 텍스트 정규화 (숫자 -> 한글)
    normalized_text = normalize_text_for_tts(text)

    # 2. 마침표가 있든 없든 무조건 마침표 하나 더 추가하여 확실한 끝맺음 유도
    normalized_text = normalized_text.strip() + "."

    base_url = base_url.rstrip('/')
    url = f"{base_url}/v1/text-to-speech/{voice_id}"
    
    headers = {
        "x-sup-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    safe_text = normalized_text[:500] 
    
    # [수정] 일본어 감지 시 언어 설정 변경
    lang_code = "ko"
    if any("\u3040" <= char <= "\u30ff" for char in safe_text):
        lang_code = "ja" # Supertone에서 일본어 지원 시

    payload = {
        "text": safe_text,
        "language": lang_code, # 언어 자동 할당
        "model": "sona_speech_1",
        "voice_settings": {
            "speed": float(speed),
            "pitch_shift": int(pitch),
            "pitch_variance": 1
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        
        if response.status_code == 200:
            filename = f"S{scene_num:03d}_audio.wav"
            full_path = os.path.join(AUDIO_OUTPUT_DIR, filename)
            
            # 파일 저장
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # [KEY FIX] 마이크로 페이드 (Micro-Fade): 끝 30ms만 살짝 줄여서 튀는 소리 제거
            try:
                saved_audio = AudioSegment.from_wav(full_path)
                
                if len(saved_audio) > 100:
                    # 0.03초(30ms)만 페이드 아웃 -> 말끝은 살리고, 기계음 '틱' 소리만 제거
                    saved_audio = saved_audio.fade_out(30)
                    saved_audio.export(full_path, format="wav")
            except Exception as e:
                print(f"Audio tail fix error: {e}")

            return full_path
        elif response.status_code == 404:
            return "VOICE_NOT_FOUND"
        else:
            return f"Error ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"System Error: {e}"

def smart_shorten_silence(file_path, max_allowed_silence_ms=300, min_silence_len=100, silence_thresh=-40):
    try:
        audio = AudioSegment.from_wav(file_path)
        silence_ranges = detect_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )

        if not silence_ranges:
            return True, "무음 구간 없음"

        output_audio = AudioSegment.empty()
        last_pos = 0

        for start, end in silence_ranges:
            output_audio += audio[last_pos:start]
            silence_duration = end - start
            if silence_duration > max_allowed_silence_ms:
                output_audio += AudioSegment.silent(duration=max_allowed_silence_ms)
            else:
                output_audio += audio[start:end]
            last_pos = end

        output_audio += audio[last_pos:]
        output_audio.export(file_path, format="wav")
        return True, "성공"

    except Exception as e:
        return False, str(e)

def process_single_tts_task(api_key, voice_id, text, scene_num, base_url, speed, pitch, apply_silence_trim):
    audio_res = generate_supertone_tts(
        api_key, voice_id, text, scene_num, base_url, speed, pitch
    )
    if "Error" not in str(audio_res) and "VOICE_NOT_FOUND" not in str(audio_res):
        if apply_silence_trim:
            smart_shorten_silence(audio_res, max_allowed_silence_ms=300)
    return audio_res

# ==========================================
# [함수] 5. 비디오 생성 (MoviePy - 고화질 설정)
# ==========================================
def create_video_with_zoom(image_path, audio_path, output_dir, scene_num, is_zoom_in=True):
    """
    이미지와 오디오를 합쳐서 자연스러운 줌 효과 비디오 생성.
    [고화질 설정 적용 완료]
    """
    try:
        output_filename = f"S{scene_num:03d}_video_zoom.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        original_pil = Image.open(image_path).convert("RGB")
        W, H = original_pil.size
        
        if W % 2 != 0: W -= 1
        if H % 2 != 0: H -= 1
        if original_pil.size != (W, H):
            original_pil = original_pil.resize((W, H), Image.LANCZOS)

        max_crop_ratio = 0.85 
        
        def effect(get_frame, t):
            progress = t / duration
            if is_zoom_in:
                current_ratio = 1.0 - (1.0 - max_crop_ratio) * progress
            else:
                current_ratio = max_crop_ratio + (1.0 - max_crop_ratio) * progress
            
            roi_w = W * current_ratio
            roi_h = H * current_ratio
            
            x0 = (W - roi_w) / 2
            y0 = (H - roi_h) / 2
            x1 = x0 + roi_w
            y1 = y0 + roi_h
            
            transformed_img = original_pil.transform(
                (W, H), 
                Image.EXTENT, 
                (x0, y0, x1, y1), 
                Image.BICUBIC 
            )
            return np.array(transformed_img)

        video = ImageClip(np.array(original_pil)).set_duration(duration).set_fps(30)
        video = video.fl(effect)
        video = video.set_audio(audio_clip)
        
        # [KEY FIX] 고화질 렌더링 설정 (비트레이트 8000k, 오디오 192k, preset=slow)
        video.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac", 
            bitrate="8000k",        # 영상 화질 대폭 향상
            audio_bitrate="192k",   # 오디오 음질 향상
            preset="slow",          # 인코딩 품질 향상 (속도는 조금 느려짐)
            logger=None
        )
        
        return output_path
        
    except Exception as e:
        return f"Error: {e}"

def process_single_video_task(item, output_dir, is_zoom_in):
    if item.get('audio_path') and os.path.exists(item['audio_path']):
        return create_video_with_zoom(
            item['path'], 
            item['audio_path'], 
            output_dir, 
            item['scene'], 
            is_zoom_in=is_zoom_in
        )
    return None

def merge_all_videos(video_paths, output_dir):
    try:
        clips = []
        for path in video_paths:
            if path and os.path.exists(path):
                clips.append(VideoFileClip(path))
        
        if not clips:
            return "No clips to merge"

        final_clip = concatenate_videoclips(clips, method="compose")
        final_output_path = os.path.join(output_dir, "FINAL_FULL_VIDEO.mp4")
        
        # [KEY FIX] 병합 시에도 고화질 유지
        final_clip.write_videofile(
            final_output_path, 
            codec="libx264", 
            audio_codec="aac", 
            bitrate="8000k",
            audio_bitrate="192k",
            preset="slow",
            logger=None
        )
        return final_output_path
    except Exception as e:
        return f"Merge Error: {e}"

# ==========================================
# [UI] 사이드바 (자동 로그인 + 장르 선택 적용)
# ==========================================
with st.sidebar:
    st.header("⚙️ 환경 설정")
    
    # 1. Google API Key 자동 로드
    if "general" in st.secrets and "google_api_key" in st.secrets["general"]:
        api_key = st.secrets["general"]["google_api_key"]
        st.success("🔑 Google API Key가 로드되었습니다.")
    else:
        api_key = st.text_input("🔑 Google API Key", type="password", help="secrets.toml이 없으면 직접 입력하세요.")

    st.markdown("---")
    
    st.subheader("🖼️ 이미지 모델 선택")
    model_choice = st.radio("사용할 AI 모델:", ("Premium (Gemini 3 Pro)", "Fast (Gemini-2.5-pro)"), index=0)
    
    if "Gemini 3 Pro" in model_choice:
        SELECTED_IMAGE_MODEL = "gemini-3-pro-image-preview" 
    else:
        SELECTED_IMAGE_MODEL = "gemini-2.5-flash-image"

    st.info(f"✅ 선택 모델: `{SELECTED_IMAGE_MODEL}`")
    
    # ==========================================
    # [NEW] 비율 선택 기능 추가 (쇼츠 대응)
    # ==========================================
    st.markdown("---")
    st.subheader("📐 화면 비율 선택")
    ratio_selection = st.radio(
        "영상 화면 비율:",
        ("16:9 (유튜브 가로형)", "9:16 (쇼츠/릴스 세로형)"),
        index=0
    )

    # 선택된 값에 따라 변수 설정
    if "9:16" in ratio_selection:
        TARGET_RATIO = "9:16"
        LAYOUT_KOREAN = "9:16 세로 비율, 스마트폰 꽉 찬 화면, 위아래로 긴 구도. 피사체가 잘리지 않게 중앙 배치."
    else:
        TARGET_RATIO = "16:9"
        LAYOUT_KOREAN = "16:9 와이드 시네마틱 비율, 영화 스크린 구도."

    st.markdown("---")
    st.subheader("⏱️ 장면 분할 설정")
    chunk_duration = st.slider("한 장면당 지속 시간 (초)", 5, 60, 20, 5)
    chars_limit = chunk_duration * 8 
    
    st.markdown("---")
    
    # ---------------------------------------------------------------------------
    # [NEW] 스마트 장르 선택 & 직접 입력 로직 (수정된 부분)
    # ---------------------------------------------------------------------------
    st.subheader("🎨 영상 장르(Mood) 설정")

    # 1. 프리셋 정의
    PRESET_INFO = """대사에 어울리는 2d 얼굴이 둥근 하얀색 스틱맨 연출로 설명과 이해가 잘되는 느낌으로 그려줘 상황을 잘 나타내게 분활화면으로 말고 하나의 장면으로 너무 어지럽지 않게, 글씨는 핵심 키워드 2~3만 나오게 한다.
글씨가 너무 많지 않게 핵심만. 2D 스틱맨을 활용해 대본을 설명이 잘되게 설명하는 연출을 한다. 자막 스타일 연출은 하지 않는다.
글씨가 나올경우 핵심 키워드 중심으로만 나오게 너무 글이 많지 않도록 한다, 글자는 배경과 사물에 자연스럽게 연출, 전체 배경 연출은 2D로 디테일하게 입체적이고 몰입감 있게 연출해서 그려줘 (16:9).
다양한 장소와 상황 연출로 배경을 디테일하게 한다. 무조건 2D 스틱맨 연출."""
    
    # [NEW] 스틱맨 사실적 연출 프리셋 (상황/감정/배경 디테일 강조)
    PRESET_REALISTIC = """고퀄리티 얼구이 둥근 2D 애니메이션 스타일, 사실적인 배경과 조명 연출.
캐릭터: 얼굴이 둥근 하얀색 2D 스틱맨들. 단순한 낙서가 아니라, 명암과 덩어리감이 느껴지는 '고급 스틱맨' 스타일. 얼굴이 크게 잘보이게 연출.
배경: 단순한 단색 배경 금지. 대본의 장소(사무실, 거리, 방 안, 전장 등)를 '사진'처럼 디테일하고 입체적으로 2d 묘사.
분위기: 정보 전달보다는 '상황극(Drama)'에 집중. 영화적인 조명(Cinematic Lighting)과 심도(Depth) 표현.
연출: 스틱맨 여러 캐릭터들이 대본 속 행동을 리얼하게 연기(Acting). 감정 표현은 표정보다는 역동적인 몸짓(Body Language)으로 극대화.
절대 금지: 화면 분할(Split Screen), 텍스트 나열, 단순 인포그래픽 스타일."""

    PRESET_HISTORY = """역사적 사실을 기반으로 한 '2D 시네마틱 얼굴이 둥근 하얀색 스틱맨 애니메이션' 스타일.
깊이 있는 색감(Dark & Rich Tone)과 극적인 조명 사용.
캐릭터는 2D 실루엣이나 스틱맨이지만 시대에 맞는 의상과 헤어스타일을 착용.
2D 스틱맨을 활용해 대본을 설명이 잘되게 설명하는 연출을 한다. 자막 스타일 연출은 하지 않는다.
전쟁, 기근 등의 묘사는 상징적이고 은유적으로 표현. 너무 고어틱한 연출은 하지 않는다.
배경 묘사에 디테일을 살려 시대적 분위기를 강조. 무조건 얼굴이 둥근 2D 스틱맨 연출."""

    PRESET_3D = """Unreal Engine 5 render style, Realistic 3D game cinematic screenshot.
피사체: 매끈하고 하얀 이목구비 없는 마네킹 머리 (Smooth white featureless mannequin head). 눈코입 없음.
복장: 가디건, 청바지, 정장 등 현실적인 의상을 입혀 기묘한 느낌 강조.
조명: 영화 같은 조명 (Cinematic lighting), 다소 어둡고 분위기 있는(Moody) 연출.
배경: 낡은 소파, 어지러진 방 등 사실적인 텍스처와 디테일(8k resolution)."""

    # [NEW] 공상과학/엔지니어링 프리셋 수정 (Clean Technical + Characters)
    PRESET_SCIFI = """3D Technical Animation (Fern, AiTelly Style).
화풍: Blender Cycles / Clean Rendering, 밝은 스튜디오 조명(Clean Studio Lighting).
연출: 기계/건축물의 단면도(Cutaway) 및 작동 원리 시각화.
인물: 엔지니어/과학자/교사/회사원/군인 등등 다양한 3d 캐릭터가 등장하여 기계를 조작하거나 설명하는 기능적 역할 수행.
분위기: 깔끔하고, 교육적이며, 명확함(Clear & Educational). 과도한 그림자 배제."""

    # [NEW] 페인트 익스플레이너 프리셋 (업데이트: 깔끔한 선 + 다채로운 배경 + 감정/행동 연출 강화)
    PRESET_PAINT = """'The Paint Explainer' 유튜브 채널 스타일 (Expressive Clean Stickman).
화풍: '깔끔하고 매끄러운 디지털 선화(Clean Smooth Lines)'와 '굵은 손글씨(Bold Handwriting)' 텍스트.
배경: 흰색 여백 금지. 하늘, 땅, 벽, 바닥 등이 단순하게 면으로 구분된 '플랫한 2D 배경'.
캐릭터: 하얀색 얼굴이 둥근 2d 스틱맨. **핵심은 과장된 표정과 역동적인 행동으로 감정을 극적으로 연출하는 것.** 캐릭터가 크게 잘 보이게 배치.
채색: 명암 없는 '다채로운 플랫 컬러'를 사용하여 생동감 부여.
연출: 직관적인 사물 표현과 만화적 기호 적극 활용."""

    # 2. 세션 상태 초기화
    if 'style_prompt_area' not in st.session_state:
        st.session_state['style_prompt_area'] = PRESET_INFO
    
    # 옵션 리스트 정의
    OPT_INFO = "밝은 정보/이슈 (Bright & Flat)"
    OPT_REALISTIC = "스틱맨 드라마/사실적 연출 (Realistic Storytelling)" # [NEW]
    OPT_HISTORY = "역사/다큐 (Cinematic & Immersive)"
    OPT_3D = "3D 다큐멘터리 (Realistic 3D Game Style)"
    OPT_SCIFI = "과학/엔지니어링 (3D Tech & Character)"
    OPT_PAINT = "심플 그림판/졸라맨 (The Paint Explainer Style)" # [NEW]
    OPT_CUSTOM = "직접 입력 (Custom Style)"

    # 3. 콜백 함수: 라디오 버튼 변경 시 -> 텍스트 업데이트
    def update_text_from_radio():
        selection = st.session_state.genre_radio_key
        if selection == OPT_INFO:
            st.session_state['style_prompt_area'] = PRESET_INFO
        elif selection == OPT_REALISTIC: # [NEW]
            st.session_state['style_prompt_area'] = PRESET_REALISTIC
        elif selection == OPT_HISTORY:
            st.session_state['style_prompt_area'] = PRESET_HISTORY
        elif selection == OPT_3D:
            st.session_state['style_prompt_area'] = PRESET_3D
        elif selection == OPT_SCIFI: 
            st.session_state['style_prompt_area'] = PRESET_SCIFI
        elif selection == OPT_PAINT: # [NEW]
            st.session_state['style_prompt_area'] = PRESET_PAINT
        # "직접 입력" 선택 시에는 텍스트를 변경하지 않음 (사용자 입력 유지)

    # 4. 콜백 함수: 텍스트 직접 수정 시 -> 라디오 버튼을 '직접 입력'으로 변경
    def set_radio_to_custom():
        st.session_state.genre_radio_key = OPT_CUSTOM

    # 5. 라디오 버튼
    genre_select = st.radio(
        "콘텐츠 성격 선택:",
        (OPT_INFO, OPT_REALISTIC, OPT_HISTORY, OPT_3D, OPT_SCIFI, OPT_PAINT, OPT_CUSTOM), # [NEW] 옵션 추가
        index=0,
        key="genre_radio_key",
        on_change=update_text_from_radio,
        help="텍스트를 직접 수정하면 자동으로 '직접 입력' 모드로 전환됩니다."
    )
    
    # 내부 로직용 모드 변수 할당
    if genre_select == OPT_INFO:
        SELECTED_GENRE_MODE = "info"
    elif genre_select == OPT_REALISTIC: # [NEW]
        SELECTED_GENRE_MODE = "realistic_stickman"
    elif genre_select == OPT_HISTORY:
        SELECTED_GENRE_MODE = "history"
    elif genre_select == OPT_3D:
        SELECTED_GENRE_MODE = "3d_docu"
    elif genre_select == OPT_SCIFI: 
        SELECTED_GENRE_MODE = "scifi"
    elif genre_select == OPT_PAINT: # [NEW]
        SELECTED_GENRE_MODE = "paint_explainer"
    else:
        # 직접 입력일 경우, 텍스트 내용에 따라 3D인지 2D인지 대략 판단하거나 기본값 설정
        current_text = st.session_state.get('style_prompt_area', "")
        if "3D" in current_text or "Unreal" in current_text or "Realistic" in current_text:
            SELECTED_GENRE_MODE = "3d_docu"
        else:
            SELECTED_GENRE_MODE = "info" # 기본값

    st.markdown("---")

    # [NEW] 이미지 내 텍스트 언어 선택
    st.subheader("🌐 이미지 텍스트 언어")
    target_language = st.selectbox(
        "이미지 속에 들어갈 글자 언어:",
        ("Korean", "English", "Japanese"),
        index=0,
        help="이미지에 텍스트가 연출될 때 어떤 언어로 적을지 선택합니다."
    )

    st.markdown("---")

    st.subheader("🖌️ 화풍(Style) 지침")
    # 텍스트 에어리어 (on_change에 set_radio_to_custom 연결)
    style_instruction = st.text_area(
        "AI에게 지시할 그림 스타일 (직접 수정 가능)", 
        key="style_prompt_area", 
        height=200,
        on_change=set_radio_to_custom # <--- 핵심: 글자를 치면 라디오버튼이 '직접입력'으로 바뀜
    )
    # ---------------------------------------------------------------------------

    st.markdown("---")

    # ==========================================
    # [NEW] 사이드바: 캐릭터 이미지 업로더 추가
    # ==========================================
    st.subheader("🧑‍🎨 캐릭터 일관성 유지 (베타)")
    st.caption("주인공 캐릭터 이미지를 올리면, AI가 그 특징을 분석하여 모든 장면에 동일하게 적용하려고 시도합니다.")
    
    if 'char_description' not in st.session_state:
        st.session_state['char_description'] = ""

    uploaded_char_img = st.file_uploader("참조 캐릭터 이미지 업로드 (PNG, JPG)", type=["png", "jpg", "jpeg"])
    
    if uploaded_char_img is not None:
        # 이미지가 업로드 되면 분석 시작
        if not api_key:
            st.error("⚠️ API Key를 먼저 입력해주세요.")
        else:
            # 이미 분석된 적이 없거나, 다른 이미지를 올렸을 때만 재분석
            # (간단하게 구현하기 위해 업로드시 매번 분석하도록 함)
            with st.spinner("비전 AI가 캐릭터의 시각적 특징을 분석 중입니다..."):
                img_bytes = uploaded_char_img.getvalue()
                desc_result = analyze_character_image(api_key, img_bytes)
                
                if "Error" not in desc_result:
                    st.session_state['char_description'] = desc_result
                    st.success("✅ 분석 완료! 이제부터 생성되는 이미지에 이 캐릭터가 적용됩니다.")
                    with st.expander("분석된 캐릭터 시각 설계도 확인 (영어)"):
                        st.write(st.session_state['char_description'])
                    st.image(uploaded_char_img, caption="참조 이미지", width=150)
                else:
                    st.error(f"분석 실패: {desc_result}")
                    st.session_state['char_description'] = ""
    else:
        # 이미지 제거 시 설명도 초기화
        if st.session_state['char_description']:
             st.session_state['char_description'] = ""
    
    st.markdown("---")
    
    # [NEW] Supertone TTS 설정
    st.subheader("🎙️ Supertone TTS 설정")
    
    supertone_base_url = st.text_input("API 주소 (Base URL)", value=DEFAULT_SUPERTONE_URL)
    
    if "general" in st.secrets and "supertone_api_key" in st.secrets["general"]:
        supertone_api_key = st.secrets["general"]["supertone_api_key"]
        st.success("🔑 Supertone API Key가 로드되었습니다.")
    else:
        supertone_api_key = st.text_input("🔑 Supertone API Key", type="password")
    
    if 'supertone_voices' not in st.session_state:
        st.session_state['supertone_voices'] = []
    
    if supertone_api_key:
        if st.button("🔌 연결 테스트 및 목소리 갱신"):
            with st.spinner("목소리 리스트 조회 중..."):
                success, voices, msg = check_connection_and_get_voices(supertone_api_key, supertone_base_url)
                if success:
                    st.session_state['supertone_voices'] = voices
                    st.success(f"{msg} ({len(voices)}개)")
                else:
                    st.error(msg)
                    st.session_state['supertone_voices'] = []
    
    selected_voice_id = ""
    
    if st.session_state['supertone_voices']:
        raw_list = st.session_state['supertone_voices']
        valid_voices = [v for v in raw_list if isinstance(v, dict) and 'name' in v and 'voice_id' in v]
        if valid_voices:
            voice_options = {f"{v['name']} ({v['voice_id']})": v['voice_id'] for v in valid_voices}
            selected_voice_label = st.selectbox("목소리 선택", list(voice_options.keys()))
            selected_voice_id = voice_options[selected_voice_label]
            
            current_voice = next((v for v in valid_voices if v['voice_id'] == selected_voice_id), None)
            if current_voice and current_voice.get('thumbnail_image_url'):
                st.image(current_voice['thumbnail_image_url'], width=100)
    else:
        selected_voice_id = st.text_input("Voice ID 직접 입력", value=DEFAULT_VOICE_ID)
    
    st.caption("TTS 옵션")
    tts_speed = st.slider("말하기 속도", 0.5, 2.0, 1.0, 0.1)
    tts_pitch = st.slider("피치 조절", -12, 12, 0, 1)

    st.markdown("---")
    max_workers = st.slider("작업 속도(병렬 수)", 1, 10, 5)

# ==========================================
# [UI] 메인 화면 1: 대본 구조화 및 생성
# ==========================================
st.title("📺 AI 유튜브 대본 구조 분석기 (Pro)")
st.caption("구조 분석 ➡️ 롱폼 대본 생성(병렬 처리) ➡️ 이미지 생성 ➡️ TTS 오디오 ➡️ 비디오 생성(Zoom 효과)")

# 세션 초기화
if 'structured_content' not in st.session_state:
    st.session_state['structured_content'] = None
if 'section_scripts' not in st.session_state:
    st.session_state['section_scripts'] = {}
if 'video_title' not in st.session_state:
    st.session_state['video_title'] = ""
if 'user_initial_title' not in st.session_state:
    st.session_state['user_initial_title'] = ""

# 1. 구조 분석 섹션
with st.container(border=True):
    user_title_input = st.text_input(
        "📌 영상 제목 (선택사항)", 
        placeholder="이 제목을 입력하면 나중에 이미지 생성 단계에서 이와 유사한 제목들을 추천받을 수 있습니다.",
        help="비워두면 대본 내용을 바탕으로 AI가 알아서 제목을 추천합니다."
    )

    raw_script = st.text_area("✍️ 분석할 원고(대본)를 여기에 붙여넣으세요:", height=200, placeholder="안녕하세요, 오늘은...")
    analyze_btn = st.button("🔍 구조 분석 실행", width="stretch", type="primary")

    if analyze_btn:
        if not api_key:
            st.error("⚠️ 사이드바에서 Google API Key를 먼저 입력해주세요.")
        elif not raw_script:
            st.warning("⚠️ 분석할 대본 내용이 없습니다.")
        else:
            st.session_state['user_initial_title'] = user_title_input

            client = genai.Client(api_key=api_key)
            with st.status("대본 내용 분석 중...", expanded=True) as status:
                status.write(f"🧠 Gemini가 내용을 읽고 구조를 잡고 있습니다...")
                result_text = generate_structure(client, raw_script)
                
                st.session_state['structured_content'] = result_text
                st.session_state['section_scripts'] = {} 

                import re
                match = re.search(r'^\s*1\.\s*\*\*(.*?)\*\*:\s*(.*)', result_text, re.MULTILINE)
                if match:
                    extracted = match.group(2).strip() if match.group(2).strip() else match.group(1).strip()
                    st.session_state['video_title'] = re.sub(r'\(.*?\)', '', extracted).strip()
                else:
                    st.session_state['video_title'] = user_title_input if user_title_input else "제목을 찾을 수 없음"

                status.update(label="✅ 분석 완료! 제목이 추출되었습니다.", state="complete", expanded=False)

# 2. 대본 생성 섹션
if st.session_state['structured_content']:
    st.divider()
    st.subheader("📑 대본 구조화 결과")
    st.markdown(st.session_state['structured_content'])
    
    st.info(f"📌 **추출된 영상 제목:** {st.session_state['video_title']} (이미지 생성 단계에서 수정 가능)")

    st.divider()
    st.subheader("⚡ 롱폼 대본 전체 일괄 생성 (병렬 처리)")
    st.caption("🚀 버튼 한번으로 모든 챕터를 동시에 작성합니다. (15분/20분/25분 옵션)")

    lines = st.session_state['structured_content'].split('\n')
    chapter_titles = ["Intro (도입부)"]
    found_chapters = re.findall(r'(?:Chapter|챕터)\s*\d+.*', st.session_state['structured_content'])
    seen = set()
    for ch in found_chapters:
        clean_ch = ch.replace('*', '').strip()
        if clean_ch not in seen:
            chapter_titles.append(clean_ch)
            seen.add(clean_ch)
    chapter_titles.append("Epilogue (결론)")
    
    for title in chapter_titles:
        if title not in st.session_state['section_scripts']:
            st.session_state['section_scripts'][title] = ""

    with st.container(border=True):
        batch_instruction = st.text_area(
            "📢 전체 대본 작성 지침 (선택 사항)", 
            placeholder="예: 아주 비판적인 어조로 써줘 / 초등학생도 이해하기 쉽게 비유를 많이 들어줘 / 반말(평어)로 작성해줘 등",
            height=70
        )

        col_batch1, col_batch2 = st.columns([1, 1])
        with col_batch1:
            target_time = st.radio(
                "🎬 총 영상 목표 시간 (텍스트 분량)",
                ("15분 (약 7,000자)", "20분 (약 10,000자)", "25분 (약 13,000자)"),
                index=1
            )
            if "15분" in target_time: batch_duration_type = "2min" 
            elif "20분" in target_time: batch_duration_type = "3min" 
            else: batch_duration_type = "4min"

        with col_batch2:
            st.write("")
            st.write("") 
            st.write("") 
            batch_btn = st.button("🚀 전체 대본 동시 생성 시작", type="primary", use_container_width=True)

    if batch_btn:
        if not api_key:
            st.error("⚠️ Google API Key가 필요합니다.")
        else:
            client = genai.Client(api_key=api_key)
            status_box = st.status("🚀 AI가 지침을 반영하여 모든 챕터를 작성 중입니다...", expanded=True)
            progress_bar = status_box.progress(0)
            
            total_tasks = len(chapter_titles)
            completed_tasks = 0
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_title = {}
                for title in chapter_titles:
                    is_fixed = any(x in title for x in ["Intro", "Epilogue", "도입부", "결론"])
                    current_duration = "fixed" if is_fixed else batch_duration_type
                    
                    future = executor.submit(
                        generate_section, 
                        client, 
                        title, 
                        st.session_state['structured_content'], 
                        current_duration, 
                        batch_instruction
                    )
                    future_to_title[future] = title
                
                for future in as_completed(future_to_title):
                    title = future_to_title[future]
                    try:
                        result_text = future.result()
                        st.session_state['section_scripts'][title] = result_text
                        st.session_state[f"txt_{title}"] = result_text 
                        completed_tasks += 1
                        progress_bar.progress(completed_tasks / total_tasks)
                        status_box.write(f"✅ 완료: {title}")
                    except Exception as e:
                        status_box.error(f"❌ 실패 ({title}): {e}")
            
            status_box.update(label="✨ 전체 생성 완료! 아래에서 확인하세요.", state="complete", expanded=False)
            time.sleep(1)
            st.rerun()

    st.subheader("📝 섹션별 확인 및 수정")
    full_combined_script = ""
    
    for title in chapter_titles:
        with st.expander(f"📌 {title}", expanded=False):
            is_intro_epilogue = any(x in title for x in ["Intro", "Epilogue", "도입부", "결론"])
            
            if is_intro_epilogue:
                if st.button(f"🔄 {title} 다시 생성", key=f"r_fix_{title}"):
                    client = genai.Client(api_key=api_key)
                    with st.spinner("재생성 중..."):
                        result = generate_section(client, title, st.session_state['structured_content'], "fixed")
                        st.session_state['section_scripts'][title] = result
                        st.session_state[f"txt_{title}"] = result 
                        st.rerun()
            else:
                c_cols = st.columns(3)
                def regen(dur):
                    client = genai.Client(api_key=api_key)
                    with st.spinner(f"{dur} 모드로 재생성 중..."):
                        dur_code = "2min" if "2분" in dur else "3min" if "3분" in dur else "4min"
                        result = generate_section(client, title, st.session_state['structured_content'], dur_code)
                        st.session_state['section_scripts'][title] = result
                        st.session_state[f"txt_{title}"] = result
                        st.rerun()

                if c_cols[0].button("🔄 다시 생성 (2분)", key=f"r2_{title}"): regen("2분")
                if c_cols[1].button("🔄 다시 생성 (3분)", key=f"r3_{title}"): regen("3분")
                if c_cols[2].button("🔄 다시 생성 (4분)", key=f"r4_{title}"): regen("4분")

            if f"txt_{title}" not in st.session_state:
                st.session_state[f"txt_{title}"] = st.session_state['section_scripts'].get(title, "")

            new_text = st.text_area(label="📜 대본 내용 (수정 가능)", height=300, key=f"txt_{title}")
            st.session_state['section_scripts'][title] = new_text
        
        if st.session_state['section_scripts'].get(title):
            full_combined_script += st.session_state['section_scripts'][title] + "\n\n"

    if full_combined_script:
        st.divider()
        st.subheader("📦 최종 완성 대본")
        col_info, col_down = st.columns([3, 1])
        with col_info:
            st.caption(f"📝 총 글자 수: {len(full_combined_script)}자 (공백 포함)")
        with col_down:
            st.download_button(label="💾 대본 다운로드 (.txt)", data=full_combined_script, file_name="final_script.txt", mime="text/plain", use_container_width=True)
        st.text_area("아래 내용을 복사하거나 위 버튼을 눌러 저장하세요", value=full_combined_script, height=500)

# ==========================================
# [수정된 UI] 메인 화면 3: 이미지 생성
# ==========================================
st.divider()
st.title("🎬 AI 씬(장면) 생성기 (Pro)")
st.caption(f"완성된 대본을 넣으면 장면별 이미지를 생성합니다. | 🎨 Model: {SELECTED_IMAGE_MODEL}")

st.subheader("📌 전체 영상 테마(제목) 설정")
st.caption("이미지 생성 시 이 제목이 '전체적인 분위기 기준'이 됩니다.")

if 'video_title' not in st.session_state:
    st.session_state['video_title'] = ""
if 'title_candidates' not in st.session_state:
    st.session_state['title_candidates'] = []

col_title_input, col_title_btn = st.columns([4, 1])

# [수정됨] 버튼 로직: 구조 분석이 없어도 제목 입력이 있으면 작동하도록 변경
with col_title_btn:
    st.write("") 
    st.write("") 
    if st.button("💡 제목 5개 추천", help="입력한 키워드나 대본을 바탕으로 제목을 추천합니다.", use_container_width=True):
        # 현재 입력된 제목(주제) 가져오기
        current_user_title = st.session_state.get('video_title', "").strip()
        has_structure = st.session_state.get('structured_content')

        if not api_key:
            st.error("API Key 필요")
        # [핵심 수정] 구조 분석도 안 했고, 제목 입력도 없으면 경고
        elif not has_structure and not current_user_title:
            st.warning("⚠️ '구조 분석'을 먼저 하거나, 왼쪽에 '주제'를 입력해주세요.")
        else:
            client = genai.Client(api_key=api_key)
            with st.spinner("AI가 최적의 제목을 고민 중입니다..."):
                
                # 1. 구조 분석 데이터는 없지만, 사용자가 입력한 주제는 있는 경우
                if current_user_title and not has_structure:
                    prompt_instruction = f"""
                    [Target Topic]
                    "{current_user_title}"
                    [Task]
                    Generate 5 click-bait YouTube video titles based on the Target Topic above.
                    사용자가 입력한거랑 최대한 비슷한 제목으로 추천, '몰락'이 들어간 경우 맨 뒤에 몰락으로 끝나게 한다.
                    """
                    context_data = "No script provided. Base it solely on the topic."

                # 2. 구조 분석 데이터가 있는 경우 (입력한 제목이 있으면 그것도 반영)
                else:
                    if current_user_title:
                        prompt_instruction = f"""
                        [Target Context]
                        "{current_user_title}"
                        [Task]
                        Generate 5 variations of this title suitable for YouTube, considering the script below.
                        '몰락'이 들어간 경우 맨 뒤에 몰락으로 끝나게 한다.
                        """
                    else:
                        prompt_instruction = f"""
                        [Task]
                        Read the provided script structure and generate 5 catchy YouTube video titles in Korean.
                        """
                    context_data = st.session_state['structured_content']

                title_prompt = f"""
                [Role] You are a YouTube viral marketing expert.
                {prompt_instruction}
                
                [Script Context]
                {context_data}
                
                [Output Format]
                - Output ONLY the list of 5 titles.
                - No numbering (1., 2.), just 5 lines of text.
                - Language: Korean
                """
                
                try:
                    resp = client.models.generate_content(
                        model=GEMINI_TEXT_MODEL_NAME, 
                        contents=title_prompt
                    )
                    candidates = [line.strip() for line in resp.text.split('\n') if line.strip()]
                    clean_candidates = []
                    import re
                    for c in candidates:
                        clean = re.sub(r'^\d+\.\s*', '', c).replace('*', '').replace('"', '').strip()
                        if clean: clean_candidates.append(clean)
                    
                    st.session_state['title_candidates'] = clean_candidates[:5]
                except Exception as e:
                    st.error(f"오류 발생: {e}")

with col_title_input:
    st.text_input(
        "영상 제목 (직접 입력하거나 우측 버튼으로 추천받으세요)",
        key="video_title", 
        placeholder="제목 혹은 만들고 싶은 주제를 입력하세요 (예: 부자들의 습관)"
    )

if st.session_state['title_candidates']:
    st.info("👇 AI가 추천한 제목입니다. 클릭하면 적용됩니다.")

    def apply_title(new_title):
        st.session_state['video_title'] = new_title
        st.session_state['title_candidates'] = [] 

    for idx, title in enumerate(st.session_state['title_candidates']):
        col_c1, col_c2 = st.columns([4, 1])
        with col_c1:
            st.markdown(f"**{idx+1}. {title}**")
        with col_c2:
            st.button(
                "✅ 선택", 
                key=f"sel_title_{idx}", 
                on_click=apply_title, 
                args=(title,), 
                use_container_width=True
            )
    
    if st.button("❌ 목록 닫기"):
        st.session_state['title_candidates'] = []

if 'section_scripts' in st.session_state and st.session_state['section_scripts']:
    intro_text_acc = ""
    main_text_acc = ""
    for title_key, text in st.session_state['section_scripts'].items():
        if "Intro" in title_key or "도입부" in title_key:
            intro_text_acc += text + "\n\n"
        else:
            main_text_acc += text + "\n\n"
            
    st.write("👇 **생성된 대본 가져오기 (클릭 시 아래 입력창에 채워집니다)**")
    
    col_get1, col_get2 = st.columns(2)
    if "image_gen_input" not in st.session_state:
        st.session_state["image_gen_input"] = ""

    with col_get1:
        if st.button("📥 인트로(Intro)만 가져오기", use_container_width=True):
            st.session_state["image_gen_input"] = intro_text_acc.strip()
            st.rerun()
    with col_get2:
        if st.button("📥 본론(Chapters) + 결론(Epilogue) 가져오기", use_container_width=True):
            st.session_state["image_gen_input"] = main_text_acc.strip()
            st.rerun()

script_input = st.text_area(
    "📜 이미지로 만들 대본 입력", 
    height=300, 
    placeholder="위 버튼을 눌러 대본을 가져오거나, 직접 붙여넣으세요...",
    key="image_gen_input"
)

if 'generated_results' not in st.session_state:
    st.session_state['generated_results'] = []
if 'is_processing' not in st.session_state:
    st.session_state['is_processing'] = False

# [KEY FIX] 버튼 클릭 시 결과물 초기화 함수 추가
def clear_generated_results():
    st.session_state['generated_results'] = []

start_btn = st.button("🚀 이미지 생성 시작", type="primary", width="stretch", on_click=clear_generated_results)

if start_btn:
    if not api_key:
        st.error("⚠️ Google API Key를 입력해주세요.")
    elif not script_input:
        st.warning("⚠️ 대본을 입력해주세요.")
    else:
        # [FIX] 기존 결과 확실히 날리기
        st.session_state['generated_results'] = [] 
        st.session_state['is_processing'] = True
        
        # [FIX] 기존 이미지 파일들 물리적으로 삭제 (찌꺼기 제거)
        if os.path.exists(IMAGE_OUTPUT_DIR):
            try:
                shutil.rmtree(IMAGE_OUTPUT_DIR) # 폴더 통째로 삭제
            except:
                pass
        init_folders() # 다시 깨끗한 폴더 생성
        
        client = genai.Client(api_key=api_key)
        
        status_box = st.status("작업 진행 중...", expanded=True)
        progress_bar = st.progress(0)
        
        # 1. 대본 분할
        status_box.write(f"✂️ 대본 분할 중...")
        chunks = split_script_by_time(script_input, chars_per_chunk=chars_limit)
        total_scenes = len(chunks)
        status_box.write(f"✅ {total_scenes}개 장면으로 분할 완료.")
        
        current_video_title = st.session_state.get('video_title', "").strip()
        if not current_video_title:
            current_video_title = "전반적인 대본 분위기에 어울리는 배경 (Context based on the script)"

        # [NEW] 현재 저장된 캐릭터 묘사 가져오기
        current_char_desc = st.session_state.get('char_description', "")

        # 2. 프롬프트 생성 (병렬)
        status_box.write(f"📝 프롬프트 작성 중 ({GEMINI_TEXT_MODEL_NAME}) - 모드: {SELECTED_GENRE_MODE} / 비율: {TARGET_RATIO}...") # (선택) 로그 메시지에 모드 표시 추가
        prompts = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for i, chunk in enumerate(chunks):
                # [수정] target_language 추가 전달
                futures.append(executor.submit(
                    generate_prompt, 
                    api_key, 
                    i, 
                    chunk, 
                    style_instruction, 
                    current_video_title, 
                    SELECTED_GENRE_MODE,
                    target_language,
                    current_char_desc, # <--- [NEW] 캐릭터 묘사 주입
                    LAYOUT_KOREAN      # <--- [NEW] 비율 구도 주입
                ))
            
            for i, future in enumerate(as_completed(futures)):
                prompts.append(future.result())
                progress_bar.progress((i + 1) / (total_scenes * 2))
        
        prompts.sort(key=lambda x: x[0])
        
        # 3. 이미지 생성 (병렬 처리 + 속도 조절)
        status_box.write(f"🎨 이미지 생성 중 ({SELECTED_IMAGE_MODEL})... (API 보호를 위해 천천히 진행됩니다)")
        results = []
        
        # [수정됨] 병렬 처리 최적화
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_meta = {}
            for s_num, prompt_text in prompts:
                idx = s_num - 1
                orig_text = chunks[idx]
                fname = make_filename(s_num, orig_text)
                
                # [수정] 3초 대기 삭제 -> 0.1초 미세 지연만 줌 (순서 꼬임 방지용)
                time.sleep(0.1) 
                
                # [NEW] 비율 정보 TARGET_RATIO 전달
                future = executor.submit(
                    generate_image, 
                    client, 
                    prompt_text, 
                    fname, 
                    IMAGE_OUTPUT_DIR, 
                    SELECTED_IMAGE_MODEL,
                    TARGET_RATIO 
                )
                future_to_meta[future] = (s_num, fname, orig_text, prompt_text)
            
            # 결과 수집
            completed_cnt = 0
            for future in as_completed(future_to_meta):
                s_num, fname, orig_text, p_text = future_to_meta[future]
                
                # [중요 수정] 변수명을 'result'로 통일하여 NameError 방지
                result = future.result() 
                
                # 성공 여부 판별 ("ERROR_DETAILS"라는 글자가 없어야 성공)
                if result and "ERROR_DETAILS" not in result:
                    path = result # 성공했으므로 경로(path)에 할당
                    results.append({
                        "scene": s_num,
                        "path": path,
                        "filename": fname,
                        "script": orig_text,
                        "prompt": p_text,
                        "audio_path": None,
                        "video_path": None 
                    })
                else:
                    # 실패 시 에러 메시지 추출
                    error_reason = result.replace("ERROR_DETAILS:", "") if result else "원인 불명 (None 반환)"
                    st.error(f"🚨 Scene {s_num} 실패!\n이유: {error_reason}")
                    st.caption(f"문제의 파일명: {fname}")

                completed_cnt += 1
                progress_bar.progress(0.5 + (completed_cnt / total_scenes * 0.5))
        
        results.sort(key=lambda x: x['scene'])
        st.session_state['generated_results'] = results
        
        status_box.update(label="✅ 완료되었습니다!", state="complete", expanded=False)
        st.session_state['is_processing'] = False
        
# ==========================================
# [수정됨] 결과창 및 개별 재생성 기능 추가
# ==========================================
if st.session_state['generated_results']:
    st.divider()
    st.header(f"📸 결과물 ({len(st.session_state['generated_results'])}장)")
    
    # ------------------------------------------------
    # 1. 일괄 작업 버튼 영역
    # ------------------------------------------------
    st.write("---")
    st.subheader("⚡ 원클릭 일괄 생성 작업")
    
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    
    with c_btn1:
        zip_data = create_zip_buffer(IMAGE_OUTPUT_DIR)
        st.download_button("📦 전체 이미지 ZIP 다운로드", data=zip_data, file_name="all_images.zip", mime="application/zip", use_container_width=True)

    # TTS 전체 생성
    with c_btn2:
        tts_batch_mode = st.selectbox("TTS 생성 모드", ["원본 음성 생성", "무음 조절 음성 (최대 0.3초)"], help="무음 조절 선택 시 공백 자동 축소")
        if st.button("🔊 TTS 일괄 생성", use_container_width=True):
            if not supertone_api_key or not selected_voice_id:
                st.error("사이드바에서 API Key와 목소리를 설정해주세요.")
            else:
                # 오디오 변경 시 통합본 삭제
                final_merged_file = os.path.join(VIDEO_OUTPUT_DIR, "FINAL_FULL_VIDEO.mp4")
                if os.path.exists(final_merged_file):
                    try: os.remove(final_merged_file)
                    except: pass

                status_box = st.status("🎙️ TTS 일괄 생성 중...", expanded=True)
                progress_bar = status_box.progress(0)
                
                apply_trim = (tts_batch_mode == "무음 조절 음성 (최대 0.3초)")
                total_files = len(st.session_state['generated_results'])
                completed_cnt = 0
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_idx = {}
                    for i, item in enumerate(st.session_state['generated_results']):
                        future = executor.submit(
                            process_single_tts_task, supertone_api_key, selected_voice_id, 
                            item['script'], item['scene'], supertone_base_url, 
                            tts_speed, tts_pitch, apply_trim
                        )
                        future_to_idx[future] = i
                    
                    for future in as_completed(future_to_idx):
                        idx = future_to_idx[future]
                        try:
                            result_path = future.result()
                            if "Error" not in str(result_path) and "VOICE_NOT_FOUND" not in str(result_path):
                                st.session_state['generated_results'][idx]['audio_path'] = result_path
                                st.session_state['generated_results'][idx]['video_path'] = None # 비디오 리셋
                            else:
                                st.write(f"⚠️ Scene {idx+1} 오류: {result_path}")
                        except Exception as e:
                            st.write(f"⚠️ Scene {idx+1} 시스템 오류: {e}")
                        
                        completed_cnt += 1
                        progress_bar.progress(completed_cnt / total_files)
                
                status_box.update(label="✅ TTS 생성 완료!", state="complete", expanded=False)
                time.sleep(1)
                st.rerun()

    # 비디오 전체 생성
    with c_btn3:
        has_audio = any(item.get('audio_path') for item in st.session_state['generated_results'])
        if st.button("🎬 비디오 전체 일괄 생성", disabled=not has_audio, use_container_width=True):
            final_merged_file = os.path.join(VIDEO_OUTPUT_DIR, "FINAL_FULL_VIDEO.mp4")
            if os.path.exists(final_merged_file):
                try: os.remove(final_merged_file)
                except: pass
            
            status_box = st.status("🎬 비디오 렌더링 중...", expanded=True)
            progress_bar = status_box.progress(0)
            
            total_files = len(st.session_state['generated_results'])
            completed_cnt = 0
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {}
                for i, item in enumerate(st.session_state['generated_results']):
                    is_zoom_in = (i % 2 == 0)
                    future = executor.submit(process_single_video_task, item, VIDEO_OUTPUT_DIR, is_zoom_in)
                    future_to_idx[future] = i
                
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        vid_path = future.result()
                        if vid_path and "Error" not in vid_path:
                            st.session_state['generated_results'][idx]['video_path'] = vid_path
                        elif vid_path:
                            st.write(f"⚠️ Scene {idx+1} 렌더링 오류: {vid_path}")
                    except Exception as e:
                        st.write(f"⚠️ Scene {idx+1} 시스템 오류: {e}")
                    
                    completed_cnt += 1
                    progress_bar.progress(completed_cnt / total_files)
            
            status_box.update(label="✅ 비디오 생성 완료!", state="complete", expanded=False)
            time.sleep(1)
            st.rerun()

    # 전체 병합
    with c_btn4:
        video_paths = [item.get('video_path') for item in st.session_state['generated_results'] if item.get('video_path')]
        final_path = os.path.join(VIDEO_OUTPUT_DIR, "FINAL_FULL_VIDEO.mp4")
        
        if video_paths:
            if st.button("🎞️ 전체 영상 합치기 (새로고침)", use_container_width=True):
                with st.spinner("모든 비디오를 하나로 합치는 중..."):
                    if os.path.exists(final_path):
                        try: os.remove(final_path)
                        except: pass
                        
                    merged_result = merge_all_videos(video_paths, VIDEO_OUTPUT_DIR)
                    if "Error" in merged_result:
                        st.error(merged_result)
                    else:
                        st.success("병합 완료!")
                        st.rerun()

            if os.path.exists(final_path):
                 with open(final_path, "rb") as f:
                    st.download_button("💾 전체 영상 다운로드 (MP4)", data=f, file_name="final_video.mp4", mime="video/mp4", use_container_width=True)
        else:
            st.button("🎞️ 전체 영상 합치기", disabled=True, use_container_width=True)

    if not supertone_api_key or not selected_voice_id:
        st.warning("🎙️ Supertone TTS 사용을 위해 API 설정을 확인하세요.")

    # ------------------------------------------------
    # 2. 개별 리스트 및 [재생성] 기능
    # ------------------------------------------------
    for index, item in enumerate(st.session_state['generated_results']):
        with st.container(border=True):
            cols = st.columns([1, 2])
            
            # [왼쪽] 이미지 및 재생성 버튼
            with cols[0]:
                try: 
                    # [핵심 수정] 비율에 따라 이미지 표시 방식 변경
                    if TARGET_RATIO == "16:9":
                        # 16:9 (가로형)일 때는 use_container_width=True로 꽉 채움
                        st.image(item['path'], use_container_width=True)
                    else:
                        # 9:16 (세로형)일 때는 가운데 정렬 및 크기 고정
                        sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1]) # 가운데 정렬용
                        with sub_c2:
                            st.image(item['path'], use_container_width=True)
                except: 
                    st.error("이미지 없음")
                
                # [NEW] 이미지 개별 재생성 버튼 (버튼은 전체 너비 사용)
                if st.button(f"🔄 이 장면만 이미지 다시 생성", key=f"regen_img_{index}", use_container_width=True):
                    if not api_key:
                        st.error("API Key가 필요합니다.")
                    else:
                        with st.spinner(f"Scene {item['scene']} 다시 그리는 중..."):
                            client = genai.Client(api_key=api_key)
                            
                            # [NEW] 현재 캐릭터 묘사 가져오기
                            current_char_desc = st.session_state.get('char_description', "")

                            # 1. 프롬프트 다시 생성 (현재 대본과 스타일, 모드 반영)
                            current_title = st.session_state.get('video_title', '')
                            # 대본이 수정되었을 수도 있으므로 item['script'] 사용
                            _, new_prompt = generate_prompt(
                                api_key, index, item['script'], style_instruction, 
                                current_title, SELECTED_GENRE_MODE,
                                target_language,
                                current_char_desc, # <--- [NEW] 캐릭터 묘사 주입
                                LAYOUT_KOREAN      # <--- [NEW] 비율 구도 주입
                            )
                            
                            # 2. 이미지 생성
                            new_path = generate_image(
                                client, new_prompt, item['filename'], 
                                IMAGE_OUTPUT_DIR, SELECTED_IMAGE_MODEL,
                                TARGET_RATIO # <--- [NEW] 비율 정보 전달
                            )
                            
                            # [수정] 개별 생성에서도 에러 체크
                            if new_path and "ERROR_DETAILS" not in new_path:
                                # 3. 결과 업데이트
                                st.session_state['generated_results'][index]['path'] = new_path
                                st.session_state['generated_results'][index]['prompt'] = new_prompt
                                # 이미지가 바뀌었으므로 기존 비디오는 무효화
                                st.session_state['generated_results'][index]['video_path'] = None
                                st.success("이미지가 변경되었습니다!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                err_msg = new_path.replace("ERROR_DETAILS:", "") if new_path else "Unknown Error"
                                st.error(f"이미지 생성 실패: {err_msg}")

            # [오른쪽] 정보 및 오디오/비디오 컨트롤
            with cols[1]:
                st.subheader(f"Scene {item['scene']:02d}")
                st.caption(f"파일명: {item['filename']}")
                
                # 대본 수정 가능하게 할지? (현재는 display만)
                st.write(f"**대본:** {item['script']}")
                
                st.markdown("---")
                audio_col1, audio_col2 = st.columns([1, 3])
                
                # 오디오 로직
                if item.get('audio_path') and os.path.exists(item['audio_path']):
                    with audio_col1:
                        st.audio(item['audio_path'])
                        if st.button("🔄 오디오 재생성", key=f"re_tts_{item['scene']}"):
                             item['audio_path'] = None
                             item['video_path'] = None 
                             st.rerun()
                    
                    with audio_col2:
                        if item.get('video_path') and os.path.exists(item['video_path']):
                            st.video(item['video_path'])
                            with open(item['video_path'], "rb") as vf:
                                st.download_button("⬇️ 비디오 저장", data=vf, file_name=f"scene_{item['scene']}.mp4", mime="video/mp4", key=f"down_vid_{item['scene']}")
                        else:
                            is_zoom_in_mode = (index % 2 == 0)
                            button_label = f"🎬 비디오 생성 ({'줌인' if is_zoom_in_mode else '줌아웃'})"

                            if st.button(button_label, key=f"gen_vid_{item['scene']}"):
                                with st.spinner("렌더링 중..."):
                                    vid_path = create_video_with_zoom(
                                        item['path'], item['audio_path'], VIDEO_OUTPUT_DIR, 
                                        item['scene'], is_zoom_in=is_zoom_in_mode
                                    )
                                    if "Error" in vid_path:
                                        st.error(vid_path)
                                    else:
                                        st.session_state['generated_results'][index]['video_path'] = vid_path
                                        st.rerun()
                else:
                    with audio_col1:
                        if st.button("🔊 TTS 생성", key=f"gen_tts_{item['scene']}"):
                            if not supertone_api_key or not selected_voice_id:
                                st.error("설정 필요")
                            else:
                                with st.spinner("오디오 생성 중..."):
                                    audio_result = generate_supertone_tts(
                                        supertone_api_key, selected_voice_id, 
                                        item['script'], item['scene'], supertone_base_url, 
                                        speed=tts_speed, pitch=tts_pitch
                                    )
                                    if "Error" not in str(audio_result) and "VOICE_NOT_FOUND" != audio_result:
                                        st.session_state['generated_results'][index]['audio_path'] = audio_result
                                        st.rerun()
                                    else:
                                        st.error(audio_result)

                with st.expander("프롬프트 확인"):
                    st.text(item['prompt'])
                try:
                    with open(item['path'], "rb") as file:
                        st.download_button("⬇️ 이미지 저장", data=file, file_name=item['filename'], mime="image/png", key=f"btn_down_{item['scene']}")
                except: pass
