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
    name = Column(String)
    is_member = Column(Boolean,default=False)
    
class Check(Base):
    __tablename__ = 'check'
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
#    ytd_gross = Column(String(80))
#    ytd_deductions = Column(String(80))
#    ytd_net = Column(String(80))
#    total = Column(String(80))
#    bottom_deductions = Column(String(80))
#    net_pay = Column(String(80))

# End of file code
engine = create_engine('sqlite:///checkstub.db')
# goes into the db and adds the classes we create as tables, DB Session establishes
#link betweeen code we execute in session and db
Base.metadata.create_all(engine)
