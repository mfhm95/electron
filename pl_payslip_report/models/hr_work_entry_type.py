from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = "hr.work.entry.type"
    printed = fields.Boolean('Printed')
