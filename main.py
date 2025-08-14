from flask import Flask, request, jsonify
import os
import mysql.connector
import bcrypt
from dotenv import load_dotenv


app = Flask(__name__)
from flask_cors import CORS
CORS(app) 

load_dotenv()

HOST_VAL = os.getenv("HOST_VAL")
PORT_VAL = os.getenv("PORT_VAL")
USER_VAL = os.getenv("USER_VAL")
PASSWORD_VAL = os.getenv("PASSWORD_VAL")
DATABASE_VAL = os.getenv("DATABASE_VAL")

def connect_db():
    return mysql.connector.connect(
        host = HOST_VAL,
        port = PORT_VAL,
        user = USER_VAL,
        password = PASSWORD_VAL,
        database = DATABASE_VAL
    )


@app.route("/")
def home():
    return jsonify({"message" : "Flappy Bird API is running!"}), 200


@app.route("/register",methods=["POST"])
def register():
    data = request.get_json()

    user_name = data.get("user_name")
    user_password = data.get("user_password")

    if not all ([user_name,user_password]):
        return jsonify({"message" : "Don't leave the fields blank. Fill it."}), 400
    else:
        hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())
        conn = connect_db()
        cursor = conn.cursor()

        check_query = "SELECT * FROM users WHERE user_name = %s"
        cursor.execute(check_query, (user_name,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({"message" : "Name already exist"}), 409
        
        score = 0
        max_score = 0
        games_played = 0
        user_password = str(data.get("password"))

        query = "insert into users (user_name, user_password, score, max_score, games_played) values (%s,%s,%s,%s,%s)"
        cursor.execute(query,(user_name, hashed_password, score, max_score, games_played))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message" : "User registered successfully"}), 201
    

@app.route("/login", methods=["POST"]) 
def login():
    data = request.get_json()

    user_name = data.get("user_name")
    user_password = str(data.get("user_password"))

    if not all ([user_name,user_password]):
        return jsonify({"message" : "Don't leave the fields blank. Fill it."}), 400
    else:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT user_password FROM users WHERE user_name = %s"
        cursor.execute(query, (user_name,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result and bcrypt.checkpw(user_password.encode('utf-8'), result['user_password'].encode('utf-8')):
            return jsonify({"message" : "Login successful"}), 200
        else:
            return jsonify({"message" : "Invalid  Name or Password"}), 401
        
        
@app.route("/score", methods=["POST"])
def score():

    data = request.get_json()
    user_name = data.get("user_name")
    score = data.get("score")

    if not all ([user_name,score]):
        return jsonify({"message" : "Score = 0"}), 400
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    score_query = "update users set score = %s where user_name = %s"
    cursor.execute(score_query,(score,user_name))

    max_score_query = "update users set max_score = score where score > max_score and user_name = %s"
    cursor.execute(max_score_query,(user_name,))

    games_played_query = "update users set games_played = games_played+1 where user_name = %s"
    cursor.execute(games_played_query,(user_name,))

    query = "SELECT score FROM users WHERE user_name = %s"
    cursor.execute(query, (user_name,))
    result = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    if result:
        return jsonify({"message" : "Your score is:", "score" : result['score']}), 200

    
@app.route("/leaderboard",methods=["GET"])
def leaderboard():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    query = "select user_name, max_score, games_played from users order by max_score desc limit 10"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    if result:
        return jsonify({"message" : result}), 200
    else:
        return jsonify({"message" : "No Players in leaderbraed yet"}), 404


@app.route("/profile/<id>",methods=["GET"])
def user(id):

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT user_name,max_score, games_played FROM users where id = %s"
    cursor.execute(query,(id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return jsonify({"message" : result}), 200
    else:
        return jsonify({"message" : "No user found"}), 404
    


@app.route("/profile/update/<id>",methods = ["PATCH"])
def user_patch(id):
    data = request.get_json()
    user_name = data.get("user_name")

    if not user_name:
        return jsonify({"message" : "Don't leave the fields blank. Fill it."}), 400
    else:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        try:
            query = "update users set user_name=%s where id = %s"
            cursor.execute(query,(user_name,id))
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({"message" : "Name changed successfully"}), 200
        
        except:
            return jsonify({"message" : "Enter correct user id"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
