from flask import Flask, render_template
import os

app = Flask(__name__, 
            template_folder=os.path.abspath('app/web/templates'),
            static_folder=os.path.abspath('app/web/static'))

@app.route('/')
def index():
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
