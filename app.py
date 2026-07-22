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
            
            try:
                # Получаем все модели с поддержкой генерации
                all_models = [
                    m.name for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods
                ]
                
                success = False
                
                for model_name in all_models:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content([prompt, image])
                        
                        st.success(f"Анализ выполнен с помощью модели: `{model_name}`")
                        st.markdown(response.text)
                        success = True
                        break # Выходим из цикла при первом успешном ответе
                    except Exception as inner_e:
                        # Если конкретная модель выдает 404 или ошибку доступа — пропукаем её
                        continue
                
                if not success:
                    st.error("Ни одна из доступных аккаунту моделей не смогла обработать запрос. Проверьте настройки API ключа.")

            except Exception as e:
                st.error(f"Произошла ошибка при получении списка моделей: {e}")
