# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import AccessError, UserError, ValidationError
import itertools



class ChequesVencimiento(models.TransientModel):
    _name = "reporte.cheques.vencimiento"


    date_from = fields.Date('Desde')
    date_to = fields.Date('Hasta')
    tipo_empresa = fields.Selection([('proveedor','Proveedor'),('cliente','Cliente')])
    conciliado = fields.Selection([('si','Si'),('no','No'),('ambos','Ambos')],default='ambos')
    bank_ids = fields.Many2many('account.journal',string='Banco')

    @api.constrains('date_from','date_to' )
    def validacion_fechas(self):

        if  self.date_from > self.date_to:
            raise ValidationError(("La fecha hasta debe ser mayor a la fecha desde"))



    def obtener_listado_cheques(self,):
        filtro=[('cheque_date','>=',self.date_from),
            ('cheque_date','<=',self.date_to)]

        if self.tipo_empresa=='proveedor':
            filtro.append(('payee_user_id.supplier_rank','>', 0))            
        else:
            filtro.append(('payee_user_id.customer_rank','>', 0))


        if len(self.bank_ids.mapped("id"))!=0:
            filtro.append(('journal_id','in',self.bank_ids.mapped("id")))
        


#######filtro de cheques
        cheques_salientes=self.env['account.cheque'].search(filtro)
        
        lista_cheques=[]

        for cheque in cheques_salientes:
            dct={}
            dct['numero_cheque']=cheque.cheque_number
            dct['banco']=cheque.journal_id.bank_id.name
            dct['monto']=cheque.amount
            dct['fecha_cheque']=cheque.cheque_date
            dct['empresa']=cheque.payee_user_id.name
            dct['terceros']=cheque.third_party_name

            paymments=self.env['account.payment'].search([('payment_method_id.code','=','check_printing'),('check_number','=',cheque.cheque_number)],limit=1)
            dct['numero_documento_pago']=paymments.name or '-'
            dct['fecha_pago']=paymments.date_to or '-'
            dct['descripcion']=paymments.communication or '-'

            if paymments.id and  paymments.state=='reconciled':
                dct['conciliado']='Si'
            else:
                dct['conciliado']='No'

            lista_cheques.append(dct)


        if self.conciliado=='Si':
            lista_cheques = filter(lambda x: x['conciliado']=='Si', lista_cheques)
        elif self.conciliado=='No':
            lista_cheques = filter(lambda x: x['conciliado']=='No', lista_cheques)



        return lista_cheques




    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'Cheques por Vencimiento'
        self.xslx_body(workbook, name)
        
        name = 'Cheques por Vencimiento'
        workbook.close()
        file_data.seek(0)
        
        name = 'Reporte Cheques por Vencimiento'
        
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

    def xslx_body(self,workbook,name,head):
        bold = workbook.add_format({'bold':True,'border':1, 'bg_color':'#CFC8C6'})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':0})
        format_title.set_center_across()
        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        format_title3 = workbook.add_format({'align': 'right', 'bold':False,'border':0 })
        format_title4 = workbook.add_format({'align': 'left', 'bold':False,'border':0 })


        body_right = workbook.add_format({'align': 'right', 'border':1 })
        body_left = workbook.add_format({'align': 'left','border':1})
        sheet = workbook.add_worksheet(name)
        
        
        
    def xslx_body(self, workbook, name):
        bold = workbook.add_format({'bold':True,'border':1})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':1})
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
        sheet.merge_range('A1:B1', 'Fecha del informe:', bold)
        sheet.merge_range('C1:I1', self.create_date, date_format_title)


        sheet.merge_range('A2:I2', 'Reporte de Cheques por Vencimiento', bold)
        sheet.merge_range('A3:C3', 'Desde:', bold)
        sheet.merge_range('D3:E3', self.date_from, date_format_title)      
        sheet.merge_range('A4:C4', 'Hasta:', bold)
        sheet.merge_range('D4:E4', self.date_to, date_format_title)
        title_main=['Fecha de Emisión','No. Cheque','Fecha de Pago','Nro. Documento Pago' ,'Empresa', 'A terceros', 'Descripción','Banco','Valor','Conciliado']

        ##Titulos
        colspan=4
        for col, head in enumerate(title_main):
            sheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), len(head) + 4)
            sheet.write(5, col, head, bold)
        
        lista_cheques=self.obtener_listado_cheques()
        line = itertools.count(start=6)

        for cheque in lista_cheques:

            current_line = next(line)
            sheet.write(current_line, 0, cheque['fecha_cheque'] ,date_format)
            sheet.write(current_line, 1, cheque['numero_cheque'] or "", body)
            sheet.write(current_line, 2, cheque['fecha_pago'] or "", date_format)
            sheet.write(current_line, 3, cheque['numero_documento_pago'] or "", body)
            sheet.write(current_line, 4, cheque['empresa'] or "" ,body)
            sheet.write(current_line, 5, cheque['terceros'] or "" ,body)
            sheet.write(current_line, 6, cheque['descripcion'] or "", body)
            sheet.write(current_line, 7, cheque['banco'] or "", body)
            sheet.write(current_line, 8, cheque['monto'] ,currency_format)
            sheet.write(current_line, 9, cheque['conciliado'] or "", body)

        fila_current=current_line+1
        bold_right=workbook.add_format({'bold':True,'border':1,'align':'right'})
        bold_right.set_bg_color('d9d9d9')

        sheet.merge_range('A{0}:H{0}'.format(fila_current+1), 'Total ', bold_right)

        lista_col_formulas=[8]
        for col in lista_col_formulas:
            col_formula = {
                    'from_col': chr(65 +col),
                    'to_col': chr(65 +col),
                    'from_row': 7,
                    'to_row': fila_current,                
                
                }
            currency_bold=workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True ,'bold':True})
            currency_bold.set_bg_color('d9d9d9')

            sheet.write_formula(
                        fila_current ,col ,
                        '=SUM({from_col}{from_row}:{to_col}{to_row})'.format(
                            **col_formula
                        ), currency_bold)



