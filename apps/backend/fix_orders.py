import re

with open('app/api/v1/orders/router.py', 'r') as f:
    content = f.read()

content = content.split('@router.post("/urgent/insert")')[0]

with open('app/api/v1/orders/router.py', 'w') as f:
    f.write(content.strip())
