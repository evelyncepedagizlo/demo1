
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
from datetime import datetime,timedelta,date




class ReporteAnalisisCartera(models.TransientModel):
    _name = "reporte.analisis.cartera"
    _inherit = "reporte.proveedor.cliente"


    


    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'Estado de Cuenta'
        self.xslx_body(workbook, name)
        

        workbook.close()
        file_data.seek(0)
        
        if self.tipo_empresa=='proveedor':
            name = 'Analisis de Cartera Proveedores {0}'.format(self.env.company.name)
        else:
            name = 'Analisis de Cartera Clientes {0}'.format(self.env.company.name)

        
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


        integer_format = workbook.add_format({'num_format': '#0','border':1,'text_wrap': True })
        integer_format.set_align('vcenter')
        float_format = workbook.add_format({'num_format': '#,##0.00','border':1,'text_wrap': True })
        float_format.set_align('vcenter')

        
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
        sheet.set_landscape()
        sheet.set_paper(9)  # A4

        sheet.set_margins(left=0.4, right=0.4, top=0.4, bottom=0.2)
        sheet.set_print_scale(100)
        sheet.fit_to_pages(1,2)




        
        sheet.merge_range('A1:G1', self.env.company.name.upper(), workbook.add_format({'bold':True,'border':0,'align': 'left','size': 14}))
        sheet.merge_range('A2:G2', 'RUC: '+self.env.company.vat, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A3:G3', 'Dirección: '+self.env.company.street, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A4:G4', 'Teléfono: '+self.env.company.phone, workbook.add_format({'bold':True,'border':0,'align': 'left'}))


        titulo='ANALISIS DE CARTERA POR CLIENTE - DETALLADO POR CUOTAS'

        sheet.merge_range('H5:M5', titulo, workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        bold.set_bg_color('b8cce4')
        
        date_format_title_no_border=workbook.add_format({'align': 'center' ,'bold':True, 'border':0,'text_wrap': True})
        date_format_title_no_border.set_bg_color('b8cce4')
        sheet.write(6,7, 'Fecha Desde:', date_format_title_no_border)
        sheet.write(6,8,self.date_from, workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':0,'text_wrap': True }))
        date_format_title_no_border.set_bg_color('b8cce4')
        sheet.write(6,9, 'Fecha Hasta:', date_format_title_no_border)
        sheet.write(6,10, self.date_to, workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':0,'text_wrap': True }))
        

        bold.set_bg_color('b8cce4')

        sheet.merge_range('J8:N8', 'Vencido (en días)', bold)
        sheet.merge_range('O8:S8', 'Por Vencer (en días)', bold)


        title_main=['Tipo','Nro. Documento','Secuencia','Nro. Cuota','Vend.','Depto.','Dias','Fecha Emisión','Fecha Vencimiento','Saldo Actual','+120','91 a 120','61 a 90','31 a 60','1 a 30','1 a 30','31 a 60','61 a 90','91+']
        bold.set_bg_color('b8cce4')

        ##Titulos
        colspan=4
        for col, head in enumerate(title_main):
            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
            sheet.write(8, col, head, bold)

            
        sheet.set_column('B:B', 15)

        filtro=[('invoice_date','>=',self.date_from),
            ('invoice_date','<=',self.date_to)]

        
        if self.tipo_empresa=='proveedor':
            filtro.append(('type','in',['in_invoice','in_debit']))            
        else:
            filtro.append(('type','in',['out_invoice','out_debit']))    




        if len(self.partner_ids.mapped("id"))!=0:
            filtro.append(('partner_id','in',self.partner_ids.mapped("id")))

        lista_partner=self.obtener_listado_partner_facturas(filtro)
        filtro_retenciones=[]


        fila=9
        filas_total_partner=[]
        for partner in lista_partner:
            filtro.append(('partner_id','=',partner['id']))

            
            lista_facturas=self.obtener_listado_facturas(filtro)
            lista_facturas= list(filter(lambda x : x['monto_adeudado']> 0, lista_facturas))

            
           
            if lista_facturas:
                sheet.write(fila, 0, partner['nombre'], workbook.add_format({'bold':True,'border':0}))
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                for factura in lista_facturas:


                    current_line = next(line)

                    sheet.write(current_line, 0, factura.get('tipo_invoice',False) or "", body)
                    sheet.write(current_line, 1, factura.get('numero_documento',False) or "", body)
                    sheet.write(current_line, 2, factura.get('secuencia',False) or "", body)
                    sheet.write(current_line, 3, factura.get('numero_cuota',0) , integer_format)
                    sheet.write(current_line, 4, factura.get('vend',False) or "", body)
                    sheet.write(current_line, 5, factura.get('depto',False) or "", body)
                    sheet.write(current_line, 6, factura.get('dias_vencidos',0) , integer_format)

                    sheet.write(current_line, 7, factura.get('fecha_emision',False), date_format)
                    sheet.write(current_line, 8, factura.get('fecha_vencimiento',False), date_format)
                    sheet.write(current_line, 9, factura.get('monto_adeudado',0), currency_format)


                    sheet.write(current_line, 10, factura.get('120',0) , currency_format)
                    sheet.write(current_line, 11, factura.get('91_120',0) , currency_format)
                    sheet.write(current_line, 12, factura.get('61_90',0) , currency_format)
                    sheet.write(current_line, 13, factura.get('31_60',0) , currency_format)
                    sheet.write(current_line, 14, factura.get('1_30',0) , currency_format)
                    sheet.write(current_line, 15, factura.get('1_30_por_vencer',0) , currency_format)
                    sheet.write(current_line, 16, factura.get('31_60_por_vencer',0) , currency_format)
                    sheet.write(current_line, 17, factura.get('61_90_por_vencer',0) , currency_format)
                    sheet.write(current_line, 18, factura.get('91_por_vencer',0) , currency_format)


                    fila_current=current_line
                    
                    
                bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
                bold_right.set_bg_color('d9d9d9')

                sheet.merge_range('A{0}:I{0}'.format(fila_current+2), 'Total '+ partner['nombre'], bold_right)

                lista_col_formulas=[9,10,11,12,13,14,15,16,17,18]
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
            filtro.remove(('partner_id','=',partner['id']))


                
        lista_col_formulas=[9,10,11,12,13,14,15,16,17,18]
        
        if len(lista_partner)>0:
            bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
            bold_right.set_bg_color('d9d9d9')

            sheet.merge_range('A{0}:I{0}'.format(fila_current+3), 'Total General', bold_right)



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






##RESUMEN TIPO DE TRANSACCION
        fila_transaccion=fila+2
        bold_right=workbook.add_format({'bold':True,'border':0,'align':'left'})
        sheet.write(fila_transaccion,0, 'RESUMEN TIPO DE TRANSACCION', bold_right)

        sheet.write(fila_transaccion+1,0, 'FAC',workbook.add_format({'border':1,'align':'left'} ))
        sheet.write(fila_transaccion+2,0, 'FE',workbook.add_format({'border':1,'align':'left'} ))

        sheet.merge_range('B{0}:D{0}'.format(fila_transaccion+2),'Factura',workbook.add_format({'border':1,'align':'left'} ))
        sheet.merge_range('B{0}:D{0}'.format(fila_transaccion+3),'Factura Electronica',workbook.add_format({'border':1,'align':'left'} ))


        filtro.append(('is_electronic','=',True))
        saldo_facturas_electronica= self.obtener_saldo(filtro)
        filtro.remove(('is_electronic','=',True))
        filtro.append(('is_electronic','=',False))
        saldo_facturas= self.obtener_saldo(filtro)

        sheet.write(fila_transaccion+1,4, saldo_facturas,currency_format)
        sheet.write(fila_transaccion+2,4,saldo_facturas_electronica,currency_format)

        
        
        
        bold_left=workbook.add_format({'bold':True,'border':1,'align':'left'})
        bold_left.set_bg_color('d9d9d9')
        sheet.merge_range('A{0}:D{0}'.format(fila_transaccion+4), 'Total', bold_left)

        

        currency_bold=workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True ,'bold':True})
        currency_bold.set_bg_color('d9d9d9')
        col_formula = {
                'from_col': chr(65 +4),
                'to_col': chr(65 +4),
                'from_row':fila_transaccion+2,
                'to_row': fila_transaccion+3,                
            
            }
        sheet.write_formula(
                    fila_transaccion+3 ,4 ,
                    '=SUM({from_col}{from_row}:{to_col}{to_row})'.format(
                        **col_formula
                    ), currency_bold)