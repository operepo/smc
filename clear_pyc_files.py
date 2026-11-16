import os

top = os.path.dirname(os.path.abspath(__file__))
print(f"Removing .pyc and .pyo files in {top}")

for root, dirs, files in os.walk(top, topdown=False):
    for name in files:
        if name.endswith(".pyc") or name.endswith(".pyo"):
            print("Removing " + name)
            os.remove(os.path.join(root, name))

