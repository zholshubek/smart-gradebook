import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

st.set_page_config(page_title="Ақылды журнал PRO", layout="wide")

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.title("📚 Меню")
menu = st.sidebar.radio("Бөлім таңдаңыз:", [
    "🏠 Dashboard",
    "📊 Аналитика",
    "🧠 Болжау",
    "📞 Ата-ана",
    "🏆 Рейтинг"
])

# -------------------------------
# ДЕРЕКТЕР
# -------------------------------
data = {
    'аты': ['Асан', 'Айгүл', 'Нұрсұлтан', 'Динара', 'Ержан', 'Мадина', 'Самат', 'Аружан'],
    'математика': [80,50,40,90,65,30,85,55],
    'физика': [70,55,45,95,60,35,88,50],
    'информатика': [85,60,50,92,70,40,90,65],
    'қазақ тілі': [75,58,48,88,68,45,86,60],
    'ағылшын тілі': [78,52,46,91,66,38,87,58],
    'қатысу': [90,60,50,95,70,40,92,65]
}

df = pd.DataFrame(data)

subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']

# -------------------------------
# ЕСЕПТЕУЛЕР
# -------------------------------
df['орташа балл'] = df[subjects].mean(axis=1)

df['қауіп'] = np.where((df['орташа балл'] < 60) | (df['қатысу'] < 60), 1, 0)

def weak_subject(row):
    low = row[subjects][row[subjects] < 50]
    if len(low) == 0:
        return "Жоқ"
    return low.idxmin()

df['ең әлсіз пән'] = df.apply(weak_subject, axis=1)

def recommendation(row):
    if row['орташа балл'] < 60 and row['қатысу'] < 60:
        return f"Ата-анамен кездесу ({row['ең әлсіз пән']})"
    elif row['орташа балл'] < 60:
        return f"Қосымша сабақ ({row['ең әлсіз пән']})"
    elif row['қатысу'] < 60:
        return "Ата-анамен байланыс"
    else:
        return "Жақсы"

df['ұсыныс'] = df.apply(recommendation, axis=1)

# -------------------------------
# ML МОДЕЛЬ
# -------------------------------
X = df[subjects + ['қатысу']]
y = df['қауіп']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# -------------------------------
# DASHBOARD
# -------------------------------
if menu == "🏠 Dashboard":
    st.title("📊 Жалпы көрсеткіштер")

    col1, col2, col3 = st.columns(3)
    col1.metric("Орташа балл", round(df['орташа балл'].mean(),2))
    col2.metric("Қауіпті %", f"{round(df['қауіп'].mean()*100,1)}%")
    col3.metric("Оқушы саны", len(df))

    st.subheader("📋 Оқушылар тізімі")
    st.dataframe(df)

# -------------------------------
# АНАЛИТИКА
# -------------------------------
elif menu == "📊 Аналитика":
    st.title("📈 Аналитика")

    col1, col2 = st.columns(2)

    fig1, ax1 = plt.subplots()
    ax1.bar(df['аты'], df['орташа балл'])
    ax1.set_title("Орташа балл")
    col1.pyplot(fig1)

    fig2, ax2 = plt.subplots()
    sns.scatterplot(x='қатысу', y='орташа балл', hue='қауіп', data=df, ax=ax2)
    ax2.set_title("Қауіпті оқушылар")
    col2.pyplot(fig2)

    fig3, ax3 = plt.subplots()
    sns.heatmap(df[subjects].corr(), annot=True, ax=ax3)
    st.pyplot(fig3)

# -------------------------------
# БОЛЖАУ
# -------------------------------
elif menu == "🧠 Болжау":
    st.title("🧠 Жаңа оқушыны болжау")

    math = st.slider("Математика", 0, 100, 60)
    physics = st.slider("Физика", 0, 100, 60)
    info = st.slider("Информатика", 0, 100, 60)
    kaz = st.slider("Қазақ тілі", 0, 100, 60)
    eng = st.slider("Ағылшын тілі", 0, 100, 60)
    att = st.slider("Қатысу", 0, 100, 70)

    if st.button("Болжау"):
        pred = model.predict([[math, physics, info, kaz, eng, att]])
        if pred[0] == 1:
            st.error("⚠️ Қауіпті оқушы!")
        else:
            st.success("✅ Қауіпсіз")

# -------------------------------
# АТА-АНА
# -------------------------------
elif menu == "📞 Ата-ана":
    st.title("📞 Ата-анамен жұмыс")

    parents = df[df['ұсыныс'].str.contains("Ата-ана")]
    st.dataframe(parents[['аты','орташа балл','ұсыныс']])

# -------------------------------
# РЕЙТИНГ
# -------------------------------
elif menu == "🏆 Рейтинг":
    st.title("🏆 Рейтинг")

    df_sorted = df.sort_values(by='орташа балл', ascending=False)
    st.dataframe(df_sorted[['аты','орташа балл']])

    fig, ax = plt.subplots()
    ax.bar(df_sorted['аты'], df_sorted['орташа балл'])
    st.pyplot(fig)
