import pandas as pd
import pickle
import re
from normalize import normalize_query
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "products.csv"
df = pd.read_csv(CSV_PATH)

VOCAB = set()


# ------------------
# Extract catalog words
# ------------------

FIELDS = [
    "title",
    "category[0]",
    "subcategory",
    "sellerName"
]

for field in FIELDS:

    if field not in df.columns:
        continue

    for value in df[field].dropna():

        text = normalize_query(str(value))

        words = re.findall(
            r"[a-z0-9]+",
            text
        )

        for word in words:

            if len(word) >= 2:
                VOCAB.add(word)


# ------------------
# CATEGORY VOCAB
# ------------------

CATEGORY_TERMS = {

# Fashion
"saree","sari","kurti","kurta","blouse","dress",
"shirt","tshirt","tee","hoodie","jacket","jeans",
"legging","pant","top","ethnic","cotton","silk",
"dupatta","nightwear","gown","fashion","women",
"men","kids","slipper","shoe","sandal","bag",
"wallet","watch","jewellery","earring","necklace",

# Consumables
"snack","food","masala","rice","oil","tea",
"coffee","biscuit","chocolate","drink","juice",
"pickle","healthy","organic","combo","pack",

# Beauty
"makeup","cosmetic","lipstick","foundation",
"compact","powder","serum","cream","soap",
"skincare","eyeliner","kajal","brush","palette",
"beauty","facewash","shampoo","conditioner",

# Home
"home","kitchen","decor","container","storage",
"bottle","cleaner","mat","bed","blanket",
"curtain","essential",

# Toys & Baby
"toy","baby","kids","doll","feeding",
"diaper","learning","educational","softtoy",

# Stationery
"pen","pencil","notebook","book","marker",
"paper","stationery","diary","craft",

# Sports
"sports","fitness","bat","ball","exercise",
"yoga","training","gym","outdoor",

# Health
"health","medicine","wellness","care",
"immunity","supplement",

# Pooja
"pooja","puja","agarbatti","lamp","diya",
"camphor","spiritual","temple"
}

VOCAB.update(CATEGORY_TERMS)


# ------------------
# SAVE
# ------------------

with open(
    "catalog_vocab.pkl",
    "wb"
) as f:
    pickle.dump(
        sorted(VOCAB),
        f
    )

print("Final vocab size:", len(VOCAB))