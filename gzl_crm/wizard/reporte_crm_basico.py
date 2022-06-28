# -*- coding: utf-8 -*-
import string
from odoo import api, fields, models, tools
from datetime import date, timedelta, datetime
from dateutil import relativedelta as rdelta 
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import ValidationError
class ReportCrm(models.TransientModel):
    _name = "report.crm"

    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Corte', required=True, default = date.today())

  

    def print_report_xls(self):
        today = date.today()
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'REPORTE CRM '+ str(today.year)
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
        
        sheet.merge_range('B1:Q1', ' ', bold)
        sheet.merge_range('A2:Q2', 'COMISIONES DEL PERIODO'+str(dia_start)+' DE '+str(mesesDic[str(mes_start)])+' DEL '+str(year)+' AL '+str(dia_end)+' DE '+str(mesesDic[str(mes_end)])+' DEL '+str(year), bold)
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
        
      
        sheet.write(2, 0, 'OPORTUNIDAD', bold2)
        sheet.write(2, 1, 'CLIENTE', bold2)
        sheet.write(2, 2, 'MONTO DE PLAN', bold2)
        sheet.write(2, 3, 'PROBABILIDAD', bold2)
        sheet.write(2, 4, 'COMERCIAL', bold2)
        sheet.write(2, 5, 'EQUIPO DE VENTAS', bold2)
        sheet.write(2, 6, 'VENTA GANADA', bold2)
        sheet.write(2, 7, 'CIERRE PREVISTO', bold2)
        sheet.write(2, 8, 'SUCURSAL', bold2)
        sheet.write(2, 9, 'PROVINCIA', bold2)
        
        sheet.write(2, 10, 'CIUDAD', bold2)
        sheet.write(2, 11, 'VALOR DE INSCRIPCION', bold2)
        sheet.write(2, 12, 'FECHA GANADA', bold2)
        sheet.write(2, 13, 'CONTRATO ASOCIADO', bold2)
        sheet.write(2, 14, 'TIPO CONTRATO ASOCIADO', bold2)
        sheet.write(2, 15, 'PRIORIDAD', bold2)
        sheet.write(2, 16, 'FACTURA', bold2)
        
        row=3
        crm = self.env['crm.lead'].search([('create_date','>=',self.date_start),('create_date','<=',self.date_end)])
        for l in crm:
            venta_ganada=''
            if l.colocar_venta_como_ganada:
                venta_ganada='SI'
            else:
                venta_ganada='NO'
            sheet.write(row,0, l.name or '###', body_center)
            sheet.write(row, 1, l.partner_id.name or '###', body_center)
            sheet.write(row, 2,l.planned_revenue or '###', body_center)
            sheet.write(row, 3, l.probability or '####', body_center)
            sheet.write(row, 4, l.user_id.name or '###', body_center)
            sheet.write(row, 5, l.team_id.name or '####', body_center)
            sheet.write(row, 6, venta_ganada or '###', body_center)
            sheet.write(row, 7, l.date_deadline or '###', body_center)
            sheet.write(row, 8, l.surcursal_id.name or '###', body_center)
            sheet.write(row, 9, l.provincia_id.name or '###', body_center)
            sheet.write(row, 10, l.ciudad_id.nombre_ciudad or '###', body_center)
            sheet.write(row, 11, l.valor_inscripcion or '###', body_center)
            sheet.write(row, 12, l.fecha_ganada or '###', body_center)
            sheet.write(row, 13, l.contrato_id.secuencia or '###', body_center)
            sheet.write(row, 14, l.tipo_contrato.name or '###', body_center)
            sheet.write(row, 15, l.priority or '###', body_center)
            sheet.write(row, 16, l.factura_inscripcion_id.name or '###', body_center)
            row+=1