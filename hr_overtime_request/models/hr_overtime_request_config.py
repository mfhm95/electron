from odoo import fields, models, api


class HrOvertimeRequestConfig(models.Model):
    _name = 'hr.overtime.request.config'
    _description = 'Overtime Request Config'
    _rec_name = 'name'

    name = fields.Char('Name', required=True)
    line_ids = fields.One2many('hr.overtime.request.config.line', 'config_id', string='Lines')



class HrOvertimeRequestConfigLine(models.Model):
    _name = 'hr.overtime.request.config.line'
    _rec_name = 'name'
    _order = 'sequence'

    sequence = fields.Integer(default=1)
    config_id = fields.Many2one('hr.overtime.request.config', 'Config')
    name = fields.Char('Stage Name', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', 'Approver')
    stage_type = fields.Selection([('submit', 'Submit'),
                                   ('middle', 'Middle Approve'),
                                   ('done', 'Final Approve'),
                                   ('refuse', 'Refuse')
                                   ], string='Stage Type')

    @api.depends('user_id', 'stage_type')
    def _compute_name(self):
        for line in self:
            if line.stage_type == 'submit':
                line.name = 'Submit'
            elif line.stage_type == 'refuse':
                line.name = 'Refused'
            else:
                line.name = '%s Approved' % line.user_id.name


    def _check_stage_approver(self):
        if self.user_id.id == self.env.user.id:
            return True
        else:
            return False

    def _check_has_refuse_permission(self):
        if self.env.user.id in self.config_id.line_ids.mapped('user_id').ids:
            return True
        else:
            return False

    def _next_approver(self):
        return self.config_id.line_ids.filtered(lambda l: l.sequence == self.sequence + 1).mapped('user_id')
