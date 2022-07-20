# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import xlsxwriter
from io import BytesIO
import base64
from calendar import monthrange

class ReportThirteenthSalary(models.TransientModel):
    _name = "report.thirteenth.salary"

    date = fields.Selection(selection=[
            ('01', 'Enero'),
            ('02', 'Febrero'),
            ('03', 'Marzo'),
            ('04', 'Abril'),
            ('05', 'Mayo'),
            ('06', 'Junio'),
            ('07', 'Julio'),
            ('08', 'Agosto'),
            ('09', 'Septiembre'),
            ('10', 'Octubre'),
            ('11', 'Noviembre'),
            ('12', 'Diciembre'),
        ], string='Fecha', required=True)




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
                        ('2030','2030'),
                        ('2031','2031'),
                        ('2032','2032'),
                        ('2033','2033'),
                        ('2034','2034'),
                        ('2035','2035'),
                        ('2036','2036'),
                        ('2037','2037'),
                        ('2038','2038'),
                        ('2039','2039'),
                        ('2040','2040'),
                        ('2041','2041'),
                        ('2042','2042'),
                        ('2043','2043'),
                        ('2044','2044'),
                        ('2045','2045'),
                        ('2046','2046'),
                        ('2047','2047'),
                        ('2048','2048'),
                        ('2049','2049'),
                        ('2050','2050'),


                        ],string="Año", default="2022")







    def report_thirteenth_salary_data(self):
        dct={}
        lis=[]
        cont=0
        employee_ids = self.env['hr.employee']
        hr_employee = employee_ids.search([('active','=',True),('identification_id','!=',False)],order='lastname')
       
        for emp in hr_employee:
            contract = self.env['hr.contract'].search([('employee_id','=',emp.id),('state','=','open')], limit=1)
            if contract:
                today = date.today()
                if today.month==12:
                    date_start = str(int(self.year_date))+'-12-01'
                else:
                    date_start = str(int(self.year_date)-1)+'-12-01'
                last_day = monthrange(int(self.year_date), int(self.date))[1]
                date_end = str(int(self.year_date))+'-'+str(self.date)+'-'+str(last_day)

                payslip = self.env['hr.payslip'].search([('employee_id','=',emp.id),('state','!=','cancel'),('date_from','>=',date_start),('date_to','<=',date_end)])
                salary = 0
                worked_day = 0
                for p in payslip:
                    hr_payslip_worked_day = self.env['hr.payslip.worked_days'].search([('payslip_id','=',p.id)])
                    salary = p.contract_id.wage
                    for wd in hr_payslip_worked_day:
                        worked_day +=  wd.number_of_days

                cont+=1
                dct = { 'nro': cont,
                        'cedula': emp.identification_id,
                        'colaborador': str(emp.lastname) +' '+ str(emp.firstname),
                        'dias_trabajados':worked_day,
                        'valor_a_pagar': round((salary/12/30)*worked_day,2) if salary else False
                        } 
                lis.append(dct)
        return lis 

    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'Décimo Tercer Sueldo'
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

    def xslx_body(self,workbook,name):
        bold = workbook.add_format({'bold':True,'border':1, 'bg_color':'#CFC8C6'})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':1})
        format_title.set_center_across()
        body_left = workbook.add_format({'align': 'left','border':1})
        body_center = workbook.add_format({'align': 'center','border':1})
        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        sheet = workbook.add_worksheet(name)
        sheet.merge_range('B1:E1', name.upper(), format_title2)
        sheet.set_column('A:A', 4)
        sheet.set_column('B:B', 11)
        sheet.set_column('C:C', 45)
        sheet.set_column('D:D', 16)
        sheet.set_column('E:E', 16)
        data = self.report_thirteenth_salary_data()
      
        sheet.write(2, 0, 'Nº', format_title)
        sheet.write(2, 1, 'CÉDULA', format_title)
        sheet.write(2, 2, 'COLABORADOR', format_title)
        sheet.write(2, 3, 'DÍAS TRABAJADOS', format_title)
        sheet.write(2, 4, 'VALOR A PAGAR', format_title)
        row=3
        for l in data:
            sheet.write(row, 0, l['nro'], body_left)
            sheet.write(row, 1, l['cedula'] or '', body_left)
            sheet.write(row, 2, l['colaborador'], body_left)
            sheet.write(row, 3, l['dias_trabajados'] or '', body_center)
            sheet.write(row, 4, l['valor_a_pagar'] or '', body_center)
            row+=1