import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import streamlit.components.v1 as components

from sklearn.ensemble import RandomForestClassifier

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter

# -------------------------------
# CONFIG
# -------------------------------


st.set_page_config(page_title="Smart School Portal", layout="wide")
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
st.markdown("""
<style>
.block-container {
    padding: 2rem;
}

.stMetric {
    background-color: #1f2937;
    padding: 10px;
    border-radius: 10px;
}

h1, h2, h3 {
    color: #2563eb;
}
</style>
""", unsafe_allow_html=True)

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

if st.sidebar.button("🚪 Шығу"):
    st.session_state.login = False
    st.rerun()

# -------------------------------
# MENU (FIXED)
# -------------------------------
menu = st.sidebar.radio("Бөлім:", [
    "Dashboard",
    "Аналитика",
    "Болжау",
    "Профиль",
    "Хабар",
    "PDF",
    "Рейтинг"
])

st.write("Қазіргі таңдалған бөлім:", menu)  # debug

# -------------------------------
# DATA
# -------------------------------
uploaded = st.sidebar.file_uploader("Excel жүктеу", type=["xlsx"])

def load_data():
    if uploaded:
        df = pd.read_excel(uploaded)
    else:
        df = pd.DataFrame({
            'аты':['Асан','Айгүл','Нұрсұлтан','Динара','Ержан','Мадина','Самат','Аружан'],
            'математика':[80,50,40,90,65,30,85,55],
            'физика':[70,55,45,95,60,35,88,50],
            'информатика':[85,60,50,92,70,40,90,65],
            'қазақ тілі':[75,58,48,88,68,45,86,60],
            'ағылшын тілі':[78,52,46,91,66,38,87,58],
            'қатысу':[90,60,50,95,70,40,92,65]
        })
    return df

df = load_data()

subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']

# -------------------------------
# PROCESSING
# -------------------------------
df['орташа балл'] = df[subjects].mean(axis=1)
df['өткен'] = df['орташа балл'] - np.random.randint(0,10,len(df))
df['қауіп'] = np.where(df['орташа балл'] < 60, 1, 0)

def weak(row):
    return subjects[np.argmin([row[s] for s in subjects])]

df['ең әлсіз пән'] = df.apply(weak, axis=1)

df['AI'] = df.apply(lambda r: f"{r['аты']} - {r['ең әлсіз пән']} жақсарту керек", axis=1)
df['тапсырма'] = df['ең әлсіз пән'] + " бойынша жұмыс"
df['хабар'] = df['аты'] + " - " + df['AI']

# ML
X = df[subjects+['қатысу']]
y = df['қауіп']
model = RandomForestClassifier()
model.fit(X,y)

# -------------------------------
# DASHBOARD
# -------------------------------
if menu == "Dashboard":
    st.title("📊 Dashboard")
    st.dataframe(df)

# -------------------------------
# ANALYTICS
# -------------------------------
elif menu == "Аналитика":

    st.title("📊 Аналитика")

    fig, ax = plt.subplots()
    sns.barplot(x='аты', y='орташа балл', data=df, ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    fig2, ax2 = plt.subplots()
    ax2.plot(df['аты'], df['орташа балл'], label="Қазір")
    ax2.plot(df['аты'], df['өткен'], label="Өткен")
    plt.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig2)

# -------------------------------
# PREDICTION
# -------------------------------
elif menu == "Болжау":

    st.title("🧠 Болжау")

    vals = [st.slider(s,0,100,60) for s in subjects]
    att = st.slider("Қатысу",0,100,70)

    if st.button("Болжау"):
        pred = model.predict([vals+[att]])[0]
        st.success("Қауіпсіз" if pred==0 else "Қауіпті")

# -------------------------------
# PROFILE
# -------------------------------
elif menu == "Профиль":
    st.title("👤 Профиль")
    s = st.selectbox("Оқушы", df['аты'])
    st.dataframe(df[df['аты']==s])

# -------------------------------
# MESSAGE
# -------------------------------
elif menu == "Хабар":

    st.title("📲 Ата-анаға хабар")

    student = st.selectbox("Оқушы таңдаңыз", df['аты'])
    row = df[df['аты'] == student].iloc[0]

    st.markdown("### 📄 Дайын хабар")

    st.info(f"""
👤 Оқушы: {row['аты']}

📊 Орташа балл: {round(row['орташа балл'],2)}  
📉 Әлсіз пән: {row['ең әлсіз пән']}  

🧠 Ұсыныс:  
{row['AI']}  

📚 Тапсырма:  
{row['тапсырма']}  

📅 Қатысу: {row['қатысу']}%
""")

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "📥 TXT жүктеу",
            data=row['хабар'],
            file_name=f"{row['аты']}_message.txt"
        )

    with col2:
        if row['орташа балл'] < 50:
            st.error("⚠️ Қауіпті деңгей")
        elif row['орташа балл'] < 70:
            st.warning("📘 Орташа деңгей")
        else:
            st.success("🏆 Жақсы нәтиже")

# -------------------------------
# PDF
# -------------------------------

elif menu == "PDF":

    st.title("🧾 PDF есеп")

    student = st.selectbox("Оқушы таңда", df['аты'])
    row = df[df['аты']==student].iloc[0]

    if st.button("📄 PDF жасау"):

        # 📊 график
        chart_path = "chart.png"

        plt.figure(figsize=(6,4))
        scores = [row[s] for s in subjects]
        plt.bar(subjects, scores, color='#4CAF50')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()

        # 📄 PDF
        doc = SimpleDocTemplate("report.pdf")
        styles = getSampleStyleSheet()

        title = ParagraphStyle(
            'title',
            fontName='DejaVu',
            fontSize=18,
            textColor=colors.darkblue
        )

        normal = ParagraphStyle(
            'normal',
            fontName='DejaVu',
            fontSize=12
        )

        content = []

        content.append(Paragraph("ОҚУШЫ ЕСЕБІ", title))
        content.append(Spacer(1,10))

        content.append(Paragraph(f"Аты: {row['аты']}", normal))
        content.append(Paragraph(f"Орташа балл: {round(row['орташа балл'],2)}", normal))
        content.append(Paragraph(f"Ұсыныс: {row['AI']}", normal))
        content.append(Spacer(1,10))

        content.append(Image(chart_path, width=400, height=250))

        doc.build(content)

        with open("report.pdf","rb") as f:
            pdf_bytes = f.read()

        # 📥 download
        st.download_button(
            "📥 PDF жүктеу",
            pdf_bytes,
            file_name=f"{row['аты']}_report.pdf",
            mime="application/pdf"
        )

        # 👁 preview
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

        components.html(
            f"""
            <embed src="data:application/pdf;base64,{base64_pdf}"
            width="100%" height="600">
            """,
            height=600
        )
# -------------------------------
# RATING
# -------------------------------
elif menu == "Рейтинг":

    st.title("🏆 Оқушылар рейтингі")

    df_sorted = df.sort_values(by='орташа балл', ascending=False).reset_index(drop=True)
    df_sorted['Рейтинг'] = df_sorted.index + 1

    # 🥇 TOP 3 CARD
    st.subheader("🥇 ТОП 3")

    col1, col2, col3 = st.columns(3)
    medals = ["🥇", "🥈", "🥉"]

    for i, col in enumerate([col1, col2, col3]):
        with col:
            st.markdown(f"### {medals[i]} {df_sorted.iloc[i]['аты']}")
            st.metric("Балл", round(df_sorted.iloc[i]['орташа балл'],2))

    st.divider()

    # 📊 ГРАФИК
    fig, ax = plt.subplots(figsize=(10,5))

    colors = ['green' if x>80 else 'orange' if x>60 else 'red'
              for x in df_sorted['орташа балл']]

    ax.bar(df_sorted['аты'], df_sorted['орташа балл'], color=colors)
    plt.xticks(rotation=45)

    for i, v in enumerate(df_sorted['орташа балл']):
        ax.text(i, v+1, str(round(v,1)), ha='center')

    st.pyplot(fig)

    st.divider()

    # 📋 КЕСТЕ
    st.subheader("📋 Толық рейтинг")
    st.dataframe(df_sorted[['Рейтинг','аты','орташа балл']])

    st.divider()

    # 🎯 ДЕҢГЕЙ
    def level(x):
        if x>=80: return "🟢 Үздік"
        elif x>=60: return "🟡 Орташа"
        else: return "🔴 Қауіпті"

    df_sorted['Деңгей'] = df_sorted['орташа балл'].apply(level)

    st.subheader("🎯 Деңгей бойынша")
    st.dataframe(df_sorted[['аты','орташа балл','Деңгей']])
