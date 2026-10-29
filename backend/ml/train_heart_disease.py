import argparse
from pathlib import Path

from ml.train_common import train_model


FEATURES = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach",
    "exang", "oldpeak", "slope", "ca", "thal",
]


def main():
    parser = argparse.ArgumentParser(description="Train the processed Cleveland heart disease classifiers.")
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "heart_disease.csv")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "artifacts" / "models")
    arguments = parser.parse_args()
    metadata = train_model(
        "heart-disease", arguments.data, FEATURES, "num", arguments.output,
        {0: 0, 1: 1, 2: 1, 3: 1, 4: 1},
    )
    print(f"Selected {metadata['selected_model']}; evaluated on {metadata['test_rows']} held-out rows.")


if __name__ == "__main__":
    main()
