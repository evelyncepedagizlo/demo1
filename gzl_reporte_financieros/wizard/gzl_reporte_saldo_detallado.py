
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




class ReporteProveedorCliente(models.TransientModel):
    _inherit = "reporte.proveedor.cliente"

        
    def xslx_body_saldo_detallado(self, workbook, name):
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

        if self.tipo_empresa=='proveedor':
            titulo='SALDO DE FACTURAS  DETALLADO DE PROVEEDORES FECHA DE CORTE '
        else:
            titulo='SALDO DE FACTURAS  DETALLADO DE CLIENTES FECHA DE CORTE '

        sheet.merge_range('A5:G5', titulo + datetime.strptime(str(self.date_to),'%Y-%m-%d').strftime('%d/%m/%Y'), workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        bold.set_bg_color('b8cce4')
        
        

        title_main=['Tipo','Documento','Secuencia' ,'Fc. Emisión', 'Fc.Vencimiento', 'Saldo','Observaciones']
        bold.set_bg_color('b8cce4')

        ##Titulos
        colspan=4
        for col, head in enumerate(title_main):
            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
            sheet.write(7, col, head, bold)

            
        sheet.set_column('A:A', 4)
        sheet.set_column('G:G', 60)
        sheet.set_column('B:B', 23)
        filtro=[('invoice_date','<=',self.date_to),('state','=','posted')]

        if self.tipo_empresa=='proveedor':
            filtro.append(('type','in',['in_invoice','in_debit']))            
        else:
            filtro.append(('type','in',['out_invoice','out_debit']))            

        if len(self.partner_ids.mapped("id"))!=0:
            filtro.append(('partner_id','in',self.partner_ids.mapped("id")))
      

        lista_partner=self.obtener_listado_partner_facturas(filtro)



        fila=8
        filas_total_partner=[]
        for partner in lista_partner:

            filtro.append(('partner_id','=',partner['id']))




            lista_facturas=self.obtener_listado_facturas(filtro)

            if lista_facturas:
                sheet.write(fila, 0, partner['nombre'], workbook.add_format({'bold':True,'border':0}))
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                for factura in lista_facturas:
                    current_line = next(line)

                    sheet.write(current_line, 0, factura['tipo_invoice'] or "", body)
                    sheet.write(current_line, 1, factura['numero_documento'] or "", body)
                    sheet.write(current_line, 2, factura['secuencia'] or "", body)
                    sheet.write(current_line, 3, factura['fecha_emision'] or "", date_format)
                    sheet.write(current_line, 4, factura['fecha_vencimiento'] or "", date_format)
                    sheet.write(current_line, 5, factura['monto_adeudado']  ,currency_format)
                    sheet.write(current_line, 6,factura['observaciones'] or "" ,body)
                    fila_current=current_line
                    
                    
                bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
                bold_right.set_bg_color('d9d9d9')

                sheet.merge_range('A{0}:E{0}'.format(fila_current+2), 'Total '+ partner['nombre'], bold_right)

                lista_col_formulas=[5]
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


                
        lista_col_formulas=[5]
        
        if len(lista_partner)>0:
            bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
            bold_right.set_bg_color('d9d9d9')

            sheet.merge_range('A{0}:E{0}'.format(fila_current+3), 'Total General', bold_right)



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


    def obtenerDatosSaldoDetallado(self,):

        filtro=[('invoice_date','<=',self.date_to)]

        if self.tipo_empresa=='proveedor':
            filtro.append(('type','=','in_invoice'))            
        else:
            filtro.append(('type','=','out_invoice'))            

        if len(self.partner_ids.mapped("id"))!=0:
            filtro.append(('partner_id','in',self.partner_ids.mapped("id")))
      

        lista_partner=self.obtener_listado_partner_facturas(filtro)

        lines=[]

        for partner in lista_partner:
            filtro.append(('partner_id','=',partner['id']))
            lines.append({'numero_documento':partner['nombre'],'reglon':'titulo'})

            lista_facturas=self.obtener_listado_facturas(filtro)
            for dct in lista_facturas:
                dctFactura={}
                dctFactura['secuencia']=dct['secuencia']
                dctFactura['numero_documento']=dct['numero_documento']
                dctFactura['fecha_emision']=dct['fecha_emision']
                dctFactura['fecha_vencimiento']=dct['fecha_vencimiento']
                dctFactura['monto_adeudado']=dct['monto_adeudado']
                dctFactura['observaciones']=dct['observaciones']
                dctFactura['tipo_invoice']=dct['tipo_invoice']
                dctFactura['reglon']='detalle'
                lines.append(dctFactura)
            dctTotal={}
            dctTotal['numero_documento']='Total '+ partner['nombre']
            dctTotal['monto_adeudado']=round(sum(map(lambda x:x['monto_adeudado'],lista_facturas)),2)
            dctTotal['reglon']='total_detalle'
            lines.append(dctTotal)
            filtro.remove(('partner_id','=',partner['id']))

        dctTotalGeneral={}
        dctTotalGeneral['numero_documento']='Total General'
        dctTotalGeneral['monto_adeudado']=round(sum(map(lambda x:x['monto_adeudado'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['reglon']='total_general'
        lines.append(dctTotalGeneral)
        lista_obj=[]
        for l in lines:
            obj_detalle=self.env['reporte.saldo.empresa'].create(l)
            lista_obj.append(obj_detalle)

        return lista_obj




