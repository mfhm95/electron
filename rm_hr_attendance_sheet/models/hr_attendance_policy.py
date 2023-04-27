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
from odoo.exceptions import ValidationError


class HrAttendancePolicy(models.Model):
    _name = 'hr.attendance.policy'
    _description = 'Attendance Sheet Policies'

    name = fields.Char(string="Name", required=True)
    overtime_rule_ids = fields.Many2many(comodel_name="hr.overtime.rule",
                                         relation="overtime_rule_policy_rel",
                                         column1="attendance_policy_col",
                                         column2="overtime_rule_col",
                                         string="Overtime Rules", )
    late_rule_id = fields.Many2one(comodel_name="hr.late.rule", required=True,
                                   string="Late In Rule")
    absence_rule_id = fields.Many2one(comodel_name="hr.absence.rule",
                                      string="Absence Rule", required=True)
    diff_rule_id = fields.Many2one(comodel_name="hr.diff.rule",
                                   string="Difference Time Rule", required=True)

    allow_late = fields.Float('Allowed No Of Hours')
    meal_allowance = fields.Float('Meal Allowance')
    presence_allowance = fields.Float('Presence Allowance')
    is_bus_registered = fields.Boolean(
        string='Bus Registered',
        required=False)
    missing_rule_id = fields.Many2one(comodel_name="hr.missing.finger.rule",
                                      string="Missing Finger Rule")

    def get_overtime(self):
        self.ensure_one()
        res = {}
        if self:
            overtime_ids = self.overtime_rule_ids
            wd_ot_id = self.overtime_rule_ids.search([('type', '=', 'workday'), ('id', 'in', overtime_ids.ids)],
                                                     order='id', limit=1)
            we_ot_id = self.overtime_rule_ids.search([('type', '=', 'weekend'), ('id', 'in', overtime_ids.ids)],
                                                     order='id', limit=1)
            ph_ot_id = self.overtime_rule_ids.search([('type', '=', 'ph'), ('id', 'in', overtime_ids.ids)], order='id',
                                                     limit=1)
            if wd_ot_id:
                res['wd_rate'] = wd_ot_id.rate
                res['wd_rate_2'] = wd_ot_id.rate_2
                res['wd_after'] = wd_ot_id.active_after
                res['wd_app_f_1'] = wd_ot_id.apply_from
                res['wd_app_f_2'] = wd_ot_id.apply_from_2
                res['wd_app_t_1'] = wd_ot_id.apply_to
                res['wd_app_t_2'] = wd_ot_id.apply_to_2
            else:
                res['wd_rate'] = 1
                res['wd_rate_2'] = 1
                res['wd_after'] = 0
                res['wd_app_f_1'] = 0
                res['wd_app_f_2'] = 0
                res['wd_app_t_1'] = 0
                res['wd_app_t_2'] = 0
            if we_ot_id:
                res['we_rate'] = we_ot_id.rate
                res['we_rate_2'] = we_ot_id.rate_2
                res['we_after'] = we_ot_id.active_after
                res['we_app_f_1'] = we_ot_id.apply_from
                res['we_app_f_2'] = we_ot_id.apply_from_2
                res['we_app_t_1'] = we_ot_id.apply_to
                res['we_app_t_2'] = we_ot_id.apply_to_2
            else:
                res['we_rate'] = 1
                res['we_rate_2'] = 1
                res['we_after'] = 0
                res['we_app_f_1'] = 0
                res['we_app_f_2'] = 0
                res['we_app_t_1'] = 0
                res['we_app_t_2'] = 0

            if ph_ot_id:
                res['ph_rate'] = ph_ot_id.rate
                res['ph_rate_2'] = ph_ot_id.rate_2
                res['ph_after'] = ph_ot_id.active_after
                res['ph_app_f_1'] = ph_ot_id.apply_from
                res['ph_app_f_2'] = ph_ot_id.apply_from_2
                res['ph_app_t_1'] = ph_ot_id.apply_to
                res['ph_app_t_2'] = ph_ot_id.apply_to_2
            else:
                res['ph_rate'] = 1
                res['ph_rate_2'] = 1
                res['ph_after'] = 0
                res['ph_app_f_1'] = 0
                res['ph_app_f_2'] = 0
                res['ph_app_t_1'] = 0
                res['ph_app_t_2'] = 0
        else:
            res['wd_rate'] = res['we_rate'] = res['ph_rate'] = 1
            res['wd_rate_2'] = res['we_rate_2'] = res['ph_rate_2'] = 1
            res['wd_after'] = res['we_after'] = res['ph_after'] = 0
            res['wd_app_f_1'] = res['we_app_f_1'] = res['ph_app_f_1'] = 0
            res['wd_app_f_2'] = res['we_app_f_2'] = res['ph_app_f_2'] = 0
            res['wd_app_t_1'] = res['we_app_t_1'] = res['ph_app_t_1'] = 0
            res['wd_app_t_2'] = res['we_app_t_2'] = res['ph_app_t_2'] = 0
        return res

    #  ***************** Late in Rules rules *****************

    # this the first method which used to get all types of polices to be used as dict in the sheet
    # to overwrite on it and get the counter
    def get_late_times(self):
        if self:
            if self.late_rule_id:
                time_ids = self.late_rule_id.line_ids.mapped('time')
                return time_ids

    # this method accepts the much of time which the employee came and returns the type of policy
    # which will be used for to get the exact number

    def get_late_type(self, period):
        self.ensure_one()
        res = period
        flag = False
        if self:
            if self.late_rule_id:
                time_ids = self.late_rule_id.line_ids.sorted(key=lambda r: r.time, reverse=True)
                for line in time_ids:
                    if period >= line.time:
                        flag = True
                        res = line.time
                        break
                if not flag:
                    res = 0
        return res

    # this method accept the type of the late and the counter and return the exact number will be applied on the sheet
    def get_late_exact(self, period, type, cnt, contract):
        self.ensure_one()
        res = period
        flag = False
        average = 1
        if self:
            if self.late_rule_id:
                time_ids = self.late_rule_id.line_ids.filtered(lambda r: r.time == type)
                for line in time_ids:
                    flag = True
                    if line.type == 'rate':
                        if cnt == 1:
                            res = line.rate * period * line.first
                        if cnt == 2:
                            res = line.rate * period * line.second
                        if cnt == 3:
                            res = line.rate * period * line.third
                        if cnt == 4:
                            res = line.rate * period * line.fourth
                        if cnt >= 5:
                            res = line.rate * period * line.fifth
                    elif line.type == 'daily':
                        # if contract.resource_calendar_id.two_shift_per_day:
                        #     average = 2
                        if cnt == 1:
                            res = contract.resource_calendar_id.hours_per_day * line.first
                        if cnt == 2:
                            res = contract.resource_calendar_id.hours_per_day * line.second
                        if cnt == 3:
                            res = contract.resource_calendar_id.hours_per_day * line.third
                        if cnt == 4:
                            res = contract.resource_calendar_id.hours_per_day * line.fourth
                        if cnt >= 5:
                            res = contract.resource_calendar_id.hours_per_day * line.fifth
                    elif line.type == 'fix':
                        res = line.amount
                    break
                if not flag:
                    res = 0
        return res

    def get_finger(self, cnt, status, contract):
        self.ensure_one()
        res = 0
        if self:
            if self.missing_rule_id:
                if status == 'fixin':
                    if len(self.missing_rule_id.missing_in_ids) > 0:
                        time_ids = self.missing_rule_id.missing_in_ids[0]
                    for line in time_ids:
                        if cnt == 1:
                            res = contract.resource_calendar_id.hours_per_day * line.first
                        if cnt == 2:
                            res = contract.resource_calendar_id.hours_per_day * line.second
                        if cnt == 3:
                            res = contract.resource_calendar_id.hours_per_day * line.third
                        if cnt == 4:
                            res = contract.resource_calendar_id.hours_per_day * line.fourth
                        if cnt >= 5:
                            res = contract.resource_calendar_id.hours_per_day * line.fifth
                if status == 'fixout':
                    if len(self.missing_rule_id.missing_out_ids) > 0:
                        time_ids = self.missing_rule_id.missing_out_ids[0]
                    for line in time_ids:
                        if cnt == 1:
                            res = contract.resource_calendar_id.hours_per_day * line.first
                        if cnt == 2:
                            res = contract.resource_calendar_id.hours_per_day * line.second
                        if cnt == 3:
                            res = contract.resource_calendar_id.hours_per_day * line.third
                        if cnt == 4:
                            res = contract.resource_calendar_id.hours_per_day * line.fourth
                        if cnt >= 5:
                            res = contract.resource_calendar_id.hours_per_day * line.fifth
        return res

    #  ***************** Diff Rules *****************

    def get_diff_times(self):
        if self:
            if self.diff_rule_id:
                time_ids = self.diff_rule_id.line_ids.mapped('time')
                return time_ids

    def get_diff_type(self, period):
        self.ensure_one()
        res = period
        flag = False
        if self:
            if self.diff_rule_id:
                time_ids = self.diff_rule_id.line_ids.sorted(key=lambda r: r.time, reverse=True)
                for line in time_ids:
                    if period >= line.time:
                        flag = True
                        res = line.time
                        break
                if not flag:
                    res = 0
        return res

    def get_diff_exact(self, period, type, cnt, contract):
        self.ensure_one()
        res = period
        flag = False
        average = 1
        if self:
            if self.diff_rule_id:
                time_ids = self.diff_rule_id.line_ids.filtered(lambda r: r.time == type)
                for line in time_ids:
                    flag = True
                    if line.type == 'rate':
                        if cnt == 1:
                            res = line.rate * period * line.first
                        if cnt == 2:
                            res = line.rate * period * line.second
                        if cnt == 3:
                            res = line.rate * period * line.third
                        if cnt == 4:
                            res = line.rate * period * line.fourth
                        if cnt >= 5:
                            res = line.rate * period * line.fifth
                    elif line.type == 'daily':
                        if contract.resource_calendar_id.two_shift_per_day:
                            average = 2
                        if cnt == 1:
                            res = contract.resource_calendar_id.hours_per_day * line.first
                        if cnt == 2:
                            res = contract.resource_calendar_id.hours_per_day * line.second
                        if cnt == 3:
                            res = contract.resource_calendar_id.hours_per_day * line.third
                        if cnt == 4:
                            res = contract.resource_calendar_id.hours_per_day * line.fourth
                        if cnt >= 5:
                            res = contract.resource_calendar_id.hours_per_day * line.fifth
                    elif line.type == 'fix':
                        res = line.amount
                    break
                if not flag:
                    res = 0
        return res

    # def get_diff(self, period, cnt, contract):
    #     self.ensure_one()
    #     res = period
    #     flag = False
    #     count = 0
    #     if self:
    #         if self.diff_rule_id:
    #             time_ids = self.diff_rule_id.line_ids.sorted(
    #                 key=lambda r: r.time, reverse=True)
    #             for line in time_ids:
    #                 if period >= line.time:
    #                     flag = True
    #                     if line.type == 'rate':
    #                         if cnt == 1:
    #                             res = line.rate * period * line.first
    #                         if cnt == 2:
    #                             res = line.rate * period * line.second
    #                         if cnt == 3:
    #                             res = line.rate * period * line.third
    #                         if cnt == 4:
    #                             res = line.rate * period * line.fourth
    #                         if cnt >= 5:
    #                             res = line.rate * period * line.fifth
    #                     elif line.type == 'daily':
    #                         if cnt == 1:
    #                             res = contract.resource_calendar_id.hours_per_day * line.first
    #                         if cnt == 2:
    #                             res = contract.resource_calendar_id.hours_per_day * line.second
    #                         if cnt == 3:
    #                             res = contract.resource_calendar_id.hours_per_day * line.third
    #                         if cnt == 4:
    #                             res = contract.resource_calendar_id.hours_per_day * line.fourth
    #                         if cnt >= 5:
    #                             res = contract.resource_calendar_id.hours_per_day * line.fifth
    #                     elif line.type == 'fix':
    #                         res = line.amount
    # 
    #                     break
    # 
    #             if not flag:
    #                 res = 0
    #     return res

    # ***************** Absence Rules *****************

    # def get_absence_times(self):
    #     if self:
    #         if self.absence_rule_id:
    #             time_ids = self.absence_rule_id.line_ids.mapped('time')
    #             print(time_ids,'<<<<<<<<<<<<<<<<<<<<<')
    #             return time_ids

    def get_absence_type(self):
        self.ensure_one()
        res = 0
        if self:
            if self.absence_rule_id and self.absence_rule_id.line_ids:
                line = self.absence_rule_id.line_ids[0]
                res = line.type
        return res

    def get_absence_exact(self, period, type, cnt, contract):
        self.ensure_one()
        res = period
        average = 1
        if self:
            if self.absence_rule_id and self.absence_rule_id.line_ids:
                line = self.absence_rule_id.line_ids[0]
                if type == 'rate':
                    if cnt == 1:
                        res = line.rate * period * line.first
                    if cnt == 2:
                        res = line.rate * period * line.second
                    if cnt == 3:
                        res = line.rate * period * line.third
                    if cnt == 4:
                        res = line.rate * period * line.fourth
                    if cnt >= 5:
                        res = line.rate * period * line.fifth
                elif type == 'daily':
                    if contract.resource_calendar_id.two_shift_per_day:
                        average = 2
                    if cnt == 1:
                        res = contract.resource_calendar_id.hours_per_day * line.first / average
                    if cnt == 2:
                        res = contract.resource_calendar_id.hours_per_day * line.second / average
                    if cnt == 3:
                        res = contract.resource_calendar_id.hours_per_day * line.third / average
                    if cnt == 4:
                        res = contract.resource_calendar_id.hours_per_day * line.fourth / average
                    if cnt >= 5:
                        res = contract.resource_calendar_id.hours_per_day * line.fifth / average
                elif type == 'fix':
                    res = line.amount
        return res

    # def get_absence(self, period, cnt, contract):
    #     res = period
    #     flag = False
    #     average = 1
    #     if self:
    #         if self.absence_rule_id:
    #             time_ids = self.absence_rule_id.line_ids.sorted(key=lambda r: r.time, reverse=True)
    #             for line in time_ids:
    #                 if period >= line.time:
    #                     flag = True
    #                     if line.type == 'rate':
    #                         if cnt == 1:
    #                             res = line.rate * period * line.first
    #                         if cnt == 2:
    #                             res = line.rate * period * line.second
    #                         if cnt == 3:
    #                             res = line.rate * period * line.third
    #                         if cnt == 4:
    #                             res = line.rate * period * line.fourth
    #                         if cnt >= 5:
    #                             res = line.rate * period * line.fifth
    #                     elif line.type == 'daily':
    #                         if contract.resource_calendar_id.two_shift_per_day:
    #                             average = 2
    #                         if cnt == 1:
    #                             res = contract.resource_calendar_id.hours_per_day * line.first / average
    #                         if cnt == 2:
    #                             res = contract.resource_calendar_id.hours_per_day * line.second / average
    #                         if cnt == 3:
    #                             res = contract.resource_calendar_id.hours_per_day * line.third / average
    #                         if cnt == 4:
    #                             res = contract.resource_calendar_id.hours_per_day * line.fourth / average
    #                         if cnt >= 5:
    #                             res = contract.resource_calendar_id.hours_per_day * line.fifth / average
    #                     elif line.type == 'fix':
    #                         res = line.amount
    #                     break
    #             if not flag:
    #                 res = 0
    #         return res

class HrMissingFingerRule(models.Model):
    _name = 'hr.missing.finger.rule'
    _description = 'Missing Finger Print Rules'

    name = fields.Char(string='name', required=True)

    missing_in_ids = fields.One2many(
        comodel_name='hr.missing.finger.line',
        inverse_name='missing_in_id',
        string='Missing in lines',
        required=False)

    missing_out_ids = fields.One2many(
        comodel_name='hr.missing.finger.line',
        inverse_name='missing_out_id',
        string='Missing out lines',
        required=False)


class HrMissingFingerLine(models.Model):
    _name = 'hr.missing.finger.line'
    _description = 'Missing Finger Print Rules'
    type = [
        ('daily', 'Daily'),
    ]

    missing_in_id = fields.Many2one(comodel_name='hr.missing.finger.rule', string='Missing in Rule')
    missing_out_id = fields.Many2one(comodel_name='hr.missing.finger.rule', string='Missing in Rule')
    type = fields.Selection(string="Type", selection=type, required=True, )
    amount = fields.Float('Amount')
    first = fields.Float('First Time', default=1)
    second = fields.Float('Second Time', default=1)
    third = fields.Float('Third Time', default=1)
    fourth = fields.Float('Fourth Time', default=1)
    fifth = fields.Float('Fifth Time', default=1)

class HrPolicy_overtimeLine(models.Model):
    _name = 'hr.policy.overtime.line'
    _description = 'Overtime Policy Lines'
    type = [
        ('weekend', 'Week End'),
        ('workday', 'Working Day'),
        ('ph', 'Public Holiday')

    ]
    overtime_rule_id = fields.Many2one(comodel_name='hr.overtime.rule',
                                       string='Name', required=True)
    type = fields.Selection(selection=type, string="Type", default='workday')
    active_after = fields.Float(string="Apply after",
                                help="After this time the overtime will be calculated")
    rate = fields.Float(string='Rate')
    attendance_policy_id = fields.Many2one(comodel_name='hr.attendance.policy')

    @api.onchange('overtime_rule_id')
    def onchange_ov_id(self):
        for line in self:
            line.type = line.overtime_rule_id.type
            line.active_after = line.overtime_rule_id.active_after
            line.rate = line.overtime_rule_id.rate


class HrOvertimeRule(models.Model):
    _name = 'hr.overtime.rule'
    _description = 'Over time Rules'
    type = [
        ('weekend', 'Week End'),
        ('workday', 'Working Day'),
        ('ph', 'Public Holiday')

    ]

    day_period = fields.Selection(
        string='Day Period', required=False,
        selection=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night')], )
    name = fields.Char(string="Name")
    type = fields.Selection(selection=type, string="Type", default='workday')
    active_after = fields.Float(string="Apply after",
                                help="After this time the overtime will be calculated")
    rate = fields.Float(string='Rate 1')
    apply_from = fields.Float(
        string='Apply from',
        required=False)
    apply_to = fields.Float(
        string='Apply to',
        required=False)
    rate_2 = fields.Float(string='Rate 2')
    apply_from_2 = fields.Float(
        string='Apply from',
        required=False)
    apply_to_2 = fields.Float(
        string='Apply to',
        required=False)


class HrLateRule(models.Model):
    _name = 'hr.late.rule'
    _description = 'Late In Rules'

    name = fields.Char(string='name', required=True)
    line_ids = fields.One2many(comodel_name='hr.late.rule.line',
                               inverse_name='late_id', string='Late In Periods')


class HrLateRuleLine(models.Model):
    _name = 'hr.late.rule.line'
    _description = 'Late In Rule Lines'
    type = [
        ('fix', 'Fixed'),
        ('rate', 'Rate'),
        ('daily', 'Daily'),
    ]

    late_id = fields.Many2one(comodel_name='hr.late.rule', string='Late Rule')
    type = fields.Selection(string="Type", selection=type, required=True, )
    rate = fields.Float(string='Rate')
    time = fields.Float('Time')
    amount = fields.Float('Amount')
    first = fields.Float('First Time', default=1)
    second = fields.Float('Second Time', default=1)
    third = fields.Float('Third Time', default=1)
    fourth = fields.Float('Fourth Time', default=1)
    fifth = fields.Float('Fifth Time', default=1)


class HrDiffRule(models.Model):
    _name = 'hr.diff.rule'
    _description = 'Diff Time Rule'

    name = fields.Char(string='name', required=True)
    line_ids = fields.One2many(comodel_name='hr.diff.rule.line',
                               inverse_name='diff_id',
                               string='Difference time Periods')


class HrDiffRuleLine(models.Model):
    _name = 'hr.diff.rule.line'
    _description = 'Diff Time Rule Line'

    type = [
        ('fix', 'Fixed'),
        ('rate', 'Rate'),
        ('daily', 'Daily'),
    ]
    diff_id = fields.Many2one(comodel_name='hr.diff.rule', string='Diff Rule')
    type = fields.Selection(string="Type", selection=type, required=True, )
    rate = fields.Float(string='Rate')
    time = fields.Float('Time')
    amount = fields.Float('Amount')
    first = fields.Float('First Time', default=1)
    second = fields.Float('Second Time', default=1)
    third = fields.Float('Third Time', default=1)
    fourth = fields.Float('Fourth Time', default=1)
    fifth = fields.Float('Fifth Time', default=1)


class HrAbsenceRule(models.Model):
    _name = 'hr.absence.rule'
    _description = 'Absence Rules'

    name = fields.Char(string='name', required=True)
    line_ids = fields.One2many(comodel_name='hr.absence.rule.line',
                               inverse_name='absence_id',
                               string='Late In Periods')

    @api.constrains('line_ids')
    def check_is_one_line(self):
        for rec in self:
            if len(rec.line_ids) > 1:
                raise ValidationError(_("you can't add more than 1 absence line !"))

class HrAbsenceRuleLine(models.Model):
    _name = 'hr.absence.rule.line'
    _description = 'Absence Rule Lines'
    times = [
        ('1', 'First Time'),
        ('2', 'Second Time'),
        ('3', 'Third Time'),
        ('4', 'Fourth Time'),
        ('5', 'Fifth Time'),
    ]
    type = [
        ('fix', 'Fixed'),
        ('rate', 'Rate'),
        ('daily', 'Daily'),
    ]
    time = fields.Float('Time') #this field should be deleted
    type = fields.Selection(string="Type", selection=type, required=True, )
    rate = fields.Float(string='Rate', )
    amount = fields.Float('Amount')
    first = fields.Float('First Time', default=1)
    second = fields.Float('Second Time', default=1)
    third = fields.Float('Third Time', default=1)
    fourth = fields.Float('Fourth Time', default=1)
    fifth = fields.Float('Fifth Time', default=1)
    absence_id = fields.Many2one(comodel_name='hr.absence.rule', string='name')
    counter = fields.Selection(string="Times", selection=times, )
