# web_practice
* Warren Liu
* Practice on using python flask to build a web service.

## About
* Study on how to use python-flask to build a web service myself. 
* The book I am reading is [Flask tutorial, written in Chinese](https://github.com/greyli/flask-tutorial/blob/master/chapters/SUMMARY.md).
* Implemented the front-end web page, back-end web service, error pages, login & logout function, edit/delete/add functions, and used SQLAlchemy as database.
* Used unittest.

## Update
* 9/24/2021: Web service is built and able to run, TODO: reconstruct codes.

## Use
To initialize database
```
flask initdb
```
To drop all existing data and then initialize database 
```
flask initdb --drop
```
To generate a admin account
```
flask admin
```
To run the web service
```
flask run
```