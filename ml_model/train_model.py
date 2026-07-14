from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "isolation_forest_model.pkl"

# Path to our real CSV dataset
CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "data_collection"
    / "delhi_aqi_historical.csv"
)


def load_and_clean_data() -> pd.DataFrame:
    """
    Load CSV and clean it before training.
    Returns a clean DataFrame ready for ML.
    """

    print(f"Loading data from: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    print(f"Raw rows loaded     : {len(df)}")

    # Step 1 — drop rows where pm25 is missing
    df = df.dropna(subset=["pm25"])
    print(f"After dropping nulls: {len(df)}")

    # Step 2 — convert to float safely
    df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")
    df = df.dropna(subset=["pm25"])

    # Step 3 — remove physically impossible values
    # PM2.5 = 0 means sensor is offline or broken
    # PM2.5 > 500 is almost always a sensor malfunction
    df = df[df["pm25"] > 0.5]
    df = df[df["pm25"] <= 500]
    print(f"After range filter  : {len(df)}")

    # Step 4 — remove exact duplicates
    df = df.drop_duplicates(subset=["pm25"])
    print(f"After deduplication : {len(df)}")

    return df


def analyze_data(df: pd.DataFrame) -> None:
    """Print statistics so we understand our training data."""

    pm25 = df["pm25"]

    print("\n── Data analysis ──────────────────────")
    print(f"Total clean readings : {len(pm25)}")
    print(f"Min PM2.5            : {pm25.min():.2f}")
    print(f"Max PM2.5            : {pm25.max():.2f}")
    print(f"Mean PM2.5           : {pm25.mean():.2f}")
    print(f"Median PM2.5         : {pm25.median():.2f}")
    print(f"Std deviation        : {pm25.std():.2f}")

    # Show distribution buckets — helps understand data spread
    print("\n── PM2.5 distribution ─────────────────")
    print(f"0–12   (Good)        : {len(pm25[pm25 <= 12])}")
    print(f"12–35  (Moderate)    : {len(pm25[(pm25 > 12) & (pm25 <= 35)])}")
    print(f"35–55  (Unhealthy)   : {len(pm25[(pm25 > 35) & (pm25 <= 55)])}")
    print(f"55–150 (Very unhlthy): {len(pm25[(pm25 > 55) & (pm25 <= 150)])}")
    print(f"150+   (Hazardous)   : {len(pm25[pm25 > 150])}")
    print("────────────────────────────────────────\n")


def train_model() -> None:
    """
    Full pipeline:
    Load → Clean → Analyze → Train → Evaluate → Save
    """

    # ── Step 1: Load and clean ───────────────────────────
    df = load_and_clean_data()

    if len(df) < 50:
        print(
            "Not enough clean data to train reliably. "
            "Need at least 50 rows."
        )
        return

    # ── Step 2: Analyze ──────────────────────────────────
    analyze_data(df)

    # ── Step 3: Prepare features ─────────────────────────
    # Isolation Forest only needs the pm25 column for now
    # Later we will add pm10, no2, hour, day_of_week etc.
    features = df[["pm25"]]

    # ── Step 4: Train/test split ─────────────────────────
    # 80% training, 20% testing — standard ML practice
    train_features, test_features = train_test_split(
        features,
        test_size=0.2,
        random_state=42,
    )

    print(f"Training rows : {len(train_features)}")
    print(f"Testing rows  : {len(test_features)}")

    # ── Step 5: Train Isolation Forest ───────────────────
    # contamination = estimated % of anomalies in the data
    # For PM2.5 data, ~5% is a reasonable starting estimate
    model = IsolationForest(
        contamination=0.05,
        n_estimators=100,   # More trees = more reliable
        random_state=42,
    )

    print("\nTraining Isolation Forest...")
    model.fit(train_features)
    print("Training complete.")

    # ── Step 6: Evaluate on test set ─────────────────────
    predictions = model.predict(test_features)

    total = len(predictions)
    anomalies = int((predictions == -1).sum())
    normal = total - anomalies

    print("\n── Test set evaluation ─────────────────")
    print(f"Total test readings : {total}")
    print(f"Classified normal   : {normal}")
    print(f"Classified anomaly  : {anomalies}")
    print(
        f"Anomaly rate        : "
        f"{anomalies/total*100:.1f}%"
    )
    print("────────────────────────────────────────")

    # ── Step 7: Quick sanity check ───────────────────────
    # Test with known values to make sure model makes sense
    print("\n── Sanity check ────────────────────────")

    test_cases = [
        (5.0,   "very clean air"),
        (15.0,  "good air"),
        (35.0,  "moderate"),
        (75.0,  "unhealthy"),
        (200.0, "very unhealthy"),
        (400.0, "hazardous"),
    ]

    for value, label in test_cases:
        sample = pd.DataFrame([{"pm25": value}])
        pred = model.predict(sample)[0]
        score = model.decision_function(sample)[0]
        status = "Anomaly" if pred == -1 else "Normal"
        print(
            f"PM2.5 {value:>6.1f} ({label:>16}) "
            f"→ {status:>7}  score: {score:.4f}"
        )

    print("────────────────────────────────────────\n")

    # ── Step 8: Save model ───────────────────────────────
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")
    print("\nModel is ready for production use.")


if __name__ == "__main__":
    train_model()