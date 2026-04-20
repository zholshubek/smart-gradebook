def ai_insight(row):
    if row['орташа балл'] < 50:
        return f"{row['аты']} оқуында айтарлықтай қиындық бар. Негізгі мәселе — {row['ең әлсіз пән']}. Жеке жұмыс қажет."
    
    elif row['орташа балл'] < 70:
        return f"{row['аты']} орташа деңгейде. {row['ең әлсіз пән']} пәніне назар аудару керек."
    
    else:
        return f"{row['аты']} жақсы оқиды. Барлық пәндер бойынша тұрақты нәтиже көрсетіп отыр."
df['AI кеңес'] = df.apply(ai_insight, axis=1)
def generate_tasks(row):
    subject = row['ең әлсіз пән']

    tasks = {
        "математика": "10 есеп шығару",
        "физика": "5 есеп + формула қайталау",
        "информатика": "Python практика",
        "қазақ тілі": "1 мәтін жазу",
        "ағылшын тілі": "20 сөз жаттау"
    }

    return tasks.get(subject, "Жалпы қайталау")

df['тапсырма'] = df.apply(generate_tasks, axis=1)
df['өткен апта'] = df['орташа балл'] - np.random.randint(0,10,size=len(df))
fig, ax = plt.subplots()

ax.plot(df['аты'], df['орташа балл'], label="Қазір")
ax.plot(df['аты'], df['өткен апта'], label="Өткен апта")

plt.xticks(rotation=45)
plt.legend()

st.pyplot(fig)
st.metric("📊 Орташа балл", round(df['орташа балл'].mean(),2))
st.metric("⚠️ Қауіпті оқушылар", df['қауіп'].sum())
st.metric("🏆 Үздік оқушылар", len(df[df['орташа балл']>80]))
def parent_message(row):
    return f"{row['аты']} - {row['ең әлсіз пән']} төмен. {row['ұсыныс']}"

df['ата-ана хабар'] = df.apply(parent_message, axis=1)
st.subheader("📲 Ата-анаға хабар")

student = st.selectbox("Оқушы", df['аты'])
msg = df[df['аты']==student]['ата-ана хабар'].values[0]

st.info(msg)
