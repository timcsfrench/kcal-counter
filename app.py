import streamlit as st
import google.generativeai as genai
from PIL import Image

# Настройка страницы
st.set_page_config(page_title="AI Калории", page_icon="🥗", layout="centered")

st.title("🥗 Сканер калорий")
st.write("Сделай фото еды или загрузи из галереи, чтобы узнать калорийность и БЖУ.")

# Подключение к Gemini через секреты Streamlit
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Ошибка настройки API ключа. Проверьте Secrets в Streamlit.")

# Загрузка фото
uploaded_file = st.file_uploader("Загрузите фото тарелки", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Ваше блюдо", use_container_width=True)
    
    if st.button("🔍 Рассчитать калории", type="primary"):
        with st.spinner("Идёт анализ..."):
            try:
                # Автоматически ищем модель, поддерживающую обработку изображений (generateContent)
                available_models = [
                    m.name for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods
                ]
                
                if not available_models:
                    st.error("Для данного ключа не найдено ни одной доступной модели с поддержкой генерации.")
                else:
                    # Выбираем первую подходящую рабочую модель
                    selected_model_name = available_models[0]
                    st.info(f"Используем рабочую модель: `{selected_model_name}`")
                    
                    model = genai.GenerativeModel(selected_model_name)
                    
                    prompt = """
                    Ты — профессиональный нутрициолог.
                    Проанализируй фото еды и выдай ответ строго на русском языке в следующем формате:
                    1. Название блюда / продуктов на фото.
                    2. Примерный вес каждого ингредиента в граммах.
                    3. Итоговая калорийность (ккал).
                    4. Белки, Жиры, Углеводы (БЖУ) в граммах.
                    5. Короткий совет по пищевой ценности этого блюда.
                    Будь максимально точен в оценке порций.
                    """
                    
                    response = model.generate_content([prompt, image])
                    
                    st.success("Готово!")
                    st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Произошла ошибка при анализе: {e}")
