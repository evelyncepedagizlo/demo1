# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from datetime import date, timedelta, datetime
from dateutil import relativedelta as rdelta 
import xlsxwriter
from io import BytesIO
import base64

class ReportVacations(models.TransientModel):
    _name = "report.vacations"

    def fix_date(self, date):
        repaired_date = date.strftime("%d/%m/%Y")
        return repaired_date
    
    def report_vacations_data(self):
        dct={}
        lis=[]
        employee_ids = self.env['hr.employee']
        hr_employee = employee_ids.search([('active','=',True),('identification_id','!=',False)],order='lastname')
        cont=0
        for emp in hr_employee:
            contract = self.env['hr.contract'].search([('employee_id','=',emp.id),('state','=','open')], limit=1)
            if contract:
                cont+=1
                today = date.today()
                payslip = self.env['hr.payslip'].search([('employee_id','=',emp.id),('state','!=','cancel')])
                date_cont=''
                total_year= days_enjoyed = days_pending = 0
                for p in payslip:
                    date_cont = self.fix_date(p.contract_id.date_start)
                    total_year = (rdelta.relativedelta(today, p.contract_id.date_start)).years
                    sum_days=0
                    days_15=15                
                    for i in range(total_year):
                        if i >= 5:
                            sum_days+=1
                    days_pending = (total_year*15)+sum_days

                    hr_payslip_worked_day = self.env['hr.payslip.worked_days'].search([('payslip_id','=',p.id)])
                    for wd in hr_payslip_worked_day:
                        if wd.work_entry_type_id.code == 'VACATION100':
                            days_enjoyed +=  wd.number_of_days
                dct = { 'nro': cont,
                        'colaborador': str(emp.lastname) +' '+ str(emp.firstname),
                        'fecha_ingreso': date_cont,
                        'dias_gozados': days_enjoyed,
                        'dias_pendientes': days_pending-days_enjoyed
                        } 
                lis.append(dct)
        return lis

    def print_report_xls(self):
        today = date.today()
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'Control de Vacaciones '+ str(today.year)
        self.xslx_body(workbook,name)
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
        body_right = workbook.add_format({'align': 'right','border':1})
        body_left = workbook.add_format({'align': 'left','border':1})
        body_center = workbook.add_format({'align': 'center','border':1})
        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        sheet = workbook.add_worksheet(name)
        sheet.merge_range('B1:E1', name.upper(), format_title2)
        sheet.set_column('A:A', 4)
        sheet.set_column('B:B', 45)
        sheet.set_column('C:C', 16)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 16)
        sheet.set_column('F:F', 17)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 11)
        sheet.set_column('I:I', 11)
        sheet.set_column('J:J', 11)
        sheet.set_column('K:K', 11)
        sheet.set_column('L:L', 11)
        sheet.set_column('M:M', 11)
        data = self.report_vacations_data()
      
        sheet.write(2, 0, '#', format_title)
        sheet.write(2, 1, 'COLABORADOR', format_title)
        sheet.write(2, 2, 'FECHA DE INGRESO', format_title)
        sheet.write(2, 3, 'DÍAS GOZADOS', format_title)
        sheet.write(2, 4, 'DÍAS PENDIENTES', format_title)
        row=3
        for l in data:
            sheet.write(row, 0, l['nro'], body_right)
            sheet.write(row, 1, l['colaborador'], body_left)
            sheet.write(row, 2, l['fecha_ingreso'] or '', body_center)
            sheet.write(row, 3, l['dias_gozados'] or '', body_right)
            sheet.write(row, 4, l['dias_pendientes'] or '', body_right)
            row+=1