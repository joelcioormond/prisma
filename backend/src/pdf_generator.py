from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import navy, blue, black, red, green, white
from datetime import datetime
import io

def gerar_pdf_completo(dados_relatorio):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    
    story = []
    
    # Cabeçalho
    orgao_nome = dados_relatorio.get('orgao', {}).get('nome', 'N/A')
    story.append(Paragraph(f"Relatório de Maturidade - {orgao_nome}", styles['h1']))
    story.append(Spacer(1, 12))
    
    # Título da avaliação mais recente
    if dados_relatorio.get("avaliacoes"):
        avaliacao_recente = dados_relatorio["avaliacoes"][0]
        story.append(Paragraph(f"Avaliação: {avaliacao_recente['titulo']}", styles["h2"]))
        story.append(Spacer(1, 12))

    # Respostas
    for resposta in dados_relatorio.get("respostas", []):
        story.append(Paragraph(f"<b>Atividade:</b> {resposta['atividade_id']}", styles["h3"]))
        
        # Instituído
        if resposta.get("instituido"):
            story.append(Paragraph("<b>Status:</b> Instituído", styles["Normal"]))
            story.append(Paragraph(f"<b>Justificativa:</b> {resposta.get('justificativa_instituido', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"<b>Evidências:</b> {resposta.get('evidencias_instituido', 'N/A')}", styles["Normal"]))
        
        # Institucionalizado
        if resposta.get("institucionalizado"):
            story.append(Paragraph("<b>Status:</b> Institucionalizado", styles["Normal"]))
            story.append(Paragraph(f"<b>Justificativa:</b> {resposta.get('justificativa_institucionalizado', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"<b>Evidências:</b> {resposta.get('evidencias_institucionalizado', 'N/A')}", styles["Normal"]))
            
        story.append(Spacer(1, 12))

    
    doc.build(story)
    buffer.seek(0)
    return buffer