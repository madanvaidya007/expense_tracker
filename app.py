from flask import Flask, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'a'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'new'

mysql = MySQL(app)
9
# HOME PAGE
@app.route("/home")
def home():
    return render_template("homepage.html")

@app.route("/")
def add():
    return render_template("home.html")

# SIGN-UP OR REGISTER
@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO user (username, email, password) VALUES (%s, %s, %s)', 
                           (username, email, hashed_password))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
        return render_template('signup.html', msg=msg)

# LOGIN PAGE
@app.route("/signin")
def signin():
    return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account and check_password_hash(account[3], password):
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            return redirect('/home')
        else:
            msg = 'Incorrect username / password!'
    return render_template('login.html', msg=msg)

# ADDING DATA
@app.route("/add")
def adding():
    return render_template('add.html')

@app.route('/addexpense', methods=['POST'])
def addexpense():
    if request.method == 'POST':
        date = request.form['date']
        expensename = request.form['expensename']
        amount = request.form['amount']
        paymode = request.form['paymode']
        category = request.form['category']
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO expenses (userid, date, expensename, amount, paymode, category) VALUES (%s, %s, %s, %s, %s, %s)', 
                       (session['id'], date, expensename, amount, paymode, category))
        mysql.connection.commit()
        return redirect("/display")
    return render_template('add.html')

# DISPLAY EXPENSES
@app.route("/display")
def display():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE userid = %s ORDER BY date DESC', (session['id'],))
    expense = cursor.fetchall()
    return render_template('display.html', expense=expense)

# DELETE DATA
@app.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = %s', (id,))
    mysql.connection.commit()
    return redirect("/display")

# UPDATE DATA
@app.route('/edit/<id>', methods=['POST', 'GET'])
def edit(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE id = %s', (id,))
    row = cursor.fetchone()
    return render_template('edit.html', expenses=row)

@app.route('/update/<id>', methods=['POST'])
def update(id):
    if request.method == 'POST':
        date = request.form['date']
        expensename = request.form['expensename']
        amount = request.form['amount']
        paymode = request.form['paymode']
        category = request.form['category']
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE expenses SET date = %s, expensename = %s, amount = %s, paymode = %s, category = %s WHERE id = %s',
                       (date, expensename, amount, paymode, category, id))
        mysql.connection.commit()
        return redirect("/display")

# LIMIT
@app.route("/limit")
def limit():
    return redirect('/limitn')

@app.route("/limitnum", methods=['POST'])
def limitnum():
    if request.method == 'POST':
        number = request.form['number']
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO limits (userid, limitss) VALUES (%s, %s)', (session['id'], number))
        mysql.connection.commit()
        return redirect('/limitn')

@app.route("/limitn")
def limitn():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT limitss FROM limits WHERE userid = %s ORDER BY id DESC LIMIT 1', (session['id'],))
    x = cursor.fetchone()
    s = x[0] if x else None
    return render_template("limit.html", y=s)

# REPORT
def calculate_expenses(expenses):
    total = sum(x[4] for x in expenses)
    categories = {'food': 0, 'entertainment': 0, 'business': 0, 'rent': 0, 'EMI': 0, 'other': 0}
    for x in expenses:
        if x[6] in categories:
            categories[x[6]] += x[4]
    return total, categories

@app.route("/today")
def today():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT TIME(date), amount FROM expenses WHERE userid = %s AND DATE(date) = CURDATE()', (session['id'],))
    texpense = cursor.fetchall()
    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND DATE(date) = CURDATE() ORDER BY date DESC', (session['id'],))
    expenses = cursor.fetchall()
    total, categories = calculate_expenses(expenses)
    return render_template("today.html", texpense=texpense, expense=expenses, total=total, **categories)

@app.route("/month")
def month():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT DATE(date), SUM(amount) FROM expenses WHERE userid = %s AND MONTH(date) = MONTH(CURDATE()) GROUP BY DATE(date) ORDER BY DATE(date)', (session['id'],))
    texpense = cursor.fetchall()
    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND MONTH(date) = MONTH(CURDATE()) ORDER BY date DESC', (session['id'],))
    expenses = cursor.fetchall()
    total, categories = calculate_expenses(expenses)
    return render_template("month.html", texpense=texpense, expense=expenses, total=total, **categories)

@app.route("/year")
def year():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT MONTH(date), SUM(amount) FROM expenses WHERE userid = %s AND YEAR(date) = YEAR(CURDATE()) GROUP BY MONTH(date) ORDER BY MONTH(date)', (session['id'],))
    texpense = cursor.fetchall()
    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND YEAR(date) = YEAR(CURDATE()) ORDER BY date DESC', (session['id'],))
    expenses = cursor.fetchall()
    total, categories = calculate_expenses(expenses)
    return render_template("year.html", texpense=texpense, expense=expenses, total=total, **categories)

# LOGOUT
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True)
