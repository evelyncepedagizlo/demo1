# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'


    calificaciones = fields.One2many('calificador.cliente', 'partner_id',track_visibility='onchange')
    calificacion = fields.Float( string="Calificacion",compute="calcular_calificacion",store=True)


    @api.depends('calificaciones')
    def calcular_calificacion(self,):
        for l in self:
            l.calificacion=sum(l.calificaciones.mapped('calificacion'))


class CalificadorCliente(models.Model):
    _name = 'calificador.cliente'
    _description = 'Calificacion de cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string="Cliente")
    motivo = fields.Char( string="Motivo")
    calificacion = fields.Float( string="Calificacion")















class CalificadorClienteParametros(models.Model):
    _name = 'calificador.cliente.parametros'
    _description = 'Paràmetros Calificacion de cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    motivo = fields.Char( string="Motivo")
    calificacion = fields.Float( string="Calificacion")
