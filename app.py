from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

# 🔤 Қазақша шрифт
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

def generate_super_pdf(row, df):
    styles = getSampleStyleSheet()

    # 🎨 стильдер
    title = ParagraphStyle(
        'title',
        parent=styles['Normal'],
        fontName='DejaVu',
        fontSize=18,
        textColor=colors.darkblue,
        spaceAfter=10
    )

    header = ParagraphStyle(
        'header',
        parent=styles['Normal'],
        fontName='DejaVu',
        fontSize=14,
        textColor=colors.black,
        spaceAfter=6
    )

    normal = ParagraphStyle(
        'normal',
        parent=styles['Normal'],
        fontName='DejaVu',
        fontSize=11
    )

    # -------------------------------
    # 📊 1. ГРАФИК (пәндер)
    # -------------------------------
    subjects = ['математика','физика','информатика','қазақ тілі','ағылшын тілі']
    scores = [row[s] for s in subjects]

    plt.figure(figsize=(6,4))
    plt.bar(subjects, scores, color='#4CAF50')
    plt.title("Пәндер бойынша балл")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("chart1.png")
    plt.close()

    # -------------------------------
    # 📈 2. ПРОГРЕСС
    # -------------------------------
    plt.figure(figsize=(6,4))
    plt.plot(["Өткен","Қазір"], [row['өткен'], row['орташа балл']], marker='o')
    plt.title("Прогресс")
    plt.tight_layout()
    plt.savefig("chart2.png")
    plt.close()

    # -------------------------------
    # 📋 КЕСТЕ
    # -------------------------------
    table_data = [["Пән", "Балл"]]
    for s in subjects:
        table_data.append([s, str(row[s])])

    # ✅ Кестені дұрыс құру (бұл жерде қате жоқ)
    table = Table(table_data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'DejaVu'),  # Қазақша шрифт қосу
    ]))

    # -------------------------------
    # 📄 PDF ҚҰРУ
    # -------------------------------
    doc = SimpleDocTemplate("super_report.pdf", pagesize=letter)
    content = []

    # Тақырып
    content.append(Paragraph("🏫 ОҚУШЫ ЕСЕБІ", title))
    content.append(Spacer(1,10))

    # Негізгі инфо
    content.append(Paragraph(f"Аты: {row['аты']}", normal))
    content.append(Paragraph(f"Орташа балл: {round(row['орташа балл'],2)}", normal))
    content.append(Paragraph(f"Әлсіз пән: {row['ең әлсіз пән']}", normal))
    content.append(Paragraph(f"Қатысу: {row['қатысу']}%", normal))
    content.append(Spacer(1,10))

    # AI
    content.append(Paragraph("🧠 ҰСЫНЫС", header))
    content.append(Paragraph(row['AI'], normal))
    content.append(Paragraph(f"Тапсырма: {row['тапсырма']}", normal))
    content.append(Spacer(1,15))

    # Кесте
    content.append(Paragraph("📋 Бағалар", header))
    content.append(table)
    content.append(Spacer(1,15))

    # График 1
    content.append(Paragraph("📊 Пәндер графигі", header))
    content.append(Image("chart1.png", width=400, height=250))
    content.append(Spacer(1,15))

    # График 2
    content.append(Paragraph("📈 Прогресс", header))
    content.append(Image("chart2.png", width=400, height=250))

    doc.build(content)

# -------------------------------
# 🖥️ STREAMLIT ИНТЕРФЕЙСІ
# -------------------------------

# Деректерді жүктеу (мысал)
# df = pd.read_csv("students.csv")  # нақты деректеріңізді жүктеңіз

# Мысал деректер (тест үшін)
data = {
    'аты': ['Алима', 'Бауыржан', 'Дана'],
    'математика': [85, 78, 92],
    'физика': [80, 88, 85],
    'информатика': [95, 82, 88],
    'қазақ тілі': [90, 85, 91],
    'ағылшын тілі': [88, 79, 86],
    'өткен': [75, 80, 82],
    'орташа балл': [87.6, 82.4, 88.4],
    'ең әлсіз пән': ['физика', 'ағылшын тілі', 'физика'],
    'қатысу': [95, 88, 92],
    'AI': ['Математиканы жақсарту керек', 'Ағылшын тіліне көңіл бөліңіз', 'Жалпы жақсы нәтиже'],
    'тапсырма': ['№15 есеп', 'Лексика жаттау', 'Қайталау']
}
df = pd.DataFrame(data)

# Streamlit интерфейсі
st.title("📚 Smart Gradebook - SUPER PDF")

student = st.selectbox("Оқушы таңда", df['аты'])
row = df[df['аты'] == student].iloc[0]

if st.button("📄 SUPER PDF жасау"):
    generate_super_pdf(row, df)
    
    with open("super_report.pdf", "rb") as f:
        st.download_button(
            "📥 Жүктеу",
            f,
            file_name=f"{row['аты']}_super_report.pdf",
            mime="application/pdf"
        )
