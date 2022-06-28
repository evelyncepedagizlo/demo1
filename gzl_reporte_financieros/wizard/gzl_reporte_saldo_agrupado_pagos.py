
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



    def obtener_saldo(self,filtro):


        lista=self.obtener_listado_facturas(filtro)

        lista_saldo=list(map(lambda x: x['monto_adeudado'], lista))
        saldo=sum(lista_saldo)

        return saldo


        
    def xslx_body_saldo_agrupado(self, workbook, name):
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
            titulo='SALDO DE FACTURAS AGRUPADO DE PROVEEDORES FECHA DE CORTE '
        else:
            titulo='SALDO DE FACTURAS AGRUPADO DE CLIENTES FECHA DE CORTE '

        sheet.merge_range('A5:H5', titulo + datetime.strptime(str(self.date_to),'%Y-%m-%d').strftime('%d/%m/%Y'), workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        bold.set_bg_color('b8cce4')
        
        

        title_main=['Empresa','Saldo' ]
        bold.set_bg_color('b8cce4')

        sheet.merge_range('A{0}:D{0}'.format(7),'Empresa', bold)

        
        sheet.write(6,4, 'Saldo',bold )


        ##Titulos
        sheet.set_column('A:D', 11)
        sheet.set_column('E:E', 24)

        filtro=[]
        if self.tipo_empresa=='proveedor':
            filtro.append(('type','in',['in_invoice','in_debit']))            
        else:
            filtro.append(('type','in',['out_invoice','out_debit']))                

        filtro.append(('invoice_date','<=',self.date_to))
        filtro.append(('state','=','posted'))

        if len(self.partner_ids.mapped("id"))!=0:
            filtro.append(('partner_id','in',self.partner_ids.mapped("id")))
        
        lista_partner=self.obtener_listado_partner_facturas(filtro)


        line = itertools.count(start=7)
        for partner in lista_partner:
            filtro.append(('partner_id','=', partner['id']))
            saldo=self.obtener_saldo(filtro)
            if saldo!=0:


                current_line = next(line)

                sheet.merge_range('A{0}:D{0}'.format(current_line+1), partner['nombre'], workbook.add_format({'border':1,'text_wrap':True}))

                sheet.write(current_line,4, saldo, currency_format)
                fila_current=current_line
            filtro.remove(('partner_id','=', partner['id']))            


##TOTAL DE REPORTE
        if len(lista_partner)>0:

            bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
            bold_right.set_bg_color('d9d9d9')
            sheet.merge_range('A{0}:D{0}'.format(fila_current+2), 'Total General', bold_right)

            currency_bold=workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True ,'bold':True})
            currency_bold.set_bg_color('d9d9d9')
            col_formula = {
                    'from_col': chr(65 +4),
                    'to_col': chr(65 +4),
                    'from_row': 8,
                    'to_row': fila_current+1,                

                }
            sheet.write_formula(
                        fila_current+1 ,4 ,
                        '=SUM({from_col}{from_row}:{to_col}{to_row})'.format(
                            **col_formula
                        ), currency_bold)

    ##RESUMEN TIPO DE TRANSACCION
            fila_transaccion=fila_current+2
            bold_right=workbook.add_format({'bold':True,'border':0,'align':'left'})
            sheet.write(fila_transaccion,0, 'RESUMEN TIPO DE TRANSACCION', bold_right)

            sheet.write(fila_transaccion+1,0, 'FAC',workbook.add_format({'border':1,'align':'left'} ))
            sheet.write(fila_transaccion+2,0, 'FE',workbook.add_format({'border':1,'align':'left'} ))

            sheet.merge_range('B{0}:D{0}'.format(fila_transaccion+2),'Factura',workbook.add_format({'border':1,'align':'left'} ))
            sheet.merge_range('B{0}:D{0}'.format(fila_transaccion+3),'Factura Electronica',workbook.add_format({'border':1,'align':'left'} ))

            if len(self.partner_ids.mapped("id"))!=0:
                filtro.append(('partner_id','in',self.partner_ids.mapped("id")))


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


    def print_report_pdf(self):
        return self.env.ref('gzl_reporte_financiero.repote_saldo_pdf_id').report_action(self)




        
    def obtenerDatosAgrupado(self,tipo_transaccion=False):
        filtro=[]
        if self.tipo_empresa=='proveedor':
            filtro.append(('type','=','in_invoice'))            
        else:
            filtro.append(('type','=','out_invoice'))            

        filtro.append(('invoice_date','<=',self.date_to))


        if len(self.partner_ids.mapped("id"))!=0:
            filtro.append(('partner_id','in',self.partner_ids.mapped("id")))
        
        lista_partner=self.obtener_listado_partner_facturas(filtro)
        lines=[]


        if not tipo_transaccion:

            for partner in lista_partner:
                filtro.append(('partner_id','=', partner['id']))
                saldo=self.obtener_saldo(filtro)
                if saldo!=0:
                    lines.append({'numero_documento':partner['nombre'],'monto_adeudado':saldo})

                filtro.remove(('partner_id','=', partner['id']))            

            dctTotalGeneral={}
            dctTotalGeneral['numero_documento']='Total General'
            dctTotalGeneral['monto_adeudado']=round(sum(map(lambda x:x['monto_adeudado'],lines)),2)
            dctTotalGeneral['reglon']='total_general'

            lines.append(dctTotalGeneral)

        else:
            dct={'tipo_invoice':'FE','numero_documento':'Factura Electronica','reglon':'detalle'}
            filtro.append(('is_electronic','=',True))

            saldo_facturas_electronica= self.obtener_saldo(filtro)
            dct['monto_adeudado']=saldo_facturas_electronica
            filtro.remove(('is_electronic','=',True))
            filtro.append(('is_electronic','=',False))
            lines.append(dct)
            saldo_facturas= self.obtener_saldo(filtro)
            dct={'tipo_invoice':'FA','numero_documento':'Factura','reglon':'detalle'}
            dct['monto_adeudado']=saldo_facturas
            lines.append(dct)

            dctTotalGeneral={}
            dctTotalGeneral['numero_documento']='Total'
            dctTotalGeneral['monto_adeudado']=round(sum(map(lambda x:x['monto_adeudado'],lines)),2)
            dctTotalGeneral['reglon']='total_detalle'
            lines.append(dctTotalGeneral)

        lista_obj=[]

        for l in lines:
            obj_detalle=self.env['reporte.saldo.empresa'].create(l)
            lista_obj.append(obj_detalle)

        return lista_obj



class ReporteAnticipoDetalle(models.TransientModel):
    _name = "reporte.saldo.empresa"

    tipo_invoice = fields.Char('Tipo de Invoice')
    numero_documento = fields.Char('Nro. Documento')
    secuencia = fields.Char('Secuencia')
    fecha_emision = fields.Date('Fc. Emision')
    fecha_vencimiento = fields.Date('Fc. Vencimiento')
    monto_adeudado = fields.Float('Monto Adeudado')
    observaciones = fields.Char('Observaciones')
    reglon = fields.Char('Reglon')

