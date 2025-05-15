from flask import Flask, render_template_string, request
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        return "Ingezonden!"
    return '''
        <form method="post">
            <input name="naam">
            <input type="submit">
        </form>
    '''

if __name__ == "__main__":
    app.run()
