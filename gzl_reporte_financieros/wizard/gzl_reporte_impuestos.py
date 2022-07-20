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
import itertools





class ReporteAnticipo(models.TransientModel):
    _name = "report.impuestos"
    #_inherit = "reporte.proveedor.cliente"
    cont_fact= fields.Char()
    cont_nv= fields.Char()
    cont_liq= fields.Char()
    fact_emi= fields.Char()
    fact_anu= fields.Char()
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
    def obtener_listado_retenciones(self,filtro,variable,tipo_imp,taxes):
        
        documents = [ 'out_invoice', 
                    'in_invoice', 
                    'out_refund', 
                    'in_refund', 
                    'out_debit',
                    'in_debit',
                    'liq_purchase']
        filtro.append(('type','in',documents))            


#######filtro de facturas
        lista_retenciones=[]
        ingeg=['vat','vat0']
        move=self.env['account.retention'].search(filtro)
        
        dct={}
        dateMonthStart = "%s-%s-01" % (self.year_date, self.month)
        dateMonthStart = datetime.strptime(dateMonthStart,'%Y-%m-%d')
        dateMonthEnd=dateMonthStart+relativedelta(months=1, day=1, days=-1)
        #date_reporte = str(dateMonthStart)+'-'+str(dateMonthEnd)
        dateMonthEnd = dateMonthEnd.strftime("%Y-%m-%d")
        dateMonthEnd = datetime.strptime(dateMonthEnd,"%Y-%m-%d")
        my =  (str(self.month)+'/'+str(self.year_date))
        obj_line=self.env['account.retention.line'].search( [('retention_id','!=',None)],order ='tax_id ')

        code=''
        valor_amount=0
        valor_ret=0
        code_ret=''
        code_group=''
        name_group=''
        name_ret=''
        list=[]
        lista_codigos=(set(obj_line.mapped('code')))
        valores = obj_line.filtered(lambda line:  line.code in lista_codigos and line.tax_id.type_tax_use == variable  and line.retention_id.date.strftime("%Y-%m-%d") >= dateMonthStart.strftime("%Y-%m-%d") and line.retention_id.date.strftime("%Y-%m-%d") <= dateMonthEnd.strftime("%Y-%m-%d")) 
        lista_codigos2=(set(valores.mapped('code')))
        for a in lista_codigos2:
            valores_mes = obj_line.filtered(lambda line:  line.code == a and line.tax_id.type_tax_use == variable and line.retention_id.date.strftime("%Y-%m-%d") >= dateMonthStart.strftime("%Y-%m-%d") and line.retention_id.date.strftime("%Y-%m-%d") <= dateMonthEnd.strftime("%Y-%m-%d")) 

            for m in valores_mes:
                dr = m.retention_id.date.strftime("%Y-%m-%d")
                dr = datetime.strptime(dr,"%Y-%m-%d")
                if dr >= dateMonthStart and dr <= dateMonthEnd and m.group_id.code in taxes :
                    valor_amount+=m.base_ret
                    valor_ret += m.amount
                    name_ret=m.tax_id.name
                    code_ret=m.code
                    code_group=m.group_id.code
                    name_group=m.group_id.name
            dct2={}
            dct2['name_ret']=name_ret
            dct2['cod_ret']=code_ret
            dct2['code_group']=code_group
            dct2['name_group']=name_group
            dct2['amount']=valor_amount
            dct2['valor_retenido']=-1*valor_ret
            if valor_amount > 0:
                lista_retenciones.append(dct2)
                valor_amount = 0.00
                valor_ret = 0.00

        return lista_retenciones
    def obtener_listado_partner_payment(self,filtro,variable,tipo_imp):
        type_doc=''
        if variable =='purchase':
            type_doc = 'in_invoice'
            documents = [ 
                        'in_invoice', 
                        #'out_refund', 
                        #'in_refund', 
                        #'out_debit',
                        'in_debit',
                        'liq_purchase']
            #filtro.append(('type','=','in_invoice'))  
        else:
            type_doc = 'out_invoice'
            documents = [ 
                        'out_invoice', 
                        #'out_refund', 
                        #'in_refund', 
                        'out_debit',
                        #'in_debit',
                        'liq_purchase']
        filtro.append(('type','in',documents))            


#######filtro de facturas
        lista_retenciones=[]
        TAXES = ['ret_vat_b', 'ret_vat_srv', 'ret_ir', 'no_ret_ir'] 
        ingeg=['vat','vat0','novat']
        move=self.env['account.move'].search(filtro)
        code=''
        cont=0
        imp_generado=0.00
        valor_neto=0.00
        amount_v=0.00
        description ='-'
        name = '-'
        code_group = '-'
        name_group = '-'
        tipo_doc='-'
        list=[]
        cont_fact=0
        cont_nv=0
        cont_liq=0
        fact_emi=0
        fact_anu=0
        valor_nc=0.00
        valor_neto_nc =0.00
        impuesto_g_por_fact=0.00
        es_diferente=False
        valor_neto_nc_ni = 0.00
        valor_netoni = 0.00
        imp_generadoni = 0.00
        amount_vni=0.00
        dateMonthStart = "%s-%s-01" % (self.year_date, self.month)
        dateMonthStart = datetime.strptime(dateMonthStart,'%Y-%m-%d')
        dateMonthEnd=dateMonthStart+relativedelta(months=1, day=1, days=-1)
        date_reporte = str(dateMonthStart)+'-'+str(dateMonthEnd)
        dateMonthStart = dateMonthStart.strftime("%Y-%m-%d")
        dateMonthEnd = dateMonthEnd.strftime("%Y-%m-%d")
        valu=[]
        factu =0
        fcont =0
        #lista_move=(set(move.mapped('id')))
        #obj_line=self.env['account.move.line'].search([],order='tax_group_id desc')
        #valores = obj_line.filtered(lambda line:  line.move_id in  lista_move ) 
        #if lista_move:
        #    raise ValidationError((str(lista_move)))
        for l in move:
            obj_line=self.env['account.move.line'].search([('move_id','=',l.id)],order='tax_group_id desc')
            #raise ValidationError((str(obj_line)))
            filtro2=[('invoice_date','>=',dateMonthStart),
            ('invoice_date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('state', '=', 'posted'),('type','in',('out_refund','in_refund')),('reversed_entry_id','=',l.id)]
            move_nc=self.env['account.move'].search(filtro2)
            valor_nc=0.00
            
            for nc in move_nc:
                valor_nc+= nc.amount_total
            no_imp= False
            no_taxes =False
            for line in obj_line:
                #raise ValidationError((str(line.tax_ids.name)))
                dct={}
                if line.tax_ids:
                    no_taxes =True
                    #raise ValidationError((str(line.tax_ids.name)))
                    for i in line.tax_ids:
                        cont_dif=0
                        #obj_tax=self.env['account.tax'].search([('name','=',i.name)], order ='description desc')
                        if tipo_imp =='ie':
                            if variable == i.type_tax_use and i.tax_group_id.code in ingeg :
                                
                                no_imp =True
                                a={}
                                a['num']=line.price_subtotal
                                valu.append(a)
                                if factu != line.move_id:
                                    fcont+=1
                                    if l.type == type_doc:
                                        
                                        if l.state =='posted':
                                            cont_fact+=1
                                            fact_emi+=1
                                        if l.state =='cancel':
                                            fact_anu+=1
                                    if l.type =='liq_purchase':
                                        cont_liq+=1
                                factu =line.move_id
                                cont+=1
                                if cont >1:
                                    if code== i.description:
                                        if valor_nc > 0:
                                            valor_neto_nc=0.00
                                            valor_neto_nc= line.price_subtotal - valor_nc
                                        #impuesto_g_por_fact = l.amount_untaxed -valor_nc
                                        amount_v+= line.price_subtotal
                                        imp_generado=imp_generado+(l.view_amount_total - l.amount_untaxed)
                                        valor_neto+=valor_nc
                                        description = i.description
                                        name = i.name
                                        code_group = i.tax_group_id.code
                                        name_group = i.tax_group_id.name
                                        #if l.type_name:
                                        tipo_doc==l.type
                                    elif code != i.description:
                                        es_diferente=True
                                        cont_dif=cont_dif+1
                                        if cont_dif==1 and amount_v!=0 and code == description:
                                            dct={}
                                            dct['id']=line.id 
                                            dct['move']=line.move_id
                                            dct['name']=name
                                            dct['tipo_doc']=tipo_doc
                                            dct['code']=description
                                            dct['code_group']=code_group
                                            dct['name_group']=name_group
                                            dct['amount']=amount_v
                                            dct['imp_generado']=imp_generado
                                            dct['valor_neto']=valor_neto
                                            lista_retenciones.append(dct)    
                                            cont_dif=0
                                            amount_v=0
                                            imp_generado=0
                                        if description != i.description:
                                            dct={}
                                            dct['id']=line.id 
                                            dct['move']=line.move_id
                                            dct['name']=i.name
                                            dct['tipo_doc']=l.type
                                            dct['code']=i.description
                                            dct['code_group']=i.tax_group_id.code
                                            dct['name_group']=i.tax_group_id.name
                                            dct['amount']=line.price_subtotal
                                            dct['imp_generado']=(l.view_amount_total - l.amount_untaxed)
                                            dct['valor_neto']=valor_nc#l.amount_untaxed - valo_nc
                                            lista_retenciones.append(dct) 
                                else:
                                    #dct={}
                                    amount_v+= line.price_subtotal
                                    valor_neto_nc= line.price_subtotal - valor_nc
                                    description = i.description
                                    name = i.name
                                    code_group = i.tax_group_id.code
                                    name_group = i.tax_group_id.name
                                    if valor_nc > 0:
                                            valor_neto_nc=0.00
                                            valor_neto_nc= line.price_subtotal - valor_nc
                                    valor_neto+=valor_nc
                                code= i.description
                            #elif variable == i.type_tax_use and i.tax_group_id.code in TAXES and idfactu != line.move_id:
                            #    valor_neto_nc_ni= l.amount_untaxed - valor_nc
                            #    amount_vni+= line.price_subtotal
                            #    imp_generadoni=imp_generadoni+(l.view_amount_total - l.amount_untaxed)
                            #    valor_netoni+=valor_neto_nc_ni
                            #idfactu = line.move_id
                #else:
                #    valor_neto_nc_ni= l.amount_untaxed - valor_nc
                #    amount_vni+= line.price_subtotal
                #    imp_generadoni=imp_generadoni+(l.view_amount_total - l.amount_untaxed)
                #    valor_netoni+=valor_neto_nc_ni
            #if not no_imp or not no_taxes : 
            #    if variable =='purchase':
            #        valor_neto_nc_ni=valor_nc# l.amount_untaxed - valor_nc
            #        amount_vni+= l.amount_untaxed
            #        imp_generadoni=imp_generadoni+(l.view_amount_total - l.amount_untaxed)
            #        valor_netoni+=valor_neto_nc_ni
            
        self.cont_fact = str(cont_fact)
        self.cont_liq =str(cont_liq)
        self.fact_emi=str(fact_emi)
        self.fact_anu=str(fact_anu)
        if not es_diferente:
            dct={}
            dct['id']='-' 
            dct['move']='-'
            dct['name']=name
            dct['tipo_doc']=tipo_doc
            dct['code']=description
            dct['code_group']=code_group
            dct['name_group']=name_group
            dct['amount']=amount_v
            dct['imp_generado']=imp_generado
            dct['valor_neto']=valor_neto
            lista_retenciones.append(dct) 
        #if amount_vni > 0.00 and variable =='purchase':
        #    dct={}
        #    dct['id']='-' 
        #    dct['move']='-'
        #    dct['name']='ADQUISICIONES NO OBJETO DE IVA'
        #    dct['tipo_doc']=tipo_doc
        #    dct['code']='531'
        #    dct['code_group']='-'
        #    dct['name_group']='-'
        #    dct['amount']=amount_vni
        #    dct['imp_generado']=imp_generadoni
        #    dct['valor_neto']=valor_netoni
        #    lista_retenciones.append(dct) 
        valorr=0.00
        #if fcont:
        #    raise ValidationError((str(fcont)+'--'))
        return lista_retenciones

        #return lista_retenciones
    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'RETENCIONES'
        self.xslx_body(workbook, name)
        
        name = 'INGRESOS-EGRESOS'
        self.xslx_body_ing_eg(workbook, name)

        workbook.close()
        file_data.seek(0)
        
        
        name = 'Reporte de Impuestos'

        
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
        bold = workbook.add_format({'bold':True,'top':2})
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
        format_title2 = workbook.add_format({'align': 'center', 'bold':False,'border':0 })
        format_titletop = workbook.add_format({'align': 'center', 'bold':False,'top':2 })
        format_titlebottom = workbook.add_format({'align': 'center', 'bold':False,'bottom':2 })
        format_titleleft = workbook.add_format({'align': 'center', 'bold':False,'left':2 })
        format_titlerig = workbook.add_format({'align': 'center', 'bold':False,'right':2 })
        boldr = workbook.add_format({'bold':True,'right':2,'top':2})
        boldl = workbook.add_format({'bold':True,'left':2,'top':2})
        boldl.set_center_across()
        boldr.set_center_across()
        sheet = workbook.add_worksheet(name)
        format_titleleftb = workbook.add_format({'align': 'center', 'bold':False,'left':2,'bottom':2 })
        format_titlerigb = workbook.add_format({'align': 'center', 'bold':False,'right':2 ,'bottom':2})
        sheet.set_portrait()
        sheet.set_paper(9)  # A4

        sheet.set_margins(left=0.4, right=0.4, top=0.4, bottom=0.2)
        sheet.set_print_scale(100)
        sheet.fit_to_pages(1,2)



        dateMonthStart = "%s-%s-01" % (self.year_date, self.month)
        dateMonthStart = datetime.strptime(dateMonthStart,'%Y-%m-%d')
        dateMonthEnd=dateMonthStart+relativedelta(months=1, day=1, days=-1)
        #date_reporte = str(dateMonthStart)+'-'+str(dateMonthEnd)
        dateMonthStart = dateMonthStart.strftime("%Y-%m-%d")
        dateMonthEnd = dateMonthEnd.strftime("%Y-%m-%d")
        date_reporte = str(dateMonthStart)+'-'+str(dateMonthEnd)
        #if dateMonthEnd:
        #    raise ValidationError((str(dateMonthStart)+'-'+str(dateMonthEnd)))
        sheet.merge_range('B1:F1', self.env.company.name.upper(), workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        sheet.merge_range('B2:F2', 'INFORME DE IMPUESTOS SOBRE RENTENCIONES EN COMPRAS Y VENTAS ', workbook.add_format({'bold':True,'border':0,'align': 'center'}))
        sheet.merge_range('B3:F3', 'EMISION: '+str(date.today()), workbook.add_format({'bold':True,'border':0,'align': 'center'}))
        sheet.merge_range('B4:F4', 'PERIODO: '+str(date_reporte), workbook.add_format({'bold':True,'border':0,'align': 'center'}))



        title_main=['Codigo de retención ','Concepto de retención ', 'Base imponible ', 'Valor retenido ']
        #bold.set_bg_color('b8cce4')

        ##Titulos
        filtro=[('date','>=',dateMonthStart),
            ('date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('state', '=', 'done')]        
        taxes= ['ret_vat_srv','ret_vat_b']
        ret_purchase=self.obtener_listado_retenciones(filtro,'purchase','ret',taxes) 
        
        fila=5
        columna=1
        fila_base=0
        fila_tit_renta=0
        fila_tit_iva=0
        if ret_purchase:
            colspan=4
            fila+=1
            fila_tit_iva = fila
            cont =0
            lenret= len(ret_purchase)
            cont_bord=0
            for l in ret_purchase:
                    #fila+=1                    
                #raise ValidationError((str(l)))
                cont_bord+=1
                if l['code_group'] in ['ret_vat_srv','ret_vat_b']:
                    cont =cont+1
                    if cont ==1:
                        sheet.merge_range('B'+str(fila)+':F'+str(fila), 'REPORTE DE RETENCIONES AL IVA  EN COMPRAS ', workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14})) 
                        fila+=1
                        cont_col=0
                        for col, head in enumerate(title_main):
                            cont_col+=1
                            if cont_col==1:
                                sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                                sheet.write(fila, col+1, head, boldl) 
                            elif cont_col==4:
                                sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                                sheet.write(fila, col+1, head, boldr) 
                            else:
                                sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                                sheet.write(fila, col+1, head, bold)   
                        fila_base=fila+1
                    ret_iva= True
                    fila+=1
                    if cont_bord == lenret:
                        sheet.write(fila, columna, str(l['cod_ret']), format_titleleftb)
                   
                        sheet.write(fila, columna+1, l['name_ret'], format_titlebottom)
                        sheet.write(fila, columna+2, l['amount'], format_titlebottom)
                        sheet.write(fila, columna+3, l['valor_retenido'], format_titlerigb)
                    else:
                        sheet.write(fila, columna, str(l['cod_ret']), format_titleleft)

                        sheet.write(fila, columna+1, l['name_ret'], format_title2)
                        sheet.write(fila, columna+2, l['amount'], format_title2)
                        sheet.write(fila, columna+3, l['valor_retenido'], format_titlerig)
                    #sheet.write(fila, columna+4, l['id'], format_title2) imp_generado
            #raise ValidationError((str(fila)))
            fila=fila+2
            format_titleleftb2 = workbook.add_format({'align': 'center', 'bold':False,'left':2,'bottom':2 ,'top':2 })
            format_titlerigb2 = workbook.add_format({'align': 'center', 'bold':False,'right':2 ,'bottom':2,'top':2 })
            format_titlebottom2 = workbook.add_format({'align': 'center', 'bold':False,'bottom':2,'top':2 })
            if len(ret_purchase) > 0:
                sheet.write(fila, 2, 'Total', format_titleleftb2)
                sheet.write(fila,3, '=+SUM(D'+str(fila_base)+':D'+str(fila)+')', format_titlebottom2)
                sheet.write(fila,4, '=+SUM(E'+str(fila_base)+':E'+str(fila)+')', format_titlerigb2)
        cont =0
        fila_base=0
        fila=fila+3
        taxes= ['ret_ir','no_ret_ir']
        ret_purchase2=self.obtener_listado_retenciones(filtro,'purchase','ret',taxes) 
        #if ret_purchase2:
        #    raise ValidationError((str(ret_purchase2)+'--'+str(taxes)))
        lenret= len(ret_purchase2)
        cont_bord=0
        for r in ret_purchase2:
            cont_bord+=1
            #raise ValidationError((str(l)))
            if r['code_group']  in ['ret_ir','no_ret_ir']:
                cont =cont +1 
                if cont ==1:
                    sheet.merge_range('B'+str(fila)+':F'+str(fila), 'REPORTE DE RETENCIONES A LA RENTA  EN COMPRAS ', workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
                    fila+=1
                    cont_col=0
                    for col, head in enumerate(title_main):
                        cont_col+=1
                        if cont_col ==1:
                            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                            sheet.write(fila, col+1, head, boldl)
                        elif cont_col==4:
                            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                            sheet.write(fila, col+1, head, boldr)
                        else:
                            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                            sheet.write(fila, col+1, head, bold)
                    fila_base=fila+1

                ret_renta= True
                fila+=1
                if cont_bord == lenret:
                    sheet.write(fila, columna, str(r['cod_ret']), format_titleleftb)

                    sheet.write(fila, columna+1, r['name_ret'], format_titlebottom)
                    sheet.write(fila, columna+2, r['amount'], format_titlebottom)
                    sheet.write(fila, columna+3, r['valor_retenido'], format_titlerigb)
                else:
                    sheet.write(fila, columna, str(r['cod_ret']), format_titleleft)

                    sheet.write(fila, columna+1, r['name_ret'], format_title2)
                    sheet.write(fila, columna+2, r['amount'], format_title2)
                    sheet.write(fila, columna+3, r['valor_retenido'], format_titlerig)
                #sheet.write(fila, columna+4, l['id'], format_title2)
                #fila+=1 
        fila+=2
        if ret_purchase2:
            format_titleleftb2 = workbook.add_format({'align': 'center', 'bold':False,'left':2,'bottom':2 ,'top':2 })
            format_titlerigb2 = workbook.add_format({'align': 'center', 'bold':False,'right':2 ,'bottom':2,'top':2 })
            format_titlebottom2 = workbook.add_format({'align': 'center', 'bold':False,'bottom':2,'top':2 })
            sheet.write(fila, 2, 'Total', format_titleleftb2)
            sheet.write(fila,3, '=+SUM(D'+str(fila_base)+':D'+str(fila)+')', format_titlebottom2)
            sheet.write(fila,4, '=+SUM(E'+str(fila_base)+':E'+str(fila)+')', format_titlerigb2)            
            fila+=1
            #raise ValidationError((str(fila)))
 
        #######################VENTA#################################################################################333
        taxes=['ret_vat_srv','ret_vat_b']
        ret_venta=self.obtener_listado_retenciones(filtro,'sale','ret',taxes)
        fila_tit_renta=0
        fila_tit_iva=0
        if ret_venta:
            cont=0
            colspan=4
            fila+=1
            fila_tit_iva=fila
            fila_base =0
            lenret= len(ret_venta)
            cont_bord=0
            for p in ret_venta:
                cont_bord+=1
                #raise ValidationError((str(l)))
                if p['code_group'] in ['ret_vat_srv','ret_vat_b']:
                    cont+=1
                    if cont == 1:
                        sheet.merge_range('B'+str(fila)+':F'+str(fila), 'REPORTE DE RETENCIONES AL IVA  EN  VENTAS ', workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
                        fila+=1
                        cont_col=0
                        for col, head in enumerate(title_main):
                            cont_col+=1
                            if cont_col ==1:
                                sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                                sheet.write(fila, col+1, head, boldl)
                            elif cont_col==4:
                                sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                                sheet.write(fila, col+1, head, boldr)
                            else:
                                sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                                sheet.write(fila, col+1, head, bold)       
                        fila_base=fila+1
                    fila+=1
                    #raise ValidationError((str(fila)))
                    if cont_bord == lenret:
                        sheet.write(fila, columna, str(p['cod_ret']), format_titleleftb)
                   
                        sheet.write(fila, columna+1, p['name_ret'], format_titlebottom)
                        sheet.write(fila, columna+2, p['amount'], format_titlebottom)
                        sheet.write(fila, columna+3, p['valor_retenido'], format_titlerigb)
                    else:
                        sheet.write(fila, columna, str(p['cod_ret']), format_titleleft)

                        sheet.write(fila, columna+1, p['name_ret'], format_title2)
                        sheet.write(fila, columna+2, p['amount'], format_title2)
                        sheet.write(fila, columna+3, p['valor_retenido'], format_titlerig)
                    #sheet.write(fila, columna+4, l['id'], format_title2)
                    #fila+=1
            fila+=2
            format_titleleftb2 = workbook.add_format({'align': 'center', 'bold':False,'left':2,'bottom':2 ,'top':2 })
            format_titlerigb2 = workbook.add_format({'align': 'center', 'bold':False,'right':2 ,'bottom':2,'top':2 })
            format_titlebottom2 = workbook.add_format({'align': 'center', 'bold':False,'bottom':2,'top':2 })
            sheet.write(fila, 2, 'Total', format_titleleftb2)
            sheet.write(fila,3, '=+SUM(D'+str(fila_base)+':D'+str(fila)+')', format_titlebottom2)
            sheet.write(fila,4, '=+SUM(E'+str(fila_base)+':E'+str(fila)+')', format_titlerigb2)    
        fila+=1
        cont =0
        fila_base =0
        taxes=['ret_ir','no_ret_ir']
        ret_venta2=self.obtener_listado_retenciones(filtro,'sale','ret',taxes)
        lenret= len(ret_venta)
        cont_bord=0
        for vent in ret_venta2:
            if vent['code_group'] not in ['ret_vat_srv','ret_vat_b']:
                cont_bord+=1
                cont +=1
                if cont == 1:
                    cont_col=0
                    sheet.merge_range('B'+str(fila)+':F'+str(fila), 'REPORTE DE RETENCIONES A LA RENTA  EN  VENTAS ', workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
                    fila+=1
                    for col, head in enumerate(title_main):
                        cont_col+=1
                        if cont_col ==1:
                            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                            sheet.write(fila, col+1, head, boldl) 
                        elif cont_col ==4:
                            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                            sheet.write(fila, col+1, head, boldr) 
                        else:
                            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                            sheet.write(fila, col+1, head, bold) 
                    fila_base=fila+1
                fila+=1
                if cont_bord == lenret:
                    sheet.write(fila, columna, str(vent['cod_ret']), format_titleleftb)
                
                    sheet.write(fila, columna+1, vent['name_ret'], format_titlebottom)
                    sheet.write(fila, columna+2, vent['amount'], format_titlebottom)
                    sheet.write(fila, columna+3, vent['valor_retenido'], format_titlerigb)
                else:
                    sheet.write(fila, columna, str(vent['cod_ret']), format_titleleft)

                    sheet.write(fila, columna+1, vent['name_ret'], format_title2)
                    sheet.write(fila, columna+2, vent['amount'], format_title2)
                    sheet.write(fila, columna+3, vent['valor_retenido'], format_titlerig)
                #sheet.write(fila, columna+4, l['id'], format_title2)
                #fila+=1
                        
        fila+=2
        if ret_venta2:
            format_titleleftb2 = workbook.add_format({'align': 'center', 'bold':False,'left':2,'bottom':2 ,'top':2 })
            format_titlerigb2 = workbook.add_format({'align': 'center', 'bold':False,'right':2 ,'bottom':2,'top':2 })
            format_titlebottom2 = workbook.add_format({'align': 'center', 'bold':False,'bottom':2,'top':2 })
            sheet.write(fila, 2, 'Total', format_titleleftb2)
            sheet.write(fila,3, '=+SUM(D'+str(fila_base)+':D'+str(fila)+')', format_titlebottom2)
            sheet.write(fila,4, '=+SUM(E'+str(fila_base)+':E'+str(fila)+')', format_titlerigb2)  
        sheet.set_column('A:A', 23)
        sheet.set_column('B:B', 23)
        sheet.set_column('H:H', 60)



    def xslx_body_ing_eg(self, workbook, name):
        bold = workbook.add_format({'bold':True,'border':0})
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
        #if dateMonthEnd:
        #    raise ValidationError((str(dateMonthStart)+'-'+str(dateMonthEnd)))
        
        sheet.merge_range('B3:F3', self.env.company.name.upper(), workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        sheet.merge_range('B4:F4', 'INFORME DE IMPUESTOS SOBRE COMPRAS Y VENTAS ', workbook.add_format({'bold':True,'border':0,'align': 'center'}))
        sheet.merge_range('B5:F5', 'EMISION: '+str(date.today()), workbook.add_format({'bold':True,'border':0,'align': 'center'}))
        sheet.merge_range('B6:F6', 'PERIODO: '+str(date_reporte), workbook.add_format({'bold':True,'border':0,'align': 'center'}))
 



        title_main=['RESUMEN DE ADQUISICIONES Y PAGOS ','CODIGO', 'VALOR BRUTO', 'VALOR NETO','IMPUESTO GENERADO']
        #bold.set_bg_color('b8cce4')
        ##Titulos
        filtro=[('invoice_date','>=',dateMonthStart),
            ('invoice_date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('state', '=','posted')]        
        ret_purchase=self.obtener_listado_partner_payment(filtro,'purchase','ie') 
        fila=7
        columna=1
        ret_iva=False
        ret_renta=False
        fila_tit_renta=0
        fila_tit_iva=0
        cont_invoice=0
        if ret_purchase:
            colspan=4
            fila_tit_iva = fila
            #fila+=1
            for l in ret_purchase:
                #raise ValidationError((str(l['tipo_doc'])))
                #if l['code_group'] in ['ret_vat_srv','ret_vat_b']:
                ret_iva= True
                fila+=1
                #if l['tipo_doc'] in ['in_invoice','out_invoice']:
                 #   cont_invoice+=1
                sheet.write(fila, columna, str(l['name']), format_title2)
                #columna+=1
                #raise ValidationError((str(fila)+'=='+str(l['code'])))
                #imp_gen = (l['amount'] - l['valor_neto'])
                sheet.write(fila, columna+1, l['code'], format_title2)
                sheet.write(fila, columna+2, l['amount'], format_title2)#tipo_doc
                sheet.write(fila, columna+3, l['amount'] - l['valor_neto'], format_title2)
                sheet.write(fila, columna+4,'=((E'+str(fila+1)+')*0.12)', format_title2)#valor_neto
            fila_tit_renta = fila +1    
            if ret_iva:
               
               for col, head in enumerate(title_main):
                    sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                    sheet.write(fila_tit_iva-1, col+1, head, bold)
            fila+=2
            sheet.write(fila, columna, 'TOTAL COMPRAS ', format_title2)
            sheet.write(fila, columna+2, '=+SUM(D8:D'+str(fila-1)+')', format_title2)
            sheet.write(fila, columna+3, '=+SUM(E8:E'+str(fila-1)+')', format_title2)
            sheet.write(fila, columna+4, '=+SUM(F8:F'+str(fila-1)+')', format_title2)
            fila=fila +2
            if int(self.cont_fact)>0 or int(self.cont_liq)>0:
                sheet.write(fila, columna, 'RESUMEN DE DOCUMENTOS', workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2,'left':2}))
                sheet.write(fila, columna+1, ' ', workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2}))
            if int(self.cont_fact)>0:
                #raise ValidationError((str(fila)))
                sheet.write(fila,columna+2, 'FACTURAS', workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2}))
                sheet.write(fila,columna+3, str(self.cont_fact), workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2,'right':2}))
            if int(self.cont_liq)>0:
                fila+=1
                sheet.write(fila,columna+2, 'LIQUIDACIONES', workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2}))
                sheet.write(fila,columna+3, str(self.cont_liq), workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2,'right':2}))
        #######################VENTA
        filtro=[('invoice_date','>=',dateMonthStart),
            ('invoice_date','<=',dateMonthEnd),('company_id', '=', self.env.company.id),('state', 'in', ('cancel','posted'))]
        ret_venta=self.obtener_listado_partner_payment(filtro,'sale','ie')
        #if ret_venta:
        #    raise ValidationError((str(ret_venta)))
        fila_tit_renta=0
        fila_tit_iva=0
        cont_invoice=0
        if ret_venta:
            ret_iva=False
            ret_renta=False
            colspan=4
            
            fila_tit_iva=fila
            fila+=2
            for p in ret_venta:
                #raise ValidationError((str(l)))
                #if l['code_group'] in ['ret_vat_srv','ret_vat_b']:
                ret_iva= True
                fila+=1
                #if l['tipo_doc'] in ['in_invoice','out_invoice']:
                 #   cont_invoice+=1
                #raise ValidationError((str(fila)))
                sheet.write(fila, columna, str(p['name']), format_title2)
                sheet.write(fila, columna+1, p['code'], format_title2)
                sheet.write(fila, columna+2, p['amount'], format_title2)
                sheet.write(fila, columna+3, p['amount'] - p['valor_neto'], format_title2)
                sheet.write(fila, columna+4,'=((E'+str(fila+1)+')*0.12)', format_title2)
                    #fila+=1
            fila_tit_renta=fila+1
            title_main=['RESUMEN DE VENTAS - INGRESOS','CODIGO', 'VALOR BRUTO', 'VALOR NETO','IMPUESTO GENERADO']
            if ret_iva:
                
                fila+=1
                for col, head in enumerate(title_main):
                    sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
                    sheet.write(fila_tit_iva+2, col+1, head, bold)
                    
            fila+=2
            sheet.write(fila, columna, 'TOTAL VENTAS ', format_title2)
            sheet.write(fila, columna+2, '=+SUM(D'+str(fila_tit_iva+2)+':D'+str(fila-1)+')', format_title2)
            sheet.write(fila, columna+3, '=+SUM(E'+str(fila_tit_iva+2)+':E'+str(fila-1)+')', format_title2)
            sheet.write(fila, columna+4, '=+SUM(F'+str(fila_tit_iva+2)+':F'+str(fila-1)+')', format_title2)
            fila=fila+2
            if int(self.cont_fact)>0 or int(self.cont_liq)>0:
                sheet.write(fila, columna, 'RESUMEN DE DOCUMENTOS', workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2,'left':2}))
                sheet.write(fila, columna+1, ' ', workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2}))
            #raise ValidationError((str(cont_invoice)))
            if int(self.fact_emi)>0 :
                sheet.write(fila,columna+2, 'FACTURAS EMITIDAS', workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2}))
                sheet.write(fila,columna+3, str(self.fact_emi),  workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2,'right':2}))
            if int(self.fact_anu)>0:
                fila+=1
                sheet.write(fila,columna+2, 'FACTURAS ANULADAS', workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2}))
                sheet.write(fila,columna+3, str(self.fact_anu),  workbook.add_format({'bold':True,'top':2,'align': 'center','bottom':2,'right':2}))
                          
 