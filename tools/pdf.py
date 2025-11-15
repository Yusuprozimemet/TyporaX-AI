# tools/pdf.py
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
# Text alignment constants
TA_LEFT = 0
TA_CENTER = 1
TA_JUSTIFY = 4


def generate_pdf(dna_report, method, progress, lesson, user_id):
    from tools.utils import ensure_dir
    user_dir = ensure_dir(f"data/users/{user_id}")
    path = f"{user_dir}/GENELINGUA_PLAN.pdf"

    # Create high-quality PDF document
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,  # Use A4 for better international compatibility
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    story = []

    # Create enhanced styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1976D2'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=18,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )

    # Style for Japanese text
    japanese_style = ParagraphStyle(
        'JapaneseText',
        parent=styles['Normal'],
        fontSize=12,
        textColor=HexColor('#2c3e50'),
        spaceAfter=4,
        fontName='Helvetica',
        wordWrap='CJK'
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=normal_style,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    )    # Title
    story.append(Paragraph("GENELINGUA v7 — Your DNA + AI Plan", title_style))
    story.append(Spacer(1, 20))

    # User info with better formatting
    user_info = f"<b>User:</b> {user_id}"

    # Handle both dict and object access for dna_report
    try:
        if isinstance(dna_report, dict):
            percentile = dna_report.get(
                'pgs_results', {}).get('percentile', 'N/A')
            z_score = dna_report.get('pgs_results', {}).get('z_score', 0.0)
        else:
            percentile = getattr(dna_report.pgs_results, 'percentile', 'N/A')
            z_score = getattr(dna_report.pgs_results, 'z_score', 0.0)

        user_info += f" | <b>DNA Percentile:</b> {percentile}th | <b>Z-Score:</b> {z_score:+.2f}"
    except:
        user_info += " | <b>DNA:</b> Analysis pending"

    story.append(Paragraph(user_info, normal_style))
    story.append(Spacer(1, 25))

    # Method section with better handling
    story.append(Paragraph("📋 Study Method", heading_style))
    try:
        if isinstance(method, dict):
            focus = method.get('focus', 'Balanced')
            blocks = method.get('blocks', ['60min study'])
        else:
            focus = getattr(method, 'focus', 'Balanced')
            blocks = getattr(method, 'blocks', ['60min study'])

        story.append(Paragraph(f"<b>Focus:</b> {focus}", normal_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Study Blocks:</b>", normal_style))

        for block in blocks:
            story.append(Paragraph(f"• {block}", bullet_style))
    except Exception as e:
        story.append(
            Paragraph("Method information not available", normal_style))

    story.append(Spacer(1, 20))

    # Progress section
    story.append(Paragraph("📈 Progress Tracker", heading_style))
    try:
        if isinstance(progress, dict):
            b2_months = progress.get('b2_months', 18)
            graph_path = progress.get('graph')
        else:
            b2_months = getattr(progress, 'b2_months', 18)
            graph_path = getattr(progress, 'graph', None)

        story.append(Paragraph(
            f"<b>Estimated time to B2 level:</b> {b2_months} months", normal_style))

        # Add progress graph if it exists
        if graph_path and os.path.exists(graph_path):
            story.append(Spacer(1, 12))
            try:
                img = Image(graph_path, width=6*inch, height=4*inch)
                story.append(img)
            except Exception as e:
                story.append(
                    Paragraph("Progress chart not available", normal_style))
    except Exception as e:
        story.append(
            Paragraph("Progress information not available", normal_style))

    story.append(Spacer(1, 20))

    # Today's Lesson section
    story.append(Paragraph("📚 Today's Lesson", heading_style))
    try:
        if isinstance(lesson, dict):
            words = lesson.get('words', [])
            sentences = lesson.get('sentences', [])
        else:
            words = getattr(lesson, 'words', [])
            sentences = getattr(lesson, 'sentences', [])

        if words:
            story.append(Paragraph("<b>Vocabulary Words:</b>", normal_style))
            story.append(Spacer(1, 6))
            for word in words[:12]:  # Show more words
                # Ensure proper encoding for Japanese characters
                try:
                    clean_word = str(word).encode('utf-8').decode('utf-8')
                    story.append(Paragraph(f"• {clean_word}", japanese_style))
                except:
                    story.append(Paragraph(f"• {word}", bullet_style))
            story.append(Spacer(1, 12))

        if sentences:
            story.append(Paragraph("<b>Practice Sentences:</b>", normal_style))
            story.append(Spacer(1, 6))
            # Show more sentences
            for i, sentence in enumerate(sentences[:8], 1):
                try:
                    clean_sentence = str(sentence).encode(
                        'utf-8').decode('utf-8')
                    story.append(
                        Paragraph(f"{i}. {clean_sentence}", japanese_style))
                except:
                    story.append(Paragraph(f"{i}. {sentence}", bullet_style))
    except Exception as e:
        story.append(Paragraph("Lesson content not available", normal_style))

    story.append(Spacer(1, 25))

    # DNA Report section with high-quality image
    story.append(Paragraph("🧬 DNA Analysis Report", heading_style))
    dna_report_path = os.path.join(user_dir, "dna_report.png")

    if os.path.exists(dna_report_path):
        try:
            # Use larger, high-quality image
            img = Image(dna_report_path, width=7*inch, height=5*inch)
            story.append(img)
            story.append(Spacer(1, 12))
            story.append(Paragraph(
                "This chart shows your genetic predisposition for language learning compared to the general population.", normal_style))
        except Exception as e:
            story.append(
                Paragraph(f"DNA report image could not be loaded: {str(e)}", normal_style))
    else:
        story.append(Paragraph(
            "DNA report will be generated after uploading your genetic data.", normal_style))

    # Build PDF with error handling
    try:
        doc.build(story)
        print(f"PDF generated successfully: {path}")
        return path
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None
