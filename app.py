import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
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
        required = ['аты','математика','физика','информатика','қазақ тілі','ағылшын тілі','қатысу']
        if not all(c in df.columns for c in required):
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
df['өткен'] = df['орташа балл'] - np.random.randint(0,10,len(df))

df['қауіп'] = np.where((df['орташа балл'] < 60) | (df['қатысу'] < 60), 1, 0)

def weak(row):
    low = row[subjects][row[subjects] < 50]
    return low.idxmin() if len(low)>0 else "Жоқ"

df['ең әлсіз пән'] = df.apply(weak, axis=1)

def ai(row):
    if row['орташа балл'] < 50:
        return f"{row['аты']} әлсіз. {row['ең әлсіз пән']} пәніне назар аудару керек."
    elif row['орташа балл'] < 70:
        return f"{row['аты']} орташа деңгейде."
    else:
        return f"{row['аты']} жақсы оқиды."

df['AI'] = df.apply(ai, axis=1)
df['тапсырма'] = df['ең әлсіз пән'] + " бойынша қосымша жұмыс"
df['хабар'] = df['аты'] + " - " + df['AI']

# -------------------------------
# ML MODEL
# -------------------------------
X = df[subjects+['қатысу']]
y = df['қауіп']
model = RandomForestClassifier()
model.fit(X,y)

# -------------------------------
# DASHBOARD
# -------------------------------
if menu == "🏠 Dashboard":
    col1,col2,col3 = st.columns(3)
    col1.metric("Орташа балл", round(df['орташа балл'].mean(),2))
    col2.metric("Қауіпті", df['қауіп'].sum())
    col3.metric("Үздік", len(df[df['орташа балл']>80]))
    st.dataframe(df)

# -------------------------------
# ANALYTICS (FULL)
# -------------------------------
elif menu == "📊 Аналитика":

    st.title("📊 Аналитика")

    col1, col2 = st.columns(2)

    fig1, ax1 = plt.subplots()
    sns.barplot(x='аты', y='орташа балл', data=df, ax=ax1)
    plt.xticks(rotation=45)
    col1.pyplot(fig1)

    fig2, ax2 = plt.subplots()
    sns.scatterplot(x='қатысу', y='орташа балл', hue='қауіп', data=df, ax=ax2)
    col2.pyplot(fig2)

    fig3, ax3 = plt.subplots()
    sns.heatmap(df[subjects].corr(), annot=True, ax=ax3)
    st.pyplot(fig3)

    fig4, ax4 = plt.subplots()
    ax4.plot(df['аты'], df['орташа балл'], label="Қазір")
    ax4.plot(df['аты'], df['өткен'], label="Өткен")
    plt.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig4)

# -------------------------------
# PREDICTION (UPGRADED)
# -------------------------------
elif menu == "🧠 Болжау":

    st.title("🧠 Болжау жүйесі")

    vals = [st.slider(s,0,100,60) for s in subjects]
    att = st.slider("Қатысу",0,100,70)

    if st.button("Болжау"):

        pred = model.predict([vals+[att]])[0]
        prob = model.predict_proba([vals+[att]])[0]

        st.metric("Қауіп ықтималдығы", f"{round(prob[1]*100,1)}%")

        if pred == 1:
            st.error("⚠️ Қауіпті")
        else:
            st.success("✅ Қауіпсіз")

# -------------------------------
# PROFILE
# -------------------------------
elif menu == "👤 Профиль":
    s = st.selectbox("Оқушы", df['аты'])
    st.dataframe(df[df['аты']==s])

# -------------------------------
# MESSAGE (UPGRADED)
# -------------------------------
elif menu == "📲 Хабар":

    st.title("📲 Ата-анаға хабар")

    s = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==s].iloc[0]

    message = f"""
Аты: {row['аты']}
Орташа: {row['орташа балл']}
Әлсіз пән: {row['ең әлсіз пән']}
Ұсыныс: {row['AI']}
"""

    st.text_area("Хабар", message)
    st.download_button("TXT жүктеу", message, file_name="message.txt")

# -------------------------------
# PDF (SAFE)
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
        content.append(Paragraph(f"Name: {row['аты']}", styles["Normal"]))
        content.append(Paragraph(f"Average: {row['орташа балл']}", styles["Normal"]))
        content.append(Image("chart.png", width=400, height=250))

        doc.build(content)

        with open("report.pdf","rb") as f:
            st.download_button("Жүктеу", f, file_name="report.pdf")

# -------------------------------
# RATING (UPGRADED)
# -------------------------------
elif menu == "🏆 Рейтинг":

    df_sorted = df.sort_values(by='орташа балл', ascending=False).reset_index(drop=True)
    df_sorted['Рейтинг'] = df_sorted.index + 1

    st.dataframe(df_sorted[['Рейтинг','аты','орташа балл']])

    fig, ax = plt.subplots()
    sns.barplot(x='аты', y='орташа балл', data=df_sorted, ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)
