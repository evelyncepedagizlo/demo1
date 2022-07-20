# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TransaccionesGrupoSocio(models.Model):
    _name = 'transaccion.grupo.adjudicado'
    _description = 'Grupo  para proceso adjudicacion'


    grupo_id = fields.Many2one('grupo.adjudicado')

    adjudicado_id = fields.Many2one('res.partner', string="Nombre")
    contrato_id = fields.Many2one('contrato', string='Contrato')
    state = fields.Selection(selection=[
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('congelar_contrato', 'Congelado'),
        ('adjudicar', 'Adjudicado'),
        ('adendum', 'Realizar Adendum'),
        ('finalizado', 'Finalizado'),
        ('cedido', 'Cesión de Derecho'),
        ('desistir', 'Desistido'),
    ], string='Estado', default='pendiente', track_visibility='onchange')

    debe=fields.Float('Débito')
    haber=fields.Float('Crédito')
    saldo=fields.Float('Saldo',compute="calculo_saldo",store=True)

    @api.depends('debe','haber')
    def calculo_saldo(self):
        for l in self:
            l.saldo=l.haber - l.debe
