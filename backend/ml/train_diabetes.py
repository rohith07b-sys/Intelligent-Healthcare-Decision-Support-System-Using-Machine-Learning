import argparse
from pathlib import Path

from ml.train_common import train_model


FEATURES = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI",
    "DiabetesPedigreeFunction", "Age",
]


def main():
    parser = argparse.ArgumentParser(description="Train the diabetes dataset classifiers.")
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "diabetes.csv")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "artifacts" / "models")
    arguments = parser.parse_args()
    metadata = train_model(
        "diabetes", arguments.data, FEATURES, "Outcome", arguments.output,
        {0: 0, 1: 1},
        zero_missing=("Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"),
    )
    print(f"Selected {metadata['selected_model']}; evaluated on {metadata['test_rows']} held-out rows.")


if __name__ == "__main__":
    main()
