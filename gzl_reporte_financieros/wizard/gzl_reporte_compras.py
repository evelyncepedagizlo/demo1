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


class ReporteCompras(models.Model):
    _inherit= "account.fiscal.position"
    apply_retention = fields.Boolean(string='Aplica retencion')


class ReporteCompras(models.TransientModel):
    _name = "report.compras"
    #_inherit = "reporte.proveedor.cliente"account.fiscal.position
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

    def obtener_listado(self):
#######filtro de facturas
        lista_retenciones=[]
        #TAXES = ['ret_vat_b', 'ret_vat_srv', 'ret_ir', 'no_ret_ir'] 
        dateMonthStart = "%s-%s-01" % (self.year_date, self.month)
        dateMonthStart = datetime.strptime(dateMonthStart,'%Y-%m-%d')
        dateMonthEnd=dateMonthStart+relativedelta(months=1, day=1, days=-1)
        
        dateMonthStart = dateMonthStart.strftime("%Y-%m-%d")
        dateMonthEnd = dateMonthEnd.strftime("%Y-%m-%d")
       
        move=self.env['account.move'].search([('invoice_date','>=',dateMonthStart),
            ('invoice_date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('type','in',('in_invoice','in_refund')),('state','=','posted')])
    #raise ValidationError((str((move))))
        cont=0
        dct={}
        num_sub =0.00
        RETS = ['ret_vat_b', 'ret_vat_srv', 'ret_ir', 'no_ret_ir'] 
        for m in move:
            dct={}
            dct['fcaducidad']=' '
            dct['fpago'] = ' '
            dct['id']=m.id
            dct['biva0']=0
            dct['bgrav']=0
            dct['miva']=0
            dct['porctretb'] ='0'
            dct['porctrets'] ='0'
            dct['retserv']='0'
            dct['retb']='0'
            dct['retiva100']='0'
            dct['tipo']='R'
            dct['sustento']= m.sustento_del_comprobante.code or ""
            #raise ValidationError((str((m.create_date))))
            #dct['tipo_id']= m.partner_id.l10n_latam_identification_type_id.name
            dct['ident']= m.partner_id.vat
            dct['razon_social']= m.partner_id.name
            dct['part_rel']= '##'
            dct['tipo_anexo']= 'C'
            dct['serie']=m.l10n_latam_document_number[3:6]
            dct['secuencia']=m.l10n_latam_document_number[6:15]
            if m.auth_number:
                dct['auth_number']=m.auth_number
            else:
                dct['auth_number']= '-'
            dct['date']=str(m.invoice_date)
            dct['create_date']=str(m.create_date.strftime("%Y-%m-%d"))#str(m.create_date)
            dct['base']='?'
            dct['total_venta']=m.amount_total
            if m.state =='posted':
                dct['state']='P'
            else:
                dct['state']= m.state 
            if m.type == 'in_invoice':
                dct['nombre_doc']='Factura Proveedor'
            elif m.type == 'in_refund':
                dct['nombre_doc']='N/C Proveedor'
            dct['num_doc']=m.l10n_latam_document_number
            dct['pais']=m.partner_id.country_id.name
            dct['ret_auth_number']=m.ret_auth_number
            if m.retention_id.date:
                dct['fret']=str(m.retention_id.date)
            else:
                dct['fret']=' '
            if m.retention_id.name:
                dct['retention']=m.retention_id.name
            else:
                dct['retention']=' '
            dct['tipo_id']=m.l10n_latam_document_type_id.code
            if m.invoice_origin:
                dct['origen'] = m.invoice_origin
            else:
                dct['origen'] ='-'
            dct['fcaducidad'] = str(m.invoice_date_due)
            dct['tipo_contrib'] = ' '
            dct['fpago'] = m.method_payment.code
            dct['apply_ret'] = 'NO'
            if m.fiscal_position_id:
                dct['tipo_contrib'] = m.fiscal_position_id.name
                if m.fiscal_position_id.apply_retention:
                    dct['apply_ret'] = 'SI'
            if m.account_cheque_id:
                dct['account_cheque_id'] = m.account_cheque_id.cheque_number
            else:
                dct['account_cheque_id'] ='0'

            num_sub+=m.amount_untaxed
            no_obj = 0.00
            no_ext = 0.00
            no_ret =False
            biva0= 0.00
            bagrav= 0.00
            bn_trf_diff = 0.00
            srv_trf_diff = 0.00
            srv_trff =0.00
            bn_trff = 0.00
            for i in m.invoice_line_ids:
                taxes=i.tax_ids.filtered(lambda l: l.tax_group_id.code in ['novat','vat'])

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
                for k in i.tax_ids:
                    if k.tax_group_id.code =='ret_vat_srv' and bagrav!=0:
                        bn_trf_diff +=  i.price_subtotal
                    if k.tax_group_id.code =='ret_vat_b' and bagrav!=0:
                        srv_trf_diff += i.price_subtotal
                    if k.tax_group_id.code =='ret_vat_b'and biva0!=0:
                        srv_trff+=i.price_subtotal
                    if k.tax_group_id.code =='ret_vat_srv' and biva0!=0:
                        bn_trff+=i.price_subtotal
                    if k.tax_group_id.code =='no_ret_ir' and biva0!=0:   
                        srv_trff += i.price_subtotal
                    if k.tax_group_id.code =='no_ret_ir' and bagrav!=0:   
                        srv_trf_diff += i.price_subtotal
                            
            dct['noobj'] = no_obj
            dct['no_ext'] = no_ext
            dct['bn_trf'] =bn_trff
            dct['srv_trf'] =srv_trff
            dct['srv_trf_dif']=srv_trf_diff
            dct['bn_trf_dif']= bn_trf_diff
            dct['biva0']=biva0
            dct['bgrav']=bagrav
            if m.ret_tax_ids:
                for l in m.ret_tax_ids:
                    
                    #if l.group_id.code != 'ret_ir':
                    dct['miva']=(m.amount_untaxed*0.12)#l.base
                    if l.group_id.code =='ret_vat_b' and l.tax_id.tax_group_id.code =='ret_vat_b':
                        dct['porctretb']=l.tax_id.tarifa
                        dct['retb']='0'
                        dct['porctrets']=l.amount
                        dct['retserv']='0'
                    if l.group_id.code =='ret_vat_srv' and l.tax_id.tax_group_id.code =='ret_vat_srv':
                        dct['porctretb']='0'
                        dct['retb']=l.tax_id.tarifa
                        dct['porctrets']='0'
                        dct['retserv']=l.amount  
                    valor= (-1)*l.amount
                    if valor == l.base:
                        dct['retiva100']=l.base
            #if dct['bgrav']==0 :
            #    dct['biva0']=m.amount_untaxed
            #    dct['bn_trf_dif']= 0
            #    dct['srv_trf_dif']=0
            #raise ValidationError((str((dct['dct']))))
            lista_retenciones.append(dct)
            
            #obj_line=self.env['account.move'].search([('retention_id','=',line.id)], order ='id desc')

        #if num_sub:
        #   raise ValidationError((str((num_sub)))) 
        return lista_retenciones

    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'compras'
        self.xslx_body(workbook, name)
        

        workbook.close()
        file_data.seek(0)
        
        
        name = 'Reporte de Compras'+str(date.today())

        
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
        sheet.write(2,1, 'ANEXO DE COMPRAS ', workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.write(3,1, 'EMISION: '+str(date.today()), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.write(4,1, 'PERIODO: '+str(date_reporte), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
 

        title_main2=['Sustento.','Tipo',    
        'Identificacion','Razon Social','Cont. Especiales',
        'Tipo ID','Parte Rel.','Tip. Anexo','Tip. Comp.',
        'Serie','Secuencial','Autorización','Fch. Emi.'
        ,'Fch. Reg.','Base IVA 0%','Base Grav.',
        'Base no Obj','Base Exenta De Iva','Subtotal','Monto IVA','Monto ICE','Total','Porc. Ret. Bien',
        'Ret. Bien.','Porc. Ret. Serv.','Ret. Serv.']

        #title_main=['isretencion']
        #bold.set_bg_color('b8cce4')#

        ##Titulos
        filtro=[('invoice_date','>=',dateMonthStart),
            ('invoice_date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('type','=','out_invoice')]        
        #taxes= ['ret_vat_srv','ret_vat_b']
        #ret_purchase=self.obtener_listado_retenciones(filtro,'purchase','ret',taxes) 
        fila =8
        for col, head in enumerate(title_main2):
            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
            sheet.write(7, col, head, bold)    
        #sheet.write(7, 26, 'País', bold)
        #sheet.write(7, 27, 'Paraiso Fiscal', bold)
        #sheet.write(7, 28, 'Dbl Tributación', bold)
        #sheet.write(7, 29, 'Suj. Ret.', bold)   
        #sheet.write(7, 30, 'DrawBack', bold)  
        sheet.write(7, 26, 'Ret. IVA 100%', bold)  
        sheet.write(7, 27, 'Contribuyente Suj. Ret.', bold)  
        sheet.write(7, 28, 'Origen', bold)  
        sheet.write(7, 29, 'Estado', bold)  
        sheet.write(7, 30, 'Nombre Docum.', bold)
        #sheet.write(7, 29, 'Docum.', bold)
        sheet.write(7, 31, 'Chq.', bold)
        sheet.write(7, 32, 'Tip S,B,A', bold)
        sheet.write(7, 33, 'Fch. Rete.', bold)
        sheet.write(7, 34, 'Serie Ret..', bold)
        sheet.write(7, 35, 'Pto.Emi.Ret.', bold)
        sheet.write(7, 36, '# Reten.', bold) 
        sheet.write(7, 37, 'Autori. Ret.', bold)
        sheet.write(7, 38, 'Bien. Tarf. Dif 0%', bold)
        sheet.write(7, 39, 'Serv. Tarf. Dif 0%', bold)
        sheet.write(7, 40, 'Acti. Tarf. Dif 0%', bold)
        sheet.write(7, 41, 'Bien. Tarf. 0%', bold)
        sheet.write(7, 42, 'Serv. Tarf. 0%.', bold)
        sheet.write(7, 43, 'Acti. Tarf. 0%', bold)
        sheet.write(7, 44, 'Cajas Banano', bold)
        sheet.write(7, 45, 'Precio Banano', bold)
        sheet.write(7, 46,  'Usuario', bold)
        sheet.write(7, 47, 'Motivo', bold)
        #sheet.write(7, 52, 'F caducidad', bold)
        sheet.write(7, 48, 'Tipo de Contribuyente', bold)
        sheet.write(7, 49, 'Forma de pago', bold)
        #move=self.obtener_listado(filtro) 
        columna=0
        #raise ValidationError((str((move))))
        move=self.obtener_listado() 
        #raise ValidationError((str(( l['miva']))))
        col=0
        cont =0
        if move:
            for l in move:
                #raise ValidationError((str(( l['fcaducidad']))))
                retention =''
                if l['retention']:
                    retention = l['retention']
                columna =0
                sheet.write(fila, columna, str(l['sustento']), format_title2)
                columna+=1
                sheet.write(fila, columna, l['tipo'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['ident'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['razon_social'], format_title2)
                columna+=1
                sheet.write(fila, columna, 'N', format_title2)#quemado porque no se d donde lo toma
                columna+=1
                sheet.write(fila, columna, l['tipo_id'], format_title2)
                columna+=1
                sheet.write(fila, columna,'NO', format_title2)#quemado porque no se d donde lo toma
                columna+=1
                sheet.write(fila, columna, l['tipo_anexo'], format_title2)
                columna+=1
                sheet.write(fila, columna,l['sustento'], format_title2)#conf donde lo dbe tomar
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
                sheet.write(fila, columna, l['biva0'], currency_format)
                columna+=1
                sheet.write(fila, columna,  l['bgrav'], currency_format)
                columna+=1
                sheet.write(fila, columna, l['noobj'] or 0, currency_format)#no se de donde se debe tomar
                columna+=1
                sheet.write(fila, columna,l['no_ext']  or  0, currency_format)#no se de donde se debe tomar
                columna+=1
                sheet.write(fila, columna,'=+SUM(O'+str(fila+1)+':R'+str(fila+1)+')', currency_format)#no se de donde se debe tomar mice subtotal
                columna+=1
                sheet.write(fila, columna, ( l['miva']) or 0, currency_format)
                columna+=1
                sheet.write(fila, columna, 0, currency_format)#no se de donde se debe tomar mice
                columna+=1
                sheet.write(fila, columna,'=+SUM(S'+str(fila+1)+':T'+str(fila+1)+')', currency_format)#no se de donde se debe tomar total
                columna+=1
                sheet.write(fila, columna, l['porctretb'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['retb'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['porctrets'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['retserv'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['retiva100'], format_title2)
                #columna+=1
                #sheet.write(fila, columna, '01', format_title2) #pago local/ext no se de donde se saca
                #columna+=1
                #sheet.write(fila, columna, l['pais'], format_title2)
                #columna+=1
                #sheet.write(fila, columna, 'NO', format_title2)#no
                #columna+=1
                #sheet.write(fila, columna, 'NA', format_title2)#no
                columna+=1
                sheet.write(fila, columna, l['apply_ret'], format_title2)
                #columna+=1
                #sheet.write(fila, columna, 'N', format_title2)
                columna+=1
                sheet.write(fila, columna,  l['origen'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['state'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['nombre_doc'], format_title2)
                #columna+=1
                #sheet.write(fila, columna, l['num_doc'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['account_cheque_id'], format_title2)
                columna+=1
                sheet.write(fila, columna, ' ', format_title2)
                columna+=1
                sheet.write(fila, columna, l['fret'], format_title2)
                columna+=1
                sheet.write(fila, columna, retention[0:2], format_title2)
                columna+=1
                sheet.write(fila, columna, retention[3:5], format_title2)
                columna+=1
                sheet.write(fila, columna, l['retention'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['ret_auth_number'], format_title2)
                columna+=1
                sheet.write(fila, columna, l['bn_trf_dif'] or 0 , currency_format)
                columna+=1
                sheet.write(fila, columna, l['srv_trf_dif'] or 0, currency_format)
                columna+=1
                sheet.write(fila, columna, 0, currency_format)
                columna+=1
                sheet.write(fila, columna, l['srv_trf'] or 0, currency_format)
                columna+=1
                sheet.write(fila, columna, l['bn_trf'] or 0, currency_format)
                columna+=1
                sheet.write(fila, columna, '0', format_title2)
                columna+=1
                sheet.write(fila, columna, '0', format_title2)
                columna+=1
                sheet.write(fila, columna, '0', format_title2)
                columna+=1
                sheet.write(fila, columna, str(self.env.user.name), format_title2)
                columna+=1
                sheet.write(fila, columna, ' ', bold)
                #columna+=1
                #sheet.write(fila, columna,str(l['fcaducidad']), format_title2)
                columna+=1
                sheet.write(fila, columna,str(l['tipo_contrib']), format_title2)
                columna+=1
                sheet.write(fila, columna,str(l['fpago']), format_title2)
                #fila+=1
        
                move2=self.env['account.move'].search([('id','=',l['id']),('invoice_date','>=',dateMonthStart),
                    ('invoice_date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('type','=','in_invoice'),('state','=','posted')])
                for m in move2:
                    if m.ret_tax_ids:
                        for l in m.ret_tax_ids:
                            if l.group_id.code=='ret_ir':
                                columna+=1
                                sheet.write(7, columna, 'Concepto', bold)
                                sheet.write(fila, columna, l.code, format_title2)
                                columna+=1
                                sheet.write(7, columna, 'Base', bold)
                                sheet.write(fila, columna, l.base_ret, currency_format)
                                columna+=1
                                sheet.write(7, columna, 'Porcentaje', bold)
                                sheet.write(fila, columna, str(l.tax_id.tarifa), format_title2)
                                columna+=1
                                sheet.write(7, columna, 'Valor Ret', bold)
                                valor2 = -1*l.amount
                                sheet.write(fila, columna, valor2, currency_format)
                                col =columna
                                #raise ValidationError((str(( col))))
                fila+=1
                col =columna
            sheet.write(fila,14, '=+SUM(O'+str(9)+':O'+str(fila)+')', currency_format)
            sheet.write(fila,15, '=+SUM(P'+str(9)+':P'+str(fila)+')', currency_format)
            sheet.write(fila,16, '=+SUM(Q'+str(9)+':Q'+str(fila)+')', currency_format)
            sheet.write(fila,17, '=+SUM(R'+str(9)+':R'+str(fila)+')', currency_format)
            sheet.write(fila,18, '=+SUM(S'+str(9)+':S'+str(fila)+')', currency_format)
            sheet.write(fila,19, '=+SUM(T'+str(9)+':T'+str(fila)+')', currency_format)
            #sheet.write(fila,36, '=+SUM(AK'+str(9)+':AK'+str(fila)+')', currency_format)
            #sheet.write(fila,37, '=+SUM(AL'+str(9)+':AL'+str(fila)+')', currency_format)
            sheet.write(fila,38, '=+SUM(AM'+str(9)+':AM'+str(fila)+')', currency_format)
            sheet.write(fila,39, '=+SUM(AN'+str(9)+':AN'+str(fila)+')', currency_format)
            sheet.write(fila,40, '=+SUM(AO'+str(9)+':AO'+str(fila)+')', currency_format)
            sheet.write(fila,41, '=+SUM(AP'+str(9)+':AP'+str(fila)+')', currency_format)
            sheet.write(fila,42, '=+SUM(AQ'+str(9)+':AQ'+str(fila)+')', currency_format)
            sheet.write(fila,43, '=+SUM(AR'+str(9)+':AR'+str(fila)+')', currency_format)
            sheet.write(fila,49, '=+SUM(AX'+str(9)+':AX'+str(fila)+')', currency_format)
            sheet.write(fila,51, '=+SUM(AZ'+str(9)+':AZ'+str(fila)+')', currency_format)
            sheet.merge_range('B'+str(fila+1)+':N'+str(fila+1), 'TOTALES', workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))

                

                
                