from odoo import fields, models, api


class PlanningSlot(models.Model):
    _name = 'planning.slot'
    _inherit = ['planning.slot','mail.thread', 'mail.activity.mixin']
    # _inherits = {'portal.mixin', 'mail.thread', 'mail.activity.mixin', 'sequence.mixin'}
    # _inherits = {'mail.message': 'message_ids'}

    day_period = fields.Selection(
        string='Day Period',required=False,
        selection=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night')], )
    
    import_helper = fields.Boolean(
        string='Import_helper',compute='get_partner_id',
        required=False)
    
    pin = fields.Char(
        string='Pin', track_visibility='always',
        required=False)
    start_datetime = fields.Datetime(track_visibility='always')
    end_datetime = fields.Datetime(track_visibility='always')
    role_id = fields.Many2one(track_visibility='always')
    allocated_hours = fields.Float(track_visibility='always')
    allocated_percentage = fields.Float(track_visibility='always')
    repeat = fields.Boolean(track_visibility='always')
    repeat_interval = fields.Integer(track_visibility='always')
    repeat_type = fields.Selection(track_visibility='always')
    repeat_until = fields.Date(track_visibility='always')

    @api.onchange('employee_id')
    def _onchange_employee_id_pin(self):
        for rec in self:
            if rec.employee_id and not rec.pin:
                rec.pin = rec.employee_id.pin
        pass

    @api.depends('pin')
    def get_partner_id(self):
        for rec in self:
            if rec.pin:
                rec.import_helper = True
                rec.employee_id = self.env['hr.employee'].search([('pin','=',rec.pin)],limit=1)
            else:
                rec.import_helper = False
