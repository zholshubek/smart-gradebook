import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="Smart School Portal", layout="wide")

# -------------------------------
# FONT (Times New Roman)
# -------------------------------
pdfmetrics.registerFont(TTFont('TNR', 'TimesNewRoman.ttf'))

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
df['қауіп'] = np.where((df['орташа балл'] < 60) | (df['қатысу'] < 60), 1, 0)
# -------------------------------
# PROGRESS (міндетті)
# -------------------------------
if 'өткен' not in df.columns:
    df['өткен'] = df['орташа балл'] - np.random.randint(0,10,len(df))
def weak(row):
    low = row[subjects][row[subjects] < 50]
    return low.idxmin() if len(low)>0 else "Жоқ"

df['ең әлсіз пән'] = df.apply(weak, axis=1)

# AI
def ai(row):
    if row['орташа балл'] < 50:
        return f"{row['аты']} әлсіз. {row['ең әлсіз пән']} пәні қиын."
    elif row['орташа балл'] < 70:
        return f"{row['аты']} орташа деңгейде."
    else:
        return f"{row['аты']} жақсы оқиды."

df['AI'] = df.apply(ai, axis=1)

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

    st.title("📊 Толық аналитика панелі")

    # -------------------------------
    # 📊 KPI
    # -------------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("📈 Орташа балл", round(df['орташа балл'].mean(),2))
    col2.metric("⚠️ Қауіпті оқушылар", df['қауіп'].sum())
    col3.metric("🏆 Үздік оқушылар", len(df[df['орташа балл']>80]))

    st.divider()

    # -------------------------------
    # 📊 1. Орташа балл (Bar Chart)
    # -------------------------------
    col1, col2 = st.columns(2)

    fig1, ax1 = plt.subplots(figsize=(6,4))
    sns.barplot(x='аты', y='орташа балл', data=df, palette='viridis', ax=ax1)
    ax1.set_title("Орташа балл")
    plt.xticks(rotation=45)
    col1.pyplot(fig1)

    # -------------------------------
    # 📊 2. Қатысу vs Балл
    # -------------------------------
    fig2, ax2 = plt.subplots(figsize=(6,4))
    sns.scatterplot(x='қатысу', y='орташа балл', hue='қауіп', data=df, ax=ax2)
    ax2.set_title("Қатысу vs Балл")
    col2.pyplot(fig2)

    st.divider()

    # -------------------------------
    # 📉 3. Балл таралуы (Histogram)
    # -------------------------------
    col1, col2 = st.columns(2)

    fig3, ax3 = plt.subplots()
    sns.histplot(df['орташа балл'], bins=5, kde=True, ax=ax3)
    ax3.set_title("Балл таралуы")
    col1.pyplot(fig3)

    # -------------------------------
    # 📊 4. Boxplot (пәндер)
    # -------------------------------
    fig4, ax4 = plt.subplots()
    sns.boxplot(data=df[subjects], ax=ax4)
    ax4.set_title("Пәндер таралуы")
    col2.pyplot(fig4)

    st.divider()

    # -------------------------------
    # 📊 5. Әлсіз пәндер
    # -------------------------------
    col1, col2 = st.columns(2)

    weak_counts = df['ең әлсіз пән'].value_counts()

    fig5, ax5 = plt.subplots()
    weak_counts.plot(kind='bar', ax=ax5)
    ax5.set_title("Ең әлсіз пәндер")
    col1.pyplot(fig5)

    # -------------------------------
    # 📊 6. Корреляция
    # -------------------------------
    fig6, ax6 = plt.subplots()
    sns.heatmap(df[subjects].corr(), annot=True, cmap='coolwarm', ax=ax6)
    ax6.set_title("Пәндер байланысы")
    col2.pyplot(fig6)

    st.divider()

    # -------------------------------
    # 🏆 7. ТОП / Әлсіз
    # -------------------------------
    col1, col2 = st.columns(2)

    top = df.nlargest(3, 'орташа балл')
    weak = df.nsmallest(3, 'орташа балл')

    col1.write("🏆 ТОП 3 оқушы")
    col1.dataframe(top[['аты','орташа балл']])

    col2.write("⚠️ Әлсіз 3 оқушы")
    col2.dataframe(weak[['аты','орташа балл']])

    st.divider()

    # -------------------------------
    # 📈 8. Прогресс
    # -------------------------------
    fig7, ax7 = plt.subplots()
    ax7.plot(df['аты'], df['орташа балл'], label="Қазір")
    ax7.plot(df['аты'], df['өткен'], label="Өткен")
    plt.xticks(rotation=45)
    plt.legend()
    ax7.set_title("Прогресс")
    st.pyplot(fig7)

    st.divider()

    # -------------------------------
    # 🧠 9. AI қорытынды
    # -------------------------------
    st.subheader("🧠 Аналитикалық қорытынды")

    avg = df['орташа балл'].mean()
    weak_sub = df['ең әлсіз пән'].value_counts().idxmax()

    st.info(f"""
📊 Сыныптың орташа баллы: {round(avg,2)}  
⚠️ Ең әлсіз пән: {weak_sub}  
📈 Жалпы деңгей: {"Жоғары" if avg>70 else "Орташа" if avg>50 else "Төмен"}
""")

# -------------------------------
# PREDICTION
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
# MESSAGE
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
# PDF (TIMES NEW ROMAN)
# -------------------------------
elif menu == "🧾 PDF":

    student = st.selectbox("Оқушы таңда", df['аты'])
    row = df[df['аты']==student].iloc[0]

    if st.button("📄 PDF жасау"):

        # график
        plt.figure()
        scores = [row[s] for s in subjects]
        plt.bar(subjects, scores)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("chart.png")
        plt.close()

        doc = SimpleDocTemplate("report.pdf", pagesize=letter)
        styles = getSampleStyleSheet()

        normal = ParagraphStyle(
            'TNR_Normal',
            parent=styles['Normal'],
            fontName='TNR',
            fontSize=12
        )

        title = ParagraphStyle(
            'TNR_Title',
            parent=styles['Normal'],
            fontName='TNR',
            fontSize=16
        )

        content = []
        content.append(Paragraph("ОҚУШЫ ЕСЕБІ", title))
        content.append(Spacer(1,12))

        content.append(Paragraph(f"Аты: {row['аты']}", normal))
        content.append(Paragraph(f"Орташа балл: {round(row['орташа балл'],2)}", normal))
        content.append(Paragraph(f"AI кеңес: {row['AI']}", normal))
        content.append(Spacer(1,20))

        content.append(Image("chart.png", width=400, height=250))

        doc.build(content)

        with open("report.pdf","rb") as f:
            st.download_button(
                "📥 PDF жүктеу",
                f,
                file_name=f"{row['аты']}_report.pdf",
                mime="application/pdf"
            )

# -------------------------------
# RATING
# -------------------------------
elif menu == "🏆 Рейтинг":

    st.title("🏆 Оқушылар рейтингі")

    # -------------------------------
    # 📊 СОРТТАУ
    # -------------------------------
    df_sorted = df.sort_values(by='орташа балл', ascending=False).reset_index(drop=True)

    # Рейтинг номер қосу
    df_sorted['Рейтинг'] = df_sorted.index + 1

    # -------------------------------
    # 🥇 ТОП 3 CARD
    # -------------------------------
    st.subheader("🥇 ТОП 3 оқушы")

    top3 = df_sorted.head(3)
    col1, col2, col3 = st.columns(3)

    medals = ["🥇", "🥈", "🥉"]

    for i, col in enumerate([col1, col2, col3]):
        with col:
            st.markdown(f"### {medals[i]} {top3.iloc[i]['аты']}")
            st.success(f"Балл: {round(top3.iloc[i]['орташа балл'],2)}")

    st.divider()

    # -------------------------------
    # 📋 ТОЛЫҚ РЕЙТИНГ КЕСТЕ
    # -------------------------------
    st.subheader("📋 Толық рейтинг")

    st.dataframe(df_sorted[['Рейтинг','аты','орташа балл']])

    st.divider()

    # -------------------------------
    # 📊 ГРАФИК (әдемі)
    # -------------------------------
    fig, ax = plt.subplots(figsize=(12,6))

    colors = ['green' if x>80 else 'orange' if x>60 else 'red' for x in df_sorted['орташа балл']]

    ax.bar(df_sorted['аты'], df_sorted['орташа балл'], color=colors)

    ax.set_title("Оқушылар рейтингі")
    plt.xticks(rotation=45)

    # мән жазу
    for i, v in enumerate(df_sorted['орташа балл']):
        ax.text(i, v + 1, str(round(v,1)), ha='center')

    st.pyplot(fig)

    st.divider()

    # -------------------------------
    # 🎯 ДЕҢГЕЙГЕ БӨЛУ
    # -------------------------------
    st.subheader("🎯 Оқушылар деңгейі")

    def level(score):
        if score >= 80:
            return "🟢 Үздік"
        elif score >= 60:
            return "🟡 Орташа"
        else:
            return "🔴 Қауіпті"

    df_sorted['Деңгей'] = df_sorted['орташа балл'].apply(level)

    st.dataframe(df_sorted[['аты','орташа балл','Деңгей']])

    st.divider()

    # -------------------------------
    # 📊 PIE CHART
    # -------------------------------
    level_counts = df_sorted['Деңгей'].value_counts()

    fig2, ax2 = plt.subplots()
    ax2.pie(level_counts, labels=level_counts.index, autopct='%1.1f%%')
    ax2.set_title("Деңгей бойынша бөлу")

    st.pyplot(fig2)
