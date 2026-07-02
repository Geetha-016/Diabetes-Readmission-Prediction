import streamlit as st
import numpy as np
import pandas as pd
import joblib
import plotly.graph_objects as go

# =============================================================
# Page Configuration
# =============================================================

st.set_page_config(
    page_title="Diabetes Readmission Risk",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================
# Styling
# =============================================================

def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        :root {
            --navy: #102A43;
            --slate: #243B53;
            --teal: #0EA5A0;
            --coral: #E0533D;
            --amber: #D9A33E;
            --bg: #F4F7FA;
            --card: #FFFFFF;
            --muted: #627D98;
            --border: #E3E8EF;
        }

        .stApp { background-color: var(--bg); }

        .app-header {
            background: linear-gradient(135deg, var(--navy) 0%, var(--slate) 100%);
            padding: 2.2rem 2.5rem;
            border-radius: 14px;
            color: white;
            margin-bottom: 1.4rem;
        }
        .app-header h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.9rem;
            margin-bottom: 0.4rem;
            letter-spacing: -0.01em;
            color: #FFFFFF !important;
        }
        .app-header p {
            color: #BCCCDC;
            font-size: 0.98rem;
            max-width: 720px;
            margin: 0;
        }

        .section-label {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--teal);
            margin-bottom: 0.4rem;
        }

        div[data-testid="stMetric"] {
            background-color: var(--card);
            padding: 1rem 1.2rem;
            border-radius: 10px;
            border: 1px solid var(--border);
        }
        div[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; }

        .stTabs [data-baseweb="tab"] { font-weight: 500; }

        div.stButton > button[kind="primary"] {
            background-color: var(--navy);
            border: none;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: var(--slate);
        }

        .risk-caption { color: var(--muted); font-size: 0.85rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()

# =============================================================
# Lookup Tables (from the dataset's ID mapping reference)
# =============================================================

ADMISSION_TYPE_MAP = {
    1: "Emergency",
    2: "Urgent",
    3: "Elective",
    4: "Newborn",
    5: "Not Available",
    6: "NULL",
    7: "Trauma Center",
    8: "Not Mapped",
}

DISCHARGE_DISPOSITION_MAP = {
    1: "Discharged to home",
    2: "Discharged/transferred to another short term hospital",
    3: "Discharged/transferred to SNF",
    4: "Discharged/transferred to ICF",
    5: "Discharged/transferred to another type of inpatient care institution",
    6: "Discharged/transferred to home with home health service",
    7: "Left AMA",
    8: "Discharged/transferred to home under care of Home IV provider",
    9: "Admitted as an inpatient to this hospital",
    10: "Neonate discharged to another hospital for neonatal aftercare",
    11: "Expired",
    12: "Still patient or expected to return for outpatient services",
    13: "Hospice / home",
    14: "Hospice / medical facility",
    15: "Discharged/transferred within this institution to Medicare approved swing bed",
    16: "Discharged/transferred/referred to another institution for outpatient services",
    17: "Discharged/transferred/referred to this institution for outpatient services",
    18: "NULL",
    19: "Expired at home (Medicaid only, hospice)",
    20: "Expired in a medical facility (Medicaid only, hospice)",
    21: "Expired, place unknown (Medicaid only, hospice)",
    22: "Discharged/transferred to another rehab facility",
    23: "Discharged/transferred to a long term care hospital",
    24: "Discharged/transferred to a nursing facility (Medicaid certified, not Medicare)",
    25: "Not Mapped",
    26: "Unknown/Invalid",
    27: "Discharged/transferred to a federal health care facility",
    28: "Discharged/transferred/referred to a psychiatric hospital",
    29: "Discharged/transferred to a Critical Access Hospital (CAH)",
    30: "Discharged/transferred to another type of health care institution",
}

ADMISSION_SOURCE_MAP = {
    1: "Physician Referral",
    2: "Clinic Referral",
    3: "HMO Referral",
    4: "Transfer from a hospital",
    5: "Transfer from a Skilled Nursing Facility (SNF)",
    6: "Transfer from another health care facility",
    7: "Emergency Room",
    8: "Court/Law Enforcement",
    9: "Not Available",
    10: "Transfer from a critical access hospital",
    11: "Normal Delivery",
    12: "Premature Delivery",
    13: "Sick Baby",
    14: "Extramural Birth",
    15: "Not Available",
    17: "NULL",
    18: "Transfer from another Home Health Agency",
    19: "Readmission to same Home Health Agency",
    20: "Not Mapped",
    21: "Unknown/Invalid",
    22: "Transfer from hospital inpatient / same facility (separate claim)",
    23: "Born inside this hospital",
    24: "Born outside this hospital",
    25: "Transfer from Ambulatory Surgery Center",
    26: "Transfer from Hospice",
}


def id_selectbox(label, mapping, default_id, help_text=None):
    """Show a human-readable dropdown but return the underlying integer ID."""
    ids_sorted = sorted(mapping.keys())
    options = [f"{i} — {mapping[i]}" for i in ids_sorted]
    default_index = ids_sorted.index(default_id) if default_id in ids_sorted else 0
    choice = st.selectbox(label, options, index=default_index, help=help_text)
    return int(choice.split(" — ")[0])


def set_dummy(df, prefix, value, baseline):
    """Set a one-hot column to 1 if value differs from the dropped baseline category."""
    if value != baseline:
        col = f"{prefix}_{value}"
        if col in df.columns:
            df[col] = 1


# =============================================================
# Load Model Artifacts
# =============================================================

@st.cache_resource
def load_artifacts():
    model = joblib.load("models/logistic_regression_model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    feature_names = joblib.load("models/feature_names.pkl")
    return model, scaler, feature_names


try:
    model, scaler, feature_names = load_artifacts()
except FileNotFoundError as e:
    st.error(f"Could not load model artifacts: {e}")
    st.stop()

# =============================================================
# Header
# =============================================================

st.markdown(
    """
    <div class="app-header">
      <h1>🩺 Diabetes 30-Day Readmission Risk</h1>
      <p>Estimate a diabetic patient's likelihood of hospital readmission within 30 days,
      based on admission details, treatment history, and medication data from the encounter record.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================
# Sidebar — About
# =============================================================

with st.sidebar:
    st.markdown("### About this tool")
    st.write(
        "A logistic regression classifier trained on the UCI "
        "*Diabetes 130-US hospitals (1999–2008)* dataset, predicting "
        "whether a diabetic patient will be readmitted within 30 days "
        "of discharge."
    )
    st.divider()
    st.markdown("**Model:** Logistic Regression")
    st.markdown("**Features:** Demographics, admission details, clinical history, medications")
    st.divider()
    st.caption(
        "⚠️ Built for portfolio / demonstration purposes only. "
        "This is not a validated clinical decision-making tool."
    )

# =============================================================
# Input Tabs
# =============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    ["👤 Patient", "🏥 Admission", "📋 History & Diagnoses", "💊 Medication"]
)

with tab1:
    st.markdown('<p class="section-label">Demographics</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        race = st.selectbox(
            "Race",
            ["AfricanAmerican", "Asian", "Caucasian", "Hispanic", "Other", "Unknown"],
        )
    with c2:
        gender = st.selectbox("Gender", ["Female", "Male"])
    with c3:
        age = st.selectbox(
            "Age Group",
            [
                "[0-10]", "[10-20]", "[20-30]", "[30-40]", "[40-50]",
                "[50-60]", "[60-70]", "[70-80]", "[80-90]", "[90-100]",
            ],
        )

with tab2:
    st.markdown('<p class="section-label">Admission Details</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        admission_type_id = id_selectbox(
            "Admission Type", ADMISSION_TYPE_MAP, default_id=1,
            help_text="How the patient was admitted to the hospital.",
        )
        admission_source_id = id_selectbox(
            "Admission Source", ADMISSION_SOURCE_MAP, default_id=7,
            help_text="Where the patient was referred or transferred from.",
        )
    with c2:
        discharge_disposition_id = id_selectbox(
            "Discharge Disposition", DISCHARGE_DISPOSITION_MAP, default_id=1,
            help_text="Where the patient went after this encounter.",
        )
        time_in_hospital = st.slider("Time in Hospital (Days)", 1, 14, 5)

with tab3:
    st.markdown('<p class="section-label">Clinical Metrics</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        num_lab_procedures = st.slider("Number of Lab Procedures", 0, 140, 40)
        num_procedures = st.slider("Number of Procedures", 0, 10, 1)
        num_medications = st.slider("Number of Medications", 1, 80, 15)
        number_diagnoses = st.slider("Number of Diagnoses", 1, 16, 5)
    with c2:
        number_outpatient = st.number_input("Outpatient Visits (prior year)", min_value=0, value=0)
        number_emergency = st.number_input("Emergency Visits (prior year)", min_value=0, value=0)
        number_inpatient = st.number_input("Previous Inpatient Visits", min_value=0, value=0)

with tab4:
    st.markdown('<p class="section-label">Medication</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        metformin = st.selectbox("Metformin", ["Down", "No", "Steady", "Up"])
        insulin = st.selectbox("Insulin", ["Down", "No", "Steady", "Up"])
    with c2:
        change = st.selectbox("Medication Changed", ["No", "Ch"])
        diabetesMed = st.selectbox("Diabetes Medication", ["No", "Yes"])

st.divider()

# =============================================================
# Risk Gauge
# =============================================================

def make_gauge(probability):
    pct = probability * 100
    if pct < 30:
        bar_color = "#0EA5A0"
    elif pct < 60:
        bar_color = "#D9A33E"
    else:
        bar_color = "#E0533D"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            number={"suffix": "%", "font": {"size": 40, "family": "IBM Plex Mono"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#627D98"},
                "bar": {"color": bar_color, "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 30], "color": "#E3F6F4"},
                    {"range": [30, 60], "color": "#FBF1DE"},
                    {"range": [60, 100], "color": "#FBE6E2"},
                ],
                "threshold": {
                    "line": {"color": "#102A43", "width": 3},
                    "thickness": 0.75,
                    "value": 50,
                },
            },
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#243B53", "family": "Inter"},
    )
    return fig


# =============================================================
# Prediction
# =============================================================

predict_clicked = st.button(
    "🔍 Predict Readmission Risk", use_container_width=True, type="primary"
)

if predict_clicked:
    input_data = pd.DataFrame(np.zeros((1, len(feature_names))), columns=feature_names)

    # Numerical features
    input_data["admission_type_id"] = admission_type_id
    input_data["discharge_disposition_id"] = discharge_disposition_id
    input_data["admission_source_id"] = admission_source_id
    input_data["time_in_hospital"] = time_in_hospital
    input_data["num_lab_procedures"] = num_lab_procedures
    input_data["num_procedures"] = num_procedures
    input_data["num_medications"] = num_medications
    input_data["number_outpatient"] = number_outpatient
    input_data["number_emergency"] = number_emergency
    input_data["number_inpatient"] = number_inpatient
    input_data["number_diagnoses"] = number_diagnoses

    # One-hot encoded categoricals (baseline category stays all-zero)
    set_dummy(input_data, "race", race, baseline="AfricanAmerican")
    set_dummy(input_data, "age", age, baseline="[0-10)")
    set_dummy(input_data, "metformin", metformin, baseline="Down")
    set_dummy(input_data, "insulin", insulin, baseline="Down")

    if gender == "Male":
        input_data["gender_Male"] = 1

    if change == "No":
        input_data["change_No"] = 1

    if diabetesMed == "Yes":
        input_data["diabetesMed_Yes"] = 1

    # Medications not exposed in the UI default to "No"
    default_columns = [
        "repaglinide_No", "nateglinide_No", "chlorpropamide_No", "glimepiride_No",
        "glipizide_No", "glyburide_No", "pioglitazone_No", "rosiglitazone_No",
        "acarbose_No", "miglitol_No", "glyburide-metformin_No",
    ]
    for col in default_columns:
        if col in input_data.columns:
            input_data[col] = 1

    # Scale + predict
    input_scaled = scaler.transform(input_data)
    prediction = model.predict(input_scaled)[0]
    probability = model.predict_proba(input_scaled)[0][1]

    st.markdown('<p class="section-label">Result</p>', unsafe_allow_html=True)
    res_col1, res_col2 = st.columns([1, 1.4])

    with res_col1:
        risk = probability * 100
        if risk < 30:
            st.success("🟢 **Low Risk** of 30-day readmission")
        elif risk <= 60:
            st.warning("🟡 **Medium Risk** of 30-day readmission")
        else:
            st.error("🔴 **High Risk** of 30-day readmission")

        st.metric("Readmission Probability", f"{probability * 100:.1f}%")
        st.markdown(
            '<p class="risk-caption">Risk band shown on the gauge — Low &lt;30% · '
            "Medium 30–60% · High &gt;60% — is for visualization only.</p>",
            unsafe_allow_html=True,
        )

    with res_col2:
        st.plotly_chart(make_gauge(probability), use_container_width=True)

st.write("")
st.write("")

st.markdown("<br><br>", unsafe_allow_html=True)


st.markdown(
    """
    <div style="text-align:center; color:#627D98; font-size:14px; padding:10px;">
        Developed by <b>Geetha Iyer</b><br>
        <a href="https://github.com/Geetha-016" target="_blank">GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
