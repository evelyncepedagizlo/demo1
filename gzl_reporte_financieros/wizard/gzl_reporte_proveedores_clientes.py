
# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from datetime import date, timedelta,datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import AccessError, UserError, ValidationError
from .funciones import *
import calendar
import datetime as tiempo
import itertools
import json



class ReporteProveedorCliente(models.TransientModel):
    _name = "reporte.proveedor.cliente"


    date_from = fields.Date('Desde')
    date_to = fields.Date('Hasta')
    tipo_empresa = fields.Selection([('proveedor','Proveedor'),('cliente','Cliente')],default='cliente')
    partner_ids = fields.Many2many('res.partner',string='Empresa')
    dominio  = fields.Char(store=False, compute="_filtro_partner",readonly=True)

    @api.depends('tipo_empresa')
    def _filtro_partner(self):
        for l in self:
            if l.tipo_empresa=='proveedor':
                l.dominio=json.dumps( [('supplier_rank','>',0)] )
            else:
                l.dominio=json.dumps( [('customer_rank','>',0)])



    @api.onchange('tipo_empresa' )
    def onchange_tipo_empresa(self):

        if  self.tipo_empresa:
            self.partner_ids=()


    @api.constrains('date_from','date_to' )
    def validacion_fechas(self):
        if self.date_from and self.date_to:
            if  self.date_from > self.date_to:
                raise ValidationError(("La fecha hasta debe ser mayor a la fecha desde"))

        
    def obtener_listado_partner_facturas(self,filtro):
        

        partners=list(set(self.env['account.move'].search(filtro,order='l10n_latam_document_number asc').mapped('partner_id').mapped('id')))
        partners=self.env['res.partner'].browse(partners)
        
        lista_partner=[]
        for partner in partners:
            dct={}
            dct['id']=partner.id 
            dct['nombre']=partner.name
            lista_partner.append(dct)

        return lista_partner



            
    def obtener_listado_facturas(self,filtro):

    
#######facturas
        facturas=self.env['account.move'].search(filtro,order='l10n_latam_document_number asc')
        
        lista_facturas=[]

        for factura in facturas:
            dct={}
            dct['secuencia']=factura.name
            dct['numero_documento']=factura.l10n_latam_document_number
            dct['invoice_id']=factura.id
            dct['fecha_emision']=factura.invoice_date
            dct['fecha_vencimiento']=factura.invoice_date_due
            dct['documento_contable']=factura.journal_id.name
##### Calculo de saldos debe ser cambiado

            pagos=sum(list(self.env['account.payment'].search([('invoice_ids','=',factura.id),('payment_date','<=',self.date_to)]).mapped('amount')))
            dct['monto_adeudado']=factura.amount_residual
            dct['monto_total']=factura.amount_total
            dct['referencia']=factura.ref
            dct['observaciones']=factura.narration

            dct['debe']=0.00
            dct['haber']=0.00
            dct['saldo_factura']=0.00


            if factura.is_electronic:
                dct['tipo_invoice']='FE'
            else:
                dct['tipo_invoice']='FA'


            if factura.type in ['in_invoice','out_invoice']:
                dct['tipo_referencia']=''
            elif factura.type in ['in_refund','out_refund']:
                dct['tipo_referencia']='NCR'
            elif factura.type in ['in_debit','out_debit']:
                dct['tipo_referencia']='NDB'

            hoy= date.today()

            lista_pagos=self.env['account.payment'].search([('invoice_ids','=',factura.id)])

            if len(lista_pagos)>0:
                dct['numero_cuota']=len(lista_pagos)
            delta = hoy - dct['fecha_vencimiento']
            
            dias=delta.days
            if dias>0:  
                dct['dias_vencidos']=dias
                if dias>120:
                    dct['120']=factura.amount_residual
                elif dias>90 and dias<120:
                    dct['91_120']=factura.amount_residual
                elif dias>60 and dias <=90:
                    dct['61_90']=factura.amount_residual
                elif dias>30 and dias<=60:
                    dct['31_60']=factura.amount_residual
                elif dias>0 and dias <=30:
                    dct['1_30']=factura.amount_residual
            else:
                dct['dias_vencidos']=0
                if abs(dias)>90:
                    dct['91_por_vencer']=factura.amount_residual
                elif abs(dias)>60 and abs(dias) <=90:
                    dct['61_90_por_vencer']=factura.amount_residual
                elif abs(delta.days)>30 and abs(dias) <=60:
                    dct['31_60_por_vencer']=factura.amount_residual
                elif abs(dias)>1 and abs(dias) <=30:
                    dct['1_30_por_vencer']=factura.amount_residual


            lista_facturas.append(dct)
        return lista_facturas




    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)

        
        name = 'Saldo Agrupado'

        self.xslx_body_saldo_agrupado(workbook, name)

        name = 'Saldo Detallado'

        self.xslx_body_saldo_detallado(workbook, name)

       # name = 'Estado de Cuenta'

        #self.xslx_body_estado_cuenta(workbook, name)


        workbook.close()
        file_data.seek(0)
        
        if self.tipo_empresa=='proveedor':
            name = 'Reporte de Saldo Proveedores {0}'.format(self.env.company.name)
        else:
            name = 'Reporte de  Saldo Clientes {0}'.format(self.env.company.name)

        
        attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(file_data.getvalue()),
            'name': name,
            'store_fname': name,
            'type': 'binary',
        })
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += "/web/content/%s?download=true" %(attachment.id)
        return{
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }


