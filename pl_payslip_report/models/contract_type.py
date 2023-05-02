from odoo import fields, models, api


class HrContractType(models.Model):
    _inherit = "hr.contract.type"
    work_entry_type = fields.Many2many('hr.work.entry.type',string="Work Entry Type")