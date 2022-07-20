
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




class ReporteAnticipo(models.TransientModel):
    _name = "reporte.anticipo"
    _inherit = "reporte.proveedor.cliente"


    def obtener_listado_partner_payment(self,filtro):
        

        if self.tipo_empresa=='proveedor':
            filtro.append(('partner_type','=','supplier'))            
        else:
            filtro.append(('partner_type','=','customer'))      

        if len(self.partner_ids.mapped("id"))!=0:
            filtro.append(('partner_id','in',self.partner_ids.mapped("id")))
        

#######filtro de facturas
        partners=list(set(self.env['account.payment'].search(filtro).mapped('partner_id').mapped('id')))
        obj_partner=self.env['res.partner'].browse(partners)
        lista_partner=[]

        for partner in obj_partner:
            dct={}
            dct['id']=partner.id 
            dct['nombre']=partner.name
            lista_partner.append(dct)



        return lista_partner



            
    def obtener_listado_payment_por_empresa(self,partner_id,filtro):
        if partner_id:
            filtro.append(('partner_id','=',partner_id))            

        if self.tipo_empresa=='proveedor':
            filtro.append(('partner_type','=','supplier'))            
        else:
            filtro.append(('partner_type','=','customer'))            

#######facturas
        payments=self.env['account.payment'].search(filtro,order='name asc')
        
        lista_facturas=[]

        for payment in payments:
            dct={}
            dct['numero_documento']=payment.name
            dct['fecha_emision']=payment.payment_date
            dct['fecha_vencimiento']=payment.date_to
##### Calculo de pagos


            dct['monto_adeudado']=payment.amount_residual
            dct['monto_aplicado']=payment.amount - payment.amount_residual
            dct['monto_anticipo']=payment.amount

            dct['observaciones']=payment.communication



            lista_facturas.append(dct)
        return lista_facturas








    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'Reporte de Anticipos'
        self.xslx_body(workbook, name)
        

        workbook.close()
        file_data.seek(0)
        
        if self.tipo_empresa=='proveedor':
            name = 'Reporte de Anticipos Proveedores {0}'.format(self.env.company.name)
        else:
            name = 'Reporte de Anticipos Clientes {0}'.format(self.env.company.name)

        
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






        
    def xslx_body(self, workbook, name):
        bold = workbook.add_format({'bold':True,'border':1})
        bold_no_border = workbook.add_format({'bold':True})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':1})
        format_title_left = workbook.add_format({'bold':True,'border':1,'align': 'left'})
        format_title_left_14 = workbook.add_format({'bold':True,'border':1,'align': 'left','size': 14})
        format_title_center_14 = workbook.add_format({'bold':True,'border':1,'align': 'center','size': 14})


        format_title.set_center_across()
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True })
        currency_format.set_align('vcenter')

        
        date_format = workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':1,'text_wrap': True })
        date_format.set_align('vcenter')
        date_format_day = workbook.add_format({'align': 'right','border':1,'text_wrap': True })
        date_format_day.set_align('vcenter')
        date_format_title = workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'left','text_wrap': True})
        date_format_title.set_align('vcenter')

        body = workbook.add_format({'align': 'center' , 'border':1,'text_wrap': True})
        body.set_align('vcenter')
        body_right = workbook.add_format({'align': 'right', 'border':1 })
        body_left = workbook.add_format({'align': 'left','bold':True})
        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':1 })
        sheet = workbook.add_worksheet(name)

        sheet.set_portrait()
        sheet.set_paper(9)  # A4

        sheet.set_margins(left=0.4, right=0.4, top=0.4, bottom=0.2)
        sheet.set_print_scale(100)
        sheet.fit_to_pages(1,2)



        
        sheet.merge_range('A1:G1', self.env.company.name.upper(), workbook.add_format({'bold':True,'border':0,'align': 'left','size': 14}))
        sheet.merge_range('A2:G2', 'RUC: '+self.env.company.vat, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A3:G3', 'Dirección: '+self.env.company.street, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A4:G4', 'Teléfono: '+self.env.company.phone, workbook.add_format({'bold':True,'border':0,'align': 'left'}))

        sheet.merge_range('A5:G5', 'ANTICIPOS PENDIENTES POR APLICAR', workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        bold.set_bg_color('b8cce4')
        
        
        date_format_title_no_border=workbook.add_format({'align': 'center' ,'bold':True, 'border':0,'text_wrap': True})
        date_format_title_no_border.set_bg_color('b8cce4')
        sheet.write(5,1, 'Fecha Desde:', date_format_title_no_border)
        sheet.write(5,2,self.date_from, workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':0,'text_wrap': True }))
        date_format_title_no_border.set_bg_color('b8cce4')
        sheet.write(5,3, 'Fecha Hasta:', date_format_title_no_border)
        sheet.write(5,4, self.date_to, workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':0,'text_wrap': True }))

        




        title_main=['Documento','Fc. Emisión', 'Fc.Vencimiento', 'Anticipo','Aplicación', 'Saldo', 'Observaciones']
        bold.set_bg_color('b8cce4')

        ##Titulos
        colspan=4
        for col, head in enumerate(title_main):
            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
            sheet.write(7, col, head, bold)

            
        sheet.set_column('A:A', 23)
        sheet.set_column('B:B', 23)
        sheet.set_column('H:H', 60)

        filtro=[('payment_date','>=',self.date_from),
            ('payment_date','<=',self.date_to),('tipo_transaccion','=','Anticipo')]

        lista_partner=self.obtener_listado_partner_payment(filtro)
        fila=8
        filas_total_partner=[]
        for partner in lista_partner:
            filtro=[('payment_date','>=',self.date_from),
                ('payment_date','<=',self.date_to),('tipo_transaccion','=','Anticipo')]
            lista_anticipos=self.obtener_listado_payment_por_empresa(partner['id'],filtro)

            if len(lista_anticipos)>0:
                sheet.write(fila, 0, partner['nombre'], workbook.add_format({'bold':True,'border':0}))
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                for anticipo in lista_anticipos:
                    current_line = next(line)

                    sheet.write(current_line, 0, anticipo['numero_documento'] or "", body)
                    sheet.write(current_line, 1, anticipo['fecha_emision'] or "", date_format)
                    sheet.write(current_line, 2, anticipo['fecha_vencimiento'] or "", date_format)
                    sheet.write(current_line, 3, anticipo['monto_anticipo'] ,currency_format)
                    sheet.write(current_line, 4, anticipo['monto_aplicado'] ,currency_format)
                    sheet.write(current_line, 5, anticipo['monto_adeudado']  ,currency_format)
                    sheet.write(current_line, 6,  anticipo['observaciones'] or "" ,body)
                    fila_current=current_line

                bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
                bold_right.set_bg_color('d9d9d9')

                sheet.merge_range('A{0}:C{0}'.format(fila_current+2), 'Total '+ partner['nombre'], bold_right)

                lista_col_formulas=[3,4,5]
                for col in lista_col_formulas:
                    col_formula = {
                            'from_col': chr(65 +col),
                            'to_col': chr(65 +col),
                            'from_row': fila+1,
                            'to_row': fila_current+1,                

                        }
                    currency_bold=workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True ,'bold':True})
                    currency_bold.set_bg_color('d9d9d9')

                    sheet.write_formula(
                                fila_current+1 ,col ,
                                '=SUM({from_col}{from_row}:{to_col}{to_row})'.format(
                                    **col_formula
                                ), currency_bold)
                filas_total_partner.append(fila_current+2)

                fila=fila_current+3

                
                
                
                
                
                
                
                
  
        lista_col_formulas=[3,4,5]
        
        if len(lista_partner)>0:

            bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
            bold_right.set_bg_color('d9d9d9')

            sheet.merge_range('A{0}:C{0}'.format(fila_current+3), 'Total General', bold_right)

              

            
            for columna in lista_col_formulas:

                currency_bold=workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True ,'bold':True})
                currency_bold.set_bg_color('d9d9d9')


                formula='='
                for fila_total in filas_total_partner:
                    formula=formula+'{0}{1}'.format(chr(65 +columna),fila_total)+'+'
                formula=formula.rstrip('+')
                sheet.write(
                            fila_current+2 ,columna ,
                            formula, currency_bold)


    def print_report_pdf(self):
        return self.env.ref('gzl_reporte_financiero.repote_anticipo_pdf_id').report_action(self)



        
    def obtenerDatos(self,):

        filtro=[('payment_date','>=',self.date_from),
            ('payment_date','<=',self.date_to),('tipo_transaccion','=','Anticipo')]


        lista_partner=self.obtener_listado_partner_payment(filtro)
        lines=[]
        

        for partner in lista_partner:
            filtro=[('payment_date','>=',self.date_from),
                ('payment_date','<=',self.date_to),('tipo_transaccion','=','Anticipo')]
            
            lines.append({'numero_documento':partner['nombre'],'reglon':'titulo'})

            lista_anticipos=self.obtener_listado_payment_por_empresa(partner['id'],filtro)
            for dct in lista_anticipos:
                dct['reglon']='detalle'
                lines.append(dct)
            dctTotal={}
            dctTotal['numero_documento']='Total '+ partner['nombre']

            dctTotal['monto_anticipo']=round(sum(map(lambda x:x['monto_anticipo'],lista_anticipos)),2)
            dctTotal['monto_aplicado']=round(sum(map(lambda x:x['monto_aplicado'],lista_anticipos)),2)
            dctTotal['monto_adeudado']=round(sum(map(lambda x:x['monto_adeudado'],lista_anticipos)),2)
            dctTotal['reglon']='total_detalle'


            lines.append(dctTotal)
        dctTotalGeneral={}
        dctTotalGeneral['numero_documento']='Total General'

        dctTotalGeneral['monto_anticipo']=round(sum(map(lambda x:x['monto_anticipo'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['monto_aplicado']=round(sum(map(lambda x:x['monto_aplicado'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['monto_adeudado']=round(sum(map(lambda x:x['monto_adeudado'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['reglon']='total_general'

        lines.append(dctTotalGeneral)
        lista_obj=[]
        for l in lines:
            obj_detalle=self.env['reporte.anticipo.detalle'].create(l)
            lista_obj.append(obj_detalle)

        return lista_obj



class ReporteAnticipoDetalle(models.TransientModel):
    _name = "reporte.anticipo.detalle"

    numero_documento = fields.Char('Nro. Documento')
    fecha_emision = fields.Date('Fc. Emision')
    fecha_vencimiento = fields.Date('Fc. Vencimiento')
    monto_anticipo = fields.Float('Monto Anticipo')
    monto_aplicado = fields.Float('Monto Aplicado')
    monto_adeudado = fields.Float('Monto Adeudado')
    observaciones = fields.Char('Observaciones')
    reglon = fields.Char('Reglon')

