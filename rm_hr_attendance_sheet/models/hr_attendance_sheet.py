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

import pytz
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date
from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY, \
    make_aware, datetime_to_string, string_to_datetime

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class AttendanceSheet(models.Model):
    _name = 'attendance.sheet'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Hr Attendance Sheet'

    name = fields.Char("name")
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',
                                  required=True)

    batch_id = fields.Many2one(comodel_name='attendance.sheet.batch',
                               string='Attendance Sheet Batch')
    department_id = fields.Many2one(related='employee_id.department_id',
                                    string='Department', store=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 copy=False, required=True,
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=lambda self: fields.Date.to_string(
                                date.today().replace(day=1)), )
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1,
                                                              days=-1)).date()))
    line_ids = fields.One2many(comodel_name='attendance.sheet.line',
                               string='Attendances', readonly=True,
                               inverse_name='att_sheet_id')
    first_contract_date = fields.Date(
        string='First contract date', related='employee_id.first_contract_date',
        required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Draft\' status is used when a HR user is creating a new  attendance sheet. '
             '\n* The \'Confirmed\' status is used when  attendance sheet is confirmed by HR user.'
             '\n* The \'Approved\' status is used when  attendance sheet is accepted by the HR Manager.')
    no_overtime = fields.Integer(compute="_compute_sheet_total",
                                 string="No of overtimes", readonly=True,
                                 store=True)
    tot_overtime = fields.Float(compute="_compute_sheet_total",
                                string="Total Over Time", readonly=True,
                                store=True)
    tot_difftime = fields.Float(compute="_compute_sheet_total",
                                string="Total Diff time Hours", readonly=True,
                                store=True)
    no_difftime = fields.Integer(compute="_compute_sheet_total",
                                 string="No of Diff Times", readonly=True,
                                 store=True)
    tot_late = fields.Float(compute="_compute_sheet_total",
                            string="Total Late In", readonly=True, store=True)
    no_late = fields.Integer(compute="_compute_sheet_total",
                             string="No of Lates",
                             readonly=True, store=True)

    tot_meal = fields.Float(compute="_compute_sheet_total",
                            string="Total Meal Allowance", readonly=True,
                            store=True)
    no_meal = fields.Integer(compute="_compute_sheet_total",
                             string="No of Meals",
                             readonly=True, store=True)
    tot_presence = fields.Float(compute="_compute_sheet_total",
                                string="Presence Allowance", readonly=True,
                                store=True)

    no_absence = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    tot_absence = fields.Float(compute="_compute_sheet_total",
                               string="Total absence Hours", readonly=True,
                               store=True)
    tot_worked_hour = fields.Float(compute="_compute_sheet_total",
                                   string="Total Working hours", readonly=True,
                                   store=True)
    att_policy_id = fields.Many2one(comodel_name='hr.attendance.policy',
                                    string="Attendance Policy ", required=True)
    payslip_id = fields.Many2one(comodel_name='hr.payslip', string='PaySlip')

    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  readonly=True,
                                  states={'draft': [('readonly', False)]})

    overtime_request_count = fields.Integer(
        string='Overtime request count', compute='get_overtime_requests',
        required=False)

    transfer_request_count = fields.Integer(
        string='Transfer request count',
        required=False)
    # compute = 'get_transfer_requests',
    absence_count = fields.Integer(
        string='Absence count',
        required=False)

    no_missing_in = fields.Integer(
        string='No of missing in',
        compute="_compute_missing_total",
        store=True,
        readonly=True,
        required=False)
    tot_missing_in = fields.Integer(
        string='Total of missing in',
        compute="_compute_missing_total",
        store=True,
        readonly=True,
        required=False)
    no_missing_out = fields.Integer(
        string='No of missing out',
        compute="_compute_missing_total",
        store=True,
        readonly=True,
        required=False)
    tot_missing_out = fields.Integer(
        string='Total of missing out',
        compute="_compute_missing_total",
        store=True,
        readonly=True,
        required=False)

    @api.depends('line_ids')
    def _compute_missing_total(self):
        """
        Compute Total Missing
        :return:
        """
        for sheet in self:
            # Compute Total Missing
            missing_in_lines = sheet.line_ids.filtered(lambda l: l.finger_status == 'fixin')
            sheet.tot_missing_in = sum([l.float_fix_in for l in missing_in_lines])
            sheet.no_missing_in = len(missing_in_lines)
            # Compute Total Late In
            missing_out_lines = sheet.line_ids.filtered(lambda l: l.finger_status == 'fixout')
            sheet.tot_missing_out = sum([l.float_fix_out for l in missing_out_lines])
            sheet.no_missing_out = len(missing_out_lines)

    @api.depends('employee_id')
    def get_overtime_requests(self):
        for rec in self:
            if rec.employee_id:
                rec.overtime_request_count = self.env['hr.overtime.request'].search_count(
                    [('employee_ids', 'in', rec.employee_id.id), ('date_from', '>=', rec.date_from),
                     ('date_to', '<=', rec.date_to), ('stage_id.stage_type', '=', 'done')])
            else:
                rec.overtime_request_count = 0

    # @api.depends('employee_id')
    # def get_transfer_requests(self):
    #     for rec in self:
    #         if rec.employee_id:
    #             rec.transfer_request_count = self.env['fleet.transfer.request'].search_count(
    #                 [('employee_id', '=', rec.employee_id.id), ('date', '>=', rec.date_from),
    #                  ('close_time', '<=', rec.date_to), ('state', '=', 'closed')])
    #         else:
    #             rec.transfer_request_count = 0

    def open_requests(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'OverTime Requests',
            'res_model': 'hr.overtime.request',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('stage_id.stage_type', '=', 'done'), ('employee_ids', 'in', self.employee_id.id),
                       ('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)]
        }

    # def open_transfers(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Transfer Requests',
    #         'res_model': 'fleet.transfer.request',
    #         'view_type': 'form',
    #         'view_mode': 'tree,form',
    #         'domain': [('employee_id', '=', self.employee_id.id), ('date', '>=', self.date_from),
    #                    ('close_time', '<=', self.date_to), ('state', '=', 'closed')]
    #     }

    def open_allocations(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'overtime Allocations',
            'res_model': 'hr.leave.allocation',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('attend_sheet_id', '=', self.id), ]
        }

    # def unlink(self):
    #     if any(self.filtered(
    #             lambda att: att.state not in ('draft'))):
    #         # TODO:un comment validation in case on non testing
    #         pass
    #         raise UserError(_(
    #             'You cannot delete an attendance sheet which is not draft !'))
    #     return super(AttendanceSheet, self).unlink()

    @api.constrains('date_from', 'date_to')
    def check_date(self):
        for sheet in self:
            emp_sheets = self.env['attendance.sheet'].search(
                [('employee_id', '=', sheet.employee_id.id),
                 ('id', '!=', sheet.id)])
            for emp_sheet in emp_sheets:
                if max(sheet.date_from, emp_sheet.date_from) < min(
                        sheet.date_to, emp_sheet.date_to):
                    raise UserError(_(
                        'You Have Already Attendance Sheet For That '
                        'Period  Please pick another date !'))

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_approve(self):
        self.action_create_payslip()
        self.write({'state': 'done'})
        self.create_time_off()

    def _check_over_time_allocation(self):
        for sheet in self.env['attendance.sheet'].search([('state', '=', 'draft')]):
            sheet.get_attendances()
            sheet.create_time_off()

    def create_time_off(self):
        compensatory_leave = self.env['hr.leave.type'].search([('type', '=', 'compensatory')], limit=1)
        if compensatory_leave:
            if (self.overtime_time_off - self.taken_leaves) / self.contract_id.resource_calendar_id.hours_per_day > 0:
                self.env['hr.leave.allocation'].create({
                    'name': 'Overtime in weekend Timeoff',
                    'holiday_status_id': compensatory_leave.id,
                    'number_of_days': (
                                              self.overtime_time_off - self.taken_leaves) / self.contract_id.resource_calendar_id.hours_per_day,
                    'employee_id': self.employee_id.id,
                    'attend_sheet_id': self.id,
                    'state': 'validate',
                })
                # taken = self.taken_leaves
                # self.taken_leaves += self.overtime_time_off - taken
                self.overtime_time_off = 0

    taken_leaves = fields.Float(
        string='Allocation Created', compute='_get_allocations',
        required=False)

    @api.depends('line_ids')
    def _get_allocations(self):
        for rec in self:
            allocations = self.env['hr.leave.allocation'].search(
                [('state', '=', 'validate'), ('attend_sheet_id', '=', rec.id)])
            rec.taken_leaves = sum(allocations.mapped('number_of_hours_display'))

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        if self.first_contract_date:
            if self.first_contract_date > self.date_from:
                date_from = self.first_contract_date
        date_to = self.date_to
        self.name = 'Attendance Sheet - %s - %s' % (self.employee_id.name or '',
                                                    format_date(self.env,
                                                                self.date_from,
                                                                date_format="MMMM y"))
        self.company_id = employee.company_id
        contracts = employee._get_contracts(date_from, date_to)
        if not contracts:
            raise ValidationError(
                _('There Is No Valid Contract For Employee %s' % employee.name))
        self.contract_id = contracts[0]
        if not self.contract_id.att_policy_id:
            raise ValidationError(_(
                "Employee %s does not have attendance policy" % employee.name))
        self.att_policy_id = self.contract_id.att_policy_id

    @api.depends('line_ids.overtime', 'line_ids.diff_time', 'line_ids.late_in')
    def _compute_sheet_total(self):
        """
        Compute Total overtime,late ,absence,diff time and worked hours
        :return:
        """
        for sheet in self:
            # Compute Total Overtime
            overtime_lines = sheet.line_ids.filtered(lambda l: l.overtime > 0)
            sheet.tot_overtime = sum([l.overtime for l in overtime_lines])
            sheet.no_overtime = len(overtime_lines)
            # Compute Total Late In
            late_lines = sheet.line_ids.filtered(lambda l: l.late_in > 0)
            sheet.tot_late = sum([l.late_in for l in late_lines])
            sheet.no_late = len(late_lines)
            # Compute worked hours
            worked_lines = sheet.line_ids.filtered(lambda l: l.worked_hours > 0)
            sheet.tot_worked_hour = sum([l.worked_hours for l in worked_lines])
            # Compute Absence
            absence_lines = sheet.line_ids.filtered(
                lambda l: l.diff_time > 0 and l.status == "ab")
            sheet.tot_absence = sum([l.diff_time for l in absence_lines])
            sheet.no_absence = len(
                absence_lines) / 2 if self.contract_id.resource_calendar_id.two_shift_per_day else len(absence_lines)

            # conmpute earlyout
            diff_lines = sheet.line_ids.filtered(
                lambda l: l.diff_time > 0 and l.status != "ab")
            sheet.tot_difftime = sum([l.diff_time for l in diff_lines])
            sheet.no_difftime = len(diff_lines)

            # compute meal allowance
            from_date = sheet.date_from
            if sheet.first_contract_date:
                if sheet.first_contract_date > sheet.date_from:
                    from_date = sheet.first_contract_date

            to_date = sheet.date_to
            no_meals = 0
            total_meals = 0
            total_presence = 0

            all_dates = [(from_date + timedelta(days=x)) for x in
                         range((to_date - from_date).days + 1)]
            presence_flag = True
            for day in all_dates:
                has_meal = False
                for line in sheet.line_ids:
                    if line.date != day:
                        continue
                    if min(line.act_overtime, line.approved_overtime) > 3:
                        has_meal = True
                    if line.pl_sign_in > 0 and line.ac_sign_in == 0:
                        presence_flag = False

                if has_meal:
                    no_meals += 1
            meal_allowance = sheet.att_policy_id.meal_allowance
            total_meals = no_meals * meal_allowance
            sheet.tot_meal = total_meals
            sheet.no_meal = no_meals
            if presence_flag:
                total_presence = sheet.att_policy_id.presence_allowance
            sheet.tot_presence = total_presence

    def _get_float_from_time(self, time):
        str_time = datetime.strftime(time, "%H:%M")
        split_time = [int(n) for n in str_time.split(":")]
        float_time = split_time[0] + split_time[1] / 60.0
        return float_time

    def get_attendance_intervals(self, employee, day_start, day_end, tz):
        """

        :param employee:
        :param day_start:datetime the start of the day in datetime format
        :param day_end: datetime the end of the day in datetime format
        :return:
        """
        day_start_native = day_start.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        day_end_native = day_end.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        res = []
        attendances = self.env['hr.attendance'].sudo().search(
            [('employee_id.id', '=', employee.id),
             ('check_in', '>=', day_start_native),
             ('check_in', '<=', day_end_native)],
            order="check_in")
        for att in attendances:
            check_in = att.check_in
            check_out = att.check_out
            state = att.state
            if not check_out:
                continue
            res.append((check_in, check_out, state))
        return res

    def _get_emp_leave_intervals(self, emp, start_datetime=None,
                                 end_datetime=None):
        leaves = []
        leave_obj = self.env['hr.leave']
        leave_ids = leave_obj.search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'validate')])

        for leave in leave_ids:
            date_from = leave.date_from
            if end_datetime and date_from > end_datetime:
                continue
            date_to = leave.date_to
            if start_datetime and date_to < start_datetime:
                continue
            leaves.append((date_from, date_to))
        return leaves

    def get_public_holiday(self, date, emp):
        public_holiday = []
        public_holidays = self.env['hr.public.holiday'].sudo().search(
            [('date_from', '<=', date), ('date_to', '>=', date),
             ('state', '=', 'active')])
        for ph in public_holidays:
            if not ph.emp_ids:
                return public_holidays
            if emp.id in ph.emp_ids.ids:
                public_holiday.append(ph.id)
        return public_holiday

    overtime_time_off = fields.Float(
        string='Overtime timeoff',
        required=False)

    def get_attendances(self):
        for att_sheet in self:
            att_sheet.overtime_time_off = 0
            contract = att_sheet.contract_id
            att_sheet.line_ids.unlink()
            att_line = self.env["attendance.sheet.line"]
            from_date = att_sheet.date_from
            if att_sheet.first_contract_date:
                if att_sheet.first_contract_date > att_sheet.date_from:
                    from_date = att_sheet.first_contract_date

            to_date = att_sheet.date_to
            emp = att_sheet.employee_id
            tz = pytz.timezone(emp.tz)
            if not tz:
                raise exceptions.Warning(
                    "Please add time zone for employee : %s" % emp.name)
            calendar_id = emp.contract_id.resource_calendar_id
            if not calendar_id:
                raise ValidationError(_(
                    'Please add working hours to the %s `s contract ' % emp.name))
            policy_id = att_sheet.att_policy_id
            if not policy_id:
                raise ValidationError(_(
                    'Please add Attendance Policy to the %s `s contract ' % emp.name))

            all_dates = [(from_date + timedelta(days=x)) for x in
                         range((to_date - from_date).days + 1)]
            abs_cnt = 1
            late_times = policy_id.get_late_times()
            late_types_counter = []
            if late_times:
                late_types_counter = dict.fromkeys(late_times, 1)

            diff_times = policy_id.get_diff_times()
            diff_types_counter = []
            if diff_times:
                diff_types_counter = dict.fromkeys(diff_times, 1)

            absence_types_counter = []
            # absence_times = policy_id.get_absence_times()
            # print(absence_times,'<<<<< absence_times')
            # if absence_times:
            absence_types_counter = dict.fromkeys([0.0], 1)
            act_total_late = 0
            diff_cnt = 0
            late_cnt = 1
            finger_in_cnt = 0
            finger_out_cnt = 0
            float_fix_in = 0
            float_fix_out = 0
            last_abs = 0
            late_type_list = []
            allow_late = policy_id.allow_late
            passed_sheet_in_this_year = self.env['attendance.sheet'].search(
                [('employee_id', '=', emp.id), ('date_from', '>=', to_date.replace(day=1, month=1)),
                 ('id', '!=', att_sheet.id)])
            if passed_sheet_in_this_year:
                last_abs = sum(passed_sheet_in_this_year.mapped('absence_count'))
                abs_cnt = last_abs
            else:
                abs_cnt = last_abs
            for day in all_dates:
                day_start = datetime(day.year, day.month, day.day)
                day_end = day_start.replace(hour=23, minute=59,
                                            second=59)
                day_str = str(day.weekday())
                date = day.strftime('%Y-%m-%d')
                approved_overtime = 0
                if contract.multi_shift:
                    work_intervals = att_sheet.employee_id.get_employee_shifts(day_start, day_end, tz)
                    work_intervals = calendar_id.att_interval_clean(work_intervals)
                else:
                    work_intervals = calendar_id.att_get_work_intervals(day_start, day_end, tz)
                # work_intervals = calendar_id.att_get_work_intervals(day_start,
                #                                                     day_end, tz)
                attendance_intervals = self.get_attendance_intervals(emp,
                                                                     day_start,
                                                                     day_end,
                                                                     tz)
                leaves = self._get_emp_leave_intervals(emp, day_start, day_end)
                public_holiday = self.get_public_holiday(date, emp)
                reserved_intervals = []
                day_period = False

                overtime_policy = policy_id.get_overtime()

                abs_flag = False
                diff_flag = False
                late_flag = False
                exc_overtime = 0
                if work_intervals:
                    if public_holiday:
                        if attendance_intervals:
                            for attendance_interval in attendance_intervals:
                                finger_status = attendance_interval[2]
                                float_fix_in = 0
                                float_fix_out = 0
                                if finger_status == 'fixin':
                                    finger_in_cnt += 1
                                    float_fix_in = policy_id.get_finger(finger_in_cnt, finger_status, contract)
                                    float_fix_out = 0
                                if finger_status == 'fixout':
                                    finger_out_cnt += 1
                                    float_fix_out = policy_id.get_finger(finger_out_cnt, finger_status, contract)
                                    float_fix_in = 0

                                overtime = attendance_interval[1] - \
                                           attendance_interval[0]
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy['ph_after']:
                                    act_float_overtime = float_overtime = 0
                                else:
                                    # act_float_overtime = (float_overtime - overtime_policy['ph_after']) hashed to get total time as overtime because it an bublic holiday
                                    act_float_overtime = float_overtime
                                    float_overtime = float_overtime * overtime_policy['ph_rate']
                                ac_sign_in = pytz.utc.localize(
                                    attendance_interval[0]).astimezone(tz)
                                float_ac_sign_in = self._get_float_from_time(
                                    ac_sign_in)
                                ac_sign_out = pytz.utc.localize(
                                    attendance_interval[1]).astimezone(tz)
                                worked_hours = attendance_interval[1] - \
                                               attendance_interval[0]
                                float_worked_hours = worked_hours.total_seconds() / 3600
                                float_ac_sign_out = float_ac_sign_in + float_worked_hours
                                if float_overtime:
                                    approved_request = self.check_overtime_request(day)
                                    if approved_request == 0:
                                        float_overtime = 0
                                    else:
                                        approved_overtime = approved_request
                                        exc_overtime = act_float_overtime - approved_request
                                        # if exc_overtime < 0:
                                        #     att_sheet.overtime_time_off += act_float_overtime
                                        # else:
                                        #     att_sheet.overtime_time_off += act_float_overtime - exc_overtime
                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'ac_sign_in': float_ac_sign_in,
                                    'ac_sign_out': float_ac_sign_out,
                                    'worked_hours': float_worked_hours,
                                    'overtime': float_overtime,
                                    'act_overtime': act_float_overtime,
                                    'exc_overtime': exc_overtime,
                                    'approved_overtime': approved_overtime,
                                    'att_sheet_id': self.id,
                                    'status': 'ph',
                                    'finger_status': attendance_interval[2],
                                    'float_fix_in': float_fix_in,
                                    'float_fix_out': float_fix_out,
                                    'note': _("working on Public Holiday")
                                }
                                att_line.create(values)
                        else:
                            values = {
                                'date': date,
                                'day': day_str,
                                'att_sheet_id': self.id,
                                'status': 'ph',
                            }
                            att_line.create(values)
                    else:
                        for i, work_interval in enumerate(work_intervals):
                            float_worked_hours = 0
                            att_work_intervals = []
                            diff_intervals = []
                            finger_status = ''
                            late_in_interval = []
                            diff_time = timedelta(hours=00, minutes=00,
                                                  seconds=00)
                            late_in = timedelta(hours=00, minutes=00,
                                                seconds=00)
                            overtime = timedelta(hours=00, minutes=00,
                                                 seconds=00)
                            for j, att_interval in enumerate(attendance_intervals):
                                finger_status = att_interval[2]
                                float_fix_in = 0
                                float_fix_out = 0
                                if finger_status == 'fixin':
                                    finger_in_cnt += 1
                                    float_fix_in = policy_id.get_finger(finger_in_cnt, finger_status, contract)
                                    float_fix_out = 0
                                if finger_status == 'fixout':
                                    finger_out_cnt += 1
                                    float_fix_out = policy_id.get_finger(finger_out_cnt, finger_status, contract)
                                    float_fix_in = 0

                                if max(work_interval[0], att_interval[0]) < min(
                                        work_interval[1], att_interval[1]):
                                    current_att_interval = att_interval
                                    if i + 1 < len(work_intervals):
                                        next_work_interval = work_intervals[
                                            i + 1]
                                        if max(next_work_interval[0],
                                               current_att_interval[0]) < min(
                                            next_work_interval[1],
                                            current_att_interval[1]):
                                            split_att_interval = (
                                                next_work_interval[0],
                                                current_att_interval[1])
                                            current_att_interval = (
                                                current_att_interval[0],
                                                next_work_interval[0])
                                            attendance_intervals[j] = current_att_interval
                                            attendance_intervals.insert(j + 1, split_att_interval)
                                    att_work_intervals.append(
                                        current_att_interval)
                            reserved_intervals += att_work_intervals
                            pl_sign_in = self._get_float_from_time(
                                pytz.utc.localize(work_interval[0]).astimezone(
                                    tz))
                            pl_sign_out = self._get_float_from_time(
                                pytz.utc.localize(work_interval[1]).astimezone(
                                    tz))
                            pl_sign_in_time = pytz.utc.localize(
                                work_interval[0]).astimezone(tz)
                            pl_sign_out_time = pytz.utc.localize(
                                work_interval[1]).astimezone(tz)
                            ac_sign_in = 0
                            ac_sign_out = 0
                            status = ""
                            note = ""
                            if att_work_intervals:
                                if len(att_work_intervals) > 1:
                                    late_in_interval = (
                                        work_interval[0],
                                        att_work_intervals[0][0])
                                    overtime_interval = (work_interval[1], att_work_intervals[-1][1])
                                    if overtime_interval[1] < overtime_interval[0]:
                                        overtime = timedelta(hours=0, minutes=0, seconds=0)
                                    else:
                                        overtime = overtime_interval[1] - overtime_interval[0]
                                    remain_interval = (att_work_intervals[0][1], work_interval[1])
                                    for att_work_interval in att_work_intervals:
                                        float_worked_hours += (att_work_interval[1] - att_work_interval[
                                            0]).total_seconds() / 3600
                                        if att_work_interval[1] <= \
                                                remain_interval[0]:
                                            continue
                                        if att_work_interval[0] >= \
                                                remain_interval[1]:
                                            break
                                        if remain_interval[0] < \
                                                att_work_interval[0] < \
                                                remain_interval[1]:
                                            diff_intervals.append((
                                                remain_interval[
                                                    0],
                                                att_work_interval[
                                                    0]))
                                            remain_interval = (
                                                att_work_interval[1],
                                                remain_interval[1])
                                    if remain_interval and remain_interval[0] <= work_interval[1]:
                                        diff_intervals.append((remain_interval[0], work_interval[1]))
                                    ac_sign_in = self._get_float_from_time(pytz.utc.localize(att_work_intervals[0][
                                                                                                 0]).astimezone(tz))
                                    ac_sign_out = self._get_float_from_time(
                                        pytz.utc.localize(
                                            att_work_intervals[-1][
                                                1]).astimezone(tz))
                                    # ac_sign_out = ac_sign_in + ((att_work_intervals[-1][1] - att_work_intervals[0][
                                    #     0]).total_seconds() / 3600)
                                else:
                                    late_in_interval = (work_interval[0], att_work_intervals[0][0])
                                    overtime_interval = (work_interval[1], att_work_intervals[-1][1])
                                    if overtime_interval[1] < overtime_interval[0]:
                                        overtime = timedelta(hours=0, minutes=0, seconds=0)
                                        diff_intervals.append((overtime_interval[1], overtime_interval[0]))
                                    else:
                                        overtime = overtime_interval[1] - overtime_interval[0]
                                    ac_sign_in = self._get_float_from_time(pytz.utc.localize(att_work_intervals[0][
                                                                                                 0]).astimezone(tz))
                                    ac_sign_out = self._get_float_from_time(pytz.utc.localize(att_work_intervals[0][
                                                                                                  1]).astimezone(tz))
                                    worked_hours = att_work_intervals[0][1] - att_work_intervals[0][0]
                                    float_worked_hours = worked_hours.total_seconds() / 3600
                                    # ac_sign_out = ac_sign_in + float_worked_hours
                            else:
                                late_in_interval = []
                                diff_intervals.append(
                                    (work_interval[0], work_interval[1]))

                                status = "ab"
                            if diff_intervals:
                                for diff_in in diff_intervals:
                                    if leaves:
                                        status = "leave"
                                        diff_clean_intervals = calendar_id.att_interval_without_leaves(diff_in, leaves)
                                        for diff_clean in diff_clean_intervals:
                                            diff_time += diff_clean[1] - diff_clean[0]
                                    else:
                                        diff_time += diff_in[1] - diff_in[0]
                            if late_in_interval:
                                if late_in_interval[1] < late_in_interval[0]:
                                    late_in = timedelta(hours=0, minutes=0, seconds=0)
                                else:
                                    if leaves:
                                        late_clean_intervals = calendar_id.att_interval_without_leaves(late_in_interval,
                                                                                                       leaves)
                                        for late_clean in late_clean_intervals:
                                            late_in += late_clean[1] - late_clean[0]
                                    else:
                                        late_in = late_in_interval[1] - \
                                                  late_in_interval[0]
                            float_overtime = overtime.total_seconds() / 3600
                            if float_overtime <= overtime_policy['wd_after']:
                                act_float_overtime = float_overtime = 0
                            else:
                                act_float_overtime = float_overtime

                                if ac_sign_out < 12.0 and overtime_policy['wd_app_f_2'] <= ac_sign_out <= \
                                        overtime_policy['wd_app_t_2']:
                                    p1_overtime = act_float_overtime - ac_sign_out
                                    p2_overtime = ac_sign_out

                                    float_overtime = (p1_overtime * overtime_policy['wd_rate']) + (
                                            p2_overtime * overtime_policy['wd_rate_2'])

                                elif overtime_policy['wd_app_f_1'] <= ac_sign_out <= \
                                        overtime_policy['wd_app_t_1']:
                                    float_overtime = (act_float_overtime * overtime_policy['wd_rate'])

                                else:
                                    float_overtime = 0.0
                                    # frist_overtime = (f2 - datetime.strptime(
                                    #     work_interval[1].astimezone(tz).strftime(DATETIME_FORMAT), DATETIME_FORMAT))
                                    # second_overtime = (datetime.strptime(
                                    #     att_work_intervals[0][1].astimezone(tz).strftime(DATETIME_FORMAT),
                                    #     DATETIME_FORMAT) - f2)
                                    # float_overtime = (frist_overtime.total_seconds() / 3600 * overtime_policy[
                                    #     'wd_rate']) + (second_overtime.total_seconds() / 3600 * overtime_policy[
                                    #     'wd_rate_2'])
                            # float_late = late_in.total_seconds() / 3600
                            act_float_late = late_in.total_seconds() / 3600
                            act_total_late += act_float_late
                            # policy_late_type = policy_id.get_late_type(float_late)
                            policy_late = 0
                            # if policy_late_type:
                            #     policy_late = policy_id.get_late_exact(float_late, policy_late_type, 1, contract)
                            #
                            if act_total_late < allow_late:
                                policy_late = 0
                            float_diff = diff_time.total_seconds() / 3600
                            act_float_diff = float_diff

                            if status == 'ab':
                                if not abs_flag:
                                    abs_cnt += 1
                                abs_flag = True
                                act_float_diff = float_diff
                                policy_absence_type = policy_id.get_absence_type()
                                if policy_absence_type:
                                    # count = absence_types_counter[policy_absence_type]
                                    float_diff = policy_id.get_absence_exact(act_float_diff, policy_absence_type,
                                                                             abs_cnt,
                                                                             contract)
                                    # absence_types_counter[policy_absence_type] = count + 1

                            else:
                                if float_diff:
                                    act_float_diff = float_diff
                                    policy_diff_type = policy_id.get_diff_type(act_float_diff)
                                    if policy_diff_type:
                                        count = diff_types_counter[policy_diff_type]
                                        float_diff = policy_id.get_diff_exact(act_float_diff, policy_diff_type, count,
                                                                              contract)
                                        diff_types_counter[policy_diff_type] = count + 1
                                        diff_flag = True

                                    # if not diff_flag:
                                    #     diff_cnt += 1
                                    # diff_flag = True
                                    # act_float_diff = float_diff
                                    # float_diff = policy_id.get_diff(float_diff, diff_cnt,contract)

                                if act_float_late:
                                    act_late_diff = act_float_late
                                    policy_late_type = policy_id.get_late_type(act_late_diff)
                                    if policy_late_type:
                                        count = late_types_counter[policy_late_type]
                                        policy_late = policy_id.get_late_exact(act_late_diff, policy_late_type, count,
                                                                               contract)
                                        late_types_counter[policy_late_type] = count + 1
                                        late_flag = True
                            if contract.overtime_approve:
                                if float_overtime:

                                    approved_request = self.check_overtime_request(day)
                                    if approved_request == 0:
                                        float_overtime = 0
                                    else:
                                        approved_overtime = approved_request
                                        exc_overtime = act_float_overtime - approved_request
                                        if exc_overtime < 0:
                                            att_sheet.overtime_time_off += act_float_overtime
                                        else:
                                            att_sheet.overtime_time_off += act_float_overtime - exc_overtime
                            else:
                                approved_request = self.check_overtime_request(day)
                                approved_overtime = approved_request
                                exc_overtime = act_float_overtime - approved_request
                                if exc_overtime < 0:
                                    att_sheet.overtime_time_off += act_float_overtime
                                else:
                                    att_sheet.overtime_time_off += act_float_overtime - exc_overtime
                            values = {
                                'date': date,
                                'day': day_str,
                                'pl_sign_in': pl_sign_in,
                                'pl_sign_out': pl_sign_out,
                                'ac_sign_in': ac_sign_in,
                                'ac_sign_out': ac_sign_out,
                                'late_in': policy_late,
                                'act_late_in': act_float_late,
                                'worked_hours': float_worked_hours,
                                'overtime': float_overtime,
                                'approved_overtime': approved_overtime,
                                'act_overtime': act_float_overtime,
                                'exc_overtime': exc_overtime,
                                'diff_time': float_diff,
                                'act_diff_time': act_float_diff,
                                'finger_status': finger_status,
                                'float_fix_in': float_fix_in,
                                'float_fix_out': float_fix_out,
                                'status': status,
                                'att_sheet_id': self.id
                            }
                            att_line.create(values)
                        out_work_intervals = [x for x in attendance_intervals if
                                              x not in reserved_intervals]
                        if out_work_intervals:
                            for att_out in out_work_intervals:
                                overtime = att_out[1] - att_out[0]
                                ac_sign_in = self._get_float_from_time(
                                    pytz.utc.localize(att_out[0]).astimezone(
                                        tz))
                                ac_sign_out = self._get_float_from_time(
                                    pytz.utc.localize(att_out[1]).astimezone(
                                        tz))
                                float_worked_hours = overtime.total_seconds() / 3600
                                # ac_sign_out = ac_sign_in + float_worked_hours
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy['wd_after']:
                                    float_overtime = act_float_overtime = 0
                                else:
                                    act_float_overtime = float_overtime
                                    float_overtime = act_float_overtime * overtime_policy['wd_rate']
                                if contract.overtime_approve:
                                    if float_overtime:
                                        approved_request = self.check_overtime_request(day)
                                        if approved_request == 0:
                                            float_overtime = 0
                                        else:
                                            approved_overtime = approved_request
                                            exc_overtime = act_float_overtime - approved_request
                                            if exc_overtime < 0:
                                                att_sheet.overtime_time_off += act_float_overtime
                                            else:
                                                att_sheet.overtime_time_off += act_float_overtime - exc_overtime
                                else:
                                    approved_request = self.check_overtime_request(day)
                                    approved_overtime = approved_request
                                    exc_overtime = act_float_overtime - approved_request
                                    if exc_overtime < 0:
                                        att_sheet.overtime_time_off += act_float_overtime
                                    else:
                                        att_sheet.overtime_time_off += act_float_overtime - exc_overtime

                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'pl_sign_in': 0,
                                    'pl_sign_out': 0,
                                    'ac_sign_in': ac_sign_in,
                                    'ac_sign_out': ac_sign_out,
                                    'overtime': float_overtime,
                                    'worked_hours': float_worked_hours,
                                    'act_overtime': act_float_overtime,
                                    'approved_overtime': approved_overtime,
                                    'exc_overtime': exc_overtime,
                                    'note': _("overtime out of work intervals"),
                                    'att_sheet_id': self.id
                                }
                                att_line.create(values)
                else:
                    if public_holiday:
                        if attendance_intervals:
                            for attendance_interval in attendance_intervals:
                                finger_status = attendance_interval[2]
                                float_fix_in = 0
                                float_fix_out = 0
                                if finger_status == 'fixin':
                                    finger_in_cnt += 1
                                    float_fix_in = policy_id.get_finger(finger_in_cnt, finger_status, contract)
                                    float_fix_out = 0
                                if finger_status == 'fixout':
                                    finger_out_cnt += 1
                                    float_fix_out = policy_id.get_finger(finger_out_cnt, finger_status, contract)
                                    float_fix_in = 0
                                overtime = attendance_interval[1] - \
                                           attendance_interval[0]
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy['ph_after']:
                                    act_float_overtime = float_overtime = 0
                                else:
                                    # act_float_overtime = (float_overtime - overtime_policy['ph_after']) hashed to get total time as overtime because it an bublic holiday
                                    act_float_overtime = float_overtime
                                    float_overtime = (float_overtime - overtime_policy['ph_after']) * overtime_policy[
                                        'ph_rate']
                                ac_sign_in = pytz.utc.localize(
                                    attendance_interval[0]).astimezone(tz)
                                float_ac_sign_in = self._get_float_from_time(
                                    ac_sign_in)
                                ac_sign_out = pytz.utc.localize(
                                    attendance_interval[1]).astimezone(tz)
                                worked_hours = attendance_interval[1] - \
                                               attendance_interval[0]
                                float_worked_hours = worked_hours.total_seconds() / 3600
                                float_ac_sign_out = float_ac_sign_in + float_worked_hours
                                if contract.overtime_approve:
                                    if float_overtime:
                                        approved_request = self.check_overtime_request(day)
                                        if approved_request == 0:
                                            float_overtime = 0
                                        else:
                                            approved_overtime = approved_request
                                            exc_overtime = act_float_overtime - approved_request
                                            if exc_overtime < 0:
                                                att_sheet.overtime_time_off += act_float_overtime
                                            else:
                                                att_sheet.overtime_time_off += act_float_overtime - exc_overtime
                                    else:
                                        approved_request = self.check_overtime_request(day)
                                        approved_overtime = approved_request
                                        exc_overtime = act_float_overtime - approved_request
                                        if exc_overtime < 0:
                                            att_sheet.overtime_time_off += act_float_overtime
                                        else:
                                            att_sheet.overtime_time_off += act_float_overtime - exc_overtime

                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'ac_sign_in': float_ac_sign_in,
                                    'ac_sign_out': ac_sign_out,
                                    'worked_hours': float_worked_hours,
                                    'overtime': float_overtime,
                                    'act_overtime': act_float_overtime,
                                    'approved_overtime': approved_overtime,
                                    'exc_overtime': exc_overtime,
                                    'att_sheet_id': self.id,
                                    'status': 'ph',
                                    'finger_status': attendance_interval[2],
                                    'float_fix_in': float_fix_in,
                                    'float_fix_out': float_fix_out,
                                    'note': _("working on Public Holiday")
                                }
                                att_line.create(values)
                        else:
                            values = {
                                'date': date,
                                'day': day_str,
                                'att_sheet_id': self.id,
                                'status': 'ph',
                            }
                            att_line.create(values)
                    if attendance_intervals and not public_holiday:
                        for attendance_interval in attendance_intervals:
                            finger_status = attendance_interval[2]
                            if finger_status == 'fixin':
                                finger_in_cnt += 1
                                float_fix_in = policy_id.get_finger(finger_in_cnt, finger_status, contract)
                                float_fix_out = 0
                            if finger_status == 'fixout':
                                finger_out_cnt += 1
                                float_fix_out = policy_id.get_finger(finger_out_cnt, finger_status, contract)
                                float_fix_in = 0

                            overtime = attendance_interval[1] - attendance_interval[0]
                            ac_sign_in = pytz.utc.localize(attendance_interval[0]).astimezone(tz)
                            ac_sign_out = pytz.utc.localize(attendance_interval[1]).astimezone(tz)
                            float_overtime = overtime.total_seconds() / 3600
                            if float_overtime <= overtime_policy['we_after']:
                                float_overtime = act_float_overtime = 0
                            else:
                                act_float_overtime = float_overtime
                                float_overtime = act_float_overtime * overtime_policy['we_rate']
                            ac_sign_in = pytz.utc.localize(
                                attendance_interval[0]).astimezone(tz)
                            ac_sign_out = pytz.utc.localize(
                                attendance_interval[1]).astimezone(tz)
                            worked_hours = attendance_interval[1] - \
                                           attendance_interval[0]
                            float_worked_hours = worked_hours.total_seconds() / 3600
                            if float_overtime:
                                approved_request = self.check_overtime_request(day)
                                if approved_request == 0:
                                    float_overtime = 0
                                else:
                                    approved_overtime = approved_request
                                    exc_overtime = act_float_overtime - approved_request
                                    if exc_overtime < 0:
                                        att_sheet.overtime_time_off += act_float_overtime
                                    else:
                                        att_sheet.overtime_time_off += act_float_overtime - exc_overtime

                            values = {
                                'date': date,
                                'day': day_str,
                                'ac_sign_in': self._get_float_from_time(
                                    ac_sign_in),
                                'ac_sign_out': self._get_float_from_time(
                                    ac_sign_out),
                                'overtime': float_overtime,
                                'act_overtime': act_float_overtime,
                                'exc_overtime': exc_overtime,
                                'worked_hours': float_worked_hours,
                                'approved_overtime': approved_overtime,
                                'att_sheet_id': self.id,
                                'status': 'weekend',
                                'finger_status': attendance_interval[2],
                                'float_fix_in': float_fix_in,
                                'float_fix_out': float_fix_out,
                                'note': _("working in weekend")
                            }
                            att_line.create(values)
                    else:
                        values = {
                            'date': date,
                            'day': day_str,
                            'att_sheet_id': self.id,
                            'status': 'weekend',
                            'note': ""
                        }
                        att_line.create(values)
            att_sheet.absence_count = abs_cnt - last_abs

    def check_overtime_request(self, day):
        ReqObj = self.env['hr.overtime.request']
        approved_request = ReqObj.search(
            [('employee_ids', 'in', self.employee_id.id), ('stage_id.stage_type', '=', 'done'),
             ('date_from', '>=', day.strftime("%Y-%m-%d 00:00:00")),
             ('date_to', '<=', day.strftime("%Y-%m-%d 23:59:59"))], )
        if approved_request:
            total_overtime = sum(approved_request.mapped('overtime'))
            return total_overtime
        else:
            return False

    def action_payslip(self):
        self.ensure_one()
        payslip_id = self.payslip_id
        if not payslip_id:
            payslip_id = self.action_create_payslip()[0]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': payslip_id.id,
            'views': [(False, 'form')],
        }

    def action_create_payslip(self):
        payslip_obj = self.env['hr.payslip']
        payslips = payslip_obj
        for sheet in self:
            contracts = sheet.employee_id._get_contracts(sheet.date_from,
                                                         sheet.date_to)
            if not contracts:
                raise ValidationError(_('There is no active contract for current employee'))
            if sheet.payslip_id:
                raise ValidationError(_('Payslip Has Been Created Before'))
            new_payslip = payslip_obj.new({
                'employee_id': sheet.employee_id.id,
                'date_from': sheet.date_from if sheet.date_from > sheet.first_contract_date else sheet.first_contract_date,
                'date_to': sheet.date_to,
                'attendence_sheet_id': sheet.id,
                'contract_id': contracts[0].id,
                'struct_id': contracts[0].structure_type_id.default_struct_id.id
            })
            new_payslip._onchange_employee()
            payslip_dict = new_payslip._convert_to_write({
                name: new_payslip[name] for name in new_payslip._cache})

            payslip_id = payslip_obj.create(payslip_dict)
            worked_day_lines = self._get_workday_lines()
            payslip_id.worked_days_line_ids = [(0, 0, x) for x in
                                               worked_day_lines]
            payslip_id.compute_sheet()
            sheet.payslip_id = payslip_id
            payslips += payslip_id
        return payslips

    def _get_workday_lines(self):
        self.ensure_one()
        work_entry_obj = self.env['hr.work.entry.type']
        overtime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHOT')])
        latin_work_entry = work_entry_obj.search([('code', '=', 'ATTSHLI')])
        missing_in_work_entry = work_entry_obj.search([('code', '=', 'ATTSHMI')])
        missing_out_work_entry = work_entry_obj.search([('code', '=', 'ATTSHMO')])
        absence_work_entry = work_entry_obj.search([('code', '=', 'ATTSHAB')])
        difftime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHDT')])
        meal_work_entry = work_entry_obj.search([('code', '=', 'ATTSHMEAL')])
        presence_work_entry = work_entry_obj.search([('code', '=', 'ATTSHPRS')])
        act_working_hours_entry = work_entry_obj.search([('code', '=', 'ATSHWH')])

        if not overtime_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Overtime With Code ATTSHOT'))
        if not latin_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Late In With Code ATTSHLI'))
        if not absence_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Absence With Code ATTSHAB'))
        if not difftime_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHDT'))
        if not meal_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Meal Allowance Time With Code ATTSHMEAL'))

        if not presence_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Presence Allowance Time With Code ATTSHPRS'))
        if not act_working_hours_entry:
                    raise ValidationError(_(
                        'Please Add Work Entry Type For Attendance Sheet Working Hours With Code ATSHWH'))

        overtime = [{
            'name': "Overtime",
            'code': 'OVT',
            'work_entry_type_id': overtime_work_entry[0].id,
            'sequence': 30,
            'number_of_days': self.no_overtime,
            'number_of_hours': self.tot_overtime,
        }]
        absence = [{
            'name': "Absence",
            'code': 'ABS',
            'work_entry_type_id': absence_work_entry[0].id,
            'sequence': 35,
            'number_of_days': self.no_absence,
            'number_of_hours': self.tot_absence,
        }]
        late = [{
            'name': "Late In",
            'code': 'LATE',
            'work_entry_type_id': latin_work_entry[0].id,
            'sequence': 40,
            'number_of_days': self.no_late,
            'number_of_hours': self.tot_late,
        }]
        difftime = [{
            'name': "Difference time",
            'code': 'DIFFT',
            'work_entry_type_id': difftime_work_entry[0].id,
            'sequence': 45,
            'number_of_days': self.no_difftime,
            'number_of_hours': self.tot_difftime,
        }]
        pre_allow = [{
            'name': "Presence Allowance",
            'code': 'ATTSHPRS',
            'work_entry_type_id': presence_work_entry[0].id,
            'sequence': 45,
            'number_of_days': 0,
            'number_of_hours': self.tot_presence,
        }]
        missing_in = [{
            'name': "Missing IN",
            'code': 'ATTSHMI',
            'work_entry_type_id': missing_in_work_entry[0].id,
            'sequence': 46,
            'is_paid': True,
            'number_of_days': self.no_missing_in,
            'number_of_hours': self.tot_missing_in,
        }]
        missing_out = [{
            'name': "Missing OUT",
            'code': 'ATTSHMO',
            'work_entry_type_id': missing_out_work_entry[0].id,
            'sequence': 47,
            'is_paid': True,
            'number_of_days': self.no_missing_out,
            'number_of_hours': self.tot_missing_out,
        }]
        working_hours = [{
            'name': "Actual Working hours ",
            'code': 'ATSHWH',
            'work_entry_type_id': act_working_hours_entry[0].id,
            'sequence': 45,
            'number_of_days': int(len(self.line_ids.filtered(lambda l: l.worked_hours > 0))/2),
            'number_of_hours': sum([l.worked_hours for l in self.line_ids]),
        }]
        worked_days_lines = overtime + late + absence + difftime + pre_allow + missing_in + missing_out + working_hours
        return worked_days_lines

    def create_payslip(self):
        payslips = self.env['hr.payslip']
        for att_sheet in self:
            if att_sheet.payslip_id:
                continue
            from_date = att_sheet.date_from
            if att_sheet.first_contract_date:
                if att_sheet.first_contract_date > att_sheet.date_from:
                    from_date = att_sheet.first_contract_date

            to_date = att_sheet.date_to
            employee = att_sheet.employee_id
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date,
                                                                    to_date,
                                                                    employee.id,
                                                                    contract_id=False)
            contract_id = slip_data['value'].get('contract_id')
            if not contract_id:
                raise exceptions.Warning(
                    'There is No Contracts for %s That covers the period of the Attendance sheet' % employee.name)
            worked_days_line_ids = slip_data['value'].get(
                'worked_days_line_ids')

            overtime = [{
                'name': "Overtime",
                'code': 'OVT',
                'contract_id': contract_id,
                'sequence': 30,
                'number_of_days': att_sheet.no_overtime,
                'number_of_hours': att_sheet.tot_overtime,
            }]
            absence = [{
                'name': "Absence",
                'code': 'ABS',
                'contract_id': contract_id,
                'sequence': 35,
                'number_of_days': att_sheet.no_absence,
                'number_of_hours': att_sheet.tot_absence,
            }]
            late = [{
                'name': "Late In",
                'code': 'LATE',
                'contract_id': contract_id,
                'sequence': 40,
                'number_of_days': att_sheet.no_late,
                'number_of_hours': att_sheet.tot_late,
            }]
            difftime = [{
                'name': "Difference time",
                'code': 'DIFFT',
                'contract_id': contract_id,
                'sequence': 45,
                'number_of_days': att_sheet.no_difftime,
                'number_of_hours': att_sheet.tot_difftime,
            }]
            worked_days_line_ids += overtime + late + absence + difftime

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': contract_id,
                'input_line_ids': [(0, 0, x) for x in
                                   slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in
                                         worked_days_line_ids],
                'date_from': from_date,
                'date_to': to_date,
            }
            new_payslip = self.env['hr.payslip'].create(res)
            att_sheet.payslip_id = new_payslip
            payslips += new_payslip
        return payslips

    def create_sheet_every_month(self):
        for contract in self.env['hr.contract'].search([('state', '=', 'open')]):
            sheetobj = self.env['attendance.sheet']
            if date.today().strftime('%d') == '1':
                sheet = sheetobj.new({
                    'employee_id': contract.employee_id.id,
                })
                sheet.onchange_employee()
                sheet_vals = sheet._convert_to_write(sheet._cache)
                sheet.create(sheet_vals)


class AttendanceSheetLine(models.Model):
    _name = 'attendance.sheet.line'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sum', 'Summary'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], related='att_sheet_id.state', store=True, )

    date = fields.Date("Date")
    day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, )
    att_sheet_id = fields.Many2one(comodel_name='attendance.sheet',
                                   ondelete="cascade",
                                   string='Attendance Sheet', readonly=True)
    employee_id = fields.Many2one(related='att_sheet_id.employee_id',
                                  string='Employee')
    pl_sign_in = fields.Float("Planned sign in", readonly=True)
    pl_sign_out = fields.Float("Planned sign out", readonly=True)
    worked_hours = fields.Float("Worked Hours", readonly=True)
    ac_sign_in = fields.Float("Actual sign in", readonly=True)
    ac_sign_out = fields.Float("Actual sign out", readonly=True)
    overtime = fields.Float("Overtime", readonly=True)
    approved_overtime = fields.Float(
        string='Approved overtime',
        required=False)
    act_overtime = fields.Float("Actual Overtime", readonly=True)
    exc_overtime = fields.Float("Overtime Exceeded", readonly=True)
    finger_status = fields.Selection(
        string='Finger_status',
        selection=[('fixin', 'Missing In'), ('fixout', 'Missing Out'), ('right', 'Right')],
        required=False, )

    late_in = fields.Float("Late In", readonly=True)
    diff_time = fields.Float("Diff Time",
                             help="Diffrence between the working time and attendance time(s) ",
                             readonly=True)
    act_late_in = fields.Float("Actual Late In", readonly=True)
    act_diff_time = fields.Float("Actual Diff Time",
                                 help="Diffrence between the working time and attendance time(s) ",
                                 readonly=True)
    float_fix_in = fields.Float("Missing In",
                                help="finger Missing in",
                                readonly=True)
    float_fix_out = fields.Float("Missing OUT",
                                 help="finger Missing out",
                                 readonly=True)
    status = fields.Selection(string="Status",
                              selection=[('ab', 'Absence'),
                                         ('weekend', 'Week End'),
                                         ('ph', 'Public Holiday'),
                                         ('leave', 'Leave'), ],
                              required=False, readonly=True)
    note = fields.Text("Note", readonly=True)
