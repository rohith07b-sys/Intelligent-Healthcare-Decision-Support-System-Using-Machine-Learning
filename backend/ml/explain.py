import logging

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


def explain_prediction(pipeline, values, feature_names, reference_values):
    try:
        import shap
    except ImportError:
        return None

    try:
        baseline = pd.DataFrame([reference_values], columns=feature_names)
        sample = pd.DataFrame([{name: values[name] for name in feature_names}], columns=feature_names)
        explainer = shap.KernelExplainer(pipeline.predict_proba, baseline.to_numpy())
        raw_values = explainer.shap_values(sample.to_numpy(), nsamples=max(2 * len(feature_names) + 1, 50))
        if isinstance(raw_values, list):
            contributions = np.asarray(raw_values[-1]).reshape(-1)
        else:
            contributions = np.asarray(raw_values)
            if contributions.ndim == 3:
                contributions = contributions[0, :, -1]
            else:
                contributions = contributions.reshape(-1)
        if len(contributions) != len(feature_names) or not np.isfinite(contributions).all():
            return None
        ordered = sorted(
            zip(feature_names, contributions.tolist()),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        return [
            {
                "feature": name,
                "contribution": round(float(contribution), 6),
                "direction": "increased" if contribution > 0 else "decreased" if contribution < 0 else "no measurable change",
            }
            for name, contribution in ordered[:5]
        ]
    except Exception as error:
        logger.warning("SHAP explanation unavailable: %s", error)
        return None
