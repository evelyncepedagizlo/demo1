# -*- coding: utf-8 -*-

from odoo import api, _, fields, models, tools
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import xlsxwriter
from io import BytesIO
import base64
from calendar import monthrange
import ast
from odoo.exceptions import ValidationError, except_orm


class CalculoComision(models.Model):
    _name = "calcula.comision"
    name = fields.Many2one('hr.employee', string='Empleado', required=True)
    partner = fields.Many2one('res.partner', string='partner', required=True,track_visibility='onchange')
    det = fields.One2many('detalle.oportunidades', 'sale_id')
    fechaInicio= fields.Date('Fecha Inicio')
    fechaFin = fields.Date( 'Fecha Fin')
    
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    company_currency = fields.Many2one(string='Currency', related='company_id.currency_id', readonly=True, relation="res.currency")

    comision = fields.Monetary(string='Comision',compute="calcular_monto_pagado",store="True",currency_field='company_currency',)

    @api.depends("det.comision")
    def calcular_monto_pagado(self):
        for l in self:
            l.comision=sum(l.det.mapped("comision"))






    #detalle_op = fields.One2many('crm.lead','partner_id',track_visibility='onchange')
    """date = fields.Selection(selection=[
            ('01', 'Enero'),
            ('02', 'Febrero'),
            ('03', 'Marzo'),
            ('04', 'Abril'),
            ('05', 'Mayo'),
            ('06', 'Junio'),
            ('07', 'Julio'),
            ('08', 'Agosto'),
            ('09', 'Septiembre'),
            ('10', 'Octubre'),
            ('11', 'Noviembre'),
            ('12', 'Diciembre'),
        ], string='Fecha', required=True)"""

    def calculo_comision(self):
        dct={}
        lis=[]
        cont=0
        self.ensure_one()
        partner_ids = self.env['res.partner']
        partner = partner_ids.search([('active','=',True),('vat','=',self.name.identification_id)])
        crm = self.env['crm.lead'].search([('partner_id','=',partner.id),('active','=',True)])
        #for l in crm:
            
        detalle =self.env['detalle.oportunidades']
        #action = self.env.ref('gzl_employee.action_calculo_comision_detalle_crm').read()[0]
       
        return action 
        """return {'name': _('Picking Prices'),
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'detalle.oportunidades',
                'view_id': action.id,
                'views': [(action.id, 'form')],
                'type': 'ir.actions.act_window',
                'context': {'default_crmlead': self.name.id}}"""
        
        
        
        
    @api.onchange('name','fechaInicio','fechaFin')
    def _onchange_name(self):
        for e in self:
            lines =[(5,0,0)]
            partner_ids = self.env['res.users']
            users = partner_ids.search([('active','=',True),('id','=',self.name.user_id.id)])
            #raise ValidationError(str(users.id))
            crm = self.env['crm.lead'].search([('user_id','=',users.id),('active','=',True),('create_date','>=',self.fechaInicio),('create_date','<=',self.fechaFin)])
            #raise ValidationError(str(crm))
            if crm :
                for l in crm :
                    #raise ValidationError(str(l.partner_id))
                    vals= {
                        'name':l.name,
                        'planned_revenue':l.planned_revenue,
                        'crmlead':l.id,
                        'company_id':l.company_id.id,
                        'company_currency':l.company_currency.id

                    }
                    lines.append((0,0,vals))
            
            e.det = lines
            #raise ValidationError(str(e.det))
                #raise ValidationError(str(l.partner_id))
                #hi = self.env['crm.lead'].filtered(lambda h:  h.partner_id == l.partner_id.id)
                #raise ValidationError(str(hi))
    #    data = []
    #    crm = self.env['crm.lead'].search([('id','=',self.cemlead.id),('active','=',True)])
        
class DetalleOportunidades(models.Model):
    _name = 'detalle.oportunidades'
    crmlead = fields.Many2one('crm.lead', string='Oportunidad')
    name = fields.Char('Oportunidad')
    planned_revenue = fields.Monetary('Monto del Plan', currency_field='company_currency', tracking=True)
    porcentaje_comision = fields.Float('Porcentaje de Comisión',  tracking=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    company_currency = fields.Many2one(string='Currency', related='company_id.currency_id', readonly=True, relation="res.currency")
    sale_id = fields.Many2one('calcula.comision')
    comision = fields.Monetary(string='Comision',compute="calcular_monto_pagado",store="True",currency_field='company_currency',)

    @api.depends("porcentaje_comision")
    def calcular_monto_pagado(self):
        for l in self:
            l.comision=l.porcentaje_comision*l.planned_revenue/100



