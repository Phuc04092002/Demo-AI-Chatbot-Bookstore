import pandas as pd
from sklearn.model_selection import train_test_split

# Giả sử bạn có DataFrame: cột "text" (câu hỏi), cột "label" (0=history,1=legal,2=medical)
df = pd.read_csv("bookstore_requests_balanced.csv")

# Tách train (90%) và temp (10%) theo stratify
train_df, val_df = train_test_split(
    df,
    test_size=0.2,   # 20% (val+test)
    stratify=df["label"],
    random_state=42
)


print("Train size:", len(train_df))
print("Val size:", len(val_df))

print("Class distribution train:")
print(train_df["label"].value_counts(normalize=True))
print("Class distribution val:")
print(val_df["label"].value_counts(normalize=True))


# Lưu ra file CSV nếu cần
train_df.to_csv("train_router_1.csv", index=False)
val_df.to_csv("val_router_1.csv", index=False)