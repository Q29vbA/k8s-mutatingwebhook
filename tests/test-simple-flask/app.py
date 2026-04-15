import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    root = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(root, 'index.html')
    with open(index_path, 'r', encoding='utf-8') as index_file:
        return index_file.read()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
