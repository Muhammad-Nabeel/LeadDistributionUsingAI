import sys
import os

# Add the root directory of the project to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import joblib
import pandas as pd
import pyodbc
from utils.db import get_connection

OUTPUT_EXCEL_PATH = "output/reassignment_report.xlsx"

def fetch_open_leads():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC GetOpenLeadsAI")
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame.from_records(rows, columns=columns)
            conn.close()
            return df
        except Exception as e:
            print(f"❌ Error executing GetOpenLeads: {e}")
            conn.close()
    return pd.DataFrame()

def fetch_call_logs():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC GetCallLogsForLeadsAI")
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame.from_records(rows, columns=columns)
            conn.close()
            return df
        except Exception as e:
            print(f"❌ Error executing GetCallLogsForLeads: {e}")
            conn.close()
    return pd.DataFrame()

def build_lead_feature_dataframe():
    leads = fetch_open_leads()
    logs = fetch_call_logs()

    if leads.empty or logs.empty:
        return pd.DataFrame()

    features = []

    for _, lead in leads.iterrows():
        lead_id = lead["LeadID"]
        taken_by = lead["TakenOverBy"]
        taken_on = lead["TakenOverOn"]
        if pd.isnull(taken_on): continue

        lead_logs = logs[logs["LeadID"] == lead_id]
        recent_logs = lead_logs.sort_values("CallDateTime", ascending=False).head(3)

        total_calls = len(lead_logs)
        recent_failures = recent_logs[recent_logs["CallStatus"] != "Connected"].shape[0]
        recent_logs["Duration"] = pd.to_numeric(recent_logs["Duration"], errors="coerce")
        avg_duration = recent_logs["Duration"].mean() if not recent_logs.empty else 0
        days_since_taken = (pd.Timestamp.now() - pd.to_datetime(taken_on)).days

        was_reassigned = 1 if recent_failures >= 3 else 0  # Label used during training

        features.append({
            "LeadID": lead_id,
            "taken_by": taken_by,
            "days_since_taken": days_since_taken,
            "total_calls": total_calls,
            "recent_failures": recent_failures,
            "avg_duration": avg_duration,
            "was_reassigned": was_reassigned
        })

    return pd.DataFrame(features)

def generate_reassignment_report():
    df = build_lead_feature_dataframe()
    if df.empty:
        print("⚠️ No data to process.")
        return

    MODEL_PATH = "models/decision_tree_model.pkl"
    ENCODER_PATH = "models/taken_by_encoder.pkl"
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        print("❌ Model or encoder not trained yet.")
        return

    # Load model and encoder
    model = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)

    # Prepare feature dataframe
    X = df.drop(columns=["LeadID", "was_reassigned"])
    X["taken_by"] = le.transform(X["taken_by"].astype(str))  # ✅ Apply same encoder

    predictions = model.predict(X)
    df["suggest_reassignment"] = predictions

    to_review = df[df["suggest_reassignment"] == 1]
    if to_review.empty:
        print("✅ No reassignment suggestions.")
    else:
        print("⚠️ Leads suggested for review:")
        print(to_review[["LeadID", "taken_by", "recent_failures", "avg_duration"]])

        # Export to Excel
        to_review.to_excel("reassignment_suggestions.xlsx", index=False)
        print("📄 Exported to reassignment_suggestions.xlsx")

    return to_review


# ✅ Run this script directly
if __name__ == "__main__":
    generate_reassignment_report()
