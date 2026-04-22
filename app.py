import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

# PDF үшін импорттар
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# sklearn импорттары
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score   # <--- ҚОСЫЛДЫ

# Шрифтті тіркеу
try:
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    FONT_AVAILABLE = True
except:
    FONT_AVAILABLE = False

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="Smart School Portal", layout="wide")

st.markdown("""
<style>
.kpi-card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    padding: 20px;
    border-radius: 15px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.kpi-title { font-size: 14px; opacity: 0.7; }
.kpi-value { font-size: 28px; font-weight: bold; }
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
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Логин")
        p = st.text_input("Құпия сөз", type="password")
        if st.button("Кіру", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state.login = True
                st.rerun()
            else:
                st.error("Қате логин немесе құпия сөз!")
    st.stop()

if st.sidebar.button("🚪 Шығу", use_container_width=True):
    st.session_state.login = False
    st.rerun()

# -------------------------------
# MENU
# -------------------------------
st.sidebar.title("📚 Smart School Portal")
menu = st.sidebar.radio(
    "Бөлімдер:", 
    ["🏠 Журнал", "📊 Аналитика", "🧠 Болжау", "👤 Профиль", "📲 Хабар", "🧾 PDF", "🏆 Рейтинг"],
    index=0
)

# -------------------------------
# DATA
# -------------------------------
uploaded = st.sidebar.file_uploader("📂 Excel файл жүктеу", type=["xlsx"])

def load_data():
    if uploaded is not None:
        df = pd.read_excel(uploaded)
        required = ['аты', 'математика', 'физика', 'информатика', 'қазақ тілі', 'ағылшын тілі', 'қатысу']
        missing = [c for c in required if c not in df.columns]
        if missing:
            st.error(f"Келесі бағандар жоқ: {missing}")
            st.stop()
        return df
    else:
        return pd.DataFrame({
            'аты': ['Асан', 'Айгүл', 'Нұрсұлтан', 'Динара', 'Ержан', 'Мадина', 'Самат', 'Аружан'],
            'математика': [80, 50, 40, 90, 65, 30, 85, 55],
            'физика': [70, 55, 45, 95, 60, 35, 88, 50],
            'информатика': [85, 60, 50, 92, 70, 40, 90, 65],
            'қазақ тілі': [75, 58, 48, 88, 68, 45, 86, 60],
            'ағылшын тілі': [78, 52, 46, 91, 66, 38, 87, 58],
            'қатысу': [90, 60, 50, 95, 70, 40, 92, 65]
        })

df = load_data()
subjects = ['математика', 'физика', 'информатика', 'қазақ тілі', 'ағылшын тілі']

# -------------------------------
# PROCESSING
# -------------------------------
df['орташа балл'] = df[subjects].mean(axis=1)
df['өткен'] = df['орташа балл'] - np.random.randint(5, 15, len(df))
df['өткен'] = df['өткен'].clip(0, 100)
df['қауіп'] = np.where((df['орташа балл'] < 60) | (df['қатысу'] < 60), 1, 0)

def find_weak_subject(row):
    scores = {s: row[s] for s in subjects}
    return min(scores, key=scores.get)

df['ең әлсіз пән'] = df.apply(find_weak_subject, axis=1)

def generate_ai_recommendation(row):
    if row['орташа балл'] < 50:
        return f"⚠️ {row['аты']} оқушысының үлгерімі өте төмен. {row['ең әлсіз пән']} пәніне ерекше назар аудару қажет. Ата-анамен байланысып, қосымша сабақ ұйымдастыру керек."
    elif row['орташа балл'] < 70:
        return f"📘 {row['аты']} оқушысы орташа деңгейде. {row['ең әлсіз пән']} пәнін жақсарту қажет. Күнделікті 30 минут қосымша жұмыс ұсынылады."
    else:
        return f"🎉 {row['аты']} оқушысы жақсы нәтиже көрсетіп отыр. Жетістігін сақтау үшін осылай жалғастыра берсін!"

df['AI'] = df.apply(generate_ai_recommendation, axis=1)
df['тапсырма'] = df['ең әлсіз пән'] + " пәнінен 10 есеп шығару"
df['хабар'] = df['аты'] + "\n" + df['AI']

# -------------------------------
# ML MODELS
# -------------------------------
X = df[subjects + ['қатысу']]
y = df['қауіп']

models = {
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
}

trained_models = {}
for name, model in models.items():
    model.fit(X, y)
    trained_models[name] = model

model = trained_models['Random Forest']

# ===============================
# 1. ЖУРНАЛ
# ===============================
if menu == "🏠 Журнал":
    st.title("📊 Оқушылар журналы")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_student = st.selectbox("Оқушы таңда", ["Барлығы"] + list(df['аты']))
    
    filtered_df = df if selected_student == "Барлығы" else df[df['аты'] == selected_student]
    
    st.subheader("📊 Орташа балл диаграммасы")
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(filtered_df['аты'], filtered_df['орташа балл'], color='#4CAF50')
    ax.axhline(y=60, color='red', linestyle='--', label='Қауіп шегі (60)')
    ax.axhline(y=80, color='green', linestyle='--', label='Үздік шегі (80)')
    ax.set_ylim(0, 100)
    ax.set_ylabel("Балл")
    ax.set_title("Оқушылардың орташа балы")
    ax.legend()
    for bar, val in zip(bars, filtered_df['орташа балл']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}', ha='center', va='bottom', fontsize=10)
    plt.xticks(rotation=45)
    st.pyplot(fig)
    
    st.subheader("📋 Оқушылар тізімі")
    def highlight_row(row):
        if row['орташа балл'] >= 80:
            return ['background-color: #166534; color: white'] * len(row)
        elif row['орташа балл'] < 60:
            return ['background-color: #991b1b; color: white'] * len(row)
        return [''] * len(row)
    
    display_df = filtered_df[['аты', 'математика', 'физика', 'информатика', 'қазақ тілі', 'ағылшын тілі', 'орташа балл', 'қатысу', 'қауіп']]
    st.dataframe(display_df.style.apply(highlight_row, axis=1), use_container_width=True)

# ===============================
# 2. АНАЛИТИКА (ТҮЗЕТІЛГЕН)
# ===============================
elif menu == "📊 Аналитика":
    st.title("📊 Аналитика панелі")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>📈 Орташа балл</div><div class='kpi-value'>{df['орташа балл'].mean():.1f}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>⚠️ Қауіпті оқушылар</div><div class='kpi-value'>{df['қауіп'].sum()}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🏆 Үздік оқушылар</div><div class='kpi-value'>{len(df[df['орташа балл'] >= 80])}</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>📚 Ең әлсіз пән</div><div class='kpi-value'>{df['ең әлсіз пән'].mode()[0]}</div></div>", unsafe_allow_html=True)
    
    st.divider()
    selected = st.selectbox("👤 Оқушыны фильтрлеу", ["Барлығы"] + list(df['аты']))
    data = df if selected == "Барлығы" else df[df['аты'] == selected]
    
    st.subheader("📊 Орташа балл (бағандық диаграмма)")
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    colors_bar = ['#4CAF50' if x >= 80 else '#FFC107' if x >= 60 else '#F44336' for x in data['орташа балл']]
    bars = ax1.bar(data['аты'], data['орташа балл'], color=colors_bar)
    ax1.axhline(y=60, color='red', linestyle='--', alpha=0.7)
    ax1.set_ylim(0, 100)
    for bar, val in zip(bars, data['орташа балл']):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}', ha='center', fontsize=9)
    plt.xticks(rotation=45)
    st.pyplot(fig1)
    
    st.subheader("📈 Прогресс (өткен vs қазір)")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    x_pos = range(len(data))
    width = 0.35
    ax2.bar([x - width/2 for x in x_pos], data['өткен'], width, label='Өткен', color='#FF9800')
    ax2.bar([x + width/2 for x in x_pos], data['орташа балл'], width, label='Қазір', color='#4CAF50')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(data['аты'], rotation=45)
    ax2.legend()
    st.pyplot(fig2)
    
    st.subheader("📉 Балл таралуы (гистограмма)")
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    sns.histplot(df['орташа балл'], bins=8, kde=True, color='#2196F3', ax=ax3)
    ax3.axvline(x=60, color='red', linestyle='--', label='Қауіп шегі')
    ax3.axvline(x=80, color='green', linestyle='--', label='Үздік шегі')
    ax3.legend()
    st.pyplot(fig3)
    
    st.subheader("📊 Пәндер арасындағы байланыс (корреляция)")
    fig4, ax4 = plt.subplots(figsize=(8, 6))
    sns.heatmap(df[subjects].corr(), annot=True, cmap='coolwarm', center=0, ax=ax4)
    st.pyplot(fig4)
    
    st.subheader("🎯 Оқушылар деңгейі бойынша бөлініс")
    def get_level(score):
        if score >= 80: return "Үздік (80+)"
        elif score >= 60: return "Орташа (60-79)"
        else: return "Қауіпті (60-тан төмен)"
    df['деңгей'] = df['орташа балл'].apply(get_level)
    level_counts = df['деңгей'].value_counts()
    fig5, ax5 = plt.subplots()
    colors_pie = ['#4CAF50', '#FFC107', '#F44336']
    ax5.pie(level_counts, labels=level_counts.index, autopct='%1.1f%%', colors=colors_pie, startangle=90)
    ax5.set_title("Деңгей бойынша бөлініс")
    st.pyplot(fig5)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🏆 ТОП 3 оқушы")
        top3 = df.nlargest(3, 'орташа балл')[['аты', 'орташа балл']]
        st.dataframe(top3, use_container_width=True)
    with col_b:
        st.subheader("⚠️ Ең әлсіз 3 оқушы")
        bottom3 = df.nsmallest(3, 'орташа балл')[['аты', 'орташа балл']]
        st.dataframe(bottom3, use_container_width=True)
    
    with st.expander("🤖 ML Модельдерінің сапасы"):
        st.subheader("Модельдерді салыстыру")
        model_comparison = []
        for name, mdl in trained_models.items():
            try:
                cv_folds = min(3, len(X)-1)
                scores = cross_val_score(mdl, X, y, cv=cv_folds)
                model_comparison.append({
                    "Модель": name,
                    "Орташа дәлдік": f"{scores.mean()*100:.1f}%",
                    "Мин/Макс": f"{scores.min()*100:.1f}% / {scores.max()*100:.1f}%",
                    "Тұрақтылық": "🔴" if scores.std() > 0.15 else "🟡" if scores.std() > 0.08 else "🟢"
                })
            except:
                model_comparison.append({
                    "Модель": name,
                    "Орташа дәлдік": "❌ Есептеу мүмкін емес",
                    "Мин/Макс": "-",
                    "Тұрақтылық": "⚪"
                })
        st.dataframe(pd.DataFrame(model_comparison), use_container_width=True)
        best_model = None
        best_score = -1
        for name, mdl in trained_models.items():
            try:
                score = cross_val_score(mdl, X, y, cv=min(3, len(X)-1)).mean()
                if score > best_score:
                    best_score = score
                    best_model = name
            except:
                pass
        if best_model:
            st.success(f"🏆 **Ұсынылатын модель:** {best_model} - ең жоғары дәлдік көрсетті!")
        else:
            st.info("ℹ️ Модельдерді салыстыру мүмкін болмады. Деректер саны жеткіліксіз.")

# ===============================
# 3. БОЛЖАУ
# ===============================
elif menu == "🧠 Болжау":
    st.title("🧠 Ақылды болжау жүйесі")
    st.markdown("Оқушының бағаларын енгізіп, қауіп тобына кіретінін болжаңыз")
    
    st.subheader("🤖 Модельді таңдаңыз")
    model_choice = st.selectbox(
        "Қай модельді қолданғыңыз келеді?",
        options=['Random Forest', 'Logistic Regression', 'Gradient Boosting'],
        help="Әр модельдің өз артықшылықтары бар."
    )
    model_info = {
        'Random Forest': "🌲 Көптеген шешім ағаштарынан тұрады. Орташа дәлдік, жылдам жұмыс.",
        'Logistic Regression': "📈 Сызықтық теңдеу негізінде жұмыс істейді. Өте жылдам.",
        'Gradient Boosting': "🎯 Қателерді кезең-кезеңімен түзетеді. Ең дәл нәтиже."
    }
    st.info(model_info[model_choice])
    
    col1, col2 = st.columns(2)
    with col1:
        math = st.slider("📘 Математика", 0, 100, 65)
        physics = st.slider("🔬 Физика", 0, 100, 65)
        info = st.slider("💻 Информатика", 0, 100, 65)
    with col2:
        kazakh = st.slider("📖 Қазақ тілі", 0, 100, 65)
        english = st.slider("🌍 Ағылшын тілі", 0, 100, 65)
        attendance = st.slider("📅 Қатысу (%)", 0, 100, 75)
    
    input_data = [[math, physics, info, kazakh, english, attendance]]
    
    st.subheader("📊 Енгізілген мәліметтер")
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(subjects, [math, physics, info, kazakh, english])
    colors_bar = ['#4CAF50' if x >= 70 else '#FFC107' if x >= 50 else '#F44336' for x in [math, physics, info, kazakh, english]]
    for bar, color in zip(bars, colors_bar):
        bar.set_color(color)
    ax.axhline(y=60, color='red', linestyle='--', alpha=0.7)
    ax.set_ylim(0, 100)
    plt.xticks(rotation=45)
    st.pyplot(fig)
    
    if st.button("🔍 Болжау жасау", type="primary", use_container_width=True):
        selected_model = trained_models[model_choice]
        prediction = selected_model.predict(input_data)[0]
        probability = selected_model.predict_proba(input_data)[0]
        
        st.divider()
        st.subheader("🎯 Болжау нәтижесі")
        
        with st.expander("📊 Барлық модельдердің нәтижелерін салыстыру"):
            comparison_data = []
            for name, mdl in trained_models.items():
                pred = mdl.predict(input_data)[0]
                prob = mdl.predict_proba(input_data)[0][1] * 100
                result_emoji = "⚠️ Қауіпті" if pred == 1 else "✅ Қауіпсіз"
                comparison_data.append({
                    "Модель": name,
                    "Нәтиже": result_emoji,
                    "Қауіп ықтималдығы": f"{prob:.1f}%",
                    "Сенімділік деңгейі": "🔴 Жоғары" if prob > 70 else "🟡 Орташа" if prob > 30 else "🟢 Төмен"
                })
            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
            predictions = [mdl.predict(input_data)[0] for mdl in trained_models.values()]
            consensus = max(set(predictions), key=predictions.count)
            consensus_percent = (predictions.count(consensus) / len(predictions)) * 100
            if consensus == 1:
                st.warning(f"🤝 **Модельдер келісімі:** {consensus_percent:.0f}% модельдер 'Қауіпті' деп есептейді")
            else:
                st.success(f"🤝 **Модельдер келісімі:** {consensus_percent:.0f}% модельдер 'Қауіпсіз' деп есептейді")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if prediction == 1:
                st.error("⚠️ ҚАУІПТІ ТОБЫ")
                st.markdown("Бұл оқушы қауіп тобына жатады. Дереу шара қолдану қажет!")
            else:
                st.success("✅ ҚАУІПСІЗ ТОБЫ")
                st.markdown("Бұл оқушы қауіп тобына жатпайды.")
        with col_b:
            st.metric("📊 Таңдалған модель", model_choice)
            st.metric("⚠️ Қауіп ықтималдығы", f"{probability[1]*100:.1f}%")
            confidence = probability[1] if prediction == 1 else probability[0]
            if confidence > 0.7:
                st.progress(confidence, text="🔴 Жоғары сенімділік")
            elif confidence > 0.4:
                st.progress(confidence, text="🟡 Орташа сенімділік")
            else:
                st.progress(confidence, text="🟢 Төмен сенімділік")
        
        st.subheader("🤖 AI ұсынысы")
        avg_score = np.mean([math, physics, info, kazakh, english])
        weakest = subjects[np.argmin([math, physics, info, kazakh, english])]
        avg_risk = np.mean([mdl.predict_proba(input_data)[0][1] for mdl in trained_models.values()]) * 100
        
        if avg_score < 50:
            st.error(f"🔴 **Жедел араласу қажет!**\n\n- Әлсіз пән: **{weakest}**\n- Орташа балл: {avg_score:.1f}\n- Модельдердің орташа қауіп бағасы: {avg_risk:.1f}%\n\n**Ұсыныстар:**\n- Жеке мұғаліммен қосымша сабақ\n- Ата-анамен кездесу\n- Күнделікті оқу жоспары")
        elif avg_score < 70:
            st.warning(f"🟡 **Орташа деңгей, жақсарту қажет**\n\n- Әлсіз пән: **{weakest}**\n- Орташа балл: {avg_score:.1f}\n- Модельдердің орташа қауіп бағасы: {avg_risk:.1f}%\n\n**Ұсыныстар:**\n- {weakest} пәніне көбірек уақыт бөлу\n- Аптасына 2 рет қосымша сабақ")
        else:
            st.success(f"🟢 **Жақсы деңгей!**\n\n- Орташа балл: {avg_score:.1f}\n- Модельдердің орташа қауіп бағасы: {avg_risk:.1f}%\n\n**Ұсыныстар:**\n- Жетістігін сақтау\n- Олимпиадаға дайындалу")
        
        if avg_risk > 70 and avg_score >= 70:
            st.warning("⚠️ **Қызық жағдай:** Бағалары жақсы, бірақ модельдер қауіпті болжайды. Қатысуды тексеріңіз!")
        elif avg_risk < 30 and avg_score < 60:
            st.info("ℹ️ **Ескерту:** Бағалары төмен, бірақ модельдер қауіпсіз деп тұр. Бұл жағдайды қадағалаңыз.")

# ===============================
# ===============================
# 4. ПРОФИЛЬ (ТҮЗЕТІЛГЕН)
# ===============================
elif menu == "👤 Профиль":
    st.title("👤 Оқушы профилі")
    student = st.selectbox("Оқушы таңдаңыз", df['аты'])
    row = df[df['аты'] == student].iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("📈 Орташа балл", f"{row['орташа балл']:.1f}")
    with col2: st.metric("📅 Қатысу", f"{row['қатысу']}%")
    with col3: st.metric("⚠️ Қауіп тобы", "Иә" if row['қауіп'] == 1 else "Жоқ")
    with col4: st.metric("📚 Әлсіз пән", row['ең әлсіз пән'])
    st.divider()
    
    st.subheader("📊 Пәндер бойынша нәтиже")
    fig, ax = plt.subplots(figsize=(8, 4))
    scores = [row[s] for s in subjects]
    bars = ax.bar(subjects, scores)
    colors_bar = ['#4CAF50' if x >= 70 else '#FFC107' if x >= 50 else '#F44336' for x in scores]
    for bar, color in zip(bars, colors_bar):
        bar.set_color(color)
    ax.axhline(y=60, color='red', linestyle='--', alpha=0.7)
    ax.set_ylim(0, 100)
    for bar, val in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, str(val), ha='center', fontsize=10)
    plt.xticks(rotation=45)
    st.pyplot(fig)
    
    st.subheader("📈 Прогресс (өткен ай vs қазір)")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(['Өткен ай', 'Қазір'], [row['өткен'], row['орташа балл']], marker='o', linewidth=2, markersize=10)
    ax2.fill_between(['Өткен ай', 'Қазір'], [row['өткен'], row['орташа балл']], alpha=0.3)
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)
    
    st.subheader("🧠 AI талдау және ұсыныс")
    st.info(row['AI'])
    st.subheader("📚 Ұсынылған тапсырма")
    st.success(f"✅ {row['тапсырма']}")
    
    with st.expander("🔮 Осы оқушыға болжау жасау"):
        st.markdown("Барлық модельдердің осы оқушы туралы болжамы:")
        student_data = [[row[s] for s in subjects] + [row['қатысу']]]
        for name, mdl in trained_models.items():
            pred = mdl.predict(student_data)[0]
            prob = mdl.predict_proba(student_data)[0][1] * 100
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{name}**")
            with col2:
                if pred == 1:
                    st.error("⚠️ Қауіпті")
                else:
                    st.success("✅ Қауіпсіз")
            with col3:
                st.write(f"{prob:.1f}%")
    
    with st.expander("📋 Толық мәлімет"):
        st.dataframe(df[df['аты'] == student], use_container_width=True)
# ===============================
# 5. ХАБАР (толық нұсқа)
# ===============================
elif menu == "📲 Хабар":
    st.title("📲 Ата-анаға хабарлама")
    student = st.selectbox("Оқушы таңдаңыз", df['аты'])
    row = df[df['аты'] == student].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if row['орташа балл'] >= 80: st.success("🟢 Үздік деңгей")
        elif row['орташа балл'] >= 60: st.warning("🟡 Орташа деңгей")
        else: st.error("🔴 Қауіпті деңгей")
    with col2: st.metric("Орташа балл", f"{row['орташа балл']:.1f}")
    with col3: st.metric("Қатысу", f"{row['қатысу']}%")
    st.divider()
    
    message = f"""ҚҰРМЕТТІ АТА-АНА!

Сіздің балаңыз: {row['аты']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ОҚУ КӨРСЕТКІШТЕРІ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Орташа балл: {row['орташа балл']:.1f}
• Қатысу: {row['қатысу']}%
• Әлсіз пән: {row['ең әлсіз пән']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 AI ҰСЫНЫС
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{row['AI']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 ТАПСЫРМА
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{row['тапсырма']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 ПӘНДЕР БОЙЫНША БАҒАЛАР
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    for s in subjects:
        message += f"\n• {s}: {row[s]} балл"
    message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nҚұрметпен,\nМектеп әкімшілігі\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    st.text_area("Хабарлама мәтіні", message, height=400)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 TXT файл ретінде жүктеу", message, file_name=f"{student}_хабарлама.txt", use_container_width=True)
    with col2:
        st.markdown(f"📧 Жіберу үшін: `{student.lower()}@school.kz` (көшіріңіз)")

# ===============================
# 6. PDF (толық нұсқа)
# ===============================
elif menu == "🧾 PDF":
    st.title("🧾 PDF есеп шығару")
    student = st.selectbox("Оқушы таңдаңыз", df['аты'])
    row = df[df['аты'] == student].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Орташа балл", f"{row['орташа балл']:.1f}")
    with col2: st.metric("Қатысу", f"{row['қатысу']}%")
    with col3: st.metric("Әлсіз пән", row['ең әлсіз пән'])
    st.info(f"💡 {row['AI'][:100]}...")
    
    if st.button("📄 PDF жасау", type="primary", use_container_width=True):
        with st.spinner("PDF дайындалуда..."):
            # Графиктерді сақтау
            chart1_path = "chart1.png"
            plt.figure(figsize=(6, 4))
            scores = [row[s] for s in subjects]
            colors_bar = ['#4CAF50' if x >= 70 else '#FFC107' if x >= 50 else '#F44336' for x in scores]
            plt.bar(subjects, scores, color=colors_bar)
            plt.axhline(y=60, color='red', linestyle='--', alpha=0.7)
            plt.ylim(0, 100)
            plt.title("Пәндер бойынша балл")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(chart1_path)
            plt.close()
            
            chart2_path = "chart2.png"
            plt.figure(figsize=(6, 4))
            plt.plot(['Өткен ай', 'Қазір'], [row['өткен'], row['орташа балл']], marker='o', linewidth=2, markersize=8)
            plt.fill_between(['Өткен ай', 'Қазір'], [row['өткен'], row['орташа балл']], alpha=0.3)
            plt.ylim(0, 100)
            plt.title("Прогресс")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(chart2_path)
            plt.close()
            
            # PDF құру
            doc = SimpleDocTemplate("report.pdf", pagesize=letter)
            styles = getSampleStyleSheet()
            if FONT_AVAILABLE:
                title_style = ParagraphStyle('title', parent=styles['Normal'], fontName='DejaVu', fontSize=18, textColor=colors.darkblue, alignment=1, spaceAfter=10)
                header_style = ParagraphStyle('header', parent=styles['Normal'], fontName='DejaVu', fontSize=14, spaceAfter=6)
                normal_style = ParagraphStyle('normal', parent=styles['Normal'], fontName='DejaVu', fontSize=11, leading=14)
            else:
                title_style = styles['Title']
                header_style = styles['Heading1']
                normal_style = styles['Normal']
            
            content = []
            content.append(Paragraph("SMART SCHOOL SYSTEM", title_style))
            content.append(Paragraph("ОҚУШЫ ЕСЕБІ", title_style))
            content.append(Spacer(1, 15))
            content.append(Paragraph(f"Аты: {row['аты']}", normal_style))
            content.append(Paragraph(f"Орташа балл: {row['орташа балл']:.1f}", normal_style))
            content.append(Paragraph(f"Қатысу: {row['қатысу']}%", normal_style))
            content.append(Spacer(1, 10))
            content.append(Paragraph("🧠 AI ҰСЫНЫСЫ", header_style))
            content.append(Paragraph(row['AI'], normal_style))
            content.append(Paragraph(f"Тапсырма: {row['тапсырма']}", normal_style))
            content.append(Spacer(1, 15))
            
            table_data = [["Пән", "Балл", "Деңгей"]]
            for s in subjects:
                score = row[s]
                level = "✅ Жақсы" if score >= 70 else "⚠️ Орташа" if score >= 50 else "❌ Әлсіз"
                table_data.append([s, str(score), level])
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            content.append(Paragraph("📋 Бағалар кестесі", header_style))
            content.append(table)
            content.append(Spacer(1, 15))
            content.append(Paragraph("📊 Пәндер графигі", header_style))
            content.append(Image(chart1_path, width=400, height=250))
            content.append(Spacer(1, 15))
            content.append(Paragraph("📈 Прогресс графигі", header_style))
            content.append(Image(chart2_path, width=400, height=250))
            doc.build(content)
        
        with open("report.pdf", "rb") as f:
            pdf_bytes = f.read()
        st.success("✅ PDF сәтті құрылды!")
        st.download_button("📥 PDF жүктеу", pdf_bytes, file_name=f"{student}_есеп.pdf", use_container_width=True)

# ===============================
# 7. РЕЙТИНГ (толық нұсқа)
# ===============================
elif menu == "🏆 Рейтинг":
    st.title("🏆 Оқушылар рейтингі")
    df_sorted = df.sort_values('орташа балл', ascending=False).reset_index(drop=True)
    df_sorted['Рейтинг'] = df_sorted.index + 1
    
    st.subheader("🥇 Жүлдегерлер")
    col1, col2, col3 = st.columns(3)
    medals = ["🥇", "🥈", "🥉"]
    colors_medal = ["#FFD700", "#C0C0C0", "#CD7F32"]
    for i, col in enumerate([col1, col2, col3]):
        if i < len(df_sorted):
            with col:
                st.markdown(f"<div style='text-align:center; padding:20px; background:linear-gradient(135deg, #1e293b, #0f172a); border-radius:15px;'><div style='font-size:48px;'>{medals[i]}</div><div style='font-size:20px; font-weight:bold;'>{df_sorted.iloc[i]['аты']}</div><div style='font-size:28px; color:{colors_medal[i]};'>{df_sorted.iloc[i]['орташа балл']:.1f}</div><div style='font-size:12px; opacity:0.7;'>балл</div></div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📊 Рейтинг графигі")
    fig, ax = plt.subplots(figsize=(12, 5))
    colors_bar = ['#4CAF50' if x >= 80 else '#FFC107' if x >= 60 else '#F44336' for x in df_sorted['орташа балл']]
    bars = ax.bar(df_sorted['аты'], df_sorted['орташа балл'], color=colors_bar)
    ax.axhline(y=60, color='red', linestyle='--', alpha=0.7, label='Қауіп шегі (60)')
    ax.axhline(y=80, color='green', linestyle='--', alpha=0.7, label='Үздік шегі (80)')
    ax.set_ylim(0, 100)
    ax.set_ylabel("Орташа балл")
    ax.set_title("Оқушылар рейтингі")
    ax.legend()
    for bar, val in zip(bars, df_sorted['орташа балл']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}', ha='center', fontsize=9)
    plt.xticks(rotation=45)
    st.pyplot(fig)
    
    st.divider()
    st.subheader("📋 Толық рейтинг кестесі")
    def get_medal_emoji(rank):
        if rank == 1: return "🥇"
        elif rank == 2: return "🥈"
        elif rank == 3: return "🥉"
        return "📌"
    df_sorted['Орны'] = df_sorted['Рейтинг'].apply(get_medal_emoji)
    display_df = df_sorted[['Орны', 'Рейтинг', 'аты', 'орташа балл', 'ең әлсіз пән', 'қатысу']]
    display_df.columns = ['Орны', 'Рейтинг', 'Аты', 'Орташа балл', 'Әлсіз пән', 'Қатысу']
    st.dataframe(display_df, use_container_width=True)
    
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("📊 Ең жоғары балл", f"{df['орташа балл'].max():.1f}")
    with col2: st.metric("📉 Ең төмен балл", f"{df['орташа балл'].min():.1f}")
    with col3: st.metric("📈 Медиана", f"{df['орташа балл'].median():.1f}")
    with col4: st.metric("📊 Стандартты ауытқу", f"{df['орташа балл'].std():.1f}")
