from flask import Flask,render_template

app = Flask(__name__, template_folder='wg-ui-plus/dist/wg-ui-plus/browser')

@app.route('/test')
def test():
    return 'Hello, World!'

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 80)
