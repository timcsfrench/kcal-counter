import streamlit as st
from google import genai
from PIL import Image

# Настройка страницы
st.set_page_config(page_title="AI Калории", page_icon="🥗", layout="centered")

st.title("🥗 Сканер калорий")
st.write("Сделай фото еды или загрузи из галереи, чтобы узнать калорийность и БЖУ.")

# Подключение к Gemini
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Загрузка фото
uploaded_file = st.file_uploader("Загрузи фото тарелки", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Показываем загруженное фото
    image = Image.open(uploaded_file)
    st.image(image, caption="Твое блюдо", use_container_width=True)
    
    # Кнопка для запуска анализа
    if st.button("🔍 Рассчитать калории", type="primary"):
        with st.spinner("Идёт анализ..."):
            try:
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
                
                # Актуальная модель
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[image, prompt]
                )
                
                st.success("Готово!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Произошла ошибка при анализе: {e}")