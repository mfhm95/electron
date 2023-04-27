from dateutil.relativedelta import relativedelta

from odoo.tools import date_utils

from odoo import fields, models, api, _
from odoo.tools.misc import format_date



class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    attendence_sheet_id = fields.Many2one(
        comodel_name='attendance.sheet',
        string='Attendence sheet',
        required=False)

    def get_attendance_sheet_worked_hours(self):
        if self.attendence_sheet_id:
            print('hiiiiiiiiiiii',self.attendence_sheet_id.tot_worked_hour)
            return self.attendence_sheet_id.tot_worked_hour
        else:
            return 0

    # @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    # def _onchange_employee(self):
    #     if (not self.employee_id) or (not self.date_from) or (not self.date_to):
    #         return
    #
    #     employee = self.employee_id
    #     date_from = self.date_from
    #     date_to = self.date_to
    #
    #     self.company_id = employee.company_id
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
    #     lang = employee.sudo().address_home_id.lang or self.env.user.lang
    #     context = {'lang': lang}
    #     payslip_name = self.struct_id.payslip_name or _('Salary Slip')
    #     del context
    #
    #     self.name = '%s - %s - %s' % (
    #         payslip_name,
    #         self.employee_id.name or '',
    #         format_date(self.env, self.date_from, date_format="MMMM y", lang_code=lang)
    #     )
    #
    #     if date_to > date_utils.end_of(fields.Date.today(), 'month'):
    #         self.warning_message = _(
    #             "This payslip can be erroneous! Work entries may not be generated for the period from %(start)s to %(end)s.",
    #             start=date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1),
    #             end=date_to,
    #         )
    #     else:
    #         self.warning_message = False
    #
    #     self.worked_days_line_ids = self._get_new_worked_days_lines()
    #
    # # def compute_sheet(self):
    # #     # Add code here
    # #     return super(HrPayslip, self).compute_sheet()
    # # @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    # # def _onchange_employee(self):
    # #     res = super()._onchange_employee()
    # #     struct_commission = self.env.ref(
    # #         'l10n_be_hr_payroll_variable_revenue.hr_payroll_structure_cp200_structure_commission')
    # #     if self.struct_id == struct_commission:
    # #         months = relativedelta(date_utils.add(self.date_to, days=1), self.date_from).months
    # #         if self.employee_id.id in self.env.context.get('commission_real_values', {}):
    # #             commission_value = self.env.context['commission_real_values'][self.employee_id.id]
    # #         else:
    # #             commission_value = self.contract_id.commission_on_target * months
    # #         commission_type = self.env.ref('l10n_be_hr_payroll_variable_revenue.cp200_other_input_commission')
    # #         lines_to_remove = self.input_line_ids.filtered(lambda x: x.input_type_id == commission_type)
    # #         to_remove_vals = [(3, line.id, False) for line in lines_to_remove]
    # #         to_add_vals = [(0, 0, {
    # #             'amount': commission_value,
    # #             'input_type_id': self.env.ref('l10n_be_hr_payroll_variable_revenue.cp200_other_input_commission').id,
    # #         })]
    # #         input_line_vals = to_remove_vals + to_add_vals
    # #         self.update({'input_line_ids': input_line_vals})
    # #     return res
    # # @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    # # def _onchange_employee(self):
    # #     res = super()._onchange_employee()
    # #     attachment_types = {
    # #         'attachment_salary': self.env.ref('l10n_be_hr_payroll.cp200_other_input_attachment_salary').id,
    # #         'assignment_salary': self.env.ref('l10n_be_hr_payroll.cp200_other_input_assignment_salary').id,
    # #         'child_support': self.env.ref('l10n_be_hr_payroll.cp200_other_input_child_support').id,
    # #     }
    # #     struct_warrant = self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_structure_warrant')
    # #     if self.struct_id == struct_warrant:
    # #         if self.employee_id.id in self.env.context.get('commission_real_values', {}):
    # #             warrant_value = self.env.context['commission_real_values'][self.employee_id.id]
    # #         else:
    # #             warrant_value = self.contract_id.commission_on_target * months
    # #         months = relativedelta(date_utils.add(self.date_to, days=1), self.date_from).months
    # #         warrant_type = self.env.ref('l10n_be_hr_payroll.cp200_other_input_warrant')
    # #         lines_to_remove = self.input_line_ids.filtered(lambda x: x.input_type_id == warrant_type)
    # #         to_remove_vals = [(3, line.id, False) for line in lines_to_remove]
    # #         to_add_vals = [(0, 0, {
    # #             'amount': warrant_value,
    # #             'input_type_id': self.env.ref('l10n_be_hr_payroll.cp200_other_input_warrant')
    # #         })]
    # #         input_line_vals = to_remove_vals + to_add_vals
    # #         self.update({'input_line_ids': input_line_vals})
    # #     if not self.contract_id:
    # #         lines_to_remove = self.input_line_ids.filtered(lambda x: x.input_type_id.id in attachment_types.values())
    # #         self.update({'input_line_ids': [(3, line.id, False) for line in lines_to_remove]})
    # #     if self.has_attachment_salary:
    # #         lines_to_keep = self.input_line_ids.filtered(lambda x: x.input_type_id.id not in attachment_types.values())
    # #         input_line_vals = [(5, 0, 0)] + [(4, line.id, False) for line in lines_to_keep]
    # #
    # #         valid_attachments = self.contract_id.attachment_salary_ids.filtered(
    # #             lambda a: a.date_from <= self.date_to and a.date_to >= self.date_from)
    # #
    # #         for garnished_type in list(set(valid_attachments.mapped('garnished_type'))):
    # #             amount = sum(valid_attachments.filtered(lambda a: a.garnished_type == garnished_type).mapped('amount'))
    # #             input_type_id = attachment_types[garnished_type]
    # #             input_line_vals.append((0, 0, {
    # #                 'amount': amount,
    # #                 'input_type_id': input_type_id,
    # #             }))
    # #         self.update({'input_line_ids': input_line_vals})
    # #     return res
    # @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    # def _onchange_employee(self):
    #     res = super()._onchange_employee()
    #     struct_commission = self.env.ref(
    #         'l10n_be_hr_payroll_variable_revenue.hr_payroll_structure_cp200_structure_commission')
    #     if self.struct_id == struct_commission:
    #         months = relativedelta(date_utils.add(self.date_to, days=1), self.date_from).months
    #         if self.employee_id.id in self.env.context.get('commission_real_values', {}):
    #             commission_value = self.env.context['commission_real_values'][self.employee_id.id]
    #         else:
    #             commission_value = self.contract_id.commission_on_target * months
    #         commission_type = self.env.ref('l10n_be_hr_payroll_variable_revenue.cp200_other_input_commission')
    #         lines_to_remove = self.input_line_ids.filtered(lambda x: x.input_type_id == commission_type)
    #         to_remove_vals = [(3, line.id, False) for line in lines_to_remove]
    #         to_add_vals = [(0, 0, {
    #             'amount': commission_value,
    #             'input_type_id': self.env.ref('l10n_be_hr_payroll_variable_revenue.cp200_other_input_commission').id,
    #         })]
    #         input_line_vals = to_remove_vals + to_add_vals
    #         self.update({'input_line_ids': input_line_vals})
    #     return res
    #
    # def compute_sheet(self):
    #     for payslip in self.filtered(lambda slip: slip.state not in ['cancel', 'done']):
    #         number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
    #         # delete old payslip lines
    #         payslip.line_ids.unlink()
    #         sheets = self.env['attendance.sheet'].search([('employee_id.id', '=', payslip.employee_id.id),
    #                                                       ('date_from', '>=', payslip.date_from),
    #                                                       ('date_from', '<=', payslip.date_to)],
    #                                                      order="date_from")
    #         if sheets:
    #             worked_day_lines = sheets[-1]._get_workday_lines()
    #             payslip.worked_days_line_ids = [(0, 0, x) for x in
    #                                             worked_day_lines]
    #         lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
    #         payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
    #     return True

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        res = super(HrPayslip, self)._prepare_line_values(line, account_id, date, debit, credit)
        # for val in res:
        #     print(val,'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        res.update({'analytic_account_id': line.slip_id.contract_id.analytic_account_id.id,
                    'analytic_tag_ids': line.slip_id.contract_id.analytic_tag_ids.ids,
                    })
        return res






















































