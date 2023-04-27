# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################


from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class HrDepartment(models.Model):
    _inherit = "hr.department"

    name = fields.Char('Department Name', required=True, translate=True)
