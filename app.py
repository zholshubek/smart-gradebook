import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import streamlit.components.v1 as components


from sklearn.ensemble import RandomForestClassifier
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('DejaVu', './DejaVuSans.ttf'))

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

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
    "Журнал",
    "Аналитика",
    "Болжау",
    "Профиль",
    "Хабар",
    "PDF",
    "Рейтинг"
])

st.markdown(f"### 📍 Қазіргі бөлім: {menu}")  # debug

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
# Журнал
# -------------------------------
if menu == "Журнал":

    st.title("📊 Журнал")

    # -------------------------------
    # 🔍 ФИЛЬТР
    # -------------------------------
    selected_student = st.selectbox("Оқушы таңда", ["Барлығы"] + list(df['аты']))

    if selected_student != "Барлығы":
        filtered_df = df[df['аты'] == selected_student]
    else:
        filtered_df = df

    # -------------------------------
    # 📊 ГРАФИК
    # -------------------------------
    st.subheader("📊 Орташа балл графигі")

    fig, ax = plt.subplots(figsize=(10,4))
    sns.barplot(x='аты', y='орташа балл', data=filtered_df, ax=ax)

    plt.xticks(rotation=45)

    # мән жазу
    for i, v in enumerate(filtered_df['орташа балл']):
        ax.text(i, v+1, str(round(v,1)), ha='center')

    st.pyplot(fig)

    # -------------------------------
    # 🎨 ТҮСПЕН TABLE
    # -------------------------------
    st.subheader("📋 Оқушылар кестесі")

    def highlight(row):
        if row['орташа балл'] >= 80:
            return ['background-color: #16a34a; color:white']*len(row)
        elif row['орташа балл'] < 50:
            return ['background-color: #dc2626; color:white']*len(row)
        else:
            return ['']*len(row)

    st.dataframe(filtered_df.style.apply(highlight, axis=1))


# -------------------------------
# ANALYTICS
# -------------------------------
elif menu == "Аналитика":

    st.title("📊 Аналитика панелі")

    # -------------------------------
    # 📊 KPI
    # -------------------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
    <div class="kpi-card">
    <div class="kpi-title">📈 Орташа балл</div>
    <div class="kpi-value">{round(df['орташа балл'].mean(),2)}</div>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">⚠️ Қауіпті</div>
    <div class="kpi-value">{df['қауіп'].sum()}</div>
</div>
""", unsafe_allow_html=True)

    col3.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">🏆 Үздік</div>
    <div class="kpi-value">{len(df[df['орташа балл']>80])}</div>
</div>
""", unsafe_allow_html=True)

    col4.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">📉 Әлсіз пән</div>
    <div class="kpi-value">{df['ең әлсіз пән'].value_counts().idxmax()}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # -------------------------------
    # 🔍 ФИЛЬТР
    # -------------------------------
    selected = st.selectbox("👤 Оқушы таңда", ["Барлығы"] + list(df['аты']))

    if selected != "Барлығы":
        data = df[df['аты'] == selected]
    else:
        data = df

    # -------------------------------
    # 📊 1. BAR CHART
    # -------------------------------
    st.subheader("📊 Орташа балл")

    fig1, ax1 = plt.subplots(figsize=(10,4))
    sns.barplot(x='аты', y='орташа балл', data=data, ax=ax1)

    plt.xticks(rotation=45)

    for i, v in enumerate(data['орташа балл']):
        ax1.text(i, v+1, str(round(v,1)), ha='center')

    st.pyplot(fig1)

    st.divider()

    # -------------------------------
    # 📈 2. ПРОГРЕСС
    # -------------------------------
    st.subheader("📈 Прогресс")

    fig2, ax2 = plt.subplots(figsize=(10,4))
    ax2.plot(data['аты'], data['орташа балл'], label="Қазір", marker='o')
    ax2.plot(data['аты'], data['өткен'], label="Өткен", marker='o')

    plt.legend()
    plt.xticks(rotation=45)

    st.pyplot(fig2)

    st.divider()

    # -------------------------------
    # 📉 3. HISTOGRAM
    # -------------------------------
    st.subheader("📉 Балл таралуы")

    fig3, ax3 = plt.subplots()
    sns.histplot(df['орташа балл'], bins=5, kde=True, ax=ax3)

    st.pyplot(fig3)

    st.divider()

    # -------------------------------
    # 📊 4. CORRELATION HEATMAP
    # -------------------------------
    st.subheader("📊 Пәндер байланысы")

    fig4, ax4 = plt.subplots()
    sns.heatmap(df[subjects].corr(), annot=True, cmap='coolwarm', ax=ax4)

    st.pyplot(fig4)

    st.divider()

    # -------------------------------
    # 📊 5. PIE CHART
    # -------------------------------
    st.subheader("🎯 Деңгей бойынша")

    def level(x):
        if x >= 80:
            return "Үздік"
        elif x >= 60:
            return "Орташа"
        else:
            return "Қауіпті"

    df['деңгей'] = df['орташа балл'].apply(level)

    level_counts = df['деңгей'].value_counts()

    fig5, ax5 = plt.subplots()
    ax5.pie(level_counts, labels=level_counts.index, autopct='%1.1f%%')

    st.pyplot(fig5)

    st.divider()

    # -------------------------------
    # 🏆 6. ТОП / ӘЛСІЗ
    # -------------------------------
    col1, col2 = st.columns(2)

    top = df.nlargest(3, 'орташа балл')
    weak = df.nsmallest(3, 'орташа балл')

    col1.subheader("🏆 ТОП 3")
    col1.dataframe(top[['аты','орташа балл']])

    col2.subheader("⚠️ Әлсіз 3")
    col2.dataframe(weak[['аты','орташа балл']])

# -------------------------------
# PREDICTION
# -------------------------------
elif menu == "Болжау":

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

    st.divider()

    # -------------------------------
    # 📊 ВИЗУАЛ
    # -------------------------------
    st.subheader("📊 Қазіргі деңгей")

    fig, ax = plt.subplots()
    bars = ax.bar(subjects, input_data[:5])

    colors = ['green' if x>70 else 'orange' if x>50 else 'red' for x in input_data[:5]]
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.divider()

    # -------------------------------
    # 🔍 НЕГІЗГІ БОЛЖАУ
    # -------------------------------
    if st.button("🔍 Болжау"):

        pred = model.predict([input_data])[0]
        prob = model.predict_proba([input_data])[0]

        st.subheader("🎯 Нәтиже")

        if pred == 1:
            st.error("⚠️ Қауіпті")
        else:
            st.success("✅ Қауіпсіз")

        st.metric("Қауіп ықтималдығы", f"{round(prob[1]*100,1)} %")

        # -------------------------------
        # 🤖 АВТО ҰСЫНЫС
        # -------------------------------
        st.subheader("🤖 Автоматты ұсыныс")

        weakest = subjects[np.argmin(input_data[:5])]
        avg = np.mean(input_data[:5])

        if avg < 50:
            st.error(f"""
🔴 Негізгі проблема: {weakest}

Ұсыныс:
- Күнделікті оқу жоспары
- Жеке мұғалім
- Ата-анамен байланыс
""")

        elif avg < 70:
            st.warning(f"""
🟡 Әлсіз пән: {weakest}

Ұсыныс:
- Аптасына 2 рет қосымша сабақ
- Практика
""")

        else:
            st.success("""
🟢 Жақсы деңгей

Ұсыныс:
- Қосымша олимпиада
- Тереңдетілген оқу
""")

    st.divider()

    # -------------------------------
    # 📈 СИМУЛЯЦИЯ
    # -------------------------------
    st.subheader("📈 Егер балл өссе не болады?")

    increase = st.slider("📊 Балл өсімі (%)", 0, 30, 10)

    new_scores = [x + (x * increase / 100) for x in input_data[:5]]

    sim_input = new_scores + [att]

    sim_pred = model.predict([sim_input])[0]
    sim_prob = model.predict_proba([sim_input])[0]

    col1, col2 = st.columns(2)

    with col1:
        st.write("🔵 Қазіргі жағдай")
        current_prob = model.predict_proba([input_data])[0]
        st.metric("Қауіп", f"{round(current_prob[1]*100,1)}%")

    with col2:
        st.write("🟢 Жаңа жағдай")
        st.metric("Қауіп", f"{round(sim_prob[1]*100,1)}%")

    # -------------------------------
    # 📊 СИМУЛЯЦИЯ ГРАФИК
    # -------------------------------
    fig2, ax2 = plt.subplots()

    ax2.plot(subjects, input_data[:5], label="Қазіргі", marker='o')
    ax2.plot(subjects, new_scores, label="Жаңа", marker='o')

    plt.xticks(rotation=45)
    plt.legend()

    st.pyplot(fig2)

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

    st.title("🧾 PDF есеп (FINAL DESIGN)")

    student = st.selectbox("Оқушы таңда", df['аты'])
    row = df[df['аты']==student].iloc[0]

    if st.button("📄 PDF жасау"):

        # 📊 график
        chart1 = "chart1.png"
        plt.figure(figsize=(6,4))
        scores = [row[s] for s in subjects]
        plt.bar(subjects, scores, color='#4CAF50')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(chart1)
        plt.close()

        # 📈 прогресс
        chart2 = "chart2.png"
        plt.figure(figsize=(6,4))
        plt.plot(["Өткен","Қазір"], [row['өткен'], row['орташа балл']], marker='o')
        plt.grid()
        plt.tight_layout()
        plt.savefig(chart2)
        plt.close()

        # PDF
        doc = SimpleDocTemplate("report.pdf")
        styles = getSampleStyleSheet()

        title = ParagraphStyle(
            'title',
            fontName='DejaVu',
            fontSize=18,
            textColor=colors.darkblue,
            alignment=1,
            spaceAfter=10
        )

        header = ParagraphStyle(
            'header',
            fontName='DejaVu',
            fontSize=14,
            spaceAfter=6
        )

        normal = ParagraphStyle(
            'normal',
            fontName='DejaVu',
            fontSize=11,
            leading=14
        )

        content = []

        # HEADER
        content.append(Paragraph("SMART SCHOOL SYSTEM", title))
        content.append(Paragraph("ОҚУШЫ ЕСЕБІ", title))
        content.append(Spacer(1,15))

        # INFO
        content.append(Paragraph(f"Аты: {row['аты']}", normal))
        content.append(Paragraph(f"Орташа балл: {round(row['орташа балл'],2)}", normal))
        content.append(Spacer(1,10))

        # KPI
        avg = round(df['орташа балл'].mean(),2)
        danger = df['қауіп'].sum()

        kpi_data = [
            ["Көрсеткіш","Мәні"],
            ["Орташа", str(avg)],
            ["Қауіпті", str(danger)]
        ]

        kpi_table = Table(kpi_data)
        kpi_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'DejaVu'),  # 🔥 ЕҢ МАҢЫЗДЫ
            ('BACKGROUND',(0,0),(-1,0),colors.green),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),1,colors.black),
            ('ALIGN',(0,0),(-1,-1),'CENTER')
        ]))

        content.append(Paragraph("KPI", header))
        content.append(kpi_table)
        content.append(Spacer(1,15))

        # AI
        content.append(Paragraph("Ұсыныс", header))
        content.append(Paragraph(row['AI'], normal))
        content.append(Spacer(1,15))

        # TABLE
        table_data = [["Пән","Балл"]]
        for s in subjects:
            table_data.append([s, str(row[s])])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'DejaVu'),   # 🔥 ОСЫ ЕҢ МАҢЫЗДЫ
            ('BACKGROUND',(0,0),(-1,0),colors.darkblue),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),1,colors.black),
            ('ALIGN',(0,0),(-1,-1),'CENTER')
        ]))

        content.append(Paragraph("Бағалар", header))
        content.append(table)
        content.append(Spacer(1,15))

        # CHART 1
        content.append(Paragraph("Пәндер", header))
        content.append(Image(chart1, width=400, height=250))

        content.append(Spacer(1,15))

        # CHART 2
        content.append(Paragraph("Прогресс", header))
        content.append(Image(chart2, width=400, height=250))

        doc.build(content)

        with open("report.pdf","rb") as f:
            pdf_bytes = f.read()

        st.download_button("📥 PDF жүктеу", pdf_bytes, file_name="report.pdf")
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
