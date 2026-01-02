from flask import Flask, jsonify, send_from_directory
import sqlite3

app = Flask(__name__, static_folder="static")

DB_PATH = "database/Videos.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/videos")
def api_videos():
    db = get_db()
    rows = db.execute("""
        SELECT
            video_id,
            title,
            thumbnail,
        FROM Playlist
        ORDER BY id DESC
    """).fetchall()
    db.close()

    return jsonify([dict(r) for r in rows])


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(debug=True)
