import datetime
import random
import uuid


def generate_random_filename(basename="testfile"):
    """generates a random filename"""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    suffix = datetime.datetime.now().strftime("%f_%H%M%S")
    return "_".join([*random.choices(letters, k=5), basename, suffix])


def write_pseudo_data(path: str):
    """Writes pseudo data to a file in the given path, returns the generated data"""
    data = uuid.uuid4().hex
    with open(path, "w") as f:
        f.write(data)
    return data




