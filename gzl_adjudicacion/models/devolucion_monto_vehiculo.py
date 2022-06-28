# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, tools,  _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime,timedelta,date
import re


class DevolucionMonto(models.Model):   
    _name = 'devolucion.monto'   
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name= 'secuencia'

    secuencia = fields.Char(index=True)

    monto = fields.Float(string='Monto')
    contrato_id = fields.Many2one('contrato')
    fsolicitud  = fields.Date(string='Fecha de Solicitud')
    state = fields.Selection(selection=[
        ('borrador', 'Borrador'),
        ('postventa', 'Analisis Postventa'),
        ('legal', 'Analisis Legal'),
        ('adjudicaciones', 'Analisis Adjudicacion'),
        ('verifvalores', 'Verificacion de Valores'),
        ('aprobgerencia', 'Aprobacion Gerencia'),
        ('salidadinero', 'Salida Dinero'),
        ('notificacion', 'Notificacion Cliente'),
        ('liquidacion', 'Liquidacion de vendedor'),
    ], string='Estado', default='borrador', track_visibility='onchange')

    rolAsignado = fields.Many2one('adjudicaciones.team', string="Rol Asignado", track_visibility='onchange')
    
    rolGerenciaFin = fields.Many2one('adjudicaciones.team', string="Rol Gerencia Financiera", track_visibility='onchange',default=lambda self:self.env.ref('gzl_adjudicacion.tipo_rol4'))
    rolAdjudicacion = fields.Many2one('adjudicaciones.team', string="Rol Adjudicacion", track_visibility='onchange',default=lambda self:self.env.ref('gzl_adjudicacion.tipo_rol2'))

    rolpostventa = fields.Many2one('adjudicaciones.team', string="Rol Post venta", track_visibility='onchange',default=lambda self:self.env.ref('gzl_adjudicacion.tipo_rol5'))
    rollegal = fields.Many2one('adjudicaciones.team', string="Rol Legal", track_visibility='onchange',default=lambda self:self.env.ref('gzl_adjudicacion.tipo_rol6'))

    rolcontab = fields.Many2one('adjudicaciones.team', string="Rol contabilidad Financiera", track_visibility='onchange',default=lambda self:self.env.ref('gzl_adjudicacion.tipo_rol7'))
    rolnomina = fields.Many2one('adjudicaciones.team', string="Rol Nomina", track_visibility='onchange',default=lambda self:self.env.ref('gzl_adjudicacion.tipo_rol8'))

    @api.model
    def create(self, vals):
        vals['secuencia'] = self.env['ir.sequence'].next_by_code('devolucion.adjudicado')


        return super(DevolucionMonto, self).create(vals)