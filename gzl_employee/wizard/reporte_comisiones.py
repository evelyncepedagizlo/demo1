# -*- coding: utf-8 -*-
import string
from odoo import api, fields, models, tools
from datetime import date, timedelta, datetime
from dateutil import relativedelta as rdelta 
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import ValidationError
class ReportComisiones(models.TransientModel):
    _name = "report.comisiones"

    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Corte', required=True, default = date.today())

  

    def print_report_xls(self):
        today = date.today()
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'REPORTE COMISIONES '+ str(today.year)
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
        bold = workbook.add_format({'bold':True,'border':0, 'bg_color':'#442484','color':'#FFFFFF','align': 'left'})
        #bold.set_center_across()
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
        #sheet.insert_image('A1:D1', '../gzl_employee/img/logo.PNG', {'x_offset': 15, 'y_offset': 10,'bg_color':'#442484'})
        sheet.insert_image('A1', "any_name.png",
                           {'image_data':  BytesIO(base64.b64decode( self.env.company.imagen_excel_company)), 'x_scale': 0.8, 'y_scale': 0.6,'x_scale': 0.8,
                            'y_scale':     0.6, 'align': 'left','bg_color':'#442484'})
        #sheet.insert_image('A1:D1', "any_name.png",
        #                   {'image_data':  BytesIO(base64.b64decode( '../gzl_employee/img/logo.jpg')), 'x_scale': 0.5, 'y_scale': 0.5,'x_scale': 0.5,
        #                    'y_scale':     0.5, 'align': 'left'})
        
        sheet.merge_range('B1:T1', ' ', bold)
        sheet.merge_range('A2:T2', 'COMISIONES DEL PERIODO DEL '+str(dia_start)+' DE '+str(mesesDic[str(mes_start)])+' DEL '+str(year)+' AL '+str(dia_end)+' DE '+str(mesesDic[str(mes_end)])+' DEL '+str(year), bold)
        sheet.merge_range('E2:T2', ' ', bold)
        
        #sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 45)
        sheet.set_column('C:C', 16)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 16)
        sheet.set_column('F:F', 17)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 16)
        sheet.set_column('J:J', 17)
        sheet.set_column('K:K', 17)
        sheet.set_column('L:L', 17)
        sheet.set_column('M:M', 17)
        sheet.set_column('N:N', 17)
        sheet.set_column('O:O', 17)
        sheet.set_column('P:P', 17)
        sheet.set_column('Q:Q', 17)
        sheet.set_column('R:R', 17)
        sheet.set_column('S:S', 17)
        sheet.set_column('T:T', 17)
        #sheet.set_column('U:U', 17)
        #sheet.set_column('V:V', 17)
        #sheet.set_column('W:W', 17)
        #sheet.set_column('X:X', 17)
        #sheet.set_column('Y:Y', 17)
        #sheet.set_column('Z:Z', 17)
        
        #sheet.set_column('AA:AA', 17)
        #sheet.set_column('AB:AB', 17)
        #sheet.set_column('AC:AC', 17)
        #sheet.set_column('AD:AD', 17)
        #sheet.set_column('AE:AE', 17)
        #sheet.set_column('AF:AF', 17)
        #sheet.set_column('AG:AG', 17)
        #sheet.set_column(1,45, 45)
        #data = self.report_vacations_data()
      
        #sheet.write(2, 0, 'PERIODO DE PAGO', bold)
        #sheet.write(2, 1, 'CARGO', bold)
        #sheet.write(2, 2, 'AGENCIA', bold)
        #sheet.write(2, 3, 'CONTRATO N', bold)
        #sheet.write(2, 4, 'NOMBRE', bold)
        #sheet.write(2, 4, 'SUBTOTAL', bold)
        #sheet.write(2, 4, 'IVA', bold)
        #sheet.write(2, 4, 'TOTAL A RECIBIR', bold)
        #sheet.write(2, 4, 'ESTADO', bold)
        #sheet.write(2, 4, 'OBSERVACION', bold)
        sheet.write(2, 0, '#', bold2)
        sheet.write(2, 1, 'Nº CONTRATO', bold2)
        sheet.write(2, 2, 'PUNTO DE VENTA', bold2)
        sheet.write(2, 3, 'CÉDULA', bold2)
        sheet.write(2, 4, 'CLIENTE	', bold2)
        sheet.write(2, 5, 'MES', bold2)
        sheet.write(2, 6, 'FECHA CONTRATO', bold2)
        sheet.write(2, 7, 'PLAZO ADQ. VEHÍCULO', bold2)
        sheet.write(2, 8, 'MONTO BASE CONTRATO', bold2)
        sheet.write(2, 9, 'CÓDIGO ASESOR', bold2)
        sheet.write(2, 10, 'VALOR INSCRIPCIÓN 5%', bold2)
        sheet.write(2, 11, 'FACTURA #', bold2)
        sheet.write(2, 12, 'COMISIÓN ASESOR $', bold2)
        sheet.write(2, 13, 'COMISIÓN ASESOR %', bold2)
        sheet.write(2, 14, 'ASESOR', bold2)
        sheet.write(2, 15, '% ASESOR', bold2)
        sheet.write(2, 16, 'SUBT. ASESOR', bold2)
        sheet.write(2, 17, 'CERRADOR', bold2)
        sheet.write(2, 18, '% CERRADOR', bold2)
        sheet.write(2, 19, 'SUBT. CERRADOR	', bold2)
        #sheet.write(2, 20, 'ASESOR PREMIUM ', bold2)  

        #sheet.write(2, 21, '% PREMIUM', bold2)
        #sheet.write(2, 22, 'SUBT. PREMIUM', bold2)
        #sheet.write(2, 23, 'SUPERVISOR GRUPAL', bold2)
        #sheet.write(2, 24, '% SUPERVISOR	', bold2)
        #sheet.write(2, 25, 'SUBT. SUPERVISOR', bold2)
        #sheet.write(2, 26, 'JEFE NACIONAL VENTAS', bold2)
        #sheet.write(2, 27, '% JEFE NACIONAL ', bold2)
        #sheet.write(2, 28, 'SUBT. JEFE DE VENTAS', bold2)
        #sheet.write(2, 29, 'GERENTE COMERCIAL', bold2)
        #sheet.write(2, 30, '% GERENTE COMERCIAL', bold2)
        #sheet.write(2, 31, 'SUBT. GERENTE COMERCIAL', bold2)
        #sheet.write(2, 32, 'PORCENTAJE TOTAL', bold2)      
        row=3
        comisiones = self.env['comision.bitacora'].search([('create_date','>=',self.date_start),('create_date','<=',self.date_end)])
            #('create_date', '<=', self.date_end),
            #('create_date', '>=', self.date_start),
        #])
        cont=0
        if len(comisiones) > 0:
            
            for l in comisiones: #contrato_id comision.bitacora
                if l.lead_id :
                    cont+=1
                    gerente_comercial =self.env['hr.employee'].search([('job_id.name','=','Gerencia Comercial')],limit=1)
                    jefe_ventas_nacional =self.env['hr.employee'].search([('job_id.name','=','Jefe de Ventas')],limit=1)
                    #porcentaje = self.env['comision'].search([('valor_min','>=',float(l.valor_inscripcion)),('valor_max','<=',float(l.valor_inscripcion)),('logica','=','asesor')])
                    #raise ValidationError(str(porcentaje))
                    sheet.write(row, 0, row, body_center)
                    sheet.write(row, 1, l.lead_id.contrato_id.secuencia, body_center)
                    sheet.write(row, 2,l.lead_id.contrato_id.ciudad.nombre_ciudad, body_center)
                    sheet.write(row, 3, l.lead_id.contrato_id.cliente.vat or '####', body_center)
                    sheet.write(row, 4, l.lead_id.contrato_id.cliente.name or '###', body_center)
                    sheet.write(row, 5, self.date_start.month or '####', body_center)
                    sheet.write(row, 6, l.lead_id.contrato_id.fecha_contrato or '###', body_center)
                    sheet.write(row, 7, l.lead_id.contrato_id.plazo_meses.numero or '###', body_center)
                    sheet.write(row, 8, l.lead_id.contrato_id.monto_financiamiento or '###', body_center)
                    sheet.write(row, 9, 'codigo asesor' or '###', body_center)
                    sheet.write(row, 10, l.valor_inscripcion or '###', body_center)
                    sheet.write(row, 11, l.lead_id.factura_inscripcion_id.name or '', body_center)
                    sheet.write(row, 12, l.comision or '', body_center)
                    sheet.write(row, 13, l.porcentaje_comision or '###', body_center)
                    sheet.write(row, 14, l.lead_id.user_id.name or '###', body_center)
                    sheet.write(row, 15, l.lead_id.porcent_asesor or '###', body_center)
                    sheet.write(row, 16, '=((M'+str(row+1)+'*P'+str(row+1)+')/100)' or '###', body_center)
                    sheet.write(row, 17, l.lead_id.cerrador.name or '###', body_center)
                    sheet.write(row, 18, str(100-l.lead_id.porcent_asesor)+' %' or '###', body_center)
                    sheet.write(row, 19, (l.comision*((100-l.lead_id.porcent_asesor)/100)) or '###', body_center)
                    #sheet.write(row, 20,'asesor premium' or '###', body_center)
                    #sheet.write(row, 21, 0.00 , body_center)
                    #sheet.write(row, 22,'subtotal asesor premium' or '###', body_center)
                    #sheet.write(row, 23,l.lead_id.supervisor.name or '###', body_center)
                    #sheet.write(row, 24,4 or '###', body_center)
                    #sheet.write(row, 25,'=((K'+str(row+1)+'/1.12)'+'*((Y'+str(row+1)+')/100))' or '###', body_center)
                    #sheet.write(row, 26,jefe_ventas_nacional.name or '###', body_center)
                    #sheet.write(row, 27,3 or '###', body_center)
                    #sheet.write(row, 28,'=((K'+str(row+1)+'/1.12)'+'*((AB'+str(row+1)+')/100))' or '###', body_center)
                    #sheet.write(row, 29,gerente_comercial.name or '###', body_center)
                    #sheet.write(row, 30,3 or '###', body_center)
                    #sheet.write(row, 31,'=((K'+str(row+1)+'/1.12)'+'*((AE'+str(row+1)+')/100))' or '###', body_center)
                    #sheet.write(row, 32,'=(N'+str(row+1)+'+V'+str(row+1)+'+Y'+str(row+1)+'+AB'+str(row+1)+'+AE'+str(row+1)+')' or '###', body_center)
                    row+=1
class companyherencia(models.Model):
    _inherit = "res.company"
    imagen_excel_company = fields.Binary('Logo Excel')