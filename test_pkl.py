import pickle
import traceback

print("---- LABEL ENCODERS ----")
with open('app/ml_models/label_encoders.pkl', 'rb') as f:
    objs = []
    while True:
        try:
            objs.append(pickle.load(f))
        except EOFError:
            break
    print("Found", len(objs), "objects")
    for idx, obj in enumerate(objs):
        print(f"[{idx}] Type:", type(obj))
        if isinstance(obj, dict):
            print("Keys:", obj.keys())
        elif hasattr(obj, 'classes_'):
            print("classes:", obj.classes_[:5])

print("---- STANDARD SCALER ----")
with open('app/ml_models/standard_scaler.pkl', 'rb') as f:
    objs = []
    while True:
        try:
            objs.append(pickle.load(f))
        except EOFError:
            break
    print("Found", len(objs), "objects")
    for idx, obj in enumerate(objs):
        print(f"[{idx}] Type:", type(obj))
