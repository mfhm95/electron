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

from odoo import models, fields, api, tools, _
import babel
import time
from datetime import datetime, timedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    is_bus_registered = fields.Boolean(
        string='Bus Registered',
        required=False)
    bus_registered = fields.Monetary('bus registered', tracking=True, help="Employee's bus registered.")

    def _default_att_policy_id(self):
        return self.env['hr.attendance.policy'].search([('is_bus_registered','=',True)], limit=1).id


    att_policy_ids = fields.Many2many('hr.attendance.policy', string='Attendance Policy')

    att_policy_id = fields.Many2one('hr.attendance.policy', string='Attendance Policy', domain='[("is_bus_registered", "=", is_bus_registered)]')


    multi_shift = fields.Boolean('Multi Shifts', default=False)


    overtime_approve = fields.Boolean('Overtime Approve Needed')



