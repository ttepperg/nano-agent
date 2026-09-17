""" A collection of utilies """

import json
import time
import re
from config import DEBUG_ON, TRACE_ON


def trace(t, l):
    if TRACE_ON:
        id = int(time.time())
        hms = time.strftime("%H:%M:%S")
        print(f'__TRACE__:{json.dumps({"id": id, "timestamp": hms, "type": t, "label": l})}')


def debug(*args, **kwargs):
    if DEBUG_ON:
        print(*args, **kwargs)


def extract_keyval(text):
    match = re.search(r"My (\w+) is (.+)", text, re.IGNORECASE)
    if match:
        key = match.group(1)
        value = match.group(2)
        return key, value
