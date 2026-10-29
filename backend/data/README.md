# Dataset placement

This folder intentionally contains no dataset or patient records. Place only datasets you have independently obtained permission to use here:

- `diabetes.csv`: headerless comma-separated Pima dataset rows in this exact order: `Pregnancies,Glucose,BloodPressure,SkinThickness,Insulin,BMI,DiabetesPedigreeFunction,Age,Outcome`. Outcome must be `0` or `1`.
- `heart_disease.csv`: headerless processed Cleveland rows in this exact order: `age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal,num`. Unknown values may use `?`; the target `num` must be `0` through `4`.

The training scripts check the number of columns, feature ranges/codes, target labels, and class counts. The application does not download datasets.

## Provenance and limitations

- **Pima Indians Diabetes Dataset:** historically associated with data from the National Institute of Diabetes and Digestive and Kidney Diseases and used in Smith et al., “Using the ADAP learning algorithm to forecast the onset of diabetes mellitus” (1988). No license is asserted by this project for copies found online. Verify the terms and permissions of the exact source you obtain before training or redistribution. This dataset describes a specific population and is not representative of everyone.
- **Heart Disease:** use the processed Cleveland subset of the [UCI Heart Disease dataset](https://archive.ics.uci.edu/dataset/45/heart+disease). The official UCI listing states CC BY 4.0 and requests attribution. Its target `num` is 0–4; this project maps `0` to dataset-negative and `1`–`4` to dataset-positive, matching the binary distinction described by the UCI documentation. The Cleveland subset is small and not representative of the general population.

Keep the dataset's required attribution with any permitted redistribution. Confirm licensing and suitability with your institution before using either dataset.
