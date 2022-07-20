# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from datetime import date, timedelta
import xlsxwriter
from io import BytesIO
import base64

class ReportPaymentFile(models.TransientModel):
    _name = "report.payment.file"

    def report_payment_file_data(self):
        dct={}
        lis=[]
        employee_ids = self.env['hr.employee']
        hr_employee = employee_ids.search([('active','=',True),('identification_id','!=',False)],order='lastname')
        
        valor=''
        for emp in hr_employee:
            contract = self.env['hr.contract'].search([('employee_id','=',emp.id),('state','=','open')], limit=1)
            if contract:
                today = date.today()
                p = self.env['hr.payslip.line'].search([('employee_id','=',emp.id),('code','=','NET')])
                for pay in p:
                    if pay:
                        if (pay.date_from).month==today.month and (pay.date_from).year==today.year:
                            valor = pay.total
                            if emp.type_identifier=='cedula':
                                tipo_identificacion='C'
                            elif emp.type_identifier=='pasaporte':
                                tipo_identificacion='P' 
                            else:
                                tipo_identificacion=''
                            if emp.res_bank_id.is_bank_gy==True:
                                bg =True
                            else:
                                bg=False
                            dct = {'bg':bg,
                                            'banco': emp.res_bank_id.name or '',
                                            'code': emp.res_bank_id.code or '',
                                            'tipo_cta': emp.account_type or '',
                                            'nro_cta': emp.number_bank or '',
                                            'valor': (str(valor)).replace('.','').replace(',',''),
                                            'beneficiario': str(emp.lastname) +' '+ str(emp.firstname),
                                            'num_identificacion': emp.identification_id or '',
                                            'tipo_identificacion':tipo_identificacion or '',
                                            } 
                            valor=''
                            lis.append(dct)
        return lis
        

    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        
        name = 'BG'
        self.xslx_body_bg(workbook,name)
        
        name = 'Otros Bancos'
        self.xslx_body_other(workbook,name)
        
        workbook.close()
        file_data.seek(0)
        
        name = 'Archivo de Pago'
        
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


    def xslx_body_bg(self,workbook,name):
        bold = workbook.add_format({'bold':True,'border':1, 'bg_color':'#CFC8C6'})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':1})
        format_title.set_center_across()
        body_left = workbook.add_format({'align': 'left','border':1})
        body_right = workbook.add_format({'align': 'right','border':1})
        body_center = workbook.add_format({'align': 'center','border':1})
        sheet = workbook.add_worksheet(name)
        sheet.set_column('A:A', 16)
        sheet.set_column('B:B', 14)
        sheet.set_column('C:C', 14)
        sheet.set_column('D:D', 45)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 87)
        data = self.report_payment_file_data()
      
        sheet.write(1, 0, 'TIPO DE CUENTA', format_title)
        sheet.write(1, 1, 'CUENTA BG', format_title)
        sheet.write(1, 2, 'VALOR', format_title)
        sheet.write(1, 3, 'NOMBRE BENEFICIARIO', format_title)
        sheet.write(1, 4, 'MOTIVO', format_title)
        sheet.write(1, 5, 'CUERPO DEL ARCHIVO DE TEXTO', format_title)
        row=2
        for l in data:
            ca = l['tipo_cta']+'00'+l['nro_cta']+'0000000000'+l['valor']+'XXY01'+'      '+l['beneficiario']+'      '+'CV2'
            if l['bg']==True:
                sheet.write(row, 0, l['tipo_cta'], body_center)
                sheet.write(row, 1, l['nro_cta'], body_center)
                sheet.write(row, 2, l['valor'], body_right)
                sheet.write(row, 3, l['beneficiario'] , body_left)
                sheet.write(row, 4, 'CV2', body_left)
                sheet.write(row, 5, ca, body_left)
                row+=1

                
    def xslx_body_other(self,workbook,name):
        bold = workbook.add_format({'bold':True,'border':1, 'bg_color':'#CFC8C6'})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':1})
        format_title.set_center_across()
        body_left = workbook.add_format({'align': 'left','border':1})
        body_right = workbook.add_format({'align': 'right','border':1})
        body_center = workbook.add_format({'align': 'center','border':1})
        sheet = workbook.add_worksheet(name)
        sheet.set_column('A:A', 16)
        sheet.set_column('B:B', 14)
        sheet.set_column('C:C', 19)
        sheet.set_column('D:D', 14)
        sheet.set_column('E:E', 45)
        sheet.set_column('F:F', 7)
        sheet.set_column('G:G', 9)
        sheet.set_column('H:H', 19)
        sheet.set_column('I:I', 12)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 107)
        data = self.report_payment_file_data()
        
        sheet.write(1, 0, 'TIPO DE CUENTA', format_title)
        sheet.write(1, 1, 'VALOR', format_title)
        sheet.write(1, 2, 'CODIGO BANCO SPI 2X', format_title)
        sheet.write(1, 3, 'CTA OTRO BANCO', format_title)
        sheet.write(1, 4, 'NOMBRE BENEFICIARIO', format_title)
        sheet.write(1, 5, 'MOTIVO', format_title)
        sheet.write(1, 6, 'CODIGO', format_title)
        sheet.write(1, 7, 'CODIGO BANCO SPI 3X', format_title)
        sheet.write(1, 8, 'TPO IDENT', format_title)
        sheet.write(1, 9, 'IDENTIFICACION', format_title)
        sheet.write(1, 10, 'CUERPO DEL ARCHIVO DE TEXTO', format_title)
        row=2
        for l in data:
            ca = l['tipo_cta']+'0000000000000000000000'+l['valor']+'XXY01'+l['code']+'000000000'+l['nro_cta']+'      '+l['beneficiario']+'      '+'CV2'+'      '+l['num_identificacion']
            if l['bg']!=True:
                sheet.write(row, 0, l['tipo_cta'], body_left)
                sheet.write(row, 1, l['valor'], body_right)
                sheet.write(row, 2, '', body_center)
                sheet.write(row, 3, l['nro_cta'], body_center)
                sheet.write(row, 4, l['beneficiario'], body_left)
                sheet.write(row, 5, 'CV2', body_left)
                sheet.write(row, 6, l['code'], body_center)
                sheet.write(row, 7, '', body_center)
                sheet.write(row, 8, l['tipo_identificacion'] , body_left)
                sheet.write(row, 9, l['num_identificacion'], body_left)
                sheet.write(row, 10, ca, body_left)
                row+=1