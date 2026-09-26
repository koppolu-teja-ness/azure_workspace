from __future__ import annotations

import streamlit as st

st.set_page_config(
	page_title="Azure -> AWS Migration Assistant",
	page_icon="M",
	layout="wide",
)

st.title("Azure -> AWS Migration Assistant")
st.caption("Phase 4 UI: discovery, approval, deployment, and reporting")

st.markdown(
	"""
Use the sidebar to open:

- `1_Discovery` to create runs from Bicep paths/directories
- `2_Migration_Plan` to inspect sequence and risk buckets
- `3_Approval_Gate` to approve, reject, or request mapping modifications
- `4_Deployment_Status` to execute target pipeline stages
- `5_Validation_Report` to inspect generated report payloads
"""
)
