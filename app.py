import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Шрифтті тіркеу
try:
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    FONT_AVAILABLE = True
except:
    FONT_AVAILABLE = False

st.set_page_config(page_title="Smart School Portal", layout="wide")
st.markdown("""
<style>
.kpi-card { background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.kpi-title { font-size: 14px; opacity: 0.7; }
.kpi-value { font-size: 28px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------- ПАЙДАЛАНУШЫЛАР ----------
users = {
    "admin": {"password": "1234", "role": "admin", "name": "Әкімші"},
    "teacher": {"password": "1111", "role": "teacher", "name": "Мұғалім"},
    "parent_asan": {"password": "2222", "role": "parent", "name": "Асанның ата-анасы", "child": "Асан"},
    "student_asan": {"password": "3333", "role": "student", "name": "Асан", "child": "Асан"}
}

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.child = None

if not st.session_state.login:
    st.title("🔐 Жүйеге кіру")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Логин")
        p = st.text_input("Құпия сөз", type="password")
        if st.button("Кіру", use_container_width=True):
            if u in users and users[u]["password"] == p:
                st.session_state.login = True
                st.session_state.role = users[u]["role"]
                st.session_state.username = users[u]["name"]
                if "child" in users[u]:
                    st.session_state.child = users[u]["child"]
                st.rerun()
            else:
                st.error("Қате логин немесе құпия сөз!")
    st.stop()

if st.sidebar.button("🚪 Шығу", use_container_width=True):
    st.session_state.login = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.child = None
    st.rerun()

st.sidebar.title("📚 Smart School Portal")
st.sidebar.write(f"**Қош келдіңіз, {st.session_state.username}!** (Рөл: {st.session_state.role})")

menu_items = ["🏠 Журнал", "📊 Аналитика", "🧠 Болжау", "👤 Профиль", "📲 Хабар", "🧾 PDF", "🏆 Рейтинг"]
extra_items = []
if st.session_state.role in ["admin", "teacher"]:
    extra_items.extend(["📅 Күнтізбе", "📋 Қатысу", "📚 Кітапхана", "🧠 Ұсыныстар", "😊 Психология"])
if st.session_state.role == "admin":
    extra_items.append("👥 Пайдаланушылар")
menu = st.sidebar.radio("Бөлімдер:", menu_items + extra_items, index=0)

# ---------- ДЕРЕКТЕР ----------
uploaded = st.sidebar.file_uploader("📂 Excel файл жүктеу", type=["xlsx"])
def load_data():
    if uploaded is not None:
        df = pd.read_excel(uploaded)
        required = ['аты', 'математика', 'физика', 'информатика', 'қазақ тілі', 'ағылшын тілі', 'қатысу']
        if any(c not in df.columns for c in required):
            st.error("Қажетті бағандар жоқ!")
            st.stop()
        return df
    else:
        return pd.DataFrame({
            'аты': ['Асан', 'Айгүл', 'Нұрсұлтан', 'Динара', 'Ержан', 'Мадина', 'Самат', 'Аружан'],
            'математика': [80,50,40,90,65,30,85,55],
            'физика': [70,55,45,95,60,35,88,50],
            'информатика': [85,60,50,92,70,40,90,65],
            'қазақ тілі': [75,58,48,88,68,45,86,60],
            'ағылшын тілі': [78,52,46,91,66,38,87,58],
            'қатысу': [90,60,50,95,70,40,92,65]
        })
df = load_data()
subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']
df['орташа балл'] = df[subjects].mean(axis=1)
df['өткен'] = (df['орташа балл'] - np.random.randint(5,15,len(df))).clip(0,100)
df['қауіп'] = np.where((df['орташа балл']<60) | (df['қатысу']<60),1,0)
def find_weak_subject(row):
    scores = {s:row[s] for s in subjects}
    return min(scores, key=scores.get)
df['ең әлсіз пән'] = df.apply(find_weak_subject, axis=1)
def generate_ai_recommendation(row):
    if row['орташа балл']<50:
        return f"⚠️ {row['аты']} оқушысының үлгерімі өте төмен. {row['ең әлсіз пән']} пәніне ерекше назар аудару қажет."
    elif row['орташа балл']<70:
        return f"📘 {row['аты']} оқушысы орташа деңгейде. {row['ең әлсіз пән']} пәнін жақсарту қажет."
    else:
        return f"🎉 {row['аты']} оқушысы жақсы нәтиже көрсетіп отыр."
df['AI'] = df.apply(generate_ai_recommendation, axis=1)
df['тапсырма'] = df['ең әлсіз пән'] + " пәнінен 10 есеп шығару"

# ML Модельдер
X = df[subjects+['қатысу']]
y = df['қауіп']
models = {
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
}
trained_models = {}
for name, m in models.items():
    m.fit(X,y)
    trained_models[name] = m

# ======================== 1. ЖУРНАЛ ========================
if menu == "🏠 Журнал":
    if st.session_state.role not in ["admin","teacher","parent","student"]:
        st.error("Қолжетімсіз")
        st.stop()
    st.title("📊 Оқушылар журналы")
    if st.session_state.role in ["parent","student"]:
        selected_student = st.session_state.child
        filtered_df = df[df['аты']==selected_student]
    else:
        selected_student = st.selectbox("Оқушы таңда", ["Барлығы"]+list(df['аты']))
        filtered_df = df if selected_student=="Барлығы" else df[df['аты']==selected_student]
    st.subheader("📊 Орташа балл (интерактивті)")
    fig = px.bar(filtered_df, x='аты', y='орташа балл', color='орташа балл',
                 color_continuous_scale=['#F44336','#FFC107','#4CAF50'],
                 text='орташа балл', height=500)
    fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Қауіп шегі (60)")
    fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Үздік шегі (80)")
    fig.update_traces(textposition='outside', texttemplate='%{text:.1f}')
    fig.update_layout(yaxis_range=[0,100], xaxis_title="Оқушы", yaxis_title="Орташа балл")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📋 Оқушылар тізімі")
    def highlight_row(r):
        if r['орташа балл']>=80: return ['background-color: #166534; color: white']*len(r)
        elif r['орташа балл']<60: return ['background-color: #991b1b; color: white']*len(r)
        return ['']*len(r)
    display_df = filtered_df[['аты','математика','физика','информатика','қазақ тілі','ағылшын тілі','орташа балл','қатысу','қауіп']]
    st.dataframe(display_df.style.apply(highlight_row, axis=1), use_container_width=True)

# ======================== 2. АНАЛИТИКА ========================
elif menu == "📊 Аналитика":
    if st.session_state.role not in ["admin","teacher"]:
        st.error("Тек мұғалім мен әкімшілік!")
        st.stop()
    st.title("📊 Аналитика панелі")
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>📈 Орташа балл</div><div class='kpi-value'>{df['орташа балл'].mean():.1f}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>⚠️ Қауіпті оқушылар</div><div class='kpi-value'>{df['қауіп'].sum()}</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🏆 Үздік оқушылар</div><div class='kpi-value'>{len(df[df['орташа балл']>=80])}</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>📚 Ең әлсіз пән</div><div class='kpi-value'>{df['ең әлсіз пән'].mode()[0]}</div></div>", unsafe_allow_html=True)
    st.divider()
    selected = st.selectbox("👤 Оқушыны фильтрлеу", ["Барлығы"]+list(df['аты']))
    data = df if selected=="Барлығы" else df[df['аты']==selected]
    st.subheader("📊 Орташа балл")
    fig1 = px.bar(data, x='аты', y='орташа балл', color='орташа балл', color_continuous_scale=['#F44336','#FFC107','#4CAF50'], text='орташа балл')
    fig1.add_hline(y=60, line_dash="dash", line_color="red")
    fig1.update_traces(textposition='outside')
    fig1.update_layout(yaxis_range=[0,100])
    st.plotly_chart(fig1, use_container_width=True)
    st.subheader("📈 Прогресс (өткен vs қазір)")
    prog = pd.melt(data, id_vars=['аты'], value_vars=['өткен','орташа балл'], var_name='Кезең', value_name='Балл')
    fig2 = px.bar(prog, x='аты', y='Балл', color='Кезең', barmode='group', text='Балл')
    fig2.update_traces(textposition='outside')
    fig2.update_layout(yaxis_range=[0,100])
    st.plotly_chart(fig2, use_container_width=True)
    st.subheader("📉 Балл таралуы")
    fig3 = px.histogram(df, x='орташа балл', nbins=8, marginal='box', color_discrete_sequence=['#2196F3'])
    fig3.add_vline(x=60, line_dash="dash", line_color="red")
    fig3.add_vline(x=80, line_dash="dash", line_color="green")
    st.plotly_chart(fig3, use_container_width=True)
    st.subheader("📊 Корреляция")
    fig4 = px.imshow(df[subjects].corr(), text_auto=True, aspect="auto", color_continuous_scale='RdBu')
    st.plotly_chart(fig4, use_container_width=True)
    st.subheader("🎯 Деңгей бойынша бөлініс")
    df['деңгей'] = df['орташа балл'].apply(lambda x: "Үздік (80+)" if x>=80 else ("Орташа (60-79)" if x>=60 else "Қауіпті (60-тан төмен)"))
    level_counts = df['деңгей'].value_counts().reset_index()
    level_counts.columns = ['Деңгей','Саны']
    fig5 = px.pie(level_counts, values='Саны', names='Деңгей', color='Деңгей',
                  color_discrete_map={"Үздік (80+)":"#4CAF50","Орташа (60-79)":"#FFC107","Қауіпті (60-тан төмен)":"#F44336"})
    st.plotly_chart(fig5, use_container_width=True)
    col_a, col_b = st.columns(2)
    with col_a: st.subheader("🏆 ТОП 3"); st.dataframe(df.nlargest(3,'орташа балл')[['аты','орташа балл']], use_container_width=True)
    with col_b: st.subheader("⚠️ Ең әлсіз 3"); st.dataframe(df.nsmallest(3,'орташа балл')[['аты','орташа балл']], use_container_width=True)
    with st.expander("🤖 ML Модельдерінің сапасы"):
        comp = []
        for name, mdl in trained_models.items():
            try:
                cv_folds = min(3,len(X)-1)
                scores = cross_val_score(mdl, X, y, cv=cv_folds)
                comp.append({"Модель": name, "Орташа дәлдік": f"{scores.mean()*100:.1f}%",
                             "Мин/Макс": f"{scores.min()*100:.1f}%/{scores.max()*100:.1f}%",
                             "Тұрақтылық": "🔴" if scores.std()>0.15 else "🟡" if scores.std()>0.08 else "🟢"})
            except:
                comp.append({"Модель": name, "Орташа дәлдік": "❌", "Мин/Макс": "-", "Тұрақтылық": "⚪"})
        st.dataframe(pd.DataFrame(comp), use_container_width=True)

# ======================== 3. БОЛЖАУ ========================
elif menu == "🧠 Болжау":
    st.title("🧠 Ақылды болжау жүйесі")
    st.markdown("Оқушының бағаларын енгізіп, қауіп тобына кіретінін болжаңыз")
    st.subheader("🤖 Модельді таңдаңыз")
    model_choice = st.selectbox("Модель", ['Random Forest','Logistic Regression','Gradient Boosting'])
    model_info = {'Random Forest':"🌲 Көптеген шешім ағаштары", 'Logistic Regression':"📈 Сызықтық теңдеу", 'Gradient Boosting':"🎯 Қателерді кезең-кезеңімен түзетеді"}
    st.info(model_info[model_choice])
    col1, col2 = st.columns(2)
    with col1:
        math = st.slider("📘 Математика",0,100,65)
        physics = st.slider("🔬 Физика",0,100,65)
        info = st.slider("💻 Информатика",0,100,65)
    with col2:
        kazakh = st.slider("📖 Қазақ тілі",0,100,65)
        english = st.slider("🌍 Ағылшын тілі",0,100,65)
        attendance = st.slider("📅 Қатысу (%)",0,100,75)
    input_data = [[math, physics, info, kazakh, english, attendance]]
    st.subheader("📊 Енгізілген мәліметтер")
    subjects_rus = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']
    values = [math, physics, info, kazakh, english]
    fig = px.bar(x=subjects_rus, y=values, color=values, color_continuous_scale=['#F44336','#FFC107','#4CAF50'], text=values)
    fig.add_hline(y=60, line_dash="dash", line_color="red")
    fig.update_layout(yaxis_range=[0,100])
    st.plotly_chart(fig, use_container_width=True)
    if st.button("🔍 Болжау жасау", type="primary", use_container_width=True):
        selected_model = trained_models[model_choice]
        pred = selected_model.predict(input_data)[0]
        prob = selected_model.predict_proba(input_data)[0]
        st.divider()
        st.subheader("🎯 Нәтиже")
        with st.expander("📊 Барлық модельдерді салыстыру"):
            comp_data = []
            for name, mdl in trained_models.items():
                p = mdl.predict(input_data)[0]
                prob2 = mdl.predict_proba(input_data)[0][1]*100
                comp_data.append({"Модель": name, "Нәтиже": "⚠️ Қауіпті" if p==1 else "✅ Қауіпсіз", "Қауіп ықтималдығы": f"{prob2:.1f}%"})
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True)
            preds = [mdl.predict(input_data)[0] for mdl in trained_models.values()]
            consensus = max(set(preds), key=preds.count)
            st.write(f"🤝 Модельдер келісімі: {preds.count(consensus)/len(preds)*100:.0f}%")
        col_a, col_b = st.columns(2)
        with col_a:
            if pred==1: st.error("⚠️ ҚАУІПТІ ТОБЫ"); st.markdown("Дереу шара қолдану қажет!")
            else: st.success("✅ ҚАУІПСІЗ ТОБЫ")
        with col_b:
            st.metric("Таңдалған модель", model_choice)
            st.metric("Қауіп ықтималдығы", f"{prob[1]*100:.1f}%")
            conf = prob[1] if pred==1 else prob[0]
            st.progress(conf, text="🔴 Жоғары" if conf>0.7 else "🟡 Орташа" if conf>0.4 else "🟢 Төмен")
        st.subheader("🤖 AI ұсынысы")
        avg_score = np.mean([math,physics,info,kazakh,english])
        weakest = subjects_rus[np.argmin([math,physics,info,kazakh,english])]
        avg_risk = np.mean([mdl.predict_proba(input_data)[0][1] for mdl in trained_models.values()])*100
        if avg_score<50: st.error(f"🔴 Жедел араласу! Әлсіз пән: {weakest}\nОрташа балл: {avg_score:.1f}")
        elif avg_score<70: st.warning(f"🟡 Орташа деңгей. {weakest} пәнін жақсарту керек.")
        else: st.success(f"🟢 Жақсы деңгей! Олимпиадаға дайындалу.")

# ======================== 4. ПРОФИЛЬ (толық портфолио+чат) ========================
elif menu == "👤 Профиль":
    st.title("👤 Оқушы профилі")
    if st.session_state.role in ["parent","student"]:
        student = st.session_state.child
    else:
        student = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==student].iloc[0]
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("📈 Орташа балл", f"{row['орташа балл']:.1f}")
    with c2: st.metric("📅 Қатысу", f"{row['қатысу']}%")
    with c3: st.metric("⚠️ Қауіп тобы", "Иә" if row['қауіп']==1 else "Жоқ")
    with c4: st.metric("📚 Әлсіз пән", row['ең әлсіз пән'])
    st.divider()
    st.subheader("📊 Пәндер бойынша нәтиже")
    scores_df = pd.DataFrame({"Пән": subjects, "Балл": [row[s] for s in subjects]})
    fig = px.bar(scores_df, x='Пән', y='Балл', color='Балл', color_continuous_scale=['#F44336','#FFC107','#4CAF50'], text='Балл')
    fig.add_hline(y=60, line_dash="dash", line_color="red")
    fig.update_layout(yaxis_range=[0,100])
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📈 Прогресс")
    prog_df = pd.DataFrame({"Кезең": ["Өткен ай", "Қазір"], "Балл": [row['өткен'], row['орташа балл']]})
    fig2 = px.line(prog_df, x='Кезең', y='Балл', markers=True)
    fig2.update_layout(yaxis_range=[0,100])
    st.plotly_chart(fig2, use_container_width=True)
    st.subheader("🧠 AI ұсыныс"); st.info(row['AI'])
    st.subheader("📚 Тапсырма"); st.success(row['тапсырма'])

    # Портфолио
    with st.expander("🏆 Оқушының жетістіктері (портфолио)"):
        if f"portfolio_{student}" not in st.session_state:
            st.session_state[f"portfolio_{student}"] = [{"Күні":"2024-12-10","Жетістік":"Математика олимпиадасына қатысу","Түрі":"🏅"}]
        st.dataframe(pd.DataFrame(st.session_state[f"portfolio_{student}"]), use_container_width=True)
        if st.session_state.role in ["admin","teacher"]:
            with st.form(f"add_achievement_{student}"):
                col1, col2 = st.columns(2)
                with col1: new_date = st.date_input("Күні")
                with col2: new_type = st.selectbox("Түрі", ["🏅 Қатысу","🥉 Жүлде","🥈 Жүлде","🥇 Жүлде"])
                new_ach = st.text_input("Жетістік")
                if st.form_submit_button("➕ Қосу"):
                    st.session_state[f"portfolio_{student}"].append({"Күні":str(new_date),"Жетістік":new_ach,"Түрі":new_type})
                    st.rerun()

    # Чат
    with st.expander("💬 Ата-ана-мұғалім байланысы"):
        if f"chat_{student}" not in st.session_state:
            st.session_state[f"chat_{student}"] = []
        for msg in st.session_state[f"chat_{student}"]:
            st.markdown(f"**{msg['рөл']}** ({msg['уақыт']}): {msg['мәтін']}")
        if st.session_state.role in ["admin","teacher","parent","student"]:
            with st.form(f"chat_form_{student}"):
                txt = st.text_area("Хабар жазыңыз")
                if st.form_submit_button("📤 Жіберу") and txt:
                    st.session_state[f"chat_{student}"].append({"рөл":st.session_state.role, "уақыт":datetime.now().strftime("%Y-%m-%d %H:%M"), "мәтін":txt})
                    st.rerun()

    # Болжау
    with st.expander("🔮 Осы оқушыға болжау"):
        student_data = [[row[s] for s in subjects] + [row['қатысу']]]
        for name, mdl in trained_models.items():
            pred = mdl.predict(student_data)[0]
            prob = mdl.predict_proba(student_data)[0][1]*100
            st.write(f"**{name}**: {'⚠️ Қауіпті' if pred==1 else '✅ Қауіпсіз'} (ықтималдық {prob:.1f}%)")

# ======================== 5. ХАБАР ========================
elif menu == "📲 Хабар":
    if st.session_state.role not in ["admin","teacher"]:
        st.error("Тек мұғалім мен әкімшілік!")
        st.stop()
    st.title("📲 Ата-анаға хабарлама")
    student = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==student].iloc[0]
    col1, col2, col3 = st.columns(3)
    with col1:
        if row['орташа балл']>=80: st.success("🟢 Үздік деңгей")
        elif row['орташа балл']>=60: st.warning("🟡 Орташа деңгей")
        else: st.error("🔴 Қауіпті деңгей")
    with col2: st.metric("Орташа балл", f"{row['орташа балл']:.1f}")
    with col3: st.metric("Қатысу", f"{row['қатысу']}%")
    message = f"""ҚҰРМЕТТІ АТА-АНА! Балаңыз: {row['аты']}
    Орташа балл: {row['орташа балл']:.1f}
    Қатысу: {row['қатысу']}%
    Әлсіз пән: {row['ең әлсіз пән']}
    AI Ұсынысы: {row['AI']}
    Тапсырма: {row['тапсырма']}"""
    st.text_area("Хабарлама мәтіні", message, height=300)
    st.download_button("📥 TXT жүктеу", message, file_name=f"{student}_хабарлама.txt")

# ======================== 6. PDF (рөлге байланысты) ========================
elif menu == "🧾 PDF":
    st.title("🧾 PDF есеп")
    if st.session_state.role in ["parent","student"]:
        student = st.session_state.child
    else:
        student = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==student].iloc[0]
    col1,col2,col3 = st.columns(3)
    with col1: st.metric("Орташа балл", f"{row['орташа балл']:.1f}")
    with col2: st.metric("Қатысу", f"{row['қатысу']}%")
    with col3: st.metric("Әлсіз пән", row['ең әлсіз пән'])
    if st.button("📄 PDF жасау"):
        with st.spinner("PDF дайындалуда..."):
            # Графиктер
            fig, ax = plt.subplots(figsize=(6,4))
            scores = [row[s] for s in subjects]
            colors = ['#4CAF50' if x>=70 else '#FFC107' if x>=50 else '#F44336' for x in scores]
            ax.bar(subjects, scores, color=colors)
            ax.axhline(60, color='red', linestyle='--')
            ax.set_ylim(0,100)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig("chart1.png"); plt.close()
            fig2, ax2 = plt.subplots(figsize=(6,4))
            ax2.plot(['Өткен ай','Қазір'], [row['өткен'], row['орташа балл']], marker='o')
            ax2.set_ylim(0,100)
            plt.savefig("chart2.png"); plt.close()
            doc = SimpleDocTemplate("report.pdf", pagesize=letter)
            styles = getSampleStyleSheet()
            content = [Paragraph("SMART SCHOOL SYSTEM", styles['Title']), Paragraph(f"Оқушы: {row['аты']}", styles['Normal']),
                       Paragraph(f"Орташа балл: {row['орташа балл']:.1f}", styles['Normal']),
                       Paragraph(f"Қатысу: {row['қатысу']}%", styles['Normal']),
                       Image("chart1.png", width=400, height=250), Image("chart2.png", width=400, height=250)]
            doc.build(content)
        with open("report.pdf","rb") as f: st.download_button("📥 PDF жүктеу", f.read(), file_name=f"{student}_есеп.pdf")

# ======================== 7. РЕЙТИНГ ========================
elif menu == "🏆 Рейтинг":
    st.title("🏆 Рейтинг")
    df_sorted = df.sort_values('орташа балл', ascending=False).reset_index(drop=True)
    fig = px.bar(df_sorted, x='аты', y='орташа балл', color='орташа балл', color_continuous_scale=['#F44336','#FFC107','#4CAF50'], text='орташа балл')
    fig.add_hline(y=60, line_dash="dash", line_color="red")
    fig.add_hline(y=80, line_dash="dash", line_color="green")
    fig.update_layout(yaxis_range=[0,100])
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_sorted[['аты','орташа балл','ең әлсіз пән','қатысу']], use_container_width=True)

# ======================== 8. КҮНТІЗБЕ ========================
elif menu == "📅 Күнтізбе":
    st.title("📅 Мектеп күнтізбесі")
    if "calendar" not in st.session_state:
        st.session_state.calendar = [{"Күні":"2025-05-15","Оқиға":"Олимпиада","Түрі":"🏆"}]
    st.dataframe(pd.DataFrame(st.session_state.calendar), use_container_width=True)
    if st.session_state.role in ["admin","teacher"]:
        with st.expander("➕ Оқиға қосу"):
            with st.form("add_cal"):
                date = st.date_input("Күні")
                event = st.text_input("Оқиға")
                t = st.selectbox("Түрі", ["🏆 Жарыс","👪 Жиналыс","🌴 Каникул"])
                if st.form_submit_button("Қосу"):
                    st.session_state.calendar.append({"Күні":str(date),"Оқиға":event,"Түрі":t})
                    st.rerun()

# ======================== 9. ҚАТЫСУ ========================
elif menu == "📋 Қатысу":
    if st.session_state.role not in ["admin","teacher"]:
        st.error("Тек мұғалім мен әкімшілік!")
        st.stop()
    st.title("📋 Күнделікті қатысу журналы")
    if "attendance" not in st.session_state:
        st.session_state.attendance = {}
    date = st.date_input("Күні", value=datetime.today())
    date_str = str(date)
    st.subheader(f"📌 {date} күнгі қатысу")
    status = {}
    cols = st.columns(3)
    for i, student in enumerate(df['аты']):
        with cols[i%3]:
            default = st.session_state.attendance.get(date_str, {}).get(student, True)
            status[student] = st.checkbox(student, value=default)
    if st.button("💾 Сақтау"):
        if date_str not in st.session_state.attendance:
            st.session_state.attendance[date_str] = {}
        for s, v in status.items():
            st.session_state.attendance[date_str][s] = v
        st.success("Сақталды!")
    with st.expander("📊 Статистика"):
        if st.session_state.attendance:
            sel = st.selectbox("Күнді таңда", list(st.session_state.attendance.keys()))
            data = st.session_state.attendance[sel]
            att_df = pd.DataFrame([{"Оқушы":k,"Қатысу":"✅" if v else "❌"} for k,v in data.items()])
            st.dataframe(att_df)
            absent = sum(1 for v in data.values() if not v)
            st.metric("Келмегендер", absent)

# ======================== 10. КІТАПХАНА ========================
elif menu == "📚 Кітапхана":
    st.title("📚 Электронды кітапхана")

    # Кітапхананы инициализациялау
    if "library" not in st.session_state:
        st.session_state.library = [
            {"Атауы": "Математика 8-сынып", "Авторы": "Әбілқасымов", "Пәні": "Математика", "Сілтеме": "https://example.com/math.pdf", "Түрі": "📘 Оқулық"}
        ]

    # ---------- ФИЛЬТР ----------
    filter_subj = st.selectbox("📖 Пән бойынша фильтр", ["Барлығы"] + subjects)
    filtered = st.session_state.library
    if filter_subj != "Барлығы":
        filtered = [b for b in filtered if b["Пәні"] == filter_subj]

    # ---------- КІТАПТАРДЫ КӨРСЕТУ ----------
    if not filtered:
        st.info("Бұл пән бойынша әлі кітап жоқ.")
    else:
        for book in filtered:
            with st.container():
                st.markdown(f"##### {book['Атауы']}")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"✍️ {book['Авторы']}  |  {book['Пәні']}  |  {book.get('Түрі', '📘 Оқулық')}")
                with col2:
                    st.link_button("📖 Оқу", book["Сілтеме"], use_container_width=True)
                st.divider()

    # ---------- ҚОЛМЕН КІТАП ҚОСУ (ТЕК ADMIN/TEACHER) ----------
    if st.session_state.role in ["admin", "teacher"]:
        with st.expander("➕ Жаңа кітапты қолмен қосу"):
            with st.form("add_book_form"):
                title = st.text_input("Атауы")
                author = st.text_input("Авторы")
                subj = st.selectbox("Пәні", subjects)
                book_type = st.selectbox("Түрі", ["📘 Оқулық", "📗 Есептер жинағы", "📕 Грамматика", "📙 Тесттер", "📄 Мақала"])
                link = st.text_input("Сілтеме (URL)")
                if st.form_submit_button("📥 Қосу"):
                    if title and link:
                        st.session_state.library.append({
                            "Атауы": title,
                            "Авторы": author if author else "Белгісіз",
                            "Пәні": subj,
                            "Сілтеме": link,
                            "Түрі": book_type
                        })
                        st.success(f"«{title}» кітапханаға қосылды!")
                        st.rerun()
                    else:
                        st.error("Атауы мен сілтеме міндетті!")

        # ========== КІТАПТАРДЫ CSV/EXCEL АРҚЫЛЫ ТОПТАП ЖҮКТЕУ ==========
        with st.expander("📤 Кітаптар тізімін CSV/Excel арқылы жүктеу (көп кітап)"):
            st.markdown("""
            **Файл құрылымы:**
            - Қажетті бағандар: `Атауы`, `Авторы`, `Пәні`, `Сілтеме`
            - Қосымша баған (міндетті емес): `Түрі` (Оқулық, Есептер жинағы, т.б.)
            - Пәні мына мәндердің бірі болуы керек: математика, физика, информатика, қазақ тілі, ағылшын тілі
            - Excel (.xlsx) немесе CSV (.csv) форматы қолданылады.
            """)
            uploaded_books = st.file_uploader("Excel/CSV файл таңдаңыз", type=["xlsx", "csv"], key="bulk_upload")
            if uploaded_books is not None:
                try:
                    if uploaded_books.name.endswith('.xlsx'):
                        books_df = pd.read_excel(uploaded_books)
                    else:
                        books_df = pd.read_csv(uploaded_books)

                    required_cols = ['Атауы', 'Авторы', 'Пәні', 'Сілтеме']
                    if not all(col in books_df.columns for col in required_cols):
                        st.error(f"Қажетті бағандар жоқ: {required_cols}. Файлда: {list(books_df.columns)}")
                    else:
                        # Түрі бағаны жоқ болса, оқулық деп белгілеу
                        if 'Түрі' not in books_df.columns:
                            books_df['Түрі'] = '📘 Оқулық'

                        added = 0
                        skipped = 0
                        for idx, row in books_df.iterrows():
                            # Пәнінің дұрыстығын тексеру
                            if row['Пәні'] not in subjects:
                                st.warning(f"Жол {idx+2}: '{row['Атауы']}' кітабының пәні ('{row['Пәні']}') танылмады. Қосылмады.")
                                skipped += 1
                                continue
                            # Қосарланбауын тексеру (Атауы мен Авторы бойынша)
                            if any(b['Атауы'] == row['Атауы'] and b['Авторы'] == row['Авторы'] for b in st.session_state.library):
                                st.info(f"«{row['Атауы']}» кітабы қазірдің өзінде бар. Қайта қосылмады.")
                                skipped += 1
                                continue

                            st.session_state.library.append({
                                "Атауы": row['Атауы'],
                                "Авторы": row['Авторы'],
                                "Пәні": row['Пәні'],
                                "Сілтеме": row['Сілтеме'],
                                "Түрі": row['Түрі']
                            })
                            added += 1

                        if added > 0:
                            st.success(f"{added} кітап сәтті қосылды! Қайталану/қате: {skipped}")
                            st.rerun()
                        else:
                            st.warning("Ешбір жаңа кітап қосылмады. Файлды тексеріңіз.")

                except Exception as e:
                    st.error(f"Қате орын алды: {e}")
# ======================== 11. ҰСЫНЫСТАР (нейрондық желі стилі) ========================
elif menu == "🧠 Ұсыныстар":
    st.title("🧠 AI ұсыныстар")
    if st.session_state.role in ["parent","student"]:
        student = st.session_state.child
    else:
        student = st.selectbox("Оқушы", df['аты'])
    row = df[df['аты']==student].iloc[0]
    st.info(f"**{student}** үшін ұсыныстар:")
    st.write(f"📌 Ең әлсіз пән: **{row['ең әлсіз пән']}**")
    st.write("📚 Кітапханадан ұсынылатын кітаптар:")
    for book in st.session_state.get("library", []):
        if book["Пәні"] == row['ең әлсіз пән']:
            st.write(f"- {book['Атауы']} ({book['Авторы']})")
    st.write("📝 Тапсырмалар: ", row['тапсырма'])
    if row['орташа балл']<60:
        st.warning("Қауіп тобында! Ата-анамен кездесу керек.")

# ======================== 12. ПСИХОЛОГИЯ ========================
elif menu == "😊 Психология":
    st.title("😊 Психологиялық көңіл-күй мониторингі")
    if st.session_state.role in ["parent","student"]:
        student = st.session_state.child
    else:
        student = st.selectbox("Оқушы", df['аты'])
    if "mood_log" not in st.session_state: st.session_state.mood_log = {}
    if "test_results" not in st.session_state: st.session_state.test_results = {}
    today = datetime.today().strftime("%Y-%m-%d")
    st.subheader("📅 Бүгінгі көңіл-күй")
    moods = {"😊 Керемет":5, "🙂 Жақсы":4, "😐 Қалыпты":3, "😕 Сәл нашар":2, "😢 Өте нашар":1}
    selected = st.selectbox("Көңіл-күй", list(moods.keys()))
    if st.button("💾 Сақтау"):
        if student not in st.session_state.mood_log: st.session_state.mood_log[student] = {}
        st.session_state.mood_log[student][today] = moods[selected]
        st.success("Сақталды!")
    if student in st.session_state.mood_log and st.session_state.mood_log[student]:
        mood_df = pd.DataFrame(list(st.session_state.mood_log[student].items()), columns=['Күні','Деңгей'])
        mood_df['Күні'] = pd.to_datetime(mood_df['Күні'])
        mood_df = mood_df.sort_values('Күні')
        fig = px.line(mood_df, x='Күні', y='Деңгей', markers=True, title=f"{student} көңіл-күй динамикасы")
        fig.update_layout(yaxis_range=[1,5])
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("📝 Стресс тесті")
    with st.form("stress_test"):
        q1 = st.slider("Қобалжу, мазасыздық",0,4,0)
        q2 = st.slider("Күйзеліс, шамадан тыс жүктеме",0,4,0)
        q3 = st.slider("Ұйқының бұзылуы",0,4,0)
        q4 = st.slider("Назарды шоғырландыру қиындығы",0,4,0)
        if st.form_submit_button("Тест тапсыру"):
            total = q1+q2+q3+q4
            if total<=4: level="🟢 Төмен стресс"
            elif total<=8: level="🟡 Орташа стресс"
            else: level="🔴 Жоғары стресс"
            st.success(f"Нәтиже: {total}/16 – {level}")
            if student not in st.session_state.test_results: st.session_state.test_results[student] = {}
            st.session_state.test_results[student][today] = {"test":"stress","score":total,"level":level}
    st.subheader("💡 Ұсыныстар")
    if student in st.session_state.mood_log and st.session_state.mood_log[student]:
        last = list(st.session_state.mood_log[student].values())[-1]
        if last<=2: st.warning("Көңіл-күй төмен. Демалуға уақыт бөліңіз.")
        elif last==3: st.info("Қалыпты күй. Күнделікті режимді сақтаңыз.")
        else: st.success("Көңіл-күй жақсы! Осылай жалғастырыңыз.")
    if st.session_state.role in ["admin","teacher"]:
        with st.expander("👥 Жалпы статистика"):
            all_moods = []
            for s, log in st.session_state.mood_log.items():
                for date, val in log.items():
                    all_moods.append({"Оқушы":s,"Көңіл-күй":val})
            if all_moods:
                fig2 = px.histogram(pd.DataFrame(all_moods), x='Көңіл-күй', nbins=5)
                st.plotly_chart(fig2, use_container_width=True)

# ======================== 13. ПАЙДАЛАНУШЫЛАР (тек admin) ========================
elif menu == "👥 Пайдаланушылар":
    if st.session_state.role != "admin":
        st.error("Тек әкімшілік!")
        st.stop()
    st.title("👥 Пайдаланушыларды басқару")
    users_df = pd.DataFrame([{"Логин":k,"Аты":v["name"],"Рөл":v["role"],"Баласы":v.get("child","-")} for k,v in users.items()])
    st.dataframe(users_df, use_container_width=True)
    with st.form("add_user"):
        login = st.text_input("Логин")
        name = st.text_input("Аты")
        pwd = st.text_input("Құпия сөз", type="password")
        role = st.selectbox("Рөл", ["admin","teacher","parent","student"])
        child = ""
        if role in ["parent","student"]:
            child = st.text_input("Баланың аты")
        if st.form_submit_button("Қосу"):
            if login in users: st.error("Логин бос емес!")
            else:
                users[login] = {"password":pwd,"role":role,"name":name}
                if child: users[login]["child"] = child
                st.success("Қосылды!")
                st.rerun()
    del_user = st.selectbox("Жоятын пайдаланушы", list(users.keys()))
    if st.button("Жою") and del_user != "admin":
        del users[del_user]
        st.rerun()
