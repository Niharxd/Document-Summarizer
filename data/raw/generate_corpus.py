"""
Generates the remaining sample corpus documents (PDF and DOCX).
Run once from the project root with the venv active.
"""
from pathlib import Path
from pypdf import PdfWriter
from docx import Document

RAW = Path("data/raw")


def write_pdf(path: Path, title: str, body: str) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    # pypdf does not support rich text drawing; embed text via annotation stream
    # Use a simple content stream approach
    content = f"BT /F1 11 Tf 50 740 Td ({title}) Tj ET"
    # For a readable PDF we write lines via multiple Td moves
    lines = [title, ""] + body.strip().splitlines()
    stream_lines = []
    stream_lines.append("BT")
    stream_lines.append("/F1 10 Tf")
    stream_lines.append("40 750 Td")
    stream_lines.append("12 TL")  # leading
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"({safe}) Tj T*")
    stream_lines.append("ET")
    content_stream = "\n".join(stream_lines).encode()
    page.get("/Resources")  # ensure Resources exists
    from pypdf.generic import (
        ArrayObject, NameObject, DictionaryObject, DecodedStreamObject
    )
    # Attach font resource
    font_dict = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    resources = DictionaryObject({
        NameObject("/Font"): DictionaryObject({
            NameObject("/F1"): font_dict
        })
    })
    stream_obj = DecodedStreamObject()
    stream_obj.set_data(content_stream)
    page[NameObject("/Resources")] = resources
    page[NameObject("/Contents")] = stream_obj
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        writer.write(f)


def write_docx(path: Path, title: str, body: str) -> None:
    doc = Document()
    doc.add_heading(title, level=1)
    for para in body.strip().split("\n\n"):
        doc.add_paragraph(para.strip())
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)


# ── LEGAL ────────────────────────────────────────────────────────────────────

LEGAL_EMPLOYMENT_CONTRACT = """\
EMPLOYMENT CONTRACT

This Employment Contract is entered into on June 1, 2024, between Harlow & Associates LLP
("Employer") and the individual identified below ("Employee").

POSITION AND DUTIES
The Employee is hired as a Senior Legal Analyst. The Employee shall perform duties including
contract review, legal research, regulatory compliance analysis, and client advisory support.

COMPENSATION
The Employee shall receive an annual base salary of ninety-two thousand dollars ($92,000),
payable bi-weekly. The Employee is eligible for an annual performance bonus of up to 15%
of base salary, subject to performance review.

BENEFITS
The Employee is entitled to: 20 days paid annual leave, 10 days sick leave, health insurance
coverage under the Employer's group plan, and participation in the 401(k) plan with 4%
employer matching.

PROBATIONARY PERIOD
The first ninety (90) days of employment constitute a probationary period during which either
party may terminate the contract with one (1) week written notice.

NON-COMPETE CLAUSE
For a period of twelve (12) months following termination, the Employee agrees not to engage
in any business activity that directly competes with the Employer within a 50-mile radius.

TERMINATION
After the probationary period, either party may terminate this contract with thirty (30) days
written notice. The Employer may terminate immediately for cause, including gross misconduct,
fraud, or material breach of this Agreement.

GOVERNING LAW
This contract is governed by the laws of the State of California.
"""

LEGAL_LEASE_AGREEMENT = """\
COMMERCIAL LEASE AGREEMENT

This Commercial Lease Agreement is made on July 15, 2024, between Pinnacle Properties LLC
("Landlord") and Vertex Tech Solutions Inc. ("Tenant").

PREMISES
The Landlord agrees to lease to the Tenant the commercial premises located at Suite 400,
Tower One Business Park, Springfield, comprising approximately 2,400 square feet of
office space ("Premises").

LEASE TERM
The lease term shall commence on August 1, 2024, and expire on July 31, 2026, unless
renewed or terminated in accordance with this Agreement.

RENT
The Tenant shall pay monthly rent of eight thousand five hundred dollars ($8,500), due on
the first day of each month. A security deposit of seventeen thousand dollars ($17,000)
is payable upon signing.

PERMITTED USE
The Premises shall be used solely for general office and technology business purposes.
The Tenant shall not use the Premises for any unlawful purpose or in any manner that
causes a nuisance to neighbouring tenants.

MAINTENANCE AND REPAIRS
The Tenant is responsible for routine maintenance and minor repairs. The Landlord is
responsible for structural repairs, roof maintenance, and HVAC servicing.

ALTERATIONS
The Tenant shall not make structural alterations to the Premises without prior written
consent from the Landlord. Approved alterations become the property of the Landlord
upon lease termination unless otherwise agreed in writing.

RENEWAL OPTION
The Tenant has the option to renew this lease for one additional two-year term at a rent
increase not exceeding 5%, provided written notice is given at least 90 days before expiry.
"""

# ── MEDICAL ──────────────────────────────────────────────────────────────────

MEDICAL_DISCHARGE_SUMMARY = """\
HOSPITAL DISCHARGE SUMMARY

Patient Reference: DISCH-2024-0112
Admission Date: May 5, 2024
Discharge Date: May 9, 2024
Attending Physician: Dr. Samuel Okafor, MD
Ward: General Surgery

REASON FOR ADMISSION
The patient, a 34-year-old female, was admitted with acute right iliac fossa pain, nausea,
and low-grade fever consistent with acute appendicitis.

INVESTIGATIONS ON ADMISSION
- WBC: 14.2 x10^9/L (elevated)
- CRP: 87 mg/L (elevated)
- Ultrasound abdomen: Non-compressible appendix, diameter 9mm, periappendiceal fat stranding
- CT abdomen/pelvis: Confirmed acute appendicitis, no perforation or abscess

PROCEDURE PERFORMED
Laparoscopic appendicectomy performed on May 6, 2024 under general anaesthesia.
Operative findings: Acutely inflamed appendix, no perforation. Procedure uncomplicated.
Specimen sent for histopathology.

POSTOPERATIVE COURSE
The patient recovered well. Oral intake resumed on postoperative day 1. Pain managed with
paracetamol and ibuprofen. No wound complications. Afebrile at discharge.

DISCHARGE MEDICATIONS
1. Paracetamol 1g every 6 hours as needed for 5 days
2. Ibuprofen 400mg every 8 hours with food for 3 days
3. No antibiotics required (uncomplicated case)

FOLLOW-UP INSTRUCTIONS
- Review with GP in 1 week for wound check
- Return to emergency if fever >38.5C, increasing pain, or wound discharge
- Histopathology results to be reviewed at outpatient appointment in 2 weeks
- Avoid strenuous activity for 2 weeks; may return to desk work after 5 days
"""

MEDICAL_RESEARCH_ABSTRACT = """\
RESEARCH ABSTRACT

Title: Efficacy of Telehealth Interventions in Managing Type 2 Diabetes in Rural Populations

Authors: Dr. Amara Nwosu, Dr. Liang Chen, Dr. Fatima Al-Rashid
Institution: Greenfield Institute of Health Sciences
Published: Journal of Rural Health Informatics, Vol. 12, Issue 3, 2024

BACKGROUND
Access to specialist diabetes care remains limited in rural communities. Telehealth platforms
offer a potential solution by enabling remote monitoring and consultation. This study evaluates
the clinical effectiveness of a structured telehealth programme for type 2 diabetes management
in rural populations over a 12-month period.

METHODS
A randomised controlled trial was conducted with 240 participants (120 intervention, 120 control)
recruited from rural health clinics across three counties. The intervention group received monthly
video consultations with a diabetes nurse educator, continuous glucose monitoring (CGM) device
support, and a mobile app for dietary tracking. The control group received standard care.
Primary outcome: change in HbA1c at 12 months. Secondary outcomes: blood pressure, BMI,
medication adherence, and patient-reported quality of life.

RESULTS
At 12 months, the intervention group demonstrated a mean HbA1c reduction of 1.4% (from 8.6%
to 7.2%) compared to 0.3% in the control group (p<0.001). Systolic blood pressure decreased
by 8.2 mmHg in the intervention group versus 1.1 mmHg in controls (p=0.003). Medication
adherence improved by 34% in the intervention group. No significant difference in BMI was
observed between groups.

CONCLUSION
Structured telehealth interventions significantly improve glycaemic control and blood pressure
in rural patients with type 2 diabetes. These findings support wider adoption of telehealth
models in underserved communities. Further research is needed to assess long-term cost-effectiveness.

KEYWORDS: telehealth, type 2 diabetes, rural health, HbA1c, randomised controlled trial
"""

# ── TECHNICAL ────────────────────────────────────────────────────────────────

TECHNICAL_API_SPEC = """\
API SPECIFICATION DOCUMENT
Service: UserAuth API v3.1
Team: Platform Security Engineering
Date: June 10, 2024

1. OVERVIEW
The UserAuth API provides authentication and authorisation services for all internal
microservices within the Helios Platform. It implements OAuth 2.0 with PKCE and supports
JWT-based access tokens with a configurable expiry window.

2. BASE URL
Production:  https://auth.helios-platform.internal/v3
Staging:     https://auth-staging.helios-platform.internal/v3

3. AUTHENTICATION FLOW
3.1 Authorization Code Flow with PKCE
  Step 1: Client generates code_verifier and code_challenge (SHA-256)
  Step 2: GET /authorize?response_type=code&client_id=...&code_challenge=...
  Step 3: User authenticates; server returns authorization_code
  Step 4: POST /token with code + code_verifier to exchange for access_token
  Step 5: Access token included as Bearer token in subsequent API requests

4. ENDPOINTS

POST /token
  Description: Exchange authorization code for access and refresh tokens
  Request Body (application/x-www-form-urlencoded):
    grant_type=authorization_code
    code=<authorization_code>
    code_verifier=<pkce_verifier>
    client_id=<client_id>
  Response 200:
    { "access_token": "...", "token_type": "Bearer",
      "expires_in": 3600, "refresh_token": "..." }
  Response 400: { "error": "invalid_grant" }

POST /token/refresh
  Description: Obtain a new access token using a refresh token
  Request Body:
    grant_type=refresh_token
    refresh_token=<token>
    client_id=<client_id>
  Response 200: { "access_token": "...", "expires_in": 3600 }
  Response 401: { "error": "invalid_token" }

POST /token/revoke
  Description: Revoke an active refresh token
  Request Body: token=<refresh_token>&client_id=<client_id>
  Response 200: {} (empty body on success)

GET /userinfo
  Description: Retrieve authenticated user profile
  Headers: Authorization: Bearer <access_token>
  Response 200:
    { "sub": "usr_abc123", "email": "user@example.com",
      "roles": ["read", "write"], "iat": 1717027200 }

5. ERROR CODES
  400 invalid_request    — Missing or malformed parameters
  401 invalid_token      — Token expired or revoked
  403 insufficient_scope — Token lacks required scope
  429 rate_limited       — Exceeded 100 requests/minute per client

6. RATE LIMITING
All endpoints are rate-limited to 100 requests per minute per client_id.
Responses include headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
"""

TECHNICAL_ML_REPORT = """\
MACHINE LEARNING MODEL EVALUATION REPORT
Project: Predictive Maintenance System — Turbine Fault Detection
Team: Applied ML Engineering
Date: July 2, 2024

1. OBJECTIVE
Develop a binary classification model to predict turbine bearing failures 48 hours in advance
using sensor telemetry data, reducing unplanned downtime by at least 30%.

2. DATASET
- Source: Industrial IoT sensor logs from 42 turbines over 36 months
- Total records: 4.2 million time-series observations
- Features: 28 sensor channels (vibration, temperature, RPM, oil pressure, acoustic emission)
- Class distribution: 96.3% normal, 3.7% pre-failure (imbalanced)
- Train/Validation/Test split: 70% / 15% / 15% (time-based split to prevent leakage)

3. MODELS EVALUATED
  Model A: Gradient Boosting (XGBoost) with SMOTE oversampling
  Model B: LSTM Recurrent Neural Network (sequence length: 48 hours)
  Model C: Isolation Forest (anomaly detection baseline)

4. RESULTS

  Model A — XGBoost + SMOTE:
    Precision: 0.87  |  Recall: 0.79  |  F1: 0.83  |  AUC-ROC: 0.94
    False Negative Rate: 21% (missed failures — critical metric)

  Model B — LSTM:
    Precision: 0.84  |  Recall: 0.91  |  F1: 0.87  |  AUC-ROC: 0.96
    False Negative Rate: 9% (best recall — preferred for safety-critical use)

  Model C — Isolation Forest (baseline):
    Precision: 0.61  |  Recall: 0.72  |  F1: 0.66  |  AUC-ROC: 0.81

5. SELECTED MODEL
Model B (LSTM) is selected for production deployment due to its superior recall (0.91)
and lowest false negative rate (9%). In a safety-critical context, missing a failure
is more costly than a false alarm.

6. FEATURE IMPORTANCE (XGBoost, for interpretability reference)
  1. Vibration RMS (Channel 3)     — 22.4%
  2. Bearing temperature delta     — 18.7%
  3. Oil pressure variance         — 14.2%
  4. Acoustic emission peak        — 11.9%
  5. RPM standard deviation        — 9.3%

7. DEPLOYMENT PLAN
- Serve LSTM model via FastAPI endpoint on GPU-enabled Kubernetes pod
- Inference latency target: <50ms per prediction
- Model retraining scheduled quarterly using rolling 6-month window
- Monitoring: track precision/recall drift via Evidently AI dashboard

8. LIMITATIONS
- Model performance may degrade for turbine models not represented in training data
- Requires minimum 6 hours of continuous sensor data for reliable prediction
- LSTM inference is not interpretable; XGBoost retained as explainability fallback
"""

if __name__ == "__main__":
    write_pdf(RAW / "legal" / "employment_contract.pdf",
              "EMPLOYMENT CONTRACT", LEGAL_EMPLOYMENT_CONTRACT)
    write_docx(RAW / "legal" / "lease_agreement.docx",
               "COMMERCIAL LEASE AGREEMENT", LEGAL_LEASE_AGREEMENT)

    write_pdf(RAW / "medical" / "discharge_summary.pdf",
              "HOSPITAL DISCHARGE SUMMARY", MEDICAL_DISCHARGE_SUMMARY)
    write_docx(RAW / "medical" / "research_abstract.docx",
               "RESEARCH ABSTRACT", MEDICAL_RESEARCH_ABSTRACT)

    write_pdf(RAW / "technical" / "api_specification.pdf",
              "API SPECIFICATION DOCUMENT", TECHNICAL_API_SPEC)
    write_docx(RAW / "technical" / "ml_evaluation_report.docx",
               "ML MODEL EVALUATION REPORT", TECHNICAL_ML_REPORT)

    print("Sample corpus generated successfully.")
