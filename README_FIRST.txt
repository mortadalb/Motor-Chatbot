1. Run the following from CMD before startup of the flask service under insert.py unless IIS is working fine then you can skip to step 4:
   wfastcgi-enable

2. Set the Flask ENV parameters before running it:
   set FLASK_APP=insert.py
   set FLASK_ENV=production

3. Run Flask:
   flask run --host=10.10.10.16 --port=8081




