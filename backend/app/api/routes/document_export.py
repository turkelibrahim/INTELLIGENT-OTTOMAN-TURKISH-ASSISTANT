from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.models.processing_outputs import ExportRecord
from app.core.security import get_current_user
import json
import csv
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

router = APIRouter(prefix="/export", tags=["Document Export"])

def check_access(doc_id: int, user: User, db: Session):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    if doc.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return doc

def get_latest_job_result(doc_id: int, db: Session):
    job = db.query(ProcessingJob).filter(
        ProcessingJob.document_id == doc_id,
        ProcessingJob.status == "COMPLETED"
    ).order_by(ProcessingJob.id.desc()).first()
    
    if not job or not job.result_summary:
        raise HTTPException(status_code=404, detail="No completed analysis found for this document")
    
    try:
        return json.loads(job.result_summary)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse analysis result")

@router.get("/txt/{document_id}")
def export_txt(document_id: int, version_type: str = "raw_ocr", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = check_access(document_id, current_user, db)
    result = get_latest_job_result(doc.id, db)
    
    record = ExportRecord(export_type=f"txt_{version_type}", document_id=doc.id, user_id=current_user.id)
    db.add(record)
    db.commit()
    
    content = ""
    if version_type == "raw_ocr":
        content = result.get("ocr", {}).get("ottoman_text", "")
    elif version_type == "latin":
        content = result.get("transliteration", {}).get("latin_text", "")
    elif version_type == "modern":
        content = result.get("modern_turkish", {}).get("text", "")
        
    return Response(content=content, media_type="text/plain", headers={
        "Content-Disposition": f"attachment; filename=document_{doc.id}_{version_type}.txt"
    })

@router.get("/json/{document_id}")
def export_json(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = check_access(document_id, current_user, db)
    result = get_latest_job_result(doc.id, db)
    
    record = ExportRecord(export_type="json_full", document_id=doc.id, user_id=current_user.id)
    db.add(record)
    db.commit()
    
    return result

@router.get("/csv/entities/{document_id}")
def export_csv_entities(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = check_access(document_id, current_user, db)
    result = get_latest_job_result(doc.id, db)
    
    record = ExportRecord(export_type="csv_entities", document_id=doc.id, user_id=current_user.id)
    db.add(record)
    db.commit()
    
    entities = result.get("entities", [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Type", "Text"])
    for ent in entities:
        writer.writerow([ent.get("label", ""), ent.get("text", "")])
        
    return Response(content=output.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename=document_{doc.id}_entities.csv"
    })

def generate_pdf(result_data, title_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    font_path = "C:/Windows/Fonts/arial.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))
        font_name = 'ArialUnicode'
    else:
        font_name = 'Helvetica'
        
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=16,
    )
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        spaceAfter=14
    )
    heading_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6
    )
    rtl_style = ParagraphStyle(
        'RTL',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=14,
        leading=20,
        alignment=2 # Right aligned
    )

    story = []
    
    # Title
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 12))
    
    # Ottoman Text (RTL)
    ottoman_raw = result_data.get("ocr", {}).get("ottoman_text", "")
    if ottoman_raw:
        story.append(Paragraph("Osmanlica Metin (OCR):", heading_style))
        for line in ottoman_raw.split('\n'):
            if line.strip():
                reshaped_text = arabic_reshaper.reshape(line)
                bidi_text = get_display(reshaped_text)
                story.append(Paragraph(bidi_text, rtl_style))
        story.append(Spacer(1, 12))
        
    # Transliteration
    latin_raw = result_data.get("transliteration", {}).get("latin_text", "")
    if latin_raw:
        story.append(Paragraph("Transliterasyon (Latin):", heading_style))
        for line in latin_raw.split('\n'):
            if line.strip():
                story.append(Paragraph(line, normal_style))
        story.append(Spacer(1, 12))
        
    # Modern Turkish
    modern_raw = result_data.get("modern_turkish", {}).get("text", "")
    if modern_raw:
        story.append(Paragraph("Modern Turkce:", heading_style))
        for line in modern_raw.split('\n'):
            if line.strip():
                story.append(Paragraph(line, normal_style))
        story.append(Spacer(1, 12))
        
    # Entities
    entities = result_data.get("entities", [])
    if entities:
        story.append(Paragraph("Tarihsel Varliklar (NER):", heading_style))
        for ent in entities:
            label = ent.get("label", "Bilinmeyen")
            text = ent.get("text", "")
            if text:
                story.append(Paragraph(f"• <b>{label}</b>: {text}", normal_style))
                
    doc.build(story)
    buffer.seek(0)
    return buffer

@router.get("/pdf/{document_id}")
def export_pdf(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = check_access(document_id, current_user, db)
    result = get_latest_job_result(doc.id, db)
    
    record = ExportRecord(export_type="pdf", document_id=doc.id, user_id=current_user.id)
    db.add(record)
    db.commit()
    
    title_text = f"Analiz Raporu: {doc.original_filename}"
    pdf_buffer = generate_pdf(result, title_text)
    
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=document_{doc.id}_report.pdf"
    })
