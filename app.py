import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

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
            st.error("Қате логин")

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
    "📲 Хабар",
    "🧾 PDF",
    "🏆 Рейтинг"
])

# -------------------------------
# DATA
# -------------------------------
uploaded = st.sidebar.file_uploader("Excel жүктеу", type=["xlsx"])

def load_data():
    if uploaded:
        df = pd.read_excel(uploaded)
        req = ['аты','математика','физика','информатика','қазақ тілі','ағылшын тілі','қатысу']
        if not all(c in df.columns for c in req):
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

df = load_data()
subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']

# -------------------------------
# PROCESSING
# -------------------------------
df['орташа балл'] = df[subjects].mean(axis=1)

# прогресс (қате болмау үшін)
df['өткен'] = df['орташа балл'] - np.random.randint(0,10,len(df))

df['қауіп'] = np.where((df['орташа балл'] < 60) | (df['қатысу'] < 60), 1, 0)

def weak(row):
    low = row[subjects][row[subjects] < 50]
    return low.idxmin() if len(low)>0 else "Жоқ"

df['ең әлсіз пән'] = df.apply(weak, axis=1)

# AI
def ai(row):
    if row['орташа балл'] < 50:
        return f"{row['аты']} әлсіз, {row['ең әлсіз пән']} пәніне назар аудару керек."
    elif row['орташа балл'] < 70:
        return f"{row['аты']} орташа деңгейде."
    else:
        return f"{row['аты']} жақсы оқиды."

df['AI'] = df.apply(ai, axis=1)

# тапсырма
def task(row):
    return f"{row['ең әлсіз пән']} пәнінен қосымша жұмыс"

df['тапсырма'] = df.apply(task, axis=1)

df['хабар'] = df['аты'] + " - " + df['AI']

# ML
X = df[subjects+['қатысу']]
y = df['қауіп']
model = RandomForestClassifier()
model.fit(X,y)

# -------------------------------
# DASHBOARD
# -------------------------------
if menu == "🏠 Dashboard":
    col1,col2,col3 = st.columns(3)
    col1.metric("Орташа", round(df['орташа балл'].mean(),2))
    col2.metric("Қауіпті", df['қауіп'].sum())
    col3.metric("Үздік", len(df[df['орташа балл']>80]))

    st.dataframe(df)

# -------------------------------
# ANALYTICS
# -------------------------------
elif menu == "📊 Аналитика":

    fig, ax = plt.subplots()
    sns.barplot(x='аты', y='орташа балл', data=df, ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    fig2, ax2 = plt.subplots()
    ax2.plot(df['аты'], df['орташа балл'], label="қазір")
    ax2.plot(df['аты'], df['өткен'], label="өткен")
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(fig2)

# -------------------------------
# PREDICTION
# -------------------------------
elif menu == "🧠 Болжау":
    vals = [st.slider(s,0,100,60) for s in subjects]
    att = st.slider("қатысу",0,100,70)

    if st.button("Болжау"):
        pred = model.predict([vals+[att]])
        st.success("Қауіпсіз" if pred[0]==0 else "Қауіпті")

# -------------------------------
# PROFILE
# -------------------------------
elif menu == "👤 Профиль":
    s = st.selectbox("Оқушы", df['аты'])
    st.dataframe(df[df['аты']==s])

# -------------------------------
# MESSAGE
# -------------------------------
elif menu == "📲 Хабар":
    s = st.selectbox("Оқушы", df['аты'])
    st.info(df[df['аты']==s]['хабар'].values[0])

# -------------------------------
# PDF (SAFE VERSION)
# -------------------------------
elif menu == "🧾 PDF":

    s = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==s].iloc[0]

    if st.button("PDF жасау"):

        plt.figure()
        scores = [row[s] for s in subjects]
        plt.bar(subjects, scores)
        plt.xticks(rotation=45)
        plt.savefig("chart.png")
        plt.close()

        doc = SimpleDocTemplate("report.pdf", pagesize=letter)
        styles = getSampleStyleSheet()

        content = []

        content.append(Paragraph("Student Report", styles["Title"]))
        content.append(Spacer(1,10))
        content.append(Paragraph(f"Name: {row['аты']}", styles["Normal"]))
        content.append(Paragraph(f"Average: {row['орташа балл']}", styles["Normal"]))
        content.append(Paragraph(f"Advice: {row['AI']}", styles["Normal"]))
        content.append(Spacer(1,20))
        content.append(Image("chart.png", width=400, height=250))

        doc.build(content)

        with open("report.pdf","rb") as f:
            st.download_button("Жүктеу", f, file_name="report.pdf", mime="application/pdf")

# -------------------------------
# RATING
# -------------------------------
elif menu == "🏆 Рейтинг":
    d = df.sort_values(by='орташа балл', ascending=False)

    fig, ax = plt.subplots()
    sns.barplot(x='аты', y='орташа балл', data=d, ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)
