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




class ReporteVentas(models.TransientModel):
    _name = "report.ventas"
    #_inherit = "reporte.proveedor.cliente"
    month = fields.Selection([('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'), ('4', 'Abril'),
                          ('5', 'Mayo'), ('6', 'Junio'), ('7', 'Julio'), ('8', 'Agosto'), 
                          ('9', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'), ], 
                         string='Mes')
    year_date = fields.Selection([
						('2020','2020'),
						('2021','2021'),
						('2022','2022'),
						('2023','2023'),
						('2024','2024'),
						('2025','2025'),
						('2026','2026'),
						('2027','2027'),
						('2028','2028'),
						('2029','2029'),
						('2030','2030')
						],string="Año")
    def obtener_listado(self,filtro):
#######filtro de facturas
        lista_retenciones=[]
        #TAXES = ['ret_vat_b', 'ret_vat_srv', 'ret_ir', 'no_ret_ir'] 
        ingeg=['vat','vat0']
        move=self.env['account.move'].search(filtro)
        #raise ValidationError((str((move))))
        cont=0
        dct={}
        for m in move:
            dct={}
            if m.type =='out_invoice':
                dct['tipo']='FAC'
            if m.type =='out_refund':
                dct['tipo']='NCR'
            dct['miva']=0
            dct['biva0']=0
            dct['reiva']=0
            dct['noobj']=0.0
            #raise ValidationError((str((m.create_date))))
            dct['tipo_id']= m.partner_id.l10n_latam_identification_type_id.name
            dct['ident']= m.partner_id.vat
            dct['razon_social']= m.partner_id.name
            dct['part_rel']= 'NO'
            dct['tipo_anexo']= 'V'
            dct['tipo_comp']= m.sustento_del_comprobante.code or ""
            dct['serie']=m.l10n_latam_document_number[3:6]
            dct['secuencia']=m.l10n_latam_document_number[6:15]
            dct['num_ret']= m.retention_id.name or ""
            dct['auth_number']=m.auth_number
            dct['date']=str(m.invoice_date)
            dct['create_date']=str(m.create_date.strftime("%Y-%m-%d"))#str(m.create_date)
            dct['total_venta']=m.amount_total
            if m.state == 'posted':
                dct['state']='P'
            else:
                dct['state']=m.state
            dct['nombre_doc']=m.journal_id.name
            dct['num_doc']=m.l10n_latam_document_number
            
            dct['vr']=m.amount_residual
            dct['sustento']= m.sustento_del_comprobante.code
            if m.invoice_origin:
                dct['origen']= m.invoice_origin
            else:
                dct['origen']=' '
            biva0= 0.00
            bagrav= 0.00
            no_ext =0.00
            no_obj=0.00
            for i in m.invoice_line_ids:
                taxes=i.tax_ids.filtered(lambda l: l.tax_group_id.code in ['vat0','novat','vat'] and l.type_tax_use == 'sale')

                if len(taxes)>0:
                    for f in taxes:
                        if  f.tax_group_id.code =='novat' and f.description == '531':
                            no_obj+= i.price_subtotal
                        elif f.tax_group_id.code =='novat' and f.description == '532':
                            no_ext += i.price_subtotal 
                            
                        else:
                            bagrav += i.price_subtotal 


                else:
                    biva0+=i.price_subtotal
            dct['base_grav']=bagrav
            dct['biva0']=biva0
            dct['miva']=bagrav * 0.12
            dct['noobj']=no_obj
            if m.ret_tax_ids:
                for l in m.ret_tax_ids:
                    if l.group_id.code =='ret_vat_b' or l.group_id.code =='ret_vat_srv':
                        
                        dct['reiva']=l.amount
            #elif not m.ret_tax_ids:
            #    dct['biva0']=m.amount_untaxed
            #    dct['base_grav'] =0
            lista_retenciones.append(dct)
            #obj_line=self.env['account.move'].search([('retention_id','=',line.id)], order ='id desc')


        return lista_retenciones

    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'VENTAS'
        self.xslx_body(workbook, name)
        

        workbook.close()
        file_data.seek(0)
        
        
        name = 'Reporte de Ventas'+str(date.today())

        
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
        bold = workbook.add_format({'bold':True,'border':0})
        bold_no_border = workbook.add_format({'bold':True})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':1})
        format_title_left = workbook.add_format({'bold':True,'border':1,'align': 'left'})
        format_title_left_14 = workbook.add_format({'bold':True,'border':1,'align': 'left','size': 14})
        format_title_center_14 = workbook.add_format({'bold':True,'border':1,'align': 'center','size': 14})


        format_title.set_center_across()
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00','border':0,'text_wrap': True })
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
        format_title2 = workbook.add_format({'align': 'center', 'bold':False,'border':0 })
        sheet = workbook.add_worksheet(name)

        sheet.set_portrait()
        sheet.set_paper(9)  # A4

        sheet.set_margins(left=0.4, right=0.4, top=0.4, bottom=0.2)
        sheet.set_print_scale(100)
        sheet.fit_to_pages(1,2)

        dateMonthStart = "%s-%s-01" % (self.year_date, self.month)
        dateMonthStart = datetime.strptime(dateMonthStart,'%Y-%m-%d')
        dateMonthEnd=dateMonthStart+relativedelta(months=1, day=1, days=-1)
        dateMonthStart = dateMonthStart.strftime("%Y-%m-%d")
        dateMonthEnd = dateMonthEnd.strftime("%Y-%m-%d")
        date_reporte = str(dateMonthStart)+'-'+str(dateMonthEnd)

        
        sheet.write(1,1, self.env.company.name.upper(), workbook.add_format({'bold':True,'border':0,'align': 'left','size': 14}))
        sheet.write(2,1, 'ANEXO DE VENTAS ', workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.write(3,1, 'EMISION: '+str(date.today()), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.write(4,1, 'PERIODO: '+str(date_reporte), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
 

        title_main2=['Tipo Vta.','Tipo Id',	'Identificacion','Razon Social','Parte Rel','Tip. Anexo','Tip. Comp.','Serie','Secuencial','Autorizacion','Fch. Emi.','Fch. Reg','No. Comprobantes','Base IVA 0%','Base Grav.','Base no Obj','Monto IVA','Monto ICE','Total Venta','Ret. IVA.','Ret. Fuente.','Ventas - Retenciones','Num. Ret','Origen','Estado','Nombre Docum.']

        #title_main=['isretencion']
        #bold.set_bg_color('b8cce4')

        ##Titulos
        filtro=[('invoice_date','>=',dateMonthStart),
            ('invoice_date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('type','=','out_invoice')]        
        #taxes= ['ret_vat_srv','ret_vat_b']
        #ret_purchase=self.obtener_listado_retenciones(filtro,'purchase','ret',taxes) 
        fila =8
        for col, head in enumerate(title_main2):
            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
            sheet.write(7, col, head, bold)    
        sheet.write(7, 25, 'Documento', bold)
        sheet.write(7, 26, 'Comentario de la Deuda', bold)
        sheet.write(7, 27, 'Comentario de Pago', bold)
        sheet.write(7, 28, 'isretencion', bold)   
        move=self.obtener_listado(filtro) 
        columna=0
        #raise ValidationError((str((move))))
        if move:
            for l in move:
                columna =0
                sheet.write(fila, columna, str(l['tipo']), format_title2)
                columna+=1
                sheet.write(fila, columna, l['tipo_id'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['ident'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['razon_social'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['part_rel'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['tipo_anexo'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['tipo_comp'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['serie'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['secuencia'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['auth_number'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['date'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['create_date'], format_title2)
                columna+=1
                sheet.write(fila, columna, 1, format_title2)
                columna+=1
                sheet.write(fila, columna, l['biva0'], currency_format)
                columna+=1
                sheet.write(fila, columna, l['base_grav'], currency_format)
                columna+=1
                sheet.write(fila, columna, l['noobj'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['miva'], currency_format)
                columna+=1
                sheet.write(fila, columna, '--', format_title2)#mice
                columna+=1
                sheet.write(fila, columna, '=+SUM(N'+str(fila+1)+':Q'+str(fila+1)+')', currency_format)#total venta 
                columna+=1
                sheet.write(fila, columna, (-1*l['reiva']), currency_format)
                columna+=1
                sheet.write(fila, columna, 0, currency_format)
                columna+=1
                sheet.write(fila, columna, '=(S'+str(fila+1)+'-T'+str(fila+1)+'-U'+str(fila+1)+')', currency_format)
                columna+=1
                sheet.write(fila, columna,  l['num_ret'], format_title2)
                columna+=1
                sheet.write(fila, columna,  l['origen'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['state'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['nombre_doc'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['num_doc'], format_title2)
                fila+=1
        filtro=[('invoice_date','>=',dateMonthStart),
            ('invoice_date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('type','=','out_refund')]  
        move=self.obtener_listado(filtro) 
        columna=0
        if move:
            for l in move:
                columna =0
                sheet.write(fila, columna, str(l['tipo']), format_title2)
                columna+=1
                sheet.write(fila, columna, l['tipo_id'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['ident'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['razon_social'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['part_rel'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['tipo_anexo'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['tipo_comp'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['serie'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['secuencia'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['auth_number'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['date'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['create_date'], format_title2)
                columna+=1
                sheet.write(fila, columna, 1, format_title2)
                columna+=1
                sheet.write(fila, columna, l['biva0'], currency_format)
                columna+=1
                sheet.write(fila, columna, l['base_grav'], currency_format)
                columna+=1
                sheet.write(fila, columna, l['no_obj'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['miva'], currency_format)
                columna+=1
                sheet.write(fila, columna, '-', format_title2)
                columna+=1
                sheet.write(fila, columna, '=+SUM(N'+str(fila+1)+':Q'+str(fila+1)+')', currency_format)#total venta 
                columna+=1
                sheet.write(fila, columna, (-1*l['reiva']), currency_format)
                columna+=1
                sheet.write(fila, columna, 0, currency_format)
                columna+=1
                sheet.write(fila, columna, '=(S'+str(fila+1)+'-T'+str(fila+1)+'-U'+str(fila+1)+')', currency_format)
                columna+=1
                sheet.write(fila, columna,  l['num_ret'], format_title2)
                columna+=1
                sheet.write(fila, columna,  l['origen'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['state'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['nombre_doc'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['num_doc'], format_title2)
                fila+=1
        sheet.write(fila,12, '=+SUM(M'+str(9)+':M'+str(fila)+')', currency_format)
        sheet.write(fila,13, '=+SUM(N'+str(9)+':N'+str(fila)+')', currency_format)
        sheet.write(fila,14, '=+SUM(O'+str(9)+':O'+str(fila)+')', currency_format)
        sheet.write(fila,15, '=+SUM(P'+str(9)+':P'+str(fila)+')', currency_format)
        sheet.write(fila,16, '=+SUM(Q'+str(9)+':Q'+str(fila)+')', currency_format)
        sheet.write(fila,17, '=+SUM(R'+str(9)+':R'+str(fila)+')', currency_format)
        sheet.write(fila,18, '=+SUM(S'+str(9)+':S'+str(fila)+')', currency_format)
        sheet.write(fila,19, '=+SUM(T'+str(9)+':T'+str(fila)+')', currency_format)
        sheet.write(fila,20, '=+SUM(U'+str(9)+':U'+str(fila)+')', currency_format)
        sheet.write(fila,21, '=+SUM(V'+str(9)+':V'+str(fila)+')', currency_format)
        #sheet.write(fila,22, '=+SUM(W'+str(9)+':W'+str(fila)+')', currency_format)
        sheet.merge_range('B'+str(fila+1)+':L'+str(fila+1), 'TOTALES', workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
