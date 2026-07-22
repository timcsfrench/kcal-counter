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
uploaded_file = st.file_uploader("Загрузи фото тарелки", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Показываем загруженное фото
    image = Image.open(uploaded_file)
    st.image(image, caption="Ваше блюдо", use_container_width=True)
    
    # Кнопка для запуска анализа
    if st.button("🔍 Рассчитать калории", type="primary"):
        with st.spinner("Идёт анализ..."):
            try:
                # Имя модели с полным суффиксом для Vertex API
                model = genai.GenerativeModel('gemini-1.5-flash-002')
                
                # Промпт для нейросети
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
                
                # Запрос к нейросети
                response = model.generate_content([prompt, image])
                
                st.success("Готово!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Произошла ошибка при анализе: {e}")
