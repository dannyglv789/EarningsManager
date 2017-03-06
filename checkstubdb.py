# Configuration code of SQLAlchemy 
import os

# The sys module provides a number of functions and variables that can manipulate python
import sys

# These will come in handy when we are writing our Mapper code
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean

# We will use declarative base in the configuration and class code
from sqlalchemy.ext.declarative import declarative_base

# We import relationship to create our foreign key relationships
from sqlalchemy.orm import relationship

# create_engine will be used at the end of the file as config code
from sqlalchemy import create_engine

# declarative_base lets sqlalchemy know that our classes are special sqlalchemy classes
# that correspond to tables in our database!
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    f_id = Column(String)
    name = Column(String)
    is_member = Column(Boolean,default=False)
    check_count = Column(Integer,default=0)
    
class Check(Base):
    __tablename__ = 'check'
    creator = Column(Integer,ForeignKey('user.id'))
    id = Column(Integer, primary_key = True)
    emp_name = Column(String(200))
    social = Column(String(80))
    rep_period = Column(String(80))
    pay_date = Column(String(80))
    emp_num = Column(String(80))
    rate = Column(String(80))
    hours = Column(String(80))
    current_pay = Column(String(80))
    fica_medi = Column(String(80))
    fica_social = Column(String(80))
    fica_medi_ytd = Column(String(80))
    fica_social_ytd = Column(String(80))
    fed_tax = Column(String(80))
    fed_ytd = Column(String(80))
    state_tax = Column(String(80))
    state_ytd = Column(String(80))
    ytd_gross = Column(String(80))
    ytd_deductions = Column(String(80))
    ytd_net = Column(String(80))
    total = Column(String(80))
    bottom_deductions = Column(String(80))
    net_pay = Column(String(80))

class Check_2(Base):
    __tablename__ = 'check2'
    creator = Column(Integer, ForeignKey('user.id'))
    id = Column(Integer, primary_key = True)
    company_name = Column(String(80))
    company_address = Column(String(80))
    company_city = Column(String(80))
    pay_begin = Column(String(80))
    pay_end = Column(String(80))
    pay_date = Column(String(80))
    status = Column(String(80))
    exemptions = Column(String(10))
    emp_name = Column(String(80))
    emp_address = Column(String(80))
    emp_city_state_zip = Column(String(80))
    reg_rate = Column(String(20))
    reg_hours = Column(String(20))
    reg_period = Column(String(20))
    reg_ytd = Column(String(20))
    ov_rate = Column(String(20))
    ov_hours = Column(String(20))
    ov_period = Column(String(20))
    ov_ytd = Column(String(20))
    vac_rate = Column(String(20))
    vac_hours = Column(String(20))
    vac_period = Column(String(20))
    vac_ytd = Column(String(20))
    gross_period = Column(String(20))
    gross_ytd = Column(String(20))
    fed_period = Column(String(20))
    fed_ytd = Column(String(20))
    soc_period = Column(String(20))
    soc_ytd = Column(String(20))
    state_selection = Column(String(2))
    state_period = Column(String(20))
    state_ytd = Column(String(20))
    net_pay = Column(String(20))
    comments = Column(String(180))
    
# End of file code
engine = create_engine('postgresql://daniel:Seven11ok@localhost/stub')
# goes into the db and adds the classes we create as tables, DB Session establishes
#link betweeen code we execute in session and db
Base.metadata.create_all(engine)
