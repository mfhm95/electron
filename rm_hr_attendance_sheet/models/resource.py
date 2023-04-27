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


import pytz
from operator import itemgetter
from odoo.tools import date_utils

from odoo import fields, models, api, _
from odoo.tools.misc import format_date


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    two_shift_per_day = fields.Boolean(
        string='2 shift per day', help='set this true if the day will be containing 2 shifts',
        required=False)

    def _attendance_intervals(self, start_dt, end_dt, resource=None, domain=None, tz=None):
        if resource is None:
            resource = self.env['resource.resource']
        return self._attendance_intervals_batch(
            start_dt, end_dt, resources=resource, domain=domain, tz=tz
        )[resource.id]

    def att_get_work_intervals(self, day_start, day_end, tz):
        day_start = day_start.replace(tzinfo=tz)
        day_end = day_end.replace(tzinfo=tz)
        attendance_intervals = self._attendance_intervals(day_start, day_end)
        working_intervals = []
        for interval in attendance_intervals:
            working_interval_tz = (interval[0].astimezone(pytz.UTC).replace(tzinfo=None),
                                   interval[1].astimezone(pytz.UTC).replace(
                                       tzinfo=None),
                                   interval[2].day_period
                                   )
            working_intervals.append(working_interval_tz)
        clean_work_intervals = self.att_interval_clean(working_intervals)

        return clean_work_intervals

    def att_interval_clean(self, intervals):
        intervals = sorted(intervals, key=itemgetter(0))  # sort on first datetime
        cleaned = []
        working_interval = None
        while intervals:
            current_interval = intervals.pop(0)
            if not self.env.context.get('is_leave', False):
                if not working_interval:  # init
                    working_interval = [current_interval[0], current_interval[1], current_interval[2]]
                elif working_interval[1] < current_interval[0]:
                    cleaned.append(tuple(working_interval))
                    working_interval = [current_interval[0], current_interval[1], current_interval[2]]
                elif working_interval[1] < current_interval[1]:
                    working_interval[1] = [current_interval[1], current_interval[2]]
            else:
                if not working_interval:  # init
                    working_interval = [current_interval[0], current_interval[1]]
                elif working_interval[1] < current_interval[
                    0]:
                    cleaned.append(tuple(working_interval))
                    working_interval = [current_interval[0], current_interval[1]]
                elif working_interval[1] < current_interval[
                    1]:
                    working_interval[1] = current_interval[1]
        if working_interval:
            cleaned.append(tuple(working_interval))
        return cleaned

    def att_interval_without_leaves(self, interval, leave_intervals):
        if not interval:
            return interval
        if leave_intervals is None:
            leave_intervals = []
        intervals = []
        leave_intervals = self.with_context(is_leave=True).att_interval_clean(leave_intervals)
        current_interval = [interval[0], interval[1]]
        for leave in leave_intervals:
            if leave[1] <= current_interval[0]:
                continue
            if leave[0] >= current_interval[1]:
                break
            if current_interval[0] < leave[0] < current_interval[1]:
                current_interval[1] = leave[0]
                intervals.append((current_interval[0], current_interval[1]))
                current_interval = [leave[1], interval[1]]
            if current_interval[0] <= leave[1]:
                current_interval[0] = leave[1]
        if current_interval and current_interval[0] < interval[1]:
            # remove intervals moved outside base interval due to leaves
            intervals.append((current_interval[0], current_interval[1]))
        return intervals


class ResourceAttendance(models.Model):
    _inherit = "resource.calendar.attendance"
    #
    day_period = fields.Selection(
        string='Day Period',
        selection=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night')], )


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id:  # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        lang = employee.sudo().address_home_id.lang or self.env.user.lang
        context = {'lang': lang}
        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        del context

        self.name = '%s - %s - %s' % (
            payslip_name,
            self.employee_id.name or '',
            format_date(self.env, self.date_to, date_format="MMMM y", lang_code=lang)
        )

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _(
                "This payslip can be erroneous! Work entries may not be generated for the period from %(start)s to %(end)s.",
                start=date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1),
                end=date_to,
            )
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()
