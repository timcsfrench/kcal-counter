import streamlit as st
import requests
import json
import base64
from PIL import Image
import io
import re

# Настройка страницы
st.set_page_config(page_title="AI Калории", page_icon="🥗", layout="centered")

st.title("🥗 Сканер калорий")
st.write("Загрузи фото блюда, проверь состав, учет скрытого сахара/масла и при необходимости скорректируй вес.")

# Проверка ключа
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    st.error("Ошибка: GEMINI_API_KEY не найден в Streamlit Secrets!")

# Инициализация состояния
if "food_items" not in st.session_state:
    st.session_state.food_items = None
if "advice" not in st.session_state:
    st.session_state.advice = ""
if "confidence" not in st.session_state:
    st.session_state.confidence = 0
if "hidden_notes" not in st.session_state:
    st.session_state.hidden_notes = ""

# Функция для конвертации картинки в base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Безопасный парсинг JSON
def parse_json_safely(text):
    cleaned = re.sub(r'```json\s*', '', text)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)

# Загрузка фото
uploaded_file = st.file_uploader("Загрузи фото тарелки", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Ваше блюдо", use_container_width=True)
    
    if st.button("🔍 Проанализировать фото", type="primary"):
        status_placeholder = st.empty()
        status_placeholder.info("⏳ Анализируем фото с помощью Gemini...")
        
        # Переводим фото в base64
        base64_image = image_to_base64(image)
        
        system_instruction = (
            "Ты — высококлассный эксперт-нутрициолог. "
            "Твоя задача — детально проанализировать фото еды, УЧИТЫВАЯ СКРЫТЫЕ ИНГРЕДИЕНТЫ "
            "(например, сметана/майонез, масло для жарки, заправка, возможный добавленный сахар в кашах/напитках/сырниках).\n"
            "Выдай ответ СТРОГО в формате валидного JSON.\n"
            "Структура ответа:\n"
            "{\n"
            '  "confidence": 90,\n'
            '  "hidden_notes": "Опиши скрытые ингредиенты и возможные нюансы",\n'
            '  "items": [\n'
            '    {"name": "Название продукта", "weight": 100, "calories_per_100g": 155, "protein_per_100g": 13, "fat_per_100g": 11, "carbs_per_100g": 1}\n'
            "  ],\n"
            '  "advice": "Короткий совет по питательной ценности на русском"\n'
            "}"
        )
        
        # REST Payload
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "parts": [
                        {"text": "Изучи фото еды. Определи продукты, учти скрытые жиры/соусы/сахар, укажи уверенность в процентах."},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        # Эндпоинты моделей (по списку приоритета)
        models_to_try = [
            "gemini-1.5-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro"
        ]
        
        success = False
        last_error = ""
        
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                res_data = response.json()
                
                if response.status_code == 200 and "candidates" in res_data:
                    raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    data = parse_json_safely(raw_text)
                    
                    st.session_state.food_items = data.get("items", [])
                    st.session_state.confidence = data.get("confidence", 80)
                    st.session_state.hidden_notes = data.get("hidden_notes", "")
                    st.session_state.advice = data.get("advice", "")
                    
                    success = True
                    status_placeholder.empty()
                    break
                else:
                    last_error = res_data.get("error", {}).get("message", response.text)
            except Exception as err:
                last_error = str(err)
                continue
                
        if not success:
            status_placeholder.empty()
            if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error or "quota" in last_error.lower():
                st.warning("⏳ Бесплатный лимит запросов исчерпан. Подождите 1 минуту и попробуйте снова.")
            else:
                st.error(f"Ошибка API: {last_error}")

# Отрисовка результатов и редактирование
if st.session_state.food_items is not None:
    st.markdown("---")
    
    col_conf, col_warn = st.columns([1, 2])
    with col_conf:
        st.metric("🎯 Уверенность ИИ", f"{st.session_state.confidence}%")
    with col_warn:
        if st.session_state.hidden_notes:
            st.warning(f"⚠️ **Скрытые ингредиенты / нюансы:**\n\n{st.session_state.hidden_notes}")

    with st.expander("➕ **Добавить скрытый сахар или соусы/масло**", expanded=True):
        st.caption("Если вы добавляли сахар или заправку, добавьте их в один клик:")
        col_sug, col_add_btn = st.columns([2, 1])
        with col_sug:
            sugar_spoons = st.number_input("Чайных ложек сахара (~5г ложка, 20 ккал):", min_value=0, max_value=10, value=0, step=1)
        with col_add_btn:
            st.write("")
            st.write("")
            if st.button("Добавить сахар"):
                if sugar_spoons > 0:
                    sugar_weight = sugar_spoons * 5
                    st.session_state.food_items.append({
                        "name": f"Сахар ({sugar_spoons} ч.л.)",
                        "weight": sugar_weight,
                        "calories_per_100g": 400,
                        "protein_per_100g": 0,
                        "fat_per_100g": 0,
                        "carbs_per_100g": 100
                    })
                    st.rerun()

    st.subheader("📝 Редактирование ингредиентов")
    
    edited_df = st.data_editor(
        st.session_state.food_items,
        column_config={
            "name": st.column_config.TextColumn("Продукт / Масло / Сахар", required=True),
            "weight": st.column_config.NumberColumn("Вес (г)", min_value=0, step=5, required=True),
            "calories_per_100g": st.column_config.NumberColumn("Ккал/100г", min_value=0, step=10),
            "protein_per_100g": st.column_config.NumberColumn("Белки/100г", min_value=0, step=1),
            "fat_per_100g": st.column_config.NumberColumn("Жиры/100г", min_value=0, step=1),
            "carbs_per_100g": st.column_config.NumberColumn("Углеводы/100г", min_value=0, step=1),
        },
        num_rows="dynamic",
        use_container_width=True
    )

    total_weight = 0
    total_cal = 0
    total_p = 0
    total_f = 0
    total_c = 0

    for item in edited_df:
        w = item.get("weight", 0) or 0
        cal_100 = item.get("calories_per_100g", 0) or 0
        p_100 = item.get("protein_per_100g", 0) or 0
        f_100 = item.get("fat_per_100g", 0) or 0
        c_100 = item.get("carbs_per_100g", 0) or 0

        total_weight += w
        total_cal += (w * cal_100) / 100
        total_p += (w * p_100) / 100
        total_f += (w * f_100) / 100
        total_c += (w * c_100) / 100

    st.markdown("---")
    st.subheader("📊 Итоговый расчет порции")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Калории", f"{round(total_cal)} ккал")
    col2.metric("Белки", f"{round(total_p, 1)} г")
    col3.metric("Жиры", f"{round(total_f, 1)} г")
    col4.metric("Углеводы", f"{round(total_c, 1)} г")

    st.caption(f"Общий вес порции: {round(total_weight)} г")

    if st.session_state.advice:
        st.success(f"💡 **Совет нутрициолога:** {st.session_state.advice}")
