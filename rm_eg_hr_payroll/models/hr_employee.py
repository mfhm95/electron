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


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # religion = fields.Selection(
    #     [('mus', 'Muslem'), ('chris', 'Christian'), ('other', 'Others')],
    #     string="Religion")
    # military_status = fields.Selection(
    #     [('not_req', 'Not Required'), ('post', 'Postponed'),
    #      ('complete', 'complete'), ('exemption', 'Exemption'),
    #      ('current', 'Currently serving ')], string="Military Status")
    age = fields.Integer(string="Age", compute="_calculate_age", readonly=True)
    # start_date = fields.Date(string="Start Working At")
    # edu_major = fields.Char(string="major")
    # edu_grad = fields.Selection(
    #     [('ex', 'Excellent'), ('vgod', 'Very Good'), ('god', 'Good'),
    #      ('pas', 'Pass')],
    #     string="Grad")
    # edu_note = fields.Text("Education Notes")
    # experience_y = fields.Integer(compute="_calculate_experience",
    #                               string="Experience",
    #                               help="experience in our company", store=True)
    # experience_m = fields.Integer(compute="_calculate_experience",
    #                               string="Experience monthes", store=True)
    # experience_d = fields.Integer(compute="_calculate_experience",
    #                               string="Experience dayes", store=True)

    @api.depends("birthday")
    def _calculate_age(self):
        for emp in self:
            if emp.birthday:
                dob = emp.birthday
                emp.age = int((datetime.today().date() - dob).days / 365)
            else:
                emp.age = 0

    # @api.depends("start_date")
    # def _calculate_experience(self):
    #     for emp in self.search([]):
    #         if emp.start_date:
    #             date_format = '%Y-%m-%d'
    #             current_date = (datetime.today()).strftime(date_format)
    #             d1 = emp.start_date
    #             d2 = datetime.strptime(current_date, date_format).date()
    #             r = relativedelta(d2, d1)
    #             emp.experience_y = r.years
    #             emp.experience_m = r.months
    #             emp.experience_d = r.days
    #         else:
    #             emp.experience_y = 0
    #             emp.experience_m = 0
    #             emp.experience_d = 0

    @api.model
    def _cron_employee_age(self):
        self._calculate_age()

    # @api.model
    # def _cron_employee_exp(self):
    #     self._calculate_experience()
