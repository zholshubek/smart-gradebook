import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

# -------------------------------
# CONFIG (ең басында 1 рет)
# -------------------------------
st.set_page_config(page_title="Smart School Portal", layout="wide")

# -------------------------------
# LOGIN SYSTEM
# -------------------------------
users = {
    "admin": "1234",
    "teacher": "1111"
}

if "login" not in st.session_state:
    st.session_state.login = False

def login_page():
    st.title("🔐 Жүйеге кіру")

    username = st.text_input("Логин")
    password = st.text_input("Құпия сөз", type="password")

    if st.button("Кіру"):
        if username in users and users[username] == password:
            st.session_state.login = True
            st.session_state.user = username
            st.success("Сәтті кірдіңіз!")
            st.rerun()
        else:
            st.error("Қате логин немесе пароль")

# Егер кірмеген болса — тек login көрсетіледі
if not st.session_state.login:
    login_page()
    st.stop()

# -------------------------------
# LOGOUT
# -------------------------------
if st.sidebar.button("🚪 Шығу"):
    st.session_state.login = False
    st.rerun()

# -------------------------------
# SIDEBAR MENU
# -------------------------------
st.sidebar.title("📚 Меню")
menu = st.sidebar.radio("Бөлім таңдаңыз:", [
    "🏠 Dashboard",
    "📊 Аналитика",
    "🧠 Болжау",
    "👤 Оқушы профилі",
    "📞 Ата-ана",
    "🏆 Рейтинг"
])

# -------------------------------
# DATA LOAD
# -------------------------------
st.sidebar.subheader("📂 Деректер")

uploaded_file = st.sidebar.file_uploader("Excel жүктеу", type=["xlsx"])

def load_data():
    if uploaded_file:
        return pd.read_excel(uploaded_file)
    else:
        return pd.DataFrame({
            'аты': ['Асан','Айгүл','Нұрсұлтан','Динара','Ержан','Мадина','Самат','Аружан'],
            'математика': [80,50,40,90,65,30,85,55],
            'физика': [70,55,45,95,60,35,88,50],
            'информатика': [85,60,50,92,70,40,90,65],
            'қазақ тілі': [75,58,48,88,68,45,86,60],
            'ағылшын тілі': [78,52,46,91,66,38,87,58],
            'қатысу': [90,60,50,95,70,40,92,65]
        })

df = load_data()

subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']

# -------------------------------
# DATA PROCESSING
# -------------------------------
df['орташа балл'] = df[subjects].mean(axis=1)
df['қауіп'] = np.where((df['орташа балл'] < 60) | (df['қатысу'] < 60), 1, 0)

def weak_subject(row):
    low = row[subjects][row[subjects] < 50]
    return low.idxmin() if len(low) > 0 else "Жоқ"

df['ең әлсіз пән'] = df.apply(weak_subject, axis=1)

def recommendation(row):
    if row['орташа балл'] < 60 and row['қатысу'] < 60:
        return f"Ата-анамен кездесу ({row['ең әлсіз пән']})"
    elif row['орташа балл'] < 60:
        return f"Қосымша сабақ ({row['ең әлсіз пән']})"
    elif row['қатысу'] < 60:
        return "Ата-анамен байланыс"
    else:
        return "Жақсы"

df['ұсыныс'] = df.apply(recommendation, axis=1)

# -------------------------------
# ML MODEL
# -------------------------------
X = df[subjects + ['қатысу']]
y = df['қауіп']

model = RandomForestClassifier()
model.fit(X, y)

# -------------------------------
# DASHBOARD
# -------------------------------
if menu == "🏠 Dashboard":
    st.title("📊 Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("Орташа балл", round(df['орташа балл'].mean(),2))
    col2.metric("Қауіпті %", f"{round(df['қауіп'].mean()*100,1)}%")
    col3.metric("Оқушы саны", len(df))

    st.dataframe(df)

# -------------------------------
# ANALYTICS
# -------------------------------
elif menu == "📊 Аналитика":
    st.title("📈 Аналитика")

    sns.set_style("whitegrid")

    fig, ax = plt.subplots(figsize=(12,6))
    sns.barplot(x='аты', y='орташа балл', data=df, palette='viridis', ax=ax)

    plt.xticks(rotation=45)
    st.pyplot(fig)

# -------------------------------
# PREDICTION
# -------------------------------
elif menu == "🧠 Болжау":
    st.title("🧠 Болжау")

    math = st.slider("Математика", 0, 100, 60)
    physics = st.slider("Физика", 0, 100, 60)
    info = st.slider("Информатика", 0, 100, 60)
    kaz = st.slider("Қазақ тілі", 0, 100, 60)
    eng = st.slider("Ағылшын тілі", 0, 100, 60)
    att = st.slider("Қатысу", 0, 100, 70)

    if st.button("Болжау"):
        pred = model.predict([[math, physics, info, kaz, eng, att]])
        st.success("Қауіпсіз" if pred[0] == 0 else "Қауіпті")

# -------------------------------
# PROFILE
# -------------------------------
elif menu == "👤 Оқушы профилі":
    st.title("👤 Оқушы профилі")

    student = st.selectbox("Оқушы таңдаңыз", df['аты'])
    st.dataframe(df[df['аты'] == student])

# -------------------------------
# PARENTS
# -------------------------------
elif menu == "📞 Ата-ана":
    st.title("📞 Ата-анамен жұмыс")

    st.dataframe(df[df['ұсыныс'].str.contains("Ата-ана")])

# -------------------------------
# RATING
# -------------------------------
elif menu == "🏆 Рейтинг":
    st.title("🏆 Рейтинг")

    df_sorted = df.sort_values(by='орташа балл', ascending=False)

    fig, ax = plt.subplots(figsize=(12,6))
    sns.barplot(x='аты', y='орташа балл', data=df_sorted, palette='coolwarm', ax=ax)

    plt.xticks(rotation=45)
    st.pyplot(fig)
