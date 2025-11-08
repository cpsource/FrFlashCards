from flask import Flask, render_template

app = Flask(__name__)

# --- Home page ---
@app.route("/")
def home():
    return render_template("index.html")

# --- About page ---
@app.route("/about")
def about():
    return render_template("about.html")

# --- Vocabulary flashcards ---
@app.route("/vocab/<category>/<word>")
def vocab_card(category, word):
    template_path = f"vocab/{category}/{word}.html"
    try:
        return render_template(template_path)
    except:
        return f"<h2>Sorry, the flashcard '{word}' in '{category}' wasn't found.</h2>", 404

if __name__ == "__main__":
    app.run(debug=True)

