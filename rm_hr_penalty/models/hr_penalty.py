from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HrPenaltyReason(models.Model):
    _name = 'hr.penalty.reason'

    name = fields.Char(string="Penalty Reason name", required=True)
    line_ids = fields.One2many(comodel_name='hr.penalty.reason.line',
                               inverse_name='reason_id',
                               string='Hr Penalty Reason Line')
    amount = fields.Float('Penalty Amount', required=True)
    type = fields.Selection(string="Penalty Type",
                            selection=[('day', 'Days'), ('amount', 'Amount'), ],
                            required=True, )
    no_days = fields.Float(string='No Of Days', )


class hr_absence_rule_line(models.Model):
    _name = 'hr.penalty.reason.line'

    times = [
        ('1', 'First Time'),
        ('2', 'Second Time'),
        ('3', 'Third Time'),
        ('4', 'Fourth Time'),
        ('5', 'Fifth Time'),

    ]

    reason_id = fields.Many2one(comodel_name='hr.penalty.reason', string='name')
    rate = fields.Float(string='Rate', required=True)
    counter = fields.Selection(string="Times", selection=times, required=True, )

    _sql_constraints = [
        ('penalty_reason_cons', 'unique(reason_id,counter)',
         'The counter Must Be unique Per Rule'),
    ]


class HrPenalty(models.Model):
    _name = 'hr.penalty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hr Penalty"

    name = fields.Char(string="Penalty Name", default="/", readonly=True)
    user = fields.Many2one(comodel_name='res.users', string='Responsible',
                           default=lambda self: self.env.uid,
                           states={'approve': [('readonly', True)],
                                   'submit': [('readonly', True)]}, )
    date = fields.Date(string="Date", default=fields.Date.today(),
                       readonly=True)
    apply_date = fields.Date(string="Applied Date", default=fields.Date.today(),
                             readonly=True,
                             help='Date to apply penalty on payslip')
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  required=True)
    parent_id = fields.Many2one('hr.employee', related="employee_id.parent_id",
                                string="Manager")
    department_id = fields.Many2one('hr.department',
                                    related="employee_id.department_id",
                                    readonly=True,
                                    string="Department")
    job_id = fields.Many2one('hr.job', related="employee_id.job_id",
                             readonly=True, string="Job Position")
    type = fields.Selection(string="Penalty Type",
                            selection=[('day', 'Days'), ('amount', 'Amount'), ],
                            required=False, related='reason_id.type')
    no_days = fields.Float(string='No Of Days', related='reason_id.no_days')

    reason_id = fields.Many2one('hr.penalty.reason', 'Penalty Reason',
                                required=True)
    amount = fields.Float(string='Penalty Amount', related='reason_id.amount',
                          store=True, readonly=True)
    desc = fields.Text('Penalty Notes')
    refuse_reason = fields.Text('Refuse Reasons')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
    ], string="State", default='draft', track_visibility='onchange',
        copy=False, )

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.penalty.seq') or ' '
        res = super(HrPenalty, self).create(values)
        return res

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_approve(self):
        self.write({'state': 'approve'})
