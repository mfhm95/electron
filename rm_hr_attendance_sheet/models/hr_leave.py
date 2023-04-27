from odoo import fields, models, api,_
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    type = fields.Selection(
        string='Type',
        selection=[('compensatory', 'Compensatory'),
                   ('annual', 'Annual'), ('casual', 'Casual'), ('sick', 'Sick'), ],
        required=False, )

class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    attend_sheet_id = fields.Many2one(
        comodel_name='attendance.sheet',
        string='Attendance sheet',
        required=False)

    # @api.model
    # def create(self, values):
    #     res = super(HrLeave, self).create(values)
    #     if res.holiday_status_id.type == 'compensatory':
    #         attendance_sheet = self.env['attendance.sheet'].search([('employee_id','=',res.employee_id.id),('state','=','draft')],limit=1)
    #         if attendance_sheet:
    #             attendance_sheet.get_attendances()
    #             attendance_sheet.create_time_off()
    #             # self.env.context['pass_comp'] = True
    #     return res

    # @api.onchange('employee_id','holiday_status_id')
    # def check_compensatory(self):
    #     if self.holiday_status_id.type == 'compensatory':
    #         # self.with_context(pass_comp=True)
    #         # self.env.context['pass_comp'] = True
    #         attendance_sheet = self.env['attendance.sheet'].search([('employee_id','=',self.employee_id.id),('state','=','draft')],limit=1)
    #         # print('1111')
    #         if attendance_sheet:
    #             # print('2222222')
    #             attendance_sheet.get_attendances()
    #             attendance_sheet.create_time_off()

    # @api.constrains('state', 'number_of_days', 'holiday_status_id')
    # def _check_holidays(self):
    #     mapped_days = self.mapped('holiday_status_id').get_employees_days(self.mapped('employee_id').ids)
    #     for holiday in self:
    #         if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
    #             continue
    #         leave_days = mapped_days[holiday.employee_id.id][holiday.holiday_status_id.id]
    #         if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
    #             print(self.env.context,'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< context')
    #             raise ValidationError(_('The number of remaining time off is not sufficient for this time off type.\n'
    #                                     'Please also check the time off waiting for validation.'))

