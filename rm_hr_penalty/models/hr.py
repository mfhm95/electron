from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta




class Employee(models.Model):
    _inherit = "hr.employee"


