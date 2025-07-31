from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import joblib
import os
from services.lead_processor import build_lead_feature_dataframe

def train_and_save_model():
    df = build_lead_feature_dataframe()

    if df.empty:
        print("⚠️ No training data found.")
        return

    X = df.drop(columns=["LeadID", "was_reassigned"])
    y = df["was_reassigned"]

    # Encode categorical column(s)
    if "taken_by" in X.columns:
        le = LabelEncoder()
        X["taken_by"] = le.fit_transform(X["taken_by"].astype(str))
        joblib.dump(le, "models/taken_by_encoder.pkl")  # Save the encoder for future use

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = DecisionTreeClassifier(random_state=42)
    clf.fit(X_train, y_train)

    os.makedirs("models", exist_ok=True)
    joblib.dump(clf, "models/decision_tree_model.pkl")
    print("✅ Model trained and saved to models/decision_tree_model.pkl")

if __name__ == "__main__":
    train_and_save_model()
