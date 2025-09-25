from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

df_train = pd.read_csv("train_router_1.csv")
df_val   = pd.read_csv("val_router_1.csv")

train_texts, train_labels = df_train["text"].tolist(), df_train["label"].tolist()
val_texts, val_labels     = df_val["text"].tolist(), df_val["label"].tolist()

train_labels = [x.strip() for x in train_labels]
val_labels = [x.strip() for x in val_labels]

le = LabelEncoder()
y_train = le.fit_transform(train_labels)
y_val   = le.transform(val_labels)


X_train = model.encode(train_texts, convert_to_numpy=True, show_progress_bar=True)
X_val   = model.encode(val_texts, convert_to_numpy=True, show_progress_bar=True)

# 5. Train XGBoost classifier
clf = xgb.XGBClassifier(
    objective="multi:softmax",
    num_class=len(le.classes_),
    eval_metric="mlogloss",
    use_label_encoder=False,
    n_estimators=300,
    learning_rate=0.1,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

clf.fit(X_train, y_train)

y_pred = clf.predict(X_val)
print(type(y_val), y_val.shape, y_val[:5])
print(type(y_pred), y_pred.shape, y_pred[:5])
print(classification_report(y_val, y_pred, target_names=le.classes_))

text = "Tôi muốn đặt 1 cuốn One Piece tập 20 ở Hà Nội"
vec = model.encode([text], convert_to_numpy=True)

pred_class = clf.predict(vec)[0]
# max_prob = np.max(probs)
# pred_class = np.argmax(probs)
label = le.inverse_transform([pred_class])[0]

print(label)

joblib.dump(clf, "model/model_xgb_1.pkl")
joblib.dump(le, "model/label_encoder_1.pkl")
