# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_loan_amount(self,employee_id,date_from,date_to):
        loanObj = self.env['hr.loan'].search([('employee_id', '=', employee_id), ('state', '=', 'approve')])
        if loanObj:
            total_loan_amount = 0
            for loan in loanObj:
                for loan_line in loan.loan_lines:
                    if date_from <= loan_line.date <= date_to and not loan_line.paid:
                        total_loan_amount -= loan_line.amount
            return total_loan_amount
        else:
            return 0
    def get_loan_lines(self,employee_id,date_from,date_to):
        loanObj = self.env['hr.loan'].search([('employee_id', '=', employee_id), ('state', '=', 'approve')])
        loan_lines = self.env['hr.loan.line']
        if loanObj:
            for loan in loanObj:
                for loan_line in loan.loan_lines:
                    if date_from <= loan_line.date <= date_to and not loan_line.paid:
                        loan_lines |= loan_line
            return loan_lines
        else:
            return False



    #
    # @api.onchange('employee_id', 'date_from', 'date_to')
    # def onchange_employee(self):
    #     if (not self.employee_id) or (not self.date_from) or (not self.date_to):
    #         return
    #
    #     employee = self.employee_id
    #     date_from = self.date_from
    #     date_to = self.date_to
    #     contract_ids = []
    #
    #     ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
    #     locale = self.env.context.get('lang') or 'en_US'
    #     self.name = _('Salary Slip of %s for %s') % (
    #         employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
    #     self.company_id = employee.company_id
    #
    #     if not self.contract_id or self.employee_id != self.contract_id.employee_id:  # Add a default contract if not already defined
    #         contracts = employee._get_contracts(date_from, date_to)
    #
    #         if not contracts or not contracts[0].structure_type_id.default_struct_id:
    #             self.contract_id = False
    #             self.struct_id = False
    #             return
    #         self.contract_id = contracts[0]
    #         self.struct_id = contracts[0].structure_type_id.default_struct_id
    #
    #     # computation of the salary input
    #     contracts = self.env['hr.contract'].browse(contract_ids)
    #     worked_days_line_ids = self._get_worked_day_lines()
    #     worked_days_lines = self.worked_days_line_ids.browse([])
    #     for r in worked_days_line_ids:
    #         worked_days_lines += worked_days_lines.new(r)
    #     self._get_workday_lines = worked_days_lines
    #     if contracts:
    #         input_line_ids = self._get_input_type(contracts, date_from, date_to)
    #         input_lines = self.input_line_ids.browse([])
    #         for r in input_line_ids:
    #             input_lines += input_lines.new(r)
    #         self.input_line_ids = input_lines
    #     return

    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('state', '=', 'approve')])
        for loan in lon_obj:
            for loan_line in loan.loan_lines:
                if date_from <= loan_line.date <= date_to and not loan_line.paid:
                    for result in res:
                        if result.get('code') == 'LO':
                            result['amount'] = loan_line.amount
                            result['loan_line_id'] = loan_line.id
        return res

    def action_payslip_done(self):
        for line in self.line_ids:
            if line.code == 'LOAN':
                loan_lines = line.slip_id.get_loan_lines(self.employee_id.id, self.date_from, self.date_to)
                if loan_lines:
                    for loan_line in loan_lines:
                            loan_line.paid = True
                            loan_line.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()
