import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Ақылды журнал", layout="wide")

st.title("🤖 Ақылды журнал")

data = {
    'аты': ['A','B','C','D','E','F','G','H'],
    'математика': [80,50,40,90,65,30,85,55],
    'физика': [70,55,45,95,60,35,88,50],
    'информатика': [85,60,50,92,70,40,90,65],
    'қазақ тілі': [75,58,48,88,68,45,86,60],
    'ағылшын тілі': [78,52,46,91,66,38,87,58],
    'қатысу': [90,60,50,95,70,40,92,65]
}

df = pd.DataFrame(data)

subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']

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

st.dataframe(df)

st.subheader("📊 KPI")
col1, col2 = st.columns(2)
col1.metric("Орташа балл", round(df['орташа балл'].mean(),2))
col2.metric("Қауіпті %", round(df['қауіп'].mean()*100,1))

st.subheader("📈 График")
fig, ax = plt.subplots()
ax.bar(df['аты'], df['орташа балл'])
st.pyplot(fig)

st.subheader("🧠 Болжау")

math = st.slider("Математика", 0, 100, 60)
physics = st.slider("Физика", 0, 100, 60)
info = st.slider("Информатика", 0, 100, 60)
kaz = st.slider("Қазақ тілі", 0, 100, 60)
eng = st.slider("Ағылшын тілі", 0, 100, 60)
att = st.slider("Қатысу", 0, 100, 70)

X = df[subjects + ['қатысу']]
y = df['қауіп']

model = RandomForestClassifier()
model.fit(X, y)

pred = model.predict([[math, physics, info, kaz, eng, att]])

if st.button("Болжау"):
    if pred[0] == 1:
        st.error("⚠️ Қауіпті")
    else:
        st.success("✅ Жақсы")
