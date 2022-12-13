# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TOTD(models.Model):
    _name = "totd.totd"
    _description = "TOTD Model"

    week_num = fields.Integer(string="Week")
    assignee_monday = fields.Many2one(comodel_name='totd_management.people', string="Monday")
    assignee_tuesday = fields.Many2one(comodel_name='totd_management.people', string="Tuesday")
    assignee_wednesday = fields.Many2one(comodel_name='totd_management.people', string="Wednesday")
    assignee_thursday = fields.Many2one(comodel_name='totd_management.people', string="Thursday")
    assignee_friday = fields.Many2one(comodel_name='totd_management.people', string="Friday")
    
    @api.depends('assignee_monday')
    def _onchange_monday(self):
        pass
    
    @api.model
    def _cron_test(self):
        pass


class People(models.Model):
    _name = "totd.people"
    _description = "ToTD Person"
    name = fields.Char(string="Name")
    backup = fields.Boolean(default=False)