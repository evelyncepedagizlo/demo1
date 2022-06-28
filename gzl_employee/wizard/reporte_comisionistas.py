# -*- coding: utf-8 -*-
import string
from odoo import api, fields, models, tools
from datetime import date, timedelta, datetime
from dateutil import relativedelta as rdelta 
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import ValidationError
class ReportComisionistas(models.TransientModel):
    _name = "report.comisionistas"

    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Corte', required=True, default = date.today())

  

    def print_report_xls(self):
        today = date.today()
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'REPORTE COMISIONISTAS '+ str(today.year)
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
        bold = workbook.add_format({'bold':True,'border':0, 'bg_color':'#442484','color':'#FFFFFF'})
        bold.set_center_across()
        bold.set_font_size(14)
        bold2 = workbook.add_format({'bold':True,'border':0, 'bg_color':'#989899','color':'#FFFFFF'})
        bold2.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':0})
        format_title.set_center_across()
        body_right = workbook.add_format({'align': 'right','border':1})
        body_left = workbook.add_format({'align': 'left','border':0})
        body_center = workbook.add_format({'align': 'center','border':0})
        body_center.set_center_across()
        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        sheet = workbook.add_worksheet(name)
        mesesDic = {
                "1":'ENERO',
                "2":'FEBRERO',
                "3":'MARZO',
                "4":'ABRIL',
                "5":'MAYO',
                "6":'JUNIO',
                "7":'JULIO',
                "8":'AGOSTO',
                "9":'SEPTIEMBRE',
                "10":'OCTUBRE',
                "11":'NOVIEMBRE',
                "12":'DICIEMBRE'
            }
        year = self.date_start.year
        mes_start = self.date_start.month
        mes_end = self.date_end.month
        dia_start = self.date_start.day
        dia_end = self.date_end.day
        sheet.insert_image('A1', "any_name.png",
                           {'image_data':  BytesIO(base64.b64decode( self.env.company.imagen_excel_company)), 'x_scale': 0.9, 'y_scale': 0.8,'x_scale': 0.8,
                            'y_scale':     0.8, 'align': 'left','bg_color':'#442484'})
        
        sheet.merge_range('B1:J1', ' ', bold)
        sheet.merge_range('A2:J2', 'REPORTE DE COMISIONISTAS S'+str(dia_start)+''+str(mesesDic[str(mes_start)])+''+str(year), bold)
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 45)
        sheet.set_column('C:C', 16)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 25)
        sheet.set_column('F:F', 17)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 16)
        sheet.set_column('J:J', 17)
        sheet.set_column('K:K', 17)
        
      
        sheet.write(2, 0, 'PERIODO DE PAGO', bold2)
        sheet.write(2, 1, 'CARGO', bold2)
        sheet.write(2, 2, 'AGENCIA', bold2)
        sheet.write(2, 3, 'CONTRATO N', bold2)
        sheet.write(2, 4, 'NOMBRE', bold2)
        sheet.write(2, 5, 'SUBTOTAL', bold2)
        sheet.write(2, 6, 'IVA', bold2)
        sheet.write(2, 7, 'TOTAL A RECIBIR', bold2)
        sheet.write(2, 8, 'ESTADO', bold2)
        sheet.write(2, 9, 'OBSERVACION', bold2)
        
        row=3
        comisiones = self.env['comision.bitacora'].search([('create_date','>=',self.date_start),('create_date','<=',self.date_end)])
        
        if len(comisiones) > 0:
            
            for l in comisiones: #contrato_id comision.bitacora
                #if l.lead_id :
                
                cargo =self.env['hr.employee'].search([('user_id','=',l.user_id.id)],limit=1)
                #jefe_ventas_nacional =self.env['hr.employee'].search([('job_id.name','=','Jefe de Ventas')],limit=1)
                #porcentaje = self.env['comision'].search([('valor_min','>=',float(l.valor_inscripcion)),('valor_max','<=',float(l.valor_inscripcion)),('logica','=','asesor')])
                #raise ValidationError(str(porcentaje))
                sheet.write(row, 0, year, body_center)
                sheet.write(row, 1, cargo.job_id.name, body_center)
                sheet.write(row, 2, 'GUAYAQUIL', body_center)
                sheet.write(row, 3, l.lead_id.contrato_id.secuencia or '####', body_center)
                sheet.write(row, 4, l.user_id.name or '###', body_center)
                sheet.write(row, 5, l.comision or '####', body_center)
                sheet.write(row, 6, l.comision*0.12 or '###', body_center)
                sheet.write(row, 7, (l.comision*0.12)+l.comision or '###', body_center)
                sheet.write(row, 8, l.lead_id.stage_id.name or '###', body_center)
                sheet.write(row, 9, '.' or '###', body_center)

                row+=1
        