
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client

st.set_page_config(
    page_title="Фокус студента",
    page_icon="🎯",
    layout="wide"
)

# Подключение к Supabase
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #f4f7fb 0%, #ffffff 45%);
}
.block-container {
    padding-top: 2rem;
    max-width: 1120px;
}
.hero {
    background: linear-gradient(120deg,#16324f,#246a73);
    padding: 1.5rem 1.8rem;
    border-radius: 18px;
    color: white;
    margin-bottom: 1rem;
}
.hero h1 {
    color: white;
    margin-bottom: .25rem;
}
.hero p {
    color: #e5f3f4;
    margin-bottom: 0;
}
div[data-testid="stForm"] {
    background: #ffffff;
    border: 1px solid #dbe5ed;
    padding: 1.2rem;
    border-radius: 16px;
}
</style>

<div class="hero">
<h1>🎯 Фокус студента</h1>
<p>Опрос о цифровых привычках и концентрации во время учёбы</p>
</div>
""", unsafe_allow_html=True)

st.write(
    "Анкета поможет изучить, как уведомления, смартфон и режим "
    "занятий связаны с субъективной концентрацией студентов. "
    "Опрос анонимный, занимает около 2 минут. "
    "Не указывайте имя и контактные данные."
)

with st.form("focus_survey"):
    st.subheader("Расскажите о своих привычках")
    left, right = st.columns(2)

    with left:
        age = st.number_input(
            "Ваш возраст", min_value=14, max_value=80,
            value=19, step=1
        )
        course = st.selectbox(
            "На каком вы курсе?",
            ["1 курс", "2 курс", "3 курс", "4 курс",
             "5 курс и выше", "Не учусь сейчас"]
        )
        phone_hours = st.select_slider(
            "Сколько времени в день обычно проводите в смартфоне?",
            options=["Менее 1 часа", "1–2 часа", "3–4 часа",
                     "5–6 часов", "7 часов и более"]
        )
        notifications = st.radio(
            "Как часто уведомления отвлекают вас во время учёбы?",
            ["Никогда", "Редко", "Иногда", "Часто", "Очень часто"]
        )

    with right:
        study_focus = st.slider(
            "Насколько легко вам сосредоточиться на учебной задаче?",
            1, 10, 6,
            help="1 — очень трудно, 10 — очень легко"
        )
        phone_during_study = st.radio(
            "Что обычно делаете с телефоном во время занятий?",
            ["Убираю и не проверяю", "Проверяю иногда",
             "Часто отвлекаюсь на него", "Использую для учебных задач"]
        )
        study_session = st.selectbox(
            "Сколько обычно длится ваша непрерывная учебная сессия?",
            ["Менее 15 минут", "15–30 минут", "31–45 минут",
             "46–60 минут", "Более часа"]
        )
        breaks = st.selectbox(
            "Как часто делаете перерывы при самостоятельной учёбе?",
            ["Примерно каждые 15–20 минут",
             "Каждые 30–45 минут", "Примерно раз в час",
             "Когда устану", "Почти не делаю перерывов"]
        )

    distractions = st.multiselect(
        "Что чаще всего мешает сосредоточиться?",
        ["Уведомления и сообщения", "Социальные сети",
         "Видео и игры", "Шум вокруг", "Усталость",
         "Сложность материала", "Личные дела",
         "Ничего из перечисленного"]
    )

    comment = st.text_area(
        "Что помогает вам лучше сосредоточиться? (необязательно)",
        max_chars=500
    )

    submitted = st.form_submit_button(
        "Отправить ответы",
        type="primary",
        use_container_width=True
    )

# Сохранение ответа в базу
if submitted:
    answer = {
        "Возраст": int(age),
        "Курс": course,
        "Время в смартфоне": phone_hours,
        "Отвлекают уведомления": notifications,
        "Концентрация (1–10)": int(study_focus),
        "Телефон во время учёбы": phone_during_study,
        "Длительность сессии": study_session,
        "Перерывы": breaks,
        "Отвлекающие факторы": ", ".join(distractions),
        "Что помогает": comment.strip(),
        "Время отправки": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    try:
        db = get_supabase()
        db.table("survey_responses").insert(
            {"answers": answer}
        ).execute()

        st.success(
            "Спасибо! Ответ успешно сохранён в базе данных."
        )

    except Exception as e:
        st.error("Не удалось сохранить ответ в Supabase.")
        st.code(str(e))

st.divider()
st.subheader("📊 Аналитика ответов")

# Загружаем ответы из базы при каждом открытии приложения
try:
    db = get_supabase()
    result = (
        db.table("survey_responses")
        .select("answers")
        .order("id", desc=True)
        .execute()
    )

    responses = [
        row["answers"]
        for row in result.data
        if row.get("answers")
    ]

    if not responses:
        st.info(
            "Пока нет ответов. Заполните анкету, "
            "чтобы увидеть сводку."
        )
    else:
        df = pd.DataFrame(responses)

        c1, c2, c3 = st.columns(3)
        c1.metric("Всего ответов", len(df))
        c2.metric(
            "Средняя концентрация",
            f"{df['Концентрация (1–10)'].mean():.1f} / 10"
        )
        c3.metric(
            "Средний возраст",
            f"{df['Возраст'].mean():.1f}"
        )

        st.dataframe(
            df.drop(columns=["Что помогает"], errors="ignore"),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Скачать ответы в CSV",
            df.to_csv(index=False).encode("utf-8-sig"),
            "student_focus_responses.csv",
            "text/csv"
        )

        a, b = st.columns(2)

        with a:
            fig = px.histogram(
                df,
                x="Концентрация (1–10)",
                nbins=10,
                title="Оценка концентрации",
                color_discrete_sequence=["#247b83"]
            )
            st.plotly_chart(fig, use_container_width=True)

        with b:
            order = [
                "Никогда", "Редко", "Иногда",
                "Часто", "Очень часто"
            ]
            counts = (
                df["Отвлекают уведомления"]
                .value_counts()
                .reindex(order, fill_value=0)
                .rename_axis("Частота")
                .reset_index(name="Количество")
            )

            fig = px.bar(
                counts,
                x="Частота",
                y="Количество",
                title="Как часто отвлекают уведомления",
                color_discrete_sequence=["#e39b55"]
            )
            st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Результаты основаны на ответах, загруженных из Supabase. "
            "Это учебный опрос, а не научно валидированный тест."
        )

except Exception as e:
    st.error(
        "Не удалось загрузить аналитику из Supabase. "
        "Проверь настройки Secrets и права доступа к таблице."
    )
    st.code(str(e))
