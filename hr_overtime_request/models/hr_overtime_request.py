# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2019-TODAY .
#    Author: Plementus <https://plementus.com>
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class HrOvertimeRequest(models.Model):
    _name = 'hr.overtime.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Overtime Request'
    _rec_name = 'name'

    name = fields.Char('Reference', required=True, default=_('New'))

    config_id = fields.Many2one('hr.overtime.request.config', 'Type', required=True, tracking=True)
    stage_id = fields.Many2one('hr.overtime.request.config.line', 'Stages', tracking=True,
                               domain="[('config_id', '=', config_id)]")
    employee_ids = fields.Many2many('hr.employee', string='Employee', required=True, tracking=True)
    date_from = fields.Datetime('Date from', required=True, tracking=True)
    date_to = fields.Datetime('Date from', required=True, tracking=True)
    submitted_by = fields.Many2one(
        comodel_name='res.users',
        string='Submitted By',
        required=False)
    note = fields.Text('Notes', required=True, tracking=True)

    state = fields.Selection([('new', 'New'),
                              ('awaiting', 'Awaiting Approvals'),
                              ('approved', 'Approved'),
                              ('refused', 'Refused')
                              ], string='State', compute='_compute_state', store=True, tracking=True)

    overtime = fields.Float('Overtime', compute='_compute_overtime', tracking=True)

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('hr.overtime.request')
        return super(HrOvertimeRequest, self).create(values)

    @api.depends('stage_id')
    def _compute_state(self):
        for request in self:
            sequences = request.stage_id.config_id.line_ids.mapped('sequence')
            if not request.stage_id.stage_type or request.stage_id.stage_type == 'submit':
                request.state = 'new'
                request.submitted_by = self.env.user.id
                if self.stage_id.stage_type == 'submit':
                    if len(sequences) > 1 and self.stage_id.sequence + 1 in sequences:
                        next_user = self.stage_id.config_id.line_ids.filtered(
                            lambda l: l.sequence == self.stage_id.sequence + 1).user_id
                        summary = _("OverTime Request Submitted")
                        note = _("%s has been Submitted this request and waiting your approval") % self.env.user.name,
                        self.notify(request, next_user, summary, note)


            elif request.stage_id.stage_type == 'refuse':
                request.state = 'refused'
                if len(sequences) > 1:
                    next_user = self.submitted_by
                    summary = _("OverTime Request Refused")
                    note = _("Your request has been refused by %s") % self.env.user.name,
                    self.notify(request, next_user, summary, note)

            elif request.stage_id.stage_type == 'done':
                request.state = 'approved'
                if len(sequences) > 1:
                    next_user = self.submitted_by
                    summary = _("OverTime Request Done")
                    note = _("Your request has been Done by %s") % self.env.user.name,
                    self.notify(request, next_user, summary, note)

            else:
                request.state = 'awaiting'
                if request.stage_id.config_id.line_ids.filtered(lambda l: l.sequence == request.stage_id.sequence + 1).stage_type == 'middle':
                    next_user = self.stage_id.config_id.line_ids.filtered(
                            lambda l: l.sequence == self.stage_id.sequence + 1).user_id
                    summary = _("OverTime Request Approval")
                    note = _("Overtime request has been Approve by %s and waitting next approval") % self.env.user.name,
                    self.notify(request, next_user, summary, note)
                elif request.stage_id.config_id.line_ids.filtered(lambda l: l.sequence == request.stage_id.sequence + 1).stage_type == 'done':
                    next_user = self.stage_id.config_id.line_ids.filtered(
                            lambda l: l.sequence == self.stage_id.sequence + 1).user_id
                    summary = _("OverTime Request Approval")
                    note = _("Overtime request has been Approve by %s and waitting final approval") % self.env.user.name,
                    self.notify(request, next_user, summary, note)


    def notify(self,reord,user,summary,note):
        data = {
            'res_model_id': self.env['ir.model'].search(
                [('model', '=', 'hr.overtime.request')]).id,
            'res_id': reord.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': summary,
            'note': note,
            'date_deadline': fields.Datetime.now(),
            'user_id': user.id,
        }
        self.env['mail.activity'].create(data)

    # @api.onchange('stage_id')
    # def _stage_notification(self):
    #     self = self.sudo()
    #     if self.stage_id:
    #         sequences = self.stage_id.config_id.line_ids.mapped('sequence')
    #         if self.stage_id.stage_type == 'submit':
    #             if len(sequences) > 1 and self.stage_id.sequence + 1 in sequences:
    #                 next_user = self.stage_id.config_id.line_ids.filtered(
    #                     lambda l: l.sequence == self.stage_id.sequence + 1).user_id
    #                 summary = _("OverTime Request Submitted")
    #                 note = _("%s has been Submitted this request and waiting your approval") % self.env.user.name,
    #                 self.notify(self, next_user, summary, note)
    #         elif len(sequences) > 1 and self.stage_id.stage_type == 'refuse':
    #             print('re')
    #         elif len(sequences) > 1 and self.stage_id.stage_type == 'done':
    #             print('mm')
    #         else:
    #             print('mm')
    @api.onchange('stage_id')
    def _onchange_stage_ids(self):
        if self.stage_id:
            if not self.stage_id.stage_type in ['submit',
                                                'refuse'] and not self.stage_id.sequence - self._origin.stage_id.sequence <= 1:
                raise ValidationError(_('Unable to overcome approval not take action'))

            if self.stage_id.stage_type == 'refuse' and self._origin.stage_id._check_stage_approver() and not self.stage_id._check_has_refuse_permission():
                raise ValidationError(_('You are not authorized to refuse.'))

            if not self.stage_id.stage_type in ['submit', 'refuse'] and not self.stage_id._check_stage_approver():
                raise ValidationError(_('You are not authorized.'))

    @api.depends('date_from', 'date_to')
    def _compute_overtime(self):
        for request in self:
            diff = 0
            if request.date_from and request.date_to:
                diff_time = request.date_to - request.date_from
                diff = diff_time.total_seconds() / 3600
            request.overtime = diff

    def unlink(self):
        if self.state not in ['new', 'awaiting']:
            raise ValidationError(_('Unable to delete request not in "New, Awaiting Approvals"'))
        return super(HrOvertimeRequest, self).unlink()

    @api.constrains('employee_ids', 'date_from', 'date_to')
    def check_overlap(self):
        for rec in self:
            requests = self.env['hr.overtime.request'].search(
                [('stage_id.stage_type', '!=', 'refuse'), ('employee_ids', 'in', rec.employee_ids.ids),
                 ('id', '!=', rec.id)])
            for request in requests:
                if (request.date_from >= rec.date_from and request.date_from <= rec.date_to) or (
                        request.date_to <= rec.date_to and request.date_to >= rec.date_from):
                    raise ValidationError(_('Unable create overlap request.'))
