from flask import Flask, render_template, url_for, request
app = Flask(__name__)
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from checkstubdb import Check, Base

# engine and db connection
engine = create_engine('sqlite:///checkstub.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/checkstub/', methods=['GET','POST'])
def check_stub():
    if request.method == 'POST':
        newCheck = Check(emp_name=request.form['emp_name'],
                         social=request.form['social'],
                         rep_period=request.form['rep_period'],
                         pay_date=request.form['pay_date'],
                         emp_num=request.form['emp_num'],
                         rate=request.form['rate'],
                         hours=request.form['hours'])
        session.add(newCheck)
        session.commit()
        return render_template('checkstub.html')
    else:
        return render_template('checkstub.html')

# the complete user checkstub
@app.route('/yourstub/<int:check_id>/')
def viewCheck(check_id):
    check = session.query(Check).filter_by(id=check_id).one()
    return render_template('checkstub_done.html',check=check)

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
