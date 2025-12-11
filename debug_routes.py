from app.main import app
import sys

print("Printing registered routes:")
for route in app.routes:
    print(f"{route.path} {route.methods}")
