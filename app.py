import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="Smart School Portal", layout="wide")

# -------------------------------
# LOGIN
# -------------------------------
users = {"admin": "1234", "teacher": "1111"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Жүйеге кіру")

    u = st.text_input("Логин")
    p = st.text_input("Құпия сөз", type="password")

    if st.button("Кіру"):
        if u in users and users[u] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Қате логин немесе пароль")

    st.stop()

# Logout
if st.sidebar.button("🚪 Шығу"):
    st.session_state.login = False
    st.rerun()

# -------------------------------
# MENU
# -------------------------------
st.sidebar.title("📚 Меню")
menu = st.sidebar.radio("Бөлім:", [
    "🏠 Dashboard",
    "📊 Аналитика",
    "🧠 Болжау",
    "👤 Профиль",
    "📲 Хабарлама",
    "🏆 Рейтинг"
])

# -------------------------------
# DATA
# -------------------------------
uploaded = st.sidebar.file_uploader("Excel жүктеу", type=["xlsx"])

def load():
    if uploaded:
        df = pd.read_excel(uploaded)
        cols = ['аты','математика','физика','информатика','қазақ тілі','ағылшын тілі','қатысу']
        if not all(c in df.columns for c in cols):
            st.error("Excel формат қате!")
            st.stop()
        return df
    else:
        return pd.DataFrame({
            'аты':['Асан','Айгүл','Нұрсұлтан','Динара','Ержан','Мадина','Самат','Аружан'],
            'математика':[80,50,40,90,65,30,85,55],
            'физика':[70,55,45,95,60,35,88,50],
            'информатика':[85,60,50,92,70,40,90,65],
            'қазақ тілі':[75,58,48,88,68,45,86,60],
            'ағылшын тілі':[78,52,46,91,66,38,87,58],
            'қатысу':[90,60,50,95,70,40,92,65]
        })

df = load()
subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']

# -------------------------------
# PROCESS
# -------------------------------
df['орташа балл'] = df[subjects].mean(axis=1)
df['қауіп'] = np.where((df['орташа балл'] < 60) | (df['қатысу'] < 60), 1, 0)

def weak(row):
    low = row[subjects][row[subjects] < 50]
    return low.idxmin() if len(low)>0 else "Жоқ"

df['ең әлсіз пән'] = df.apply(weak, axis=1)

# AI кеңес
def ai(row):
    if row['орташа балл'] < 50:
        return f"{row['аты']} - {row['ең әлсіз пән']} өте төмен. Жеке жұмыс қажет."
    elif row['орташа балл'] < 70:
        return f"{row['аты']} - {row['ең әлсіз пән']} жақсарту керек."
    else:
        return f"{row['аты']} жақсы оқиды."

df['AI кеңес'] = df.apply(ai, axis=1)

# тапсырма
tasks = {
    "математика":"10 есеп",
    "физика":"5 есеп",
    "информатика":"Python практика",
    "қазақ тілі":"мәтін жазу",
    "ағылшын тілі":"20 сөз жаттау"
}

df['тапсырма'] = df['ең әлсіз пән'].map(tasks).fillna("Қайталау")

# ата-ана хабар
df['хабар'] = df['аты'] + " - " + df['AI кеңес']

# прогресс (демо)
df['өткен'] = df['орташа балл'] - np.random.randint(0,10,len(df))

# ML
X = df[subjects+['қатысу']]
y = df['қауіп']
model = RandomForestClassifier()
model.fit(X,y)

# -------------------------------
# DASHBOARD
# -------------------------------
if menu == "🏠 Dashboard":
    st.title("📊 Dashboard")

    col1,col2,col3 = st.columns(3)
    col1.metric("Орташа", round(df['орташа балл'].mean(),2))
    col2.metric("Қауіпті", df['қауіп'].sum())
    col3.metric("Үздік", len(df[df['орташа балл']>80]))

    st.dataframe(df)

# -------------------------------
# ANALYTICS
# -------------------------------
elif menu == "📊 Аналитика":
    st.title("📈 Аналитика")

    sns.set_style("whitegrid")

    fig,ax = plt.subplots(figsize=(12,6))
    sns.barplot(x='аты',y='орташа балл',data=df,ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # progress
    fig2,ax2 = plt.subplots()
    ax2.plot(df['аты'],df['орташа балл'],label="қазір")
    ax2.plot(df['аты'],df['өткен'],label="өткен")
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(fig2)

# -------------------------------
# PREDICTION
# -------------------------------
elif menu == "🧠 Болжау":
    st.title("🧠 Болжау")

    vals = [st.slider(s,0,100,60) for s in subjects]
    att = st.slider("қатысу",0,100,70)

    if st.button("Болжау"):
        pred = model.predict([vals+[att]])
        st.success("Қауіпсіз" if pred[0]==0 else "Қауіпті")

# -------------------------------
# PROFILE
# -------------------------------
elif menu == "👤 Профиль":
    st.title("👤 Профиль")

    s = st.selectbox("Оқушы",df['аты'])
    st.dataframe(df[df['аты']==s])

# -------------------------------
# MESSAGE
# -------------------------------
elif menu == "📲 Хабарлама":
    st.title("📲 Ата-ана хабар")

    s = st.selectbox("Оқушы таңда",df['аты'])
    msg = df[df['аты']==s]['хабар'].values[0]

    st.info(msg)

# -------------------------------
# RATING
# -------------------------------
elif menu == "🏆 Рейтинг":
    st.title("🏆 Рейтинг")

    d = df.sort_values(by='орташа балл',ascending=False)

    fig,ax = plt.subplots(figsize=(12,6))
    sns.barplot(x='аты',y='орташа балл',data=d,ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)
