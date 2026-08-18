import streamlit as st

from dashboard.auth import require_login
from dashboard.ui import PRODUCT_NAME, inject_base_css

st.set_page_config(page_title=PRODUCT_NAME, layout="wide")
require_login()
inject_base_css()

home = st.Page("views/home.py", title="Home", icon=":material/home:", default=True)

appt_type = st.Page("pages/1_📋_Appointment_Type_Wise.py", title="Appointment Type", icon="📋")
clinic = st.Page("pages/2_🏥_Clinic_Wise.py", title="Clinic", icon="🏥")
doctor = st.Page("pages/3_🩺_Doctor_Wise.py", title="Doctor", icon="🩺")

show_clinic = st.Page("pages/4_🏥_Show_Clinic_Wise.py", title="Clinic", icon="🏥")
show_customer = st.Page("pages/5_🧑_Show_Customer_Type_Wise.py", title="Customer Type", icon="🧑")
show_diagnosis = st.Page("pages/6_🩹_Show_Diagnosis_Wise.py", title="Diagnosis", icon="🩹")
show_followup_type = st.Page("pages/7_🔁_Show_Followup_Type_Wise.py", title="Follow-up Type", icon="🔁")

nav = st.navigation(
    {
        "Overview": [home],
        "Creation Dashboard": [appt_type, clinic, doctor],
        "Show Dashboard": [show_clinic, show_customer, show_diagnosis, show_followup_type],
    }
)
nav.run()
