# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
import datetime

class GrupoSocios(models.Model):
    _name = 'grupo.adjudicado'
    _description = 'Grupo  para proceso adjudicacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    secuencia_id= fields.Many2one('ir.sequence',"Codigo de Contrato")
    name=fields.Char('Nombre',  required=True , track_visibility='onchange')
    codigo = fields.Char(string='Código',track_visibility='onchange')
    descripcion=fields.Text('Descripcion', required=True)
    active=fields.Boolean(default=True, string='Activo',track_visibility='onchange')
    integrantes = fields.One2many('integrante.grupo.adjudicado','grupo_id',track_visibility='onchange')
    asamblea_id = fields.Many2one('asamblea')
    estado = fields.Selection(selection=[
            ('en_conformacion', 'En Conformación'),
            ('cerrado', 'Cerrado')
            ], string='Estado', copy=False, tracking=True, default='en_conformacion',track_visibility='onchange')
    cantidad_integrantes = fields.Integer(string='Cantidad de Integrantes',track_visibility='onchange')
    maximo_integrantes = fields.Integer(string='Máximo de Integrantes',track_visibility='onchange')

    integrantes = fields.One2many('integrante.grupo.adjudicado','grupo_id',track_visibility='onchange')
    transacciones_ids = fields.One2many('transaccion.grupo.adjudicado','grupo_id',track_visibility='onchange')

    idGrupo = fields.Char("ID de Grupo en Cotnrato")#acunalema



    _sql_constraints = [
        ('codigo_uniq', 'unique (codigo)', 'El código ya existe.')
    ]
    



    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)


    recuperacionCartera = fields.Monetary(compute='calculo_recuperacion_cartera',string='Recuperación de Cartera', currency_field='currency_id', track_visibility='onchange')

    @api.depends('transacciones_ids')
    def calculo_recuperacion_cartera(self):
        for l in self:
            hoy=date.today()
            grupoParticipante=l.transacciones_ids.filtered(lambda l: l.create_date.month==hoy.month and l.create_date.year==hoy.year)
            l.recuperacionCartera=sum(grupoParticipante.mapped('haber'))









    contador_transacciones = fields.Integer(string='Contador de Transacciones',compute="calcular_transacciones",store=True)


    @api.depends("transacciones_ids")
    def calcular_transacciones(self,):
        for l in self:
            l.contador_transacciones=len(self.transacciones_ids)


    def action_transacciones_grupo(self):


        return {
            'name': ('Transacciones Grupo'),
            'view_mode': 'tree,form',
            'res_model': 'transaccion.grupo.adjudicado',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('grupo_id', '=',self.id)],
        }





    @api.depends('integrantes.monto')
    def compute_monto_cartera(self):
        num_integrantes=0
        for l in self.integrantes:
            num_integrantes +=1
            if num_integrantes > self.maximo_integrantes:
                raise ValidationError('Ha excedido el máximo de integrantes.')
        self.cantidad_integrantes=num_integrantes
   


    monto_grupo = fields.Float(string='Fondo',compute="calcular_monto_pagado")


    @api.depends("integrantes.contrato_id.state","integrantes")
    def calcular_monto_pagado(self,):
        for l in self:
            monto=sum(l.transacciones_ids.mapped('haber'))-sum(l.transacciones_ids.mapped('debe'))
            l.monto_grupo=monto


    def cerrar_grupo(self,):
        self.estado='cerrado'

    def abrir_grupo(self,):
        self.estado='en_conformacion'


class IntegrantesGrupo(models.Model):
    _name = 'integrante.grupo.adjudicado'
    _description = 'Integrantes de Grupo para proceso adjudicacion'
  
    descripcion=fields.Char('Descripcion',  )
    grupo_id = fields.Many2one('grupo.adjudicado')
    monto=fields.Float('Monto')
    nro_cuota_licitar = fields.Integer(string='Nro de Cuotas a Licitar')
    carta_licitacion = fields.Selection([('si', 'Si'), ('no', 'No')], string='Carta Licitación')
    codigo_integrante = fields.Char(string='Código')
    codigo_cliente = fields.Char(string='Código Cliente', related='adjudicado_id.codigo_cliente')
    vat = fields.Char(string='No. Identificación', related='adjudicado_id.vat')
    adjudicado_id = fields.Many2one('res.partner', string="Nombre", domain="[('tipo','=','adjudicado')]")
    mobile = fields.Char(string='Móvil', related='adjudicado_id.mobile')
    contrato_id = fields.Many2one('contrato', string='Contrato')
    cupo = fields.Selection(selection=[
            ('ocupado', 'Ocupado'),
            ('desocupado', 'Desocupado')
            ], string='Cupo', default='ocupado')




    @api.constrains("adjudicado_id")
    @api.onchange("adjudicado_id")
    def agregar_contrato(self):

        if self.adjudicado_id.id:
            contrato=self.env['contrato'].search([('cliente','=',self.adjudicado_id.id)],limit=1)
            if len(contrato)>0:
                self.contrato_id=contrato.id
            else:
                self.contrato_id=False





    @api.constrains("adjudicado_id")
    def validar_cliente_en_otro_grupo(self, ):


        if self.adjudicado_id.id:
            grupos=self.env['grupo.adjudicado'].search([('id','!=',self.grupo_id.id)])
            listaIntegrantes=[]

            for grupo in grupos:
                listaIntegrantes=listaIntegrantes + (grupo.integrantes.mapped('adjudicado_id').ids)
            listaIntegrantes=list(set(listaIntegrantes))

            if self.adjudicado_id.id in listaIntegrantes:
                raise ValidationError("El integrante {0} ya está ingresado en otro grupo".format(self.adjudicado_id.name))











    @api.model
    def create(self, vals):
        grupo = self.env['grupo.adjudicado'].search([('id','=',vals['grupo_id'] )])

        return super(IntegrantesGrupo, self).create(vals)