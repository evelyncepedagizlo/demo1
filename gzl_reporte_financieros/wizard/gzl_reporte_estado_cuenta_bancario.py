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




class ReporteEstadoCuentaBancario(models.TransientModel):
    _name = "reporte.estado.cuenta.bancario"
    _inherit = "reporte.proveedor.cliente"

    bank_id = fields.Many2one('account.journal',string='Diario')

        
    def obtener_listado_meses_saldo_inicial(self,):
        date_from_formulario=self.date_from
        date_to_formulario=self.date_to

        date_from=date(date_from_formulario.year, date_from_formulario.month, 1)
        date_to=date(date_to_formulario.year, date_to_formulario.month,(calendar.monthrange(date_to_formulario.year, date_to_formulario.month)[1]))

        start_date = datetime(date_from.year, date_from.month, date_from.day)

        end_date = datetime(date_to.year, date_to.month, date_to.day)
        num_months = [i-12 if i>12 else i for i in range(start_date.month, monthdelta(start_date, end_date)+start_date.month+1)]

        print(num_months)

        

        
        monthly_daterange = [start_date + relativedelta(months=+i) for i in range(0,len(num_months))]

        lista_mes=[]
        dct_nombre_mes={
            1:'Enero',
            2:'Febrero',
            3:'Marzo',
            4:'Abril',
            5:'Mayo',
            6:'Junio',
            7:'Julio',
            8:'Agosto',
            9:'Septiembre',
            10:'Octubre',
            11:'Noviembre',
            12:'Diciembre',



        }
        cont=0
        for mes in monthly_daterange:
            dct_mes={}


            dct_mes['nombre']=dct_nombre_mes[mes.month]
 
 
            fecha_actual="%s-%s-01" % (mes.year, mes.month)
            fecha_fin_tarea="%s-%s-%s" %(mes.year, mes.month,(calendar.monthrange(mes.year, mes.month)[1]))


            dct_mes['fecha_inicio']=fecha_actual
            dct_mes['fecha_fin']=fecha_fin_tarea
            dct_mes['anio']=mes.year
            if cont==0 and date_from_formulario.day!=1:
                dct_mes['fecha_inicio']="%s-%s-%s" %(date_from_formulario.year, date_from_formulario.month,date_from_formulario.day)
            if cont==(len(monthly_daterange)-1) and (date_to_formulario.day not in [30,31]):
                dct_mes['fecha_fin']="%s-%s-%s" %(mes.year, mes.month,date_to_formulario.day)

            cont+=1

            lista_mes.append(dct_mes)



        for mes in lista_mes:
            filtro=""" where fecha<'{0}' """.format(mes['fecha_inicio'])

            mes['saldo_inicial']=self.obtener_saldo_inicial(filtro,self.bank_id.id)


        return lista_mes




















    def obtener_saldo_inicial(self,filtro,banco):

        cuentas=self.env['account.journal'].search([('id','=',banco)]).mapped('default_debit_account_id').ids

        sql=self.obtener_sql_de_listas(cuentas)
        query_final=sql + ' select coalesce (sum(debe) - sum(haber),0) as saldo_inicial from lista_movimientos {0}  '.format(filtro)

        
        self.env.cr.execute(query_final)

        saldo=self.env.cr.dictfetchall()
    

        return saldo[0]['saldo_inicial']



    def obtener_saldo_inicial(self,filtro,account_id):

        cuentas=[]
        cuentas.append(account_id)
        sql=self.obtener_sql_de_listas(cuentas)
        query_final=sql + ' select coalesce (sum(debe) - sum(haber),0) as saldo_inicial from lista_movimientos {0}  '.format(filtro)

        
        self.env.cr.execute(query_final)

        saldo=self.env.cr.dictfetchall()
    

        return saldo[0]['saldo_inicial']





            
    def obtener_listado_movimientos(self,filtro,banco):

        cuentas=self.env['account.journal'].search([('id','=',banco)]).mapped('default_debit_account_id').ids

        sql=self.obtener_sql_de_listas(cuentas)
        query_final=sql + ' select * from lista_movimientos {0} order by fecha '.format(filtro)

        self.env.cr.execute(query_final)

        lista_facturas=self.env.cr.dictfetchall()
    

        return lista_facturas

    def obtener_sql_de_listas(self,cuentas):



        #filtro_tipo_documento=" and am.type = ANY (array['in_refund','in_debit','out_refund','out_debit'])"

        # query_facturas=(""" select 
        #                             am.name as secuencia,
        #                             am.l10n_latam_document_number as numero_documento, 
        #                             am.invoice_date as fecha, 
        #                             aj.name as documento_contable, 
        #                             rpb.acc_number as numero_cuenta, 
        #                             am.ref as detalle, 
        #                             rp.name as orden,
        #                             '' as numero_cheque,

        #                             case    when am.type = ANY (array['in_invoice','out_invoice','in_debit','out_debit']) then am.amount_total 
        #                                     else 0 end as debe ,


        #                             case    when am.type = ANY (array['in_refund','out_refund']) then am.amount_total 
        #                                     else 0  end as haber ,

        #                             case    when am.type = ANY (array['in_refund','out_refund']) then 'NCR' 
        #                                     when am.type = ANY (array['in_debit','out_debit']) then 'NDB' 
        #                                     else ''  end as tt ,
        #                             case    
        #                                     when am.state='posted' then 'Si' 
        #                                     else 'No'  end as conciliado 


        #                             from 
        #                                 account_move am, 
        #                                 account_journal aj ,
        #                                 res_partner_bank rpb,
        #                                 res_partner rp 
        #                             where 
        #                                 am.journal_id=aj.id and
        #                                 am.partner_id=rp.id and
        #                                 am.journal_id=ANY (array{0}) {1}  """.format(cuentas,filtro_tipo_documento))




        # query_pagos=(""" select 
        #                             '' as secuencia,
        #                             ap.name as numero_documento, 
        #                             ap.payment_date as fecha, 

        #                             ap.communication as detalle, 

        #                             case    
        #                                     when ap.to_third_party =True  then ap.third_party_name                                       
        #                                     else rp.name  end as orden ,
        #                             ap.check_number as numero_cheque,


        #                             case    when ap.payment_type = ANY   (array['inbound'])  then ap.amount 
        #                                     else 0 end as debe ,


        #                             case    when ap.payment_type = ANY (array['outbound','transfer']) then ap.amount 
        #                                     else 0  end as haber ,


        #                             case    
        #                                     when ap.check_number  is not null  then 'CHQ' 
        #                                     when ap.payment_type = ANY (array['outbound','transfer']) then 'DEB'                                            
        #                                     else ''  end as tt ,


        #                             case    
        #                                     when ap.state='reconciled' then 'Si' 
        #                                     else 'No'  end as conciliado 

        #                             from 
        #                                 account_payment ap, 
        #                                 account_journal aj ,
        #                                 res_partner_bank rpb,
        #                                 res_partner rp 

        #                             where 
        #                                 ap.journal_id=aj.id and
        #                                 ap.partner_id=rp.id and
        #                                 aj.bank_account_id=rpb.id and

        #                                 ap.journal_id=ANY (array{0})   """.format(cuentas))



        query_pagos=(""" select 
                                    '' as secuencia,
                                   ap.name as numero_documento,
                                    aml.date as fecha, 
                                     aj.name as documento_contable, 
                                     rpb.acc_number as numero_cuenta, 
                                   ap.communication as detalle, 
                                   rp.name as orden,
                                     case    
                                             when ap.to_third_party =True  then ap.third_party_name                                       
                                             else rp.name  end as orden ,
                                     ap.check_number as numero_cheque,

                                    aml.debit as  debe ,


                                    aml.credit as haber ,


                                    case    
                                             when ap.check_number  is not null  then 'CHQ' 
                                             when ap.payment_type = ANY (array['outbound','transfer']) then 'DEB'                                            
                                             else ''  end as tt ,


                                    case    
                                            when ap.state='reconciled' then 'Si' 
                                             else 'No'  end as conciliado 

                                    from 
                                        account_move_line aml
                                        LEFT JOIN account_journal aj
                                            ON aml.journal_id=aj.id
                                        LEFT JOIN res_partner rp
                                            ON rp.id =aml.partner_id
                                        LEFT JOIN res_partner_bank rpb
                                            ON rpb.id =aj.bank_account_id                                        
                                        LEFT JOIN account_payment ap
                                           ON  ap.id=aml.payment_id 

                                    where 


                                        aml.account_id=ANY (array{0})   """.format(cuentas))



        #query_final='with lista_movimientos as ( '+query_facturas+' union all ' +query_pagos  +' )'

        
        query_final='with lista_movimientos as ( ' +query_pagos  +' )'



        return query_final
















    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'Estado de Cuenta Bancario'
        self.xslx_body(workbook, name)
        

        workbook.close()
        file_data.seek(0)
        

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


        titulo='ESTADO DE CUENTA BANCARIO '+ self.bank_id.name.upper()

        sheet.merge_range('A5:G5', titulo, workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        bold.set_bg_color('b8cce4')
        
        date_format_title_no_border=workbook.add_format({'align': 'center' ,'bold':True, 'border':0,'text_wrap': True})
        date_format_title_no_border.set_bg_color('b8cce4')
        sheet.write(6,2, 'Fecha Desde:', date_format_title_no_border)
        sheet.write(6,3,self.date_from, workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':0,'text_wrap': True }))
        date_format_title_no_border.set_bg_color('b8cce4')
        sheet.write(6,4, 'Fecha Hasta:', date_format_title_no_border)
        sheet.write(6,5, self.date_to, workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':0,'text_wrap': True }))
        



        

        title_main=['Cuenta','Nombre Cuenta','Fecha', 'No. Doc.','T. T.','No. Cheque','Conciliado','Orden','Detalle','Debe','Haber','Saldo']
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

        lista_meses=self.obtener_listado_meses_saldo_inicial()



        fila=8
        filas_total_meses=[]
        for mes in lista_meses:

            filtro=""" where fecha>='{0}' and fecha<='{1}' """.format(mes['fecha_inicio'],mes['fecha_fin'])
            
            lista_facturas=self.obtener_listado_movimientos(filtro,self.bank_id.id)

            if lista_facturas:
                sheet.write(fila, 0, mes['nombre'] +' ' +str(mes['anio']), workbook.add_format({'bold':True,'border':0}))
                sheet.write(fila, 10, 'Saldo Inicial', workbook.add_format({'bold':True,'border':0}))
                sheet.write(fila, 11, mes['saldo_inicial'],currency_format)
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                for factura in lista_facturas:


                    current_line = next(line)
                    sheet.write(current_line, 0, factura['documento_contable'] or "", body)
                    sheet.write(current_line, 1, factura['numero_cuenta'] or "", body)
                    sheet.write(current_line, 2, factura['fecha'] or "", date_format)
                    sheet.write(current_line, 3, factura['numero_documento'] or "", body)
                    sheet.write(current_line, 4, factura['tt'] or "", body)
                    sheet.write(current_line, 5, factura['numero_cheque'] or "", body)
                    sheet.write(current_line, 6, factura['conciliado'] or "", body)
                    sheet.write(current_line, 7, factura['orden'] or "", body)
                    sheet.write(current_line, 8, factura['detalle'] or "" , body)
                    sheet.write(current_line, 9, abs(factura['debe'])  ,currency_format)
                    sheet.write(current_line, 10,abs(factura['haber'] ) ,currency_format)

                    sheet.write_formula(
                                current_line,11 ,
                                '={0}{1}+'.format(chr(65 +11),current_line)+'{0}{1}-'.format(chr(65 +9),current_line+1)+'{0}{1}'.format(chr(65 +10),current_line+1)
                                , currency_format)



                    fila_current=current_line
                    
                    
                bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
                bold_right.set_bg_color('d9d9d9')

                sheet.merge_range('A{0}:I{0}'.format(fila_current+2), 'Saldo Final {0} {1}'.format(mes['nombre'], mes['anio']), bold_right)

                lista_col_formulas=[9,10]
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

                filas_total_meses.append(fila_current+2)

                fila=fila_current+3
            else:
                fila_current=9
        if fila==8:
            fila_current=8
                
        lista_col_formulas=[9,10]
        
        if len(lista_meses)>0:
            bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
            bold_right.set_bg_color('d9d9d9')

            sheet.merge_range('A{0}:I{0}'.format(fila+3), 'Saldo General', bold_right)



            for columna in lista_col_formulas:

                currency_bold=workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True ,'bold':True})
                currency_bold.set_bg_color('d9d9d9')


                formula='='
                for fila_total in filas_total_meses:
                    formula=formula+'{0}{1}'.format(chr(65 +columna),fila_total)+'+'
                formula=formula.rstrip('+')
                sheet.write(
                            fila+2 ,columna ,
                            formula, currency_bold)



    def print_report_pdf(self):
        return self.env.ref('gzl_reporte_financiero.repote_estado_cuenta_bancario_pdf_id').report_action(self)



        
    def obtenerDatos(self,):

        lista_meses=self.obtener_listado_meses_saldo_inicial()


        lines=[]
        

        for mes in lista_meses:

            filtro=""" where fecha>='{0}' and fecha<='{1}' """.format(mes['fecha_inicio'],mes['fecha_fin'])
            
            lista_facturas=self.obtener_listado_movimientos(filtro,self.bank_id.id)


            lines.append({'documento_contable':mes['nombre'] +' ' +str(mes['anio']),'reglon':'titulo'})
            lines.append({'reglon':'detalle','detalle':'Saldo Inicial','saldo':mes['saldo_inicial']})
            saldo=mes['saldo_inicial']
            for dct in lista_facturas:
                dct.pop('secuencia')
                
                dct['debe']=abs(dct['debe'])
                dct['haber']=abs(dct['haber'])

                dct['reglon']='detalle'
                dct['saldo']=saldo+abs(dct['debe']) - abs(dct['haber'])
                saldo=dct['saldo']
                lines.append(dct)



            dctTotal={}
            dctTotal['detalle']='Total '+ mes['nombre'] +' ' +str(mes['anio'])


            dctTotal['debe']=round(sum(map(lambda x:x['debe'],lista_facturas)),2)
            dctTotal['haber']=round(sum(map(lambda x:x['haber'],lista_facturas)),2)
            dctTotal['reglon']='total_detalle'


            lines.append(dctTotal)
        dctTotalGeneral={}
        dctTotalGeneral['detalle']='Total General'

        dctTotalGeneral['debe']=round(sum(map(lambda x:x['debe'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['haber']=round(sum(map(lambda x:x['haber'],list(filter(lambda x: x['reglon']=='total_detalle', lines)))),2)
        dctTotalGeneral['reglon']='total_general'

        lines.append(dctTotalGeneral)
        lista_obj=[]
        for l in lines:
            obj_detalle=self.env['reporte.estado.cuenta.bancario.detalle'].create(l)
            lista_obj.append(obj_detalle)

        return lista_obj



class ReporteEstadoCuentaDetalleBancario(models.TransientModel):
    _name = "reporte.estado.cuenta.bancario.detalle"


    documento_contable = fields.Char('Cuenta')
    numero_cuenta = fields.Char('Nombre Cuenta')
    fecha = fields.Date('Fecha')
    numero_documento = fields.Char('No. Doc.')
    tt = fields.Char('T. T.')
    numero_cheque = fields.Char('No. Cheque')
    conciliado = fields.Char('Conciliado')
    orden = fields.Char('Orden')
    detalle = fields.Char('Detalle')
    debe = fields.Float('Debe')
    haber = fields.Float('Haber')
    saldo = fields.Float('Saldo')

    
    
    reglon = fields.Char('Reglon')
