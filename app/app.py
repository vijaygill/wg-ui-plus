from flask import Flask,render_template,send_from_directory

BASE_DIR = 'wg-ui-plus/dist/wg-ui-plus/browser'

app = Flask(__name__, template_folder = BASE_DIR )

@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
  return send_from_directory(BASE_DIR, path)

@app.route('/test')
def test():
    return 'Hello, World!'

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 80)
