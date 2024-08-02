Directory:
Techtalk/
-static
  -group_posts
  -uploads(for image/video uploads)
    -folders for storing the uploaded images/videos
-templates(HTML files)
-firstflask.py
-all python files
-db files


Open the terminal
Install flask
Install the requirements.txt

Create the database (new_database):
flask db init
flask db migrate
flask db upgrade

Flask run

The main application routes are stored in firstflask.py
In the terminal we need to get into the directory where firstflask.py is stored (inside TechTalk)
They run the file in python - python firstflask.py

Open any browser
Go to http://127.0.0.1:5000
You should see the login page