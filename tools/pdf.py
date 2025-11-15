import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


def generate_pdf(dna_report, method, progress, lesson, user_id):
    from tools.utils import ensure_dir
    user_dir = ensure_dir(f"data/users/{user_id}")
    path = f"{user_dir}/GENELINGUA_COMPREHENSIVE_REPORT.pdf"

    # Create high-quality PDF document
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
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

    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )

    japanese_style = ParagraphStyle(
        'JapaneseText',
        parent=styles['Normal'],
        fontSize=11,
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
    )

    warning_style = ParagraphStyle(
        'WarningStyle',
        parent=normal_style,
        fontSize=9,
        textColor=HexColor('#e65100')
    )

    # =========================
    # TITLE PAGE
    # =========================
    story.append(Paragraph("GENELINGUA v7", title_style))
    story.append(Paragraph("Comprehensive DNA + AI Language Learning Report", ParagraphStyle(
        'Subtitle', parent=normal_style, fontSize=14, alignment=TA_CENTER, textColor=HexColor('#666'))))
    story.append(Spacer(1, 30))

    # User info
    try:
        if isinstance(dna_report, dict):
            percentile = dna_report.get(
                'pgs_results', {}).get('percentile', 'N/A')
            z_score = dna_report.get('pgs_results', {}).get('z_score', 0.0)
            ancestry = dna_report.get('metadata', {}).get(
                'selected_ancestry', 'N/A')
            ancestry_label = dna_report.get(
                'metadata', {}).get('ancestry_label', ancestry)
        else:
            percentile = getattr(dna_report.pgs_results, 'percentile', 'N/A')
            z_score = getattr(dna_report.pgs_results, 'z_score', 0.0)
            ancestry = 'N/A'
            ancestry_label = 'N/A'

        user_info = f"""<b>User:</b> {user_id}<br/>
<b>Ancestry:</b> {ancestry_label}<br/>
<b>DNA Percentile:</b> {percentile}th percentile<br/>
<b>Z-Score:</b> {z_score:+.2f}<br/>
<b>Generated:</b> {dna_report.get('metadata', {}).get('generated', 'N/A')[:10] if isinstance(dna_report, dict) else 'N/A'}"""
        story.append(Paragraph(user_info, normal_style))
    except:
        story.append(Paragraph(f"<b>User:</b> {user_id}", normal_style))

    story.append(Spacer(1, 30))

    # =========================
    # TABLE OF CONTENTS (UPDATED ORDER)
    # =========================
    story.append(Paragraph("TABLE OF CONTENTS", heading_style))
    toc_items = [
        "1. Polygenic Score Results",
        "2. Visual Analytics (Charts & Graphs)",
        "3. Genetic Details (SNP Contributions)",
        "4. Learning Scenarios & Time Estimates",
        "5. Your Personalized Study Plan",
        "6. Today's Lesson Content",
        "7. Executive Summary",
        "8. Scientific Limitations & Disclaimers"
    ]
    for item in toc_items:
        story.append(Paragraph(item, bullet_style))

    story.append(PageBreak())

    # =========================
    # POLYGENIC SCORE RESULTS
    # =========================
    story.append(Paragraph("POLYGENIC SCORE RESULTS", heading_style))

    try:
        if isinstance(dna_report, dict):
            pgs = dna_report.get('pgs_results', {})
            raw_score = pgs.get('raw_score', 0)
            z_score = pgs.get('z_score', 0)
            percentile = pgs.get('percentile', 50)
            category = pgs.get('category', 'Average')
            r2 = pgs.get('estimated_r2_percent', 0)
            n_valid = pgs.get('n_valid_snps', 0)
            n_total = pgs.get('n_total_snps', 0)

            score_info = f"""<b>Raw Score:</b> {raw_score:.4f}<br/>
<b>Z-Score:</b> {z_score:+.3f}<br/>
<b>Percentile:</b> {percentile:.1f}%<br/>
<b>Category:</b> {category}<br/>
<b>Valid SNPs:</b> {n_valid} / {n_total}<br/>
<b>Estimated R² (variance explained):</b> {r2:.2f}%"""
            story.append(Paragraph(score_info, normal_style))
    except:
        story.append(
            Paragraph("Polygenic score data not available", normal_style))

    story.append(Spacer(1, 20))

    # =========================
    # INTERPRETATION (FIXED TEXT FOR "Above Average")
    # =========================
    story.append(Paragraph("INTERPRETATION", heading_style))

    try:
        if isinstance(dna_report, dict):
            interp = dna_report.get('interpretation', {})

            # FORCE CORRECT MESSAGE FOR "Above Average"
            if interp.get('category') == 'Above Average':
                interp['main_text'] = (
                    "Your polygenic score is above average. "
                    "This is where most successful learners are."
                )

            story.append(
                Paragraph(f"<b>Category:</b> {interp.get('category', 'N/A')}", normal_style))
            story.append(Spacer(1, 8))
            story.append(Paragraph(interp.get('main_text', ''), normal_style))
            story.append(Spacer(1, 8))
            story.append(
                Paragraph("<b>What this means for you:</b>", subheading_style))
            story.append(Paragraph(interp.get('advice', ''), normal_style))
            story.append(Spacer(1, 8))
            story.append(Paragraph(interp.get(
                'variance_text', ''), normal_style))
    except Exception as e:
        story.append(Paragraph(f"Interpretation error: {e}", normal_style))

    story.append(PageBreak())

    # =========================
    # VISUAL ANALYTICS SECTION
    # =========================
    story.append(Paragraph("VISUAL ANALYTICS", heading_style))
    story.append(Paragraph(
        "This section contains all charts and visualizations from your analysis.", normal_style))
    story.append(Spacer(1, 20))

    # DNA VISUALIZATION
    story.append(Paragraph("DNA Analysis Visualization", subheading_style))
    dna_report_path = os.path.join(user_dir, "dna_report.png")

    if os.path.exists(dna_report_path):
        try:
            img = Image(dna_report_path, width=7*inch, height=4.5*inch)
            story.append(img)
            story.append(Spacer(1, 12))
            story.append(Paragraph(
                "This visualization shows: (1) Your score vs population distribution, (2) Percentile rank, "
                "(3) Individual SNP contributions, (4) Evidence quality distribution, (5) Contributions by cognitive domain.",
                normal_style))
        except Exception as e:
            story.append(
                Paragraph(f"DNA visualization could not be loaded: {str(e)}", normal_style))
    else:
        story.append(Paragraph(
            "DNA visualization will be generated after processing.", normal_style))

    story.append(Spacer(1, 20))

    # PROGRESS TRACKER CHART
    story.append(Paragraph("Progress Projection", subheading_style))
    try:
        if isinstance(progress, dict):
            b2_months = progress.get('b2_months', 18)
            graph_path = progress.get('graph')
        else:
            b2_months = getattr(progress, 'b2_months', 18)
            graph_path = getattr(progress, 'graph', None)

        story.append(Paragraph(
            f"<b>Estimated time to B2 level:</b> {b2_months} months with consistent practice", normal_style))

        if graph_path and os.path.exists(graph_path):
            story.append(Spacer(1, 12))
            try:
                img = Image(graph_path, width=6*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 12))
                story.append(Paragraph(
                    "This chart projects your language proficiency level over time based on consistent daily practice.",
                    normal_style))
            except:
                pass
    except:
        story.append(
            Paragraph("Progress visualization not available", normal_style))

    story.append(PageBreak())

    # =========================
    # GENETIC DETAILS SECTION
    # =========================
    story.append(Paragraph("GENETIC DETAILS", heading_style))

    # TOP CONTRIBUTORS
    story.append(Paragraph("Top Genetic Contributors", subheading_style))

    try:
        if isinstance(dna_report, dict):
            top_contribs = dna_report.get('top_contributors', [])
            for tc in top_contribs[:5]:
                story.append(Paragraph(
                    f"<b>{tc['rsid']}</b> ({tc['gene']}) - {tc['dosage_text']}", subheading_style))
                contrib_info = f"""<b>Your genotype:</b> {tc['genotype']} | <b>Contribution:</b> {tc['contribution']:+.5f}<br/>
<b>Phenotype:</b> {tc['phenotype']}<br/>
<b>Evidence:</b> {tc['evidence']} | <b>Study:</b> {tc['population']}<br/>
<i>{tc['notes']}</i>"""
                story.append(Paragraph(contrib_info, normal_style))
                story.append(Spacer(1, 10))
    except:
        story.append(
            Paragraph("Top contributors data not available", normal_style))

    story.append(Spacer(1, 20))

    # DETAILED SNP TABLE
    story.append(
        Paragraph("Complete SNP Contributions Table", subheading_style))

    try:
        if isinstance(dna_report, dict):
            snp_data = []
            snp_data.append(['SNP', 'Gene', 'Geno', 'Dose',
                            'Beta', 'Contrib', 'Evidence'])

            contribs = dna_report.get('snp_contributions', {})
            for rsid, c in sorted(contribs.items(), key=lambda x: abs(x[1].get('contrib', 0) or 0), reverse=True)[:16]:
                snp_data.append([
                    rsid,
                    c['gene'][:10],
                    c['genotype'],
                    str(c['dosage']) if c['dosage'] is not None else '—',
                    f"{c['beta']:+.3f}",
                    f"{c['contrib']:+.4f}" if c['contrib'] is not None else '—',
                    c['evidence'][:4]
                ])

            table = Table(snp_data, colWidths=[
                          1.2*cm, 1.8*cm, 1*cm, 0.8*cm, 1*cm, 1.2*cm, 1.2*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [HexColor('#f9f9f9'), HexColor('#ffffff')])
            ]))
            story.append(table)
    except Exception as e:
        story.append(
            Paragraph(f"SNP table could not be generated: {str(e)}", normal_style))

    story.append(PageBreak())

    # =========================
    # SCENARIO COMPARISONS
    # =========================
    story.append(Paragraph("LEARNING TIME SCENARIOS", heading_style))
    story.append(Paragraph(
        "Time to reach B2 level (conversational fluency) under different conditions:",
        normal_style))
    story.append(Spacer(1, 12))

    try:
        if isinstance(dna_report, dict):
            scenarios = dna_report.get('scenarios', [])
            scenario_data = [['Scenario', 'Genetics',
                              'Method', 'Daily Min', 'Hours', 'Months']]

            for scen in scenarios[:6]:
                scenario_data.append([
                    scen['scenario'][:25],
                    scen['genetics'],
                    scen['method'][:6],
                    str(scen['daily_minutes']),
                    str(scen['total_hours']),
                    str(scen['months_to_b2'])
                ])

            table = Table(scenario_data, colWidths=[
                          5*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [HexColor('#f9f9f9'), HexColor('#ffffff')])
            ]))
            story.append(table)

            story.append(Spacer(1, 12))
            story.append(Paragraph(
                "<b>Key Insight:</b> Notice how 'Bottom 10% genetics + optimal method' beats 'Top 10% genetics + poor method' by 10+ months. "
                "This shows the real-world importance of study method vs. genetics.",
                ParagraphStyle('KeyInsight', parent=normal_style, fontSize=10, textColor=HexColor('#27ae60'))))
    except:
        story.append(Paragraph("Scenario data not available", normal_style))

    story.append(PageBreak())

    # =========================
    # PERSONALIZED STUDY PLAN
    # =========================
    story.append(Paragraph("YOUR PERSONALIZED STUDY PLAN", heading_style))

    # Study Method
    story.append(Paragraph("Your Recommended Approach", subheading_style))
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
    except:
        story.append(
            Paragraph("Method information not available", normal_style))

    story.append(Spacer(1, 20))

    # EVIDENCE-BASED LEARNING PLAN
    story.append(Paragraph("Evidence-Based Framework", subheading_style))

    learning_plan = """<b>The 70-20-10 Framework (2 hours/day)</b><br/><br/>
<b>1. Comprehensible Input (70% = 84 min/day)</b><br/>
• Listening: Podcasts, YouTube, audiobooks at 90%% comprehension level<br/>
• Reading: Graded readers → native materials with popup dictionaries<br/>
• Focus: Volume over perfection. Aim for 10+ hours/week of input<br/><br/>

<b>2. Explicit Study (20% = 24 min/day)</b><br/>
• SRS (Anki): 15 min/day of sentence mining or frequency-based decks<br/>
• Grammar: 10 min/day learning patterns in context<br/>
• Pronunciation: 5 min shadowing or phonetic drills<br/><br/>

<b>3. Production Practice (10% = 12 min/day)</b><br/>
• Speaking: iTalki tutors, language exchange, or shadowing<br/>
• Writing: Journaling with corrections<br/><br/>

<b>Factors that predict success (sorted by effect size):</b><br/>
Total hours of practice (R² ≈ 0.40-0.60)<br/>
Quality of input (R² ≈ 0.15-0.25)<br/>
Age of acquisition (R² ≈ 0.10-0.20 for pronunciation)<br/>
Working memory (R² ≈ 0.05-0.10)<br/>
Motivation & persistence (R² ≈ 0.05-0.10)<br/>
Your genetic variants (R² ≈ 0.02-0.04)<br/><br/>

<b>Translation:</b> If you score at the 10th genetic percentile but study 2 hours/day with good methods,
you'll surpass someone at the 90th percentile who studies 30 min/day poorly."""

    story.append(Paragraph(learning_plan, normal_style))

    story.append(PageBreak())

    # =========================
    # TODAY'S LESSON
    # =========================
    story.append(Paragraph("TODAY'S PERSONALIZED LESSON", heading_style))
    try:
        if isinstance(lesson, dict):
            words = lesson.get('words', [])
            sentences = lesson.get('sentences', [])
            language = lesson.get('language', 'japanese')
        else:
            words = getattr(lesson, 'words', [])
            sentences = getattr(lesson, 'sentences', [])
            language = 'japanese'

        if words:
            story.append(
                Paragraph(f"<b>Vocabulary Words ({language.title()}):</b>", subheading_style))
            story.append(Spacer(1, 6))
            for word in words[:15]:
                try:
                    clean_word = str(word).encode('utf-8').decode('utf-8')
                    story.append(Paragraph(f"• {clean_word}", japanese_style))
                except:
                    story.append(Paragraph(f"• {word}", bullet_style))
            story.append(Spacer(1, 12))

        if sentences:
            story.append(
                Paragraph("<b>Practice Sentences:</b>", subheading_style))
            story.append(Spacer(1, 6))
            for i, sentence in enumerate(sentences[:8], 1):
                try:
                    clean_sentence = str(sentence).encode(
                        'utf-8').decode('utf-8')
                    story.append(
                        Paragraph(f"{i}. {clean_sentence}", japanese_style))
                except:
                    story.append(Paragraph(f"{i}. {sentence}", bullet_style))
    except:
        story.append(Paragraph("Lesson content not available", normal_style))

    # =========================
    # EXECUTIVE SUMMARY (MOVED TO END)
    # =========================
    story.append(PageBreak())
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))

    try:
        if isinstance(dna_report, dict):
            pgs = dna_report.get('pgs_results', {})
            percentile = pgs.get('percentile', 50)
            category = pgs.get('category', 'Average')

            executive_summary = f"""<b>Your Genetic Profile:</b> {category} ({percentile:.1f}th percentile)<br/><br/>
<b>Key Takeaway:</b> Your genetics account for approximately 2-4%% of language learning variance. 
Study method, time invested, and motivation are 20-50x more impactful.<br/><br/>
<b>Recommended Focus:</b> Prioritize evidence-based methods (comprehensible input, spaced repetition) 
over genetic optimization.<br/><br/>
<b>Time to B2 Fluency:</b> {progress.get('b2_months', 18) if isinstance(progress, dict) else getattr(progress, 'b2_months', 18)} months 
with 2 hours/day of optimal practice."""
            story.append(Paragraph(executive_summary, normal_style))
    except Exception as e:
        story.append(Paragraph(f"Summary error: {e}", normal_style))

    # =========================
    # SCIENTIFIC LIMITATIONS & DISCLAIMERS (MOVED TO END)
    # =========================
    story.append(PageBreak())
    story.append(
        Paragraph("SCIENTIFIC LIMITATIONS & DISCLAIMERS", heading_style))
    warnings = [
        "• No validated 'language learning PGS' exists. These SNPs come from studies of reading, memory, hearing, and cognitive ability.",
        "• Small effect sizes: Combined, these variants explain ~2-4% of variance in related cognitive traits.",
        "• Ancestry matters critically: Most studies are European-ancestry. COMT shows opposite effects in East Asian populations.",
        "• Environment >> Genetics: Study method, motivation, immersion time, and instruction quality are 20-50x more important.",
        "• Educational tool only: Not diagnostic, not predictive of individual success."
    ]
    for warning in warnings:
        story.append(Paragraph(warning, warning_style))
        story.append(Spacer(1, 4))

    # Build PDF
    try:
        doc.build(story)
        print(f"Comprehensive PDF generated successfully: {path}")
        return path
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None
