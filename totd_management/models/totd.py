# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TOTD(models.Model):
    _name = "totd.totd"
    _description = "TOTD Model"

    week_num = fields.Integer(string="Week")
    assignee_monday = fields.Many2one(comodel_name='totd.people', string="Monday")
    assignee_tuesday = fields.Many2one(comodel_name='totd.people', string="Tuesday")
    assignee_wednesday = fields.Many2one(comodel_name='totd.people', string="Wednesday")
    assignee_thursday = fields.Many2one(comodel_name='totd.people', tring="Thursday")
    assignee_friday = fields.Many2one(comodel_name='totd.people', string="Friday")


class People(models.Model):
    _name = 'totd.people'
    name = fields.Char(string="name")
    backup = fields.Boolean(default=False)