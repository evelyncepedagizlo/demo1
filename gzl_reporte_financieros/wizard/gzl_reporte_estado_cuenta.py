
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




class ReporteEstadoCuenta(models.TransientModel):
    _name = "reporte.estado.cuenta"
    _inherit = "reporte.proveedor.cliente"


        
    def obtener_listado_partner_saldo_inicial(self,filtro):
        

        partners=self.obtener_listado_partner_facturas(filtro)
        filtro_sql=""" where fecha_emision<'{0}' """.format(self.date_from)

        for partner in partners:

            partner['saldo_inicial']=self.obtener_saldo_inicial(filtro_sql,partner['id'])


        return partners


    def obtener_saldo_inicial(self,filtro,partner_id):

        sql=self.obtener_sql_de_listas(partner_id)
        query_final=sql + ' select coalesce (sum(debe) - sum(haber),0) as saldo_inicial from lista_documentos {0}  '.format(filtro)
        self.env.cr.execute(query_final)

        saldo=self.env.cr.dictfetchall()
    

        return saldo[0]['saldo_inicial']







            
    def obtener_listado_facturas(self,filtro,partner_id):


        sql=self.obtener_sql_de_listas(partner_id)
        query_final=sql + ' select * from lista_documentos {0} order by fecha_emision,create_date '.format(filtro)
        self.env.cr.execute(query_final)

        lista_facturas=self.env.cr.dictfetchall()

        for factura in lista_facturas:
            if factura.get('tipo_invoice')!='' and factura.get('tipo_referencia') in ['NCR','NDB']:
                obj=self.env['account.move'].browse(int(factura['tipo_invoice']))
                factura['tipo_invoice']=obj.l10n_latam_document_number
            if factura.get('tipo_referencia') in ['PAG']:
                obj=self.env['account.payment'].browse(factura['id'])
                if obj.state=='posted':
                    if len(obj.reconciled_invoice_ids)>0:
                        factura['tipo_invoice']=str(obj.invoice_ids.mapped('l10n_latam_document_number')).replace('[','').replace(']','').replace("'",'')
                if obj.state=='reconciled':
                        factura['tipo_invoice']=str(obj.reconciled_invoice_ids.mapped('l10n_latam_document_number')).replace('[','').replace(']','').replace("'",'')

        return lista_facturas

    def obtener_sql_de_listas(self,partner_id):


        if self.tipo_empresa=='proveedor':
            filtro_tipo_empresa=" and am.type = ANY (array['in_invoice','in_refund','in_debit','liq_purchase'])"
        else:
            filtro_tipo_empresa=" and am.type = ANY (array['out_invoice','out_refund','out_debit'])"

        query_facturas=(""" select 
                                    am.id,
                                    'account.move' as modelo,
                                    am.create_date ,
                                    am.name as secuencia,
                                    am.nombre_mostrar as numero_documento, 
                                    am.invoice_date as fecha_emision, 
                                    am.invoice_date_due as fecha_vencimiento, 
                                    aj.name as documento_contable, 
                                    abs(am.amount_residual) as monto_adeudado, 
                                    abs(am.amount_total) as monto_total, 
                                    am.ref as referencia, 
                                    am.narration as observaciones, 

                                    case    when am.type = ANY (array['in_debit','out_debit']) then coalesce(abs(am.amount_total),0) 
                                            when am.type = ANY (array['in_invoice','out_invoice']) then coalesce(abs(am.view_amount_total),0) 

                                            else 0 end as debe ,


                                    case    when am.type = ANY (array['in_refund','out_refund']) then abs(am.amount_total )
                                            else 0  end as haber ,


                                    case    when am.type = ANY (array['in_refund','out_refund']) then  coalesce(am.reversed_entry_id,0) ::VARCHAR
                                            when am.type = ANY (array['in_debit','out_debit']) then  coalesce(am.debit_origin_id,0) :: VARCHAR
                                            else ''  end as tipo_invoice ,

                                    case    when am.type = ANY (array['in_refund','out_refund']) then 'NCR' 
                                            when am.type = ANY (array['in_debit','out_debit']) then 'NDB' 
                                            when am.type = ANY (array['out_invoice','in_invoice']) and am.is_electronic=True then 'FE'
                                            when am.type = ANY (array['out_invoice','in_invoice']) and am.is_electronic=False then 'FAC'
                                            else ''  end as tipo_referencia 



                                    from 
                                        account_move am, 
                                        account_journal aj 
                                    where 
                                        am.journal_id=aj.id and
                                        am.state='posted' and

                                        am.partner_id={0} {1}  """.format(partner_id,filtro_tipo_empresa))



        if self.tipo_empresa=='proveedor':
            filtro_tipo_empresa_pago=" and ap.partner_type = 'supplier'"
        else:
            filtro_tipo_empresa_pago=" and ap.partner_type = 'customer'"

        query_pagos=(""" select 
                                    ap.id,
                                    'account.payment' as modelo,
                                    ap.create_date ,
                                    '' as secuencia,
                                    ap.name as numero_documento, 
                                    ap.payment_date as fecha_emision, 
                                    ap.date_to as fecha_vencimiento, 
                                    aj.name as documento_contable, 

                                    case    when ap.tipo_transaccion = 'Pago' and parent_id is null  then 0
                                            when ap.tipo_transaccion = 'Pago' and parent_id is not null  then ap.amount_residual
                                            when ap.tipo_transaccion = 'Anticipo'  then ap.amount
                                            else  0 end as monto_adeudado ,


                                    abs(ap.amount) as monto_total, 
                                    ap.communication as referencia, 
                                    '' as observaciones, 

                                    0 as debe ,

                                     abs(ap.amount)    as haber ,

                                    '' as tipo_invoice ,

                                    case    when ap.tipo_transaccion = 'Pago' and parent_id is null then 'PAG' 
                                            when ap.tipo_transaccion = 'Pago' and parent_id is not null then 'APLIC. ANTICI' 
                                            when ap.tipo_transaccion = 'Anticipo' then 'ANTICI' 
                                            else ''  end as tipo_referencia 


                                    from 
                                        account_payment ap, 
                                        account_journal aj 
                                    where 
                                        ap.journal_id=aj.id and

                                        ap.state=ANY (array['reconciled','posted', 'anticipo']) and


                                        ap.partner_id={0} {1}   """.format(partner_id,filtro_tipo_empresa_pago))


        query_pagos_anticipo=(""" select 
                                    apav.id,
                                    'account.payment.anticipo.valor' as modelo,
                                    apav.create_date ,
                                    '' as secuencia,
                                    ap.name as numero_documento, 
                                    apav."fechaAplicacion"::date as fecha_emision, 
                                     apav."fechaAplicacion"::date as fecha_vencimiento, 
                                    aj.name as documento_contable, 

                                    0 as monto_adeudado ,


                                    abs(apav.aplicacion_anticipo) as monto_total, 
                                    ap.communication as referencia, 
                                    '' as observaciones, 

                                    apav.aplicacion_anticipo as debe ,

                                     0    as haber ,

                                    '' as tipo_invoice ,

                                    'TRA' as tipo_referencia 


                                    from 
                                        account_payment ap , 
                                        account_payment_anticipo_valor apav, 
                                        account_journal aj 


                                    where 
                                        ap.id=apav.payment_id and
                                        ap.journal_id=aj.id and

                                        ap.state=ANY (array['reconciled','posted', 'anticipo']) and


                                        ap.partner_id={0} {1}   """.format(partner_id,filtro_tipo_empresa_pago))
















        if self.tipo_empresa=='proveedor':
            filtro_tipo_retencion=" and ar.in_type  = ANY (array['ret_in_invoice', 'ret_liq_purchase'])"
        else:
            filtro_tipo_retencion=" and ar.in_type  = ANY (array['ret_out_invoice'])"




        query_retenciones=("""select 
                                    ar.id,
                                    'account.retention' as modelo,
                                    ar.create_date ,
                                    '' as secuencia,
                                    ar.name as numero_documento, 
                                    ar.date as fecha_emision, 
                                    am.invoice_date_due as fecha_vencimiento, 
                                    aj.name as documento_contable, 
                                    0 as monto_adeudado, 
                                    abs(ar.amount_total) as monto_total, 


                                    am.ref as referencia, 
                                    am.narration as observaciones, 

                                    0 debe ,


                                    abs(ar.amount_total) haber ,

                                    am.l10n_latam_document_number as tipo_invoice ,

                                    'RET' as tipo_referencia 



                                    from 
                                        account_retention ar,
                                        account_move am, 
                                        account_journal aj 
                                    where 
                                        ar.invoice_id=am.id and
                                        am.journal_id=aj.id and

                                        ar.state='done' and

                                        ar.partner_id={0} {1} """.format(partner_id,filtro_tipo_retencion))



        query_final='with lista_documentos as ( '+query_facturas+' union all ' +query_pagos +' union all '+query_retenciones +' union all '+   query_pagos_anticipo +' )'

    

        return query_final
















    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'Estado de Cuenta'
        self.xslx_body(workbook, name)
        

        workbook.close()
        file_data.seek(0)
        
        if self.tipo_empresa=='proveedor':
            name = 'Estado de Cuenta Proveedores {0}'.format(self.env.company.name)
        else:
            name = 'Estado de Cuenta Clientes {0}'.format(self.env.company.name)

        
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
        sheet.set_landscape()
        sheet.set_paper(9)  # A4

        sheet.set_margins(left=0.4, right=0.4, top=0.4, bottom=0.2)
        sheet.set_print_scale(100)
        sheet.fit_to_pages(1,2)











        
        sheet.merge_range('A1:G1', self.env.company.name.upper(), workbook.add_format({'bold':True,'border':0,'align': 'left','size': 14}))
        sheet.merge_range('A2:G2', 'RUC: '+self.env.company.vat, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A3:G3', 'Dirección: '+self.env.company.street, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A4:G4', 'Teléfono: '+self.env.company.phone, workbook.add_format({'bold':True,'border':0,'align': 'left'}))


        if self.tipo_empresa=='proveedor':
            titulo = 'Estado de Cuenta Proveedores '
        else:
            titulo = 'Estado de Cuenta Clientes'



        sheet.merge_range('A5:G5', titulo, workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        bold.set_bg_color('b8cce4')
        
        date_format_title_no_border=workbook.add_format({'align': 'center' ,'bold':True, 'border':0,'text_wrap': True})
        date_format_title_no_border.set_bg_color('b8cce4')
        sheet.write(6,2, 'Fecha Desde:', date_format_title_no_border)
        sheet.write(6,3,self.date_from, workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':0,'text_wrap': True }))
        date_format_title_no_border.set_bg_color('b8cce4')
        sheet.write(6,4, 'Fecha Hasta:', date_format_title_no_border)
        sheet.write(6,5, self.date_to, workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':0,'text_wrap': True }))
        



        

        title_main=['Fecha Emisión','Tipo','Nro. Documento', 'Tipo de Ref.','Referencia','Docu. Count','Concepto','Saldo Docum','Debe','Haber','Saldo']
        bold.set_bg_color('b8cce4')

        ##Titulos
        colspan=4
        for col, head in enumerate(title_main):
            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 7)
            sheet.write(7, col, head, bold)

            
        sheet.set_column('B:B', 8)
        sheet.set_column('C:C', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 50)


        filtro_partner=[]
        if self.tipo_empresa=='proveedor':
            filtro_partner.append(('type','in',['in_invoice','in_refund','in_debit']))            
        else:
            filtro_partner.append(('type','in',['out_invoice','out_refund','out_debit']))            

        if len(self.partner_ids.mapped("id"))!=0:
            filtro_partner.append(('partner_id','in',self.partner_ids.mapped("id")))


        lista_partner=self.obtener_listado_partner_saldo_inicial(filtro_partner)



        fila=8
        filas_total_partner=[]
        for partner in lista_partner:
            filtro=""" where fecha_emision>='{0}' and fecha_emision<='{1}' """.format(self.date_from,self.date_to)
            
            lista_facturas=self.obtener_listado_facturas(filtro,partner['id'])

            if lista_facturas:
                sheet.write(fila, 0, partner['nombre'], workbook.add_format({'bold':True,'border':0}))
                sheet.write(fila, 9, 'Saldo Inicial', workbook.add_format({'bold':True,'border':0}))
                sheet.write(fila, 10, partner['saldo_inicial'],currency_format)
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                for factura in lista_facturas:


                    current_line = next(line)
                    sheet.write(current_line, 0, factura['fecha_emision'] or "", date_format)
                    sheet.write(current_line, 1, factura['tipo_referencia'] or "", body)
                    sheet.write(current_line, 2, factura['numero_documento'] or "", body)
                    sheet.write(current_line, 3, factura['tipo_invoice'] or "", body)
                    sheet.write(current_line, 4, factura['referencia'] or "", body)
                    sheet.write(current_line, 5, factura['documento_contable'] or "", body)
                    sheet.write(current_line, 6, factura['observaciones'] or "", body)
                    sheet.write(current_line, 7, abs(factura['monto_adeudado']) , currency_format)
                    sheet.write(current_line, 8, abs(factura['debe'])  ,currency_format)
                    sheet.write(current_line, 9,abs(factura['haber'])  ,currency_format)

                    sheet.write_formula(
                                current_line,10 ,
                                '={0}{1}+'.format(chr(65 +10),current_line)+'{0}{1}-'.format(chr(65 +8),current_line+1)+'{0}{1}'.format(chr(65 +9),current_line+1)
                                , currency_format)



                    fila_current=current_line
                    
                    
                bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
                bold_right.set_bg_color('d9d9d9')

                sheet.merge_range('A{0}:G{0}'.format(fila_current+2), 'Total '+ partner['nombre'], bold_right)

                lista_col_formulas=[7,8,9]
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


                
        lista_col_formulas=[7,8,9]
        
        if len(lista_partner)>0:
            bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
            bold_right.set_bg_color('d9d9d9')

            sheet.merge_range('A{0}:G{0}'.format(fila), 'Total General', bold_right)



            for columna in lista_col_formulas:

                currency_bold=workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True ,'bold':True})
                currency_bold.set_bg_color('d9d9d9')


                formula='='
                for fila_total in filas_total_partner:
                    formula=formula+'{0}{1}'.format(chr(65 +columna),fila_total)+'+'
                formula=formula.rstrip('+')
                sheet.write(
                            fila-1 ,columna ,
                            formula, currency_bold)



    def print_report_pdf(self):
        return self.env.ref('gzl_reporte_financiero.repote_estado_cuenta_pdf_id').report_action(self)



        
    def obtenerDatos(self,):

        filtro_partner=[]
        if self.tipo_empresa=='proveedor':
            filtro_partner.append(('type','in',['in_invoice','in_refund','in_debit']))            
        else:
            filtro_partner.append(('type','in',['out_invoice','out_refund','out_debit']))            

        if len(self.partner_ids.mapped("id"))!=0:
            filtro_partner.append(('partner_id','in',self.partner_ids.mapped("id")))


        lista_partner=self.obtener_listado_partner_saldo_inicial(filtro_partner)
        lines=[]
        

        for partner in lista_partner:

            filtro=""" where fecha_emision>='{0}' and fecha_emision<='{1}' """.format(self.date_from,self.date_to)
            
            lista_facturas=self.obtener_listado_facturas(filtro,partner['id'])



            lines.append({'tipo_invoice':partner['nombre'],'reglon':'titulo'})
            lines.append({'reglon':'detalle','numero_documento':'Saldo Inicial','saldo':partner['saldo_inicial']})
            saldo=partner['saldo_inicial']
            for dct in lista_facturas:
                dct.pop('secuencia')
                dct.pop('fecha_vencimiento')
                dct.pop('modelo')
                dct['monto_adeudado']=abs(dct['monto_adeudado'])
                dct['debe']=abs(dct['debe'])
                dct['haber']=abs(dct['haber'])


                dct['reglon']='detalle'
                dct['saldo']=saldo+abs(dct['debe']) - abs(dct['haber'])
                saldo=dct['saldo']
                lines.append(dct)



            dctTotal={}
            dctTotal['observaciones']='Total '+ partner['nombre']




            dctTotal['monto_adeudado']=round(sum(map(lambda x:x['monto_adeudado'],lista_facturas)),2)
            dctTotal['debe']=round(sum(map(lambda x:x['debe'],lista_facturas)),2)
            dctTotal['haber']=round(sum(map(lambda x:x['haber'],lista_facturas)),2)
            dctTotal['reglon']='total_detalle'


            lines.append(dctTotal)
        dctTotalGeneral={}
        dctTotalGeneral['observaciones']='Total General'

        dctTotalGeneral['monto_adeudado']=round(sum(map(lambda x:x['monto_adeudado'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['debe']=round(sum(map(lambda x:x['debe'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['haber']=round(sum(map(lambda x:x['haber'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['reglon']='total_general'

        lines.append(dctTotalGeneral)
        lista_obj=[]
        for l in lines:
            obj_detalle=self.env['reporte.estado.cuenta.detalle'].create(l)
            lista_obj.append(obj_detalle)

        return lista_obj



class ReporteAnticipoDetalle(models.TransientModel):
    _name = "reporte.estado.cuenta.detalle"

    fecha_emision = fields.Date('Fc. Emision')
    tipo_invoice = fields.Char('Tipo Invoice')
    numero_documento = fields.Char('Nro. Documento')
    tipo_referencia = fields.Char('Tipo refencia')
    referencia = fields.Char('Referencia')
    documento_contable = fields.Char('Documento Contable')
    observaciones = fields.Char('Observaciones')

    monto_total = fields.Float('Monto Total')
    monto_adeudado = fields.Float('Monto Adeudado')
    debe = fields.Float('Debe')
    haber = fields.Float('Haber')
    saldo = fields.Float('Saldo')
    

    reglon = fields.Char('Reglon')




