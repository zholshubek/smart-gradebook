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
# -------------------------------
# SMART ТАПСЫРМА (міндетті)
# -------------------------------
def tasks(row):
    subject = row['ең әлсіз пән']

    if subject == "Жоқ":
        return "Қосымша тапсырма қажет емес"
    
    if subject == "математика":
        return "10 есеп шығару"
    elif subject == "физика":
        return "5 есеп + формула қайталау"
    elif subject == "информатика":
        return "Python практика"
    elif subject == "қазақ тілі":
        return "1 мәтін жазу"
    elif subject == "ағылшын тілі":
        return "20 сөз жаттау"
    else:
        return "Қайталау"

df['тапсырма'] = df.apply(tasks, axis=1)
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

    st.title("🧠 Ақылды болжау жүйесі")

    st.markdown("### 📊 Оқушы мәліметін енгізіңіз")

    col1, col2 = st.columns(2)

    with col1:
        math = st.slider("📘 Математика", 0, 100, 60)
        physics = st.slider("🔬 Физика", 0, 100, 60)
        info = st.slider("💻 Информатика", 0, 100, 60)

    with col2:
        kaz = st.slider("📖 Қазақ тілі", 0, 100, 60)
        eng = st.slider("🌍 Ағылшын тілі", 0, 100, 60)
        att = st.slider("📅 Қатысу", 0, 100, 70)

    input_data = [math, physics, info, kaz, eng, att]

    if st.button("🔍 Болжау"):

        # 🔮 Болжау
        pred = model.predict([input_data])[0]

        # 📊 Ықтималдық
        prob = model.predict_proba([input_data])[0]

        st.divider()

        # -------------------------------
        # 🎯 НӘТИЖЕ
        # -------------------------------
        if pred == 1:
            st.error("⚠️ Оқушы қауіп тобында")
        else:
            st.success("✅ Оқушы қауіпсіз")

        st.metric("📊 Қауіп ықтималдығы", f"{round(prob[1]*100,1)} %")

        st.divider()

        # -------------------------------
        # 🧠 AI ТҮСІНДІРУ
        # -------------------------------
        st.subheader("🧠 AI түсіндірме")

        weak_subject = subjects[np.argmin(input_data[:5])]

        if pred == 1:
            st.warning(f"""
Бұл оқушының нәтижесі төмен болуы мүмкін.

Негізгі әлсіз пән: **{weak_subject}**

Себептері:
- Балл төмен
- Қатысу жеткіліксіз

Ұсыныс:
- Қосымша сабақ
- Күнделікті практика
""")
        else:
            st.info(f"""
Оқушының жағдайы жақсы.

Күшті жақтары:
- Жоғары орташа балл
- Қатысу жақсы

Ұсыныс:
- Нәтижені сақтау
- Әлсіз пәндерді аздап қайталау
""")

        st.divider()

        # -------------------------------
        # 📊 ВИЗУАЛИЗАЦИЯ
        # -------------------------------
        st.subheader("📊 Пәндер бойынша анализ")

        fig, ax = plt.subplots()

        bars = ax.bar(subjects, input_data[:5])

        # түстер
        colors = ['green' if x>70 else 'orange' if x>50 else 'red' for x in input_data[:5]]
        for bar, color in zip(bars, colors):
            bar.set_color(color)

        plt.xticks(rotation=45)
        ax.set_title("Пәндер деңгейі")

        st.pyplot(fig)

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

    st.title("📲 Ата-анаға хабарлама жүйесі")

    # -------------------------------
    # 👤 ОҚУШЫ ТАҢДАУ
    # -------------------------------
    student = st.selectbox("Оқушы таңдаңыз", df['аты'])
    row = df[df['аты'] == student].iloc[0]

    st.divider()

    # -------------------------------
    # 📋 ХАБАР МӘТІНІ (AI + DATA)
    # -------------------------------
    message = f"""
Құрметті ата-ана!

Сіздің балаңыз: {row['аты']}

📊 Орташа балл: {round(row['орташа балл'],2)}
📉 Әлсіз пән: {row['ең әлсіз пән']}

🧠 Ұсыныс:
{row['AI']}

📚 Тапсырма:
{row['тапсырма']}

📅 Қатысу: {row['қатысу']}%

Құрметпен,
Мектеп әкімшілігі
"""

    st.subheader("📄 Дайын хабарлама")
    st.text_area("Хабар мәтіні", message, height=250)

    st.divider()

    # -------------------------------
    # 📋 QUICK STATUS
    # -------------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("Балл", round(row['орташа балл'],2))
    col2.metric("Қатысу", f"{row['қатысу']}%")
    col3.metric("Қауіп", "Иә" if row['орташа балл'] < 60 else "Жоқ")

    st.divider()

    # -------------------------------
    # 📥 КӨШІРУ / ЖҮКТЕУ
    # -------------------------------
    st.subheader("📥 Экспорт")

    st.download_button(
        label="📄 TXT ретінде жүктеу",
        data=message,
        file_name=f"{row['аты']}_message.txt"
    )

    st.code(message)

    st.divider()

    # -------------------------------
    # 🎯 AI ҰСЫНЫС
    # -------------------------------
    st.subheader("🧠 Қосымша кеңес")

    if row['орташа балл'] < 50:
        st.error("⚠️ Жедел араласу қажет (ата-ана + мұғалім)")
    elif row['орташа балл'] < 70:
        st.warning("📘 Қосымша дайындық ұсынылады")
    else:
        st.success("✅ Жақсы нәтиже")

# -------------------------------
# -------------------------------
# 🧾 PDF (PRO VERSION)
# -------------------------------
elif menu == "🧾 PDF":

    student = st.selectbox("Оқушы таңда", df['аты'])
    row = df[df['аты']==student].iloc[0]

    if st.button("📄 PDF жасау"):

        # -------------------------------
        # 📊 ГРАФИК ЖАСАУ
        # -------------------------------
        chart_path = "chart.png"

        plt.figure(figsize=(6,4))
        scores = [row[s] for s in subjects]
        plt.bar(subjects, scores, color='skyblue')
        plt.xticks(rotation=45)
        plt.title("Пәндер бойынша балл")
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()

        # -------------------------------
        # 📄 PDF ҚҰРУ
        # -------------------------------
        doc = SimpleDocTemplate("report.pdf", pagesize=letter)
        styles = getSampleStyleSheet()

        # Times New Roman стиль
        normal = ParagraphStyle(
            'TNR_Normal',
            parent=styles['Normal'],
            fontName='TNR',
            fontSize=12,
            leading=14
        )

        title = ParagraphStyle(
            'TNR_Title',
            parent=styles['Normal'],
            fontName='TNR',
            fontSize=18,
            spaceAfter=10
        )

        content = []

        # -------------------------------
        # 🏫 ТАҚЫРЫП
        # -------------------------------
        content.append(Paragraph("ОҚУШЫ ЕСЕБІ", title))
        content.append(Spacer(1,10))

        # -------------------------------
        # 👤 НЕГІЗГІ МӘЛІМЕТ
        # -------------------------------
        content.append(Paragraph(f"Аты: {row['аты']}", normal))
        content.append(Paragraph(f"Орташа балл: {round(row['орташа балл'],2)}", normal))
        content.append(Paragraph(f"Әлсіз пән: {row['ең әлсіз пән']}", normal))
        content.append(Paragraph(f"Қатысу: {row['қатысу']}%", normal))

        content.append(Spacer(1,12))

        # -------------------------------
        # 🧠 AI ҰСЫНЫС
        # -------------------------------
        content.append(Paragraph("ҰСЫНЫС:", title))
        content.append(Paragraph(row['AI'], normal))
        content.append(Paragraph(f"Тапсырма: {row['тапсырма']}", normal))

        content.append(Spacer(1,15))

        # -------------------------------
        # 📊 КЕСТЕ
        # -------------------------------
        table_data = [["Пән", "Балл"]]

        for s in subjects:
            table_data.append([s, str(row[s])])

        table = Table(table_data)

        content.append(Paragraph("Бағалар:", title))
        content.append(table)

        content.append(Spacer(1,15))

        # -------------------------------
        # 📈 ГРАФИК ҚОСУ
        # -------------------------------
        content.append(Paragraph("График:", title))
        content.append(Image(chart_path, width=400, height=250))

        # -------------------------------
        # PDF ҚҰРУ
        # -------------------------------
        doc.build(content)

        # -------------------------------
        # 📥 ЖҮКТЕУ
        # -------------------------------
        with open("report.pdf","rb") as f:
            st.download_button(
                "📥 PDF жүктеу",
                f,
                file_name=f"{row['аты']}_report.pdf",
                mime="application/pdf"
            )
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
