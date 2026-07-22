import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re

# Настройка страницы
st.set_page_config(page_title="AI Калории", page_icon="🥗", layout="centered")

st.title("🥗 Сканер калорий")
st.write("Загрузите фото блюда, проверьте состав, учет скрытого сахара/масла и при необходимости скорректируйте вес.")

# Подключение к Gemini через секреты Streamlit
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Ошибка настройки API ключа. Проверьте Secrets в Streamlit.")

# Инициализация состояния
if "food_items" not in st.session_state:
    st.session_state.food_items = None
if "advice" not in st.session_state:
    st.session_state.advice = ""
if "confidence" not in st.session_state:
    st.session_state.confidence = 0
if "hidden_notes" not in st.session_state:
    st.session_state.hidden_notes = ""

# Функция для безопасного извлечения JSON
def parse_json_safely(text):
    # Убираем возможные блоки ```json ... ```
    cleaned = re.sub(r'```json\s*', '', text)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()
    
    # Ищем фигурные скобки, если есть лишний текст
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
        
    return json.loads(cleaned)

# Загрузка фото
uploaded_file = st.file_uploader("Загрузите фото тарелки", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Ваше блюдо", use_container_width=True)
    
    if st.button("🔍 Проанализировать фото", type="primary"):
        with st.spinner("Идёт анализ..."):
            
            system_prompt = (
                "Ты — профессиональный нутрициолог. "
                "Твоя задача — детально проанализировать фото еды, УЧИТЫВАЯ СКРЫТЫЕ ИНГРЕДИЕНТЫ "
                "(например, масло для жарки, соусы, возможный добавленный сахар в напитках/кашах/десертах/соусах).\n"
                "Выдай ответ СТРОГО в формате валидного JSON.\n"
                "Структура ответа:\n"
                "{\n"
                '  "confidence": 85,\n'
                '  "hidden_notes": "Опиши скрытые ингредиенты и возможные нюансы",\n'
                '  "items": [\n'
                '    {"name": "Яйцо жареное", "weight": 100, "calories_per_100g": 155, "protein_per_100g": 13, "fat_per_100g": 11, "carbs_per_100g": 1},\n'
                '    {"name": "Масло для жарки (оценка)", "weight": 5, "calories_per_100g": 900, "protein_per_100g": 0, "fat_per_100g": 100, "carbs_per_100g": 0}\n'
                "  ],\n"
                '  "advice": "Короткий совет по питательной ценности на русском"\n'
                "}"
            )
            
            prompt = "Изучи фото еды. Определи продукты, учти скрытое масло/соусы/сахар, укажи уверенность в процентах и что могло остаться незамеченным."
            
            priority_models = [
                'models/gemini-1.5-pro',
                'models/gemini-1.5-pro-latest',
                'models/gemini-2.0-flash',
                'models/gemini-1.5-flash'
            ]
            
            success = False
            last_error = ""
            
            for model_name in priority_models:
                try:
                    # Включаем гарантированный режим вывода JSON
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response = model.generate_content([image, prompt])
                    
                    if response.text:
                        data = parse_json_safely(response.text)
                        
                        st.session_state.food_items = data.get("items", [])
                        st.session_state.confidence = data.get("confidence", 80)
                        st.session_state.hidden_notes = data.get("hidden_notes", "")
                        st.session_state.advice = data.get("advice", "")
                        success = True
                        break
                except Exception as err:
                    # Попытка без принудительного response_mime_type, если модель его не поддерживает
                    try:
                        model = genai.GenerativeModel(
                            model_name=model_name,
                            system_instruction=system_prompt
                        )
                        response = model.generate_content([image, prompt])
                        if response.text:
                            data = parse_json_safely(response.text)
                            st.session_state.food_items = data.get("items", [])
                            st.session_state.confidence = data.get("confidence", 80)
                            st.session_state.hidden_notes = data.get("hidden_notes", "")
                            st.session_state.advice = data.get("advice", "")
                            success = True
                            break
                    except Exception as inner_err:
                        last_error = str(inner_err)
                        continue
            
            if not success:
                st.error(f"Ошибка при анализе фото. Детали ошибки: {last_error}")

# Если ингредиенты успешно получены из фото
if st.session_state.food_items is not None:
    st.markdown("---")
    
    # Вывод уровня уверенности и скрытых факторов
    col_conf, col_warn = st.columns([1, 2])
    with col_conf:
        st.metric("🎯 Уверенность анализа", f"{st.session_state.confidence}%")
    with col_warn:
        if st.session_state.hidden_notes:
            st.warning(f"⚠️ **Скрытые ингредиенты / нюансы:**\n\n{st.session_state.hidden_notes}")

    # Блок быстрого добавления скрытого сахара и заправок
    with st.expander("➕ **Добавить скрытый сахар или соусы/масло**", expanded=True):
        st.caption("Если вы добавляли сахар в чашку/блюдо или поливали соусом, добавьте их в один клик:")
        
        col_sug, col_add_btn = st.columns([2, 1])
        with col_sug:
            sugar_spoons = st.number_input("Чайных ложек сахара (~5г ложка, 20 ккал):", min_value=0, max_value=10, value=0, step=1)
        with col_add_btn:
            st.write("")
            st.write("")
            if st.button("Добавить сахар"):
                if sugar_spoons > 0:
                    sugar_weight = sugar_spoons * 5
                    sugar_exists = False
                    for item in st.session_state.food_items:
                        if "сахар" in item["name"].lower():
                            item["weight"] += sugar_weight
                            sugar_exists = True
                            break
                    if not sugar_exists:
                        st.session_state.food_items.append({
                            "name": f"Сахар ({sugar_spoons} ч.л.)",
                            "weight": sugar_weight,
                            "calories_per_100g": 400,
                            "protein_per_100g": 0,
                            "fat_per_100g": 0,
                            "carbs_per_100g": 100
                        })
                    st.success(f"Добавлено {sugar_weight}г сахара!")
                    st.rerun()

    st.subheader("📝 Редактирование ингредиентов")
    st.caption("Вы можете изменить вес продуктов, удалить или вручную вписать любой ингредиент:")

    # Вывод редактируемой таблицы
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

    # Пересчет итогов
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

    st.caption(f"Общий вес порции (включая сахара и масла): {round(total_weight)} г")

    if st.session_state.advice:
        st.success(f"💡 **Совет нутрициолога:** {st.session_state.advice}")
