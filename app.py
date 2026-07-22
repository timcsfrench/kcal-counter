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
            
            # Приоритетные быстрые модели в порядке очереди
            priority_models = [
                'models/gemini-1.5-flash-latest',
                'models/gemini-1.5-flash',
                'models/gemini-2.0-flash-exp',
                'models/gemini-1.5-pro'
            ]
            
            success = False
            
            # 1. Сначала пробуем самые быстрые известные модели
            for model_name in priority_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content([image, prompt])
                    st.success("Готово!")
                    st.markdown(response.text)
                    success = True
                    break
                except Exception:
                    continue
            
            # 2. Если ни одна из быстрых не ответила — ищем остаток среди всех доступных Gemini
            if not success:
                try:
                    all_gemini = [
                        m.name for m in genai.list_models() 
                        if 'generateContent' in m.supported_generation_methods 
                        and 'gemini' in m.name.lower()
                    ]
                    for model_name in all_gemini:
                        if model_name in priority_models:
                            continue # Пропускаем те, что уже проверяли
                        try:
                            model = genai.GenerativeModel(model_name)
                            response = model.generate_content([image, prompt])
                            st.success("Готово!")
                            st.markdown(response.text)
                            success = True
                            break
                        except Exception:
                            continue
                except Exception:
                    pass

            if not success:
                st.error("Не удалось подлючиться к модели. Попробуйте еще раз.")
