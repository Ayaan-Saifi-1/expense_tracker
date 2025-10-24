from flask import Flask, url_for, render_template, redirect, request,session
from dotenv import load_dotenv
import mysql.connector
import os
import secrets
# Load environment variables from .env file
load_dotenv()

# Fetch credentials
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name=os.getenv("DB_NAME")
# # Print values to debug (optional)
# print("Host:", db_host)
# print("User:", db_user)
# print("Password:", db_password)
try:
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = conn.cursor()
    # print("✅ Connected successfully!")
except mysql.connector.Error as err:
     print("❌ Connection failed:", err)

app=Flask(__name__) #create name of Flask app which is name here


app.secret_key = os.getenv('SECRET_KEY')

@app.route("/") #the route made for the port 5000
def index():
   if 'username' in session:
      return redirect(url_for('home'))
   return render_template("index.html")


@app.route("/login",methods=['GET','POST'])  #route for the port 5000/login
# there are two http methods-> get and post 
# here we need to take the input in the login form from user so the method is POST 
# by default if not mentioned route takes GET method 
# GET method is used to fetch and show data to user
def login():
   # this method checks user credentials and redirects them to home or login
 msg='' 
 if request.method=='POST':
      username=request.form['username']
      password=request.form['password']
      
      cursor.execute("select * from users where username=%s and password=%s",(username,password))
      record=cursor.fetchone()
      if(record):
         session['logged_in']=True
         session['username']=username
        #  or session['username']=record[1]
         session['user_id']=record[0]
         return redirect(url_for('home'))
      else:
       msg='Wrong Credentials, Try Again.'

 return render_template("login.html",msg=msg)


@app.route("/home") 
def home():
   if 'user_id' not in session:
      return redirect(url_for('login'))
   return render_template("home.html",username=session.get('username'))


@app.route("/logout")
def logout():
 session.pop('logged_in',None)
 session.pop('user_id',None)
 session.pop('username',None)
 return redirect(url_for('login'))

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        name=request.form['name']
        if len(password) < 8:
            msg = "Password must be at least 8 characters."
            return render_template("signup.html", msg=msg)

        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        record = cursor.fetchone()

        if record:
            msg = "User already exists. Try again."
        else:
            try:
                cursor.execute("INSERT INTO users VALUES (DEFAULT, %s, %s, %s,%s,DEFAULT)", (username, email, password,name))
                conn.commit()
                return redirect(url_for('login'))
            except mysql.connector.Error as err:
                msg = f"Signup failed: {err}"

    return render_template("signup.html", msg=msg)

@app.route("/view_expense")
def view_expense():
   
   if 'user_id' not in session:
      return redirect(url_for('login'))
   else:
      user_id=session['user_id']
      query = (
            "SELECT e.description, e.spent_on, e.amount, e.expense_id "
            "FROM expenses e "
            "JOIN users u ON u.user_id = e.user_id "
            "WHERE u.user_id = %s"
            " ORDER BY e.spent_on DESC"
        )
      cursor.execute(query,(user_id,))
      expenses=cursor.fetchall()
      return render_template('view_expenses.html', expenses=expenses,username=session['username'])

      
@app.route ("/add_expense", methods=['GET', 'POST'])
def add_expense():
   msg=''
   

   if 'user_id' not in session:
     return redirect(url_for('login'))
    
   else:
      if request.method=='POST':
         description=request.form['description']
         amount=request.form['amount']
         spent_on=request.form['date']
         user_id=session['user_id']
         try:
            cursor.execute("INSERT INTO expenses VALUES (DEFAULT, %s, %s, %s, %s)",(user_id,amount,description,spent_on))
            conn.commit()
            msg="Expense Added Successfully"
         except mysql.connector.Error as err:
            msg=f"Failed to add expense: {err}"
          
   return render_template("add_expense.html",msg=msg,username=session['username'])

@app.route("/delete_expense", methods=['POST'])
def delete_expense():
   if 'user_id' not in session:
      return redirect(url_for('login'))
   else:
      expense_id=request.form['expense_id']
      user_id=session['user_id']
      try:
         cursor.execute("DELETE FROM expenses WHERE expense_id=%s" ,(expense_id,))
         conn.commit()
         msg="Expense Deleted Successfully"
      except mysql.connector.Error as err:
         msg=f"Failed to delete expense: {err}"
      return redirect(url_for('view_expense'))

@app.route("/edit_expense", methods=['POST'])
def edit_expense():
   if 'user_id' not in session:
      return redirect(url_for('login'))
   else:
      expense_id=request.form['expense_id']
      user_id=session['user_id']
      cursor.execute("SELECT * FROM expenses WHERE expense_id=%s AND user_id=%s", (expense_id, user_id))
      expense=cursor.fetchone()
      if expense:
         expense_data = {
            'expense_id': expense[0],
            'user_id': expense[1],
            'amount': expense[2],
            'description': expense[3],
            'date': expense[4].strftime('%Y-%m-%dT%H:%M')  # Format for datetime-local input
         }
         return render_template("update_expense.html", expense=expense_data)
      else:
         return redirect(url_for('view_expense'))

@app.route("/update_expense", methods=['POST'])
def update_expense():            
   if 'user_id' not in session:
      return redirect(url_for('login'))
   else:
      expense_id=request.form['expense_id']
      description=request.form['description']
      amount=request.form['amount']
      date=request.form['date']
      user_id=session['user_id']
      try:
         cursor.execute("UPDATE expenses SET description=%s, amount=%s, spent_on=%s WHERE expense_id=%s AND user_id=%s",(description,amount,date,expense_id,user_id))
         conn.commit()
         msg="Expense Updated Successfully"
      except mysql.connector.Error as err:
         msg=f"Failed to update expense: {err}"
      return redirect(url_for('view_expense'))


if(__name__=="__main__"):
  app.run(debug=True,port='8000')


