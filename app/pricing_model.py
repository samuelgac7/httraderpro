import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.tree import DecisionTreeRegressor

FEATURES = ["playmaking", "passing", "defending", "scoring", "winger", "form", "tsi", "age_days", "specialty_index"]
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "player_sales.csv"
MODEL_PATH = BASE_DIR / "pricing_model.pkl"

def train_model(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH) -> DecisionTreeRegressor:
    """Train a pricing model and persist it to disk."""
    df = pd.read_csv(data_path)
    X = df[FEATURES]
    y = df["price"]
    model = DecisionTreeRegressor(random_state=0)
    model.fit(X, y)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    return model

def load_model(model_path: Path = MODEL_PATH) -> DecisionTreeRegressor:
    """Load the pricing model from disk, training it if necessary."""
    if not model_path.exists():
        return train_model(model_path=model_path)
    with open(model_path, "rb") as f:
        return pickle.load(f)

def predict(player: dict, model: DecisionTreeRegressor | None = None) -> float:
    """Predict the price for a player dict."""
    if model is None:
        model = load_model()
    x = np.array([[player.get(feat, 0) for feat in FEATURES]])
    return float(model.predict(x)[0])
