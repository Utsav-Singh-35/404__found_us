"""
Agent 8: Report Agent
Purpose: Generate professional PDF reports
"""

from jinja2 import Template
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId
from app.database import (
    submissions_collection,
    claims_collection,
    fact_checks_collection,
    evidence_collection,
    summaries_collection
)
import os

class ReportAgent:
    """Agent 8: PDF report generation"""
    
    def __init__(self):
        # Ensure reports directory exists
        os.makedirs("./storage/reports", exist_ok=True)
    
    def generate_report(self, claim_id: ObjectId) -> Dict[str, Any]:
        """
        Generate PDF report
        
        Returns:
            {
                "pdf_path": "./storage/reports/report123.pdf",
                "generated_at": datetime
            }
        """
        
        # Gather all data
        claim = claims_collection.find_one({"_id": claim_id})
        if not claim:
            raise ValueError("Claim not found")
        
        submission = submissions_collection.find_one(
            {"_id": claim['submission_id']}
        )
        fact_checks = list(fact_checks_collection.find({"claim_id": claim_id}))
        evidence = list(evidence_collection.find({"claim_id": claim_id}))
        summary = summaries_collection.find_one({"claim_id": claim_id})
        
        # If no summary, create a basic one
        if not summary:
            summary = {
                "short_explanation": "Analysis in progress or unavailable.",
                "confidence": 0.5,
                "llm_confidence": 0.5,
                "calculated_confidence": 0.5,
                "top_sources": [],
                "metadata": {
                    "fact_checks_found": len(fact_checks),
                    "evidence_collected": len(evidence),
                    "model_used": "N/A"
                }
            }
        
        # Prepare context
        context = {
            "report_id": str(ObjectId()),
            "submission": submission,
            "claim": claim,
            "fact_checks": fact_checks,
            "evidence": evidence,
            "summary": summary,
            "generated_at": datetime.utcnow()
        }
        
        # Render HTML
        html_content = self._render_template(context)
        
        # Generate PDF
        pdf_path = f"./storage/reports/report_{claim_id}.pdf"
        
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(pdf_path)
            print(f"✓ PDF generated with WeasyPrint: {pdf_path}")
        except ImportError:
            print("⚠️  WeasyPrint not available, saving HTML instead")
            # Fallback: save as HTML
            pdf_path = f"./storage/reports/report_{claim_id}.html"
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            print(f"⚠️  PDF generation failed: {e}")
            # Fallback: save as HTML
            pdf_path = f"./storage/reports/report_{claim_id}.html"
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return {
            "pdf_path": pdf_path,
            "generated_at": context['generated_at']
        }
    
    def _render_template(self, context: Dict[str, Any]) -> str:
        """Render HTML template for PDF"""
        
        template_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Fact-Check Report</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
        }
        
        .header {
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 28px;
        }
        
        .header .subtitle {
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 10px;
        }
        
        .section {
            margin-bottom: 30px;
            page-break-inside: avoid;
        }
        
        .section h2 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 15px;
            font-size: 20px;
        }
        
        .info-box {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        
        .info-box strong {
            color: #2c3e50;
        }
        
        .verdict-box {
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: center;
        }
        
        .verdict-box.high {
            background: #d4edda;
            border: 2px solid #28a745;
        }
        
        .verdict-box.medium {
            background: #fff3cd;
            border: 2px solid #ffc107;
        }
        
        .verdict-box.low {
            background: #f8d7da;
            border: 2px solid #dc3545;
        }
        
        .verdict-box .confidence {
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .verdict-box.high .confidence {
            color: #28a745;
        }
        
        .verdict-box.medium .confidence {
            color: #ffc107;
        }
        
        .verdict-box.low .confidence {
            color: #dc3545;
        }
        
        .evidence-item {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }
        
        .evidence-item h3 {
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 16px;
        }
        
        .evidence-item .meta {
            color: #7f8c8d;
            font-size: 12px;
            margin-bottom: 8px;
        }
        
        .evidence-item .snippet {
            color: #555;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .evidence-item a {
            color: #3498db;
            text-decoration: none;
            word-break: break-all;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .badge.supports {
            background: #d4edda;
            color: #155724;
        }
        
        .badge.refutes {
            background: #f8d7da;
            color: #721c24;
        }
        
        .badge.neutral {
            background: #e2e3e5;
            color: #383d41;
        }
        
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #7f8c8d;
        }
        
        .footer h3 {
            color: #2c3e50;
            font-size: 14px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        table th {
            background: #2c3e50;
            color: white;
            padding: 10px;
            text-align: left;
        }
        
        table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <h1>🔍 AI Fact-Check Report</h1>
        <div class="subtitle">
            Report ID: {{ report_id }}<br>
            Generated: {{ generated_at.strftime('%B %d, %Y at %H:%M UTC') }}
        </div>
    </div>
    
    <!-- Section 1: Original Input -->
    <div class="section">
        <h2>1. Original Submission</h2>
        <div class="info-box">
            <strong>Input Type:</strong> {{ submission.input_type|upper }}<br>
            <strong>Submitted:</strong> {{ submission.created_at.strftime('%Y-%m-%d %H:%M UTC') }}<br>
            {% if submission.input_type == 'image' %}
            <strong>Image:</strong> Uploaded image file<br>
            {% elif submission.input_type == 'url' %}
            <strong>URL:</strong> <a href="{{ submission.input_ref }}">{{ submission.input_ref }}</a><br>
            {% else %}
            <strong>Text:</strong> {{ submission.input_ref }}<br>
            {% endif %}
        </div>
    </div>
    
    <!-- Section 2: Extracted Claim -->
    <div class="section">
        <h2>2. Extracted Claim</h2>
        <div class="info-box">
            <strong>Original Claim:</strong><br>
            <p style="font-size: 16px; margin: 10px 0;">{{ claim.claim_text }}</p>
            
            <strong>Normalized Claim:</strong><br>
            <p style="font-size: 16px; margin: 10px 0; color: #2c3e50;">{{ claim.normalized_claim }}</p>
            
            {% if claim.entities %}
            <strong>Entities Detected:</strong> {{ claim.entities|join(', ') }}
            {% endif %}
        </div>
    </div>
    
    <!-- Section 3: Verification Result -->
    <div class="section">
        <h2>3. Verification Result</h2>
        
        {% set conf = summary.confidence %}
        {% if conf >= 0.7 %}
        <div class="verdict-box high">
        {% elif conf >= 0.4 %}
        <div class="verdict-box medium">
        {% else %}
        <div class="verdict-box low">
        {% endif %}
            <div style="font-size: 14px; color: #7f8c8d;">CONFIDENCE SCORE</div>
            <div class="confidence">{{ (conf * 100)|round|int }}%</div>
            <div style="font-size: 14px; color: #7f8c8d;">
                {% if conf >= 0.7 %}HIGH CONFIDENCE{% elif conf >= 0.4 %}MEDIUM CONFIDENCE{% else %}LOW CONFIDENCE{% endif %}
            </div>
        </div>
        
        <div class="info-box">
            <strong>Explanation:</strong><br>
            <p style="font-size: 15px; margin: 10px 0;">{{ summary.short_explanation }}</p>
        </div>
        
        <div style="margin-top: 15px;">
            <strong>Analysis Details:</strong>
            <table>
                <tr>
                    <td><strong>Fact-Checks Found:</strong></td>
                    <td>{{ summary.metadata.fact_checks_found }}</td>
                </tr>
                <tr>
                    <td><strong>Evidence Collected:</strong></td>
                    <td>{{ summary.metadata.evidence_collected }}</td>
                </tr>
                <tr>
                    <td><strong>LLM Confidence:</strong></td>
                    <td>{{ (summary.llm_confidence * 100)|round|int }}%</td>
                </tr>
                <tr>
                    <td><strong>Calculated Confidence:</strong></td>
                    <td>{{ (summary.calculated_confidence * 100)|round|int }}%</td>
                </tr>
                <tr>
                    <td><strong>Model Used:</strong></td>
                    <td>{{ summary.metadata.model_used }}</td>
                </tr>
            </table>
        </div>
    </div>
    
    <!-- Section 4: Authoritative Fact-Checks -->
    {% if fact_checks %}
    <div class="section">
        <h2>4. Authoritative Fact-Checks</h2>
        <p>Found {{ fact_checks|length }} authoritative fact-check(s):</p>
        
        {% for fc in fact_checks %}
        <div class="evidence-item">
            <h3>{{ fc.api_name }} - Verdict: <strong>{{ fc.verdict|upper }}</strong></h3>
            <div class="meta">
                Publisher: {{ fc.publisher }}<br>
                Retrieved: {{ fc.retrieved_at.strftime('%Y-%m-%d') }}
                {% if fc.similarity_score %}
                | Similarity: {{ (fc.similarity_score * 100)|round|int }}%
                {% endif %}
            </div>
            <p>{{ fc.summary }}</p>
            <a href="{{ fc.url }}" target="_blank">{{ fc.url }}</a>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Section 5: Web Evidence -->
    {% if evidence %}
    <div class="section">
        <h2>5. Web Evidence</h2>
        <p>Collected {{ evidence|length }} evidence source(s) from the web:</p>
        
        {% for ev in evidence %}
        <div class="evidence-item">
            <h3>
                {{ ev.title }}
                <span class="badge {{ ev.supports_claim }}">{{ ev.supports_claim }}</span>
            </h3>
            <div class="meta">
                Reliability: {{ (ev.reliability_score * 100)|round|int }}%
                {% if ev.published_date %}
                | Published: {{ ev.published_date.strftime('%Y-%m-%d') }}
                {% endif %}
            </div>
            <p class="snippet">{{ ev.snippet }}</p>
            <a href="{{ ev.source_url }}" target="_blank">{{ ev.source_url }}</a>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Section 6: Top Sources -->
    <div class="section">
        <h2>6. Top Sources</h2>
        <p>Most relevant sources for this verification:</p>
        <ol>
        {% for source in summary.top_sources %}
            <li style="margin-bottom: 15px;">
                <a href="{{ source.url }}" target="_blank">{{ source.url }}</a><br>
                <em style="color: #7f8c8d;">{{ source.why }}</em>
            </li>
        {% endfor %}
        </ol>
    </div>
    
    <!-- Footer -->
    <div class="footer">
        <h3>About This Report</h3>
        <p>
            This report was generated by an AI-powered fact-checking system that analyzes claims 
            using multiple authoritative sources and web evidence.
        </p>
        
        <h3>Methodology</h3>
        <ul style="margin: 10px 0;">
            <li>Claims are extracted using OCR and NLP techniques</li>
            <li>Multiple fact-checking APIs are queried (Google Fact Check, etc.)</li>
            <li>Web evidence is collected and scored for reliability</li>
            <li>AI ({{ summary.metadata.model_used }}) analyzes all evidence</li>
            <li>Confidence score calculated using weighted formula</li>
        </ul>
        
        <h3>Confidence Score Formula</h3>
        <p>
            <code>confidence = 0.6 × fact_check_score + 0.25 × evidence_ratio + 0.15 × avg_reliability</code>
        </p>
        
        <h3>Disclaimer</h3>
        <p>
            This is an automated analysis. While we strive for accuracy, this report should not be 
            the sole basis for critical decisions. Always verify with multiple sources and use 
            critical thinking.
        </p>
        
        {% if summary.hallucination_detected %}
        <p style="color: #dc3545;">
            <strong>⚠️ Note:</strong> Some AI-generated content was flagged as potentially unreliable 
            and has been filtered from this report.
        </p>
        {% endif %}
    </div>
</body>
</html>
        """
        
        template = Template(template_html)
        return template.render(**context)

# Create singleton
report_agent = ReportAgent()
