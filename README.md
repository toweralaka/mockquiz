# mockquiz

This is a quiz app based on Django as the backend. 

## Setting up a development environment

1. Have Python 3
2. Create a virtualenv:
   ```console
   $ python3 -m venv env
   ```
3. Activate the venv:
   ```console
   $ . env/bin/activate  # or a Windows alternative
   ```
   *Note that you have to run this every time you start a new
   terminal shell session.*
4. Run the following to have the same requirements as on
   production installed in your local virtualenv you've just activated:
   ```console
   $ python3 -m pip install -r requirements.txt
   ```
5. Set up "dotenv" by copying the example file and altering the values:
   ```console
   $ cp -v .env{.example,}
   $ code .env  # edit stuff at this step
   ```
   Don't edit the `DATABASE_URL`, its
   example value is enough to get you going unless you want to replicate
   the production installation of PostgreSQL on your machine.
   `DEBUG` may remain `True`, it only controls how much helpful info
   Django will show to you on errors. `DJANGO_SECRET_KEY` should be set
   to any random string, don't copy this value from production, use your
   own. 
   *It is safe to add secrets to `.env` — it's gitignored, it's not safe
   to do this with `.env.example`, though.*
6. Populate your development database with the tables according to
   the app models: 
   ```console
   $ ./manage.py migrate
   ```
7. With the following, you'll start a Python server instance:
   ```console
   $ ./manage.py runserver --nostatic
   ```
   You will see a similar output
   ```
   Watching for file changes with StatReloader
   Performing system checks...
   
   System check identified no issues (0 silenced).
   February 03, 2022 - 06:05:51
   Django version 3.2.12, using settings 'mockquiz.settings'
   Starting development server at http://127.0.0.1:8000/
   Quit the server with CONTROL-C.
   ```
   See that log line that is second to last? It means that to see the
   app in your browser, you may open http://127.0.0.1:8000/ -- you may
   do this now.
   Keep the process running for as long as you're doing the development
   work.
