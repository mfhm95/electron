# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) 2020.
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#    website': https://www.linkedin.com/in/ramadan-khalil-a7088164
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import pytz


class hrEmployee(models.Model):
    _inherit = "hr.employee"

    def get_employee_shifts(self, day_start, day_end, tz):
        self.ensure_one()
        plan_slot_obj = self.env['planning.slot']
        day_start_native = day_start.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        day_end_native = day_end.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        slot_ids = plan_slot_obj.search(
            [('employee_id','=',self.id),
             ('start_datetime', '>=', day_start_native),
             ('start_datetime', '<=', day_end_native)])
        working_intervals = []
        for slot in slot_ids:
            working_intervals.append((slot.start_datetime, slot.end_datetime,slot.day_period))
        return working_intervals

    attendance_sheet_count = fields.Integer(
        string='Attendance sheet count', compute='_get_attendance_sheet_count',
        required=False)

    def _get_attendance_sheet_count(self):
        for rec in self:
            rec.attendance_sheet_count = self.sudo().env['attendance.sheet'].search_count([('employee_id','=',rec.id)])

    def open_attendance_sheets(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'My attendance Sheets',
            'res_model': 'attendance.sheet',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('employee_id','=',self.id)]
        }