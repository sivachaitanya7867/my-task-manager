# Imports
from flask import Flask, render_template, redirect, request
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# My App
app = Flask(__name__) #app is a varibale
Scss(app)

# configuring the app with sql alchemy database by giving it the name mydatabase. this code line is available in flask-sqlalchemy 
# documentation. go to cofigure the extension part
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydatabase.db"
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False # so that when a new user uses the app, it's not gonna have a pre-existing database becuase it won't track it.

#now creating the database itself
db = SQLAlchemy(app) #db is a var

# Data class ~ since it is gonna hold the information
class MyTask(db.Model): #Model means a row of data in our database. it essentially collects and holds data for each item.
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False) # means can not have a null
    completed = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    # The Model itself is a row. so each row consists of all these columns.

    def __repr__(self):
        return f"Task {self.id}" #output in the form of Task 1, Task 2......


with app.app_context(): # to set up the necessary environment for interacting with the database.
    db.create_all() # to create all the tables in the database, if they don’t already exist.


# Home Page
@app.route('/', methods=['POST', 'GET']) # we have to give a route to the homepage. since it is homepage, we can just give '/'
def index(): # index is like the home page of the website
    # Add a task
    if request.method == "POST": # REMEMBER, WE IMPORTED THIS REQUEST WORD FROM FLASK IN FIRST LINE.
        current_task = request.form['content'] # form is the one we created in index.html
        # so it's taking whatever the user typed in the form content box, assigning it to variable current_task 
        new_task = MyTask(content = current_task) #now the stored content current task is sent to db as a new task
        try:
            db.session.add(new_task) # creating new session(a temporary workspace where changes are tracked before they are actually applied to the db) and adding the new task to the database
            db.session.commit() #tells SQLAlchemy to apply all the changes you've made to actual database.
            # Until you call commit(), changes are only in the session, not yet saved to the database.
            return redirect('/') # redirecting back to the homepage. even though we are already in the home page.
        except Exception as e:
            print(f"ERROR: {e}")
            return f"ERROR: {e}" #returning the print again because we used return in try:, or else it might throw errors
            
    # See all current tasks
    else:
        tasks = MyTask.query.order_by(MyTask.created).all() #.query retrieves all tasks stored in MyTask table. It is a method to interact with the database
        return render_template("index.html", tasks=tasks) #rend temp looks for html file inside templates folder. Even though WE created a 
        # templates folder, flask just knows it needs to check that particular folder automatically
        # tasks in Python is a list of all tasks from the database.
        # tasks=tasks in render_template makes this list available in your HTML so you can display it.
        # You can’t just return tasks because Flask is expecting HTML content from render_template, not raw Python data.
        # tasks=tasks allows you to pass data from Python to the HTML template, and inside the template, you'll access it using the variable name tasks.


# Delete an Item
@app.route('/delete/<int:id>') # creating a new page delete and then routing it according to the task id
def delete(id:int): # takes a parameter id with int as it's value
    delete_task = MyTask.query.get_or_404(id) # we won't get 404 error anyway because, delete link option appears only when a task is added. so it should not be a problem
    try:
        db.session.delete(delete_task)
        db.session.commit()
        return redirect('/') # delete the task and redirect back home 
    except Exception as e:
        return f"ERROR: {e}"


# Edit an item
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id:int):
    task = MyTask.query.get_or_404(id)
    if request.method == "POST": # If I send information meaning that I click on edit and want to update the content
        task.content = request.form['content'] # we are updating the task.content to newly edited content.
        try:
            db.session.commit() # since we already updated the content in db, we just have to commit it by logging in to the session
            return redirect('/')
        except Exception as e:
            return f"ERROR: {e}"
    else:
        return render_template('edit.html', task=task)






if __name__ == "__main__":
    app.run(debug=True)