import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import streamlit.components.v1 as components

from sklearn.ensemble import RandomForestClassifier

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="Smart School Portal", layout="wide")

# -------------------------------
# STYLE
# -------------------------------
st.markdown("""
<style>
.kpi-card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    padding: 20px;
    border-radius: 15px;
    color: white;
    text-align: center;
}
.kpi-title { font-size: 14px; }
.kpi-value { font-size: 28px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# LOGIN
# -------------------------------
users = {"admin": "1234"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Кіру")
    u = st.text_input("Логин")
    p = st.text_input("Пароль", type="password")

    if st.button("Кіру"):
        if u in users and users[u] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Қате логин")
    st.stop()

# -------------------------------
# MENU
# -------------------------------
menu = st.sidebar.radio("Бөлім:", [
    "Журнал","Аналитика","Болжау","Профиль","Хабар","PDF","Рейтинг"
])

st.markdown(f"### 📍 Қазіргі бөлім: {menu}")

# -------------------------------
# DATA
# -------------------------------
df = pd.DataFrame({
    'аты':['Асан','Айгүл','Нұрсұлтан','Динара'],
    'математика':[80,50,40,90],
    'физика':[70,55,45,95],
    'информатика':[85,60,50,92],
    'қазақ тілі':[75,58,48,88],
    'ағылшын тілі':[78,52,46,91],
    'қатысу':[90,60,50,95]
})

subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']

# -------------------------------
# PROCESSING
# -------------------------------
df['орташа балл'] = df[subjects].mean(axis=1)
df['өткен'] = df['орташа балл'] - np.random.randint(0,10,len(df))
df['қауіп'] = np.where(df['орташа балл'] < 60, 1, 0)

df['ең әлсіз пән'] = df[subjects].idxmin(axis=1)
df['AI'] = df['аты'] + " - " + df['ең әлсіз пән'] + " жақсарту керек"
df['тапсырма'] = df['ең әлсіз пән'] + " бойынша жұмыс"

# -------------------------------
# MODEL
# -------------------------------
X = df[subjects+['қатысу']]
y = df['қауіп']
model = RandomForestClassifier()
model.fit(X,y)

# -------------------------------
# ЖУРНАЛ
# -------------------------------
if menu == "Журнал":
    st.dataframe(df)

# -------------------------------
# АНАЛИТИКА
# -------------------------------
elif menu == "Аналитика":

    col1, col2, col3 = st.columns(3)

    col1.metric("Орташа", round(df['орташа балл'].mean(),2))
    col2.metric("Қауіпті", df['қауіп'].sum())
    col3.metric("Үздік", len(df[df['орташа балл']>80]))

    fig, ax = plt.subplots()
    sns.barplot(x='аты', y='орташа балл', data=df)
    st.pyplot(fig)

# -------------------------------
# БОЛЖАУ
# -------------------------------
elif menu == "Болжау":

    vals = [st.slider(s,0,100,60) for s in subjects]
    att = st.slider("Қатысу",0,100,70)

    if st.button("Болжау"):
        pred = model.predict([vals+[att]])[0]
        st.success("Қауіпсіз" if pred==0 else "Қауіпті")

# -------------------------------
# ПРОФИЛЬ
# -------------------------------
elif menu == "Профиль":

    s = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==s].iloc[0]

    st.metric("Орташа", round(row['орташа балл'],2))
    st.write(row)

# -------------------------------
# ХАБАР
# -------------------------------
elif menu == "Хабар":

    s = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==s].iloc[0]

    st.info(row['AI'])

# -------------------------------
# PDF
# -------------------------------
elif menu == "PDF":

    s = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==s].iloc[0]

    if st.button("PDF жасау"):

        plt.figure()
        scores = [row[s] for s in subjects]
        plt.bar(subjects, scores)
        plt.savefig("chart.png")
        plt.close()

        doc = SimpleDocTemplate("report.pdf")
        styles = getSampleStyleSheet()

        content = []
        content.append(Paragraph("Student Report", styles["Title"]))
        content.append(Paragraph(row['AI'], styles["Normal"]))
        content.append(Image("chart.png", width=400, height=250))

        doc.build(content)

        with open("report.pdf","rb") as f:
            pdf_bytes = f.read()

        st.download_button("Жүктеу", pdf_bytes)

        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

        components.html(
            f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600">',
            height=600
        )

# -------------------------------
# РЕЙТИНГ
# -------------------------------
elif menu == "Рейтинг":

    df_sorted = df.sort_values(by='орташа балл', ascending=False)

    st.dataframe(df_sorted)

    fig, ax = plt.subplots()
    sns.barplot(x='аты', y='орташа балл', data=df_sorted)
    st.pyplot(fig)
