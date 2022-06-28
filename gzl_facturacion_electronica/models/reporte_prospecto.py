# -*- coding: utf-8 -*-
import string
from odoo import api, fields, models, tools
from datetime import date, timedelta, datetime
from dateutil import relativedelta as rdelta 
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import ValidationError


# class Users(models.Model):
#     _inherit = 'res.users'

#     codigo_asesor=fields.Char("Codigo de Asesor")

class ReportCrm(models.TransientModel):
    _name = "report.crm.prospecto"

    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Corte', required=True, default = date.today())


    def print_report_xls(self):
        today = date.today()
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'REPORTE DE PROSPECTOS '+ str(today.year)
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
        
        formato_fecha = workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                                'border':True,'bg_color':'#3bbf13','color':'#0f0000','num_format': 'dd/mm/yy'})
        formato_numero = workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                            'border':True,'bg_color':'#3bbf13','color':'#0f0000','num_format': '#,##0.00'})
        registros_tabla= workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                                'border':True,'bg_color':'#3bbf13','color':'#0f0000'})

        bold = workbook.add_format({'bold':True,'border':True, 'bg_color':'#442484','color':'#FFFFFF'})
        bold.set_center_across()
        bold.set_font_size(14)

        bold2 = workbook.add_format({'align':'center','valign':'vcenter','bold':True,'font_size': 13, 'bg_color':'#989899',
                                    'color':'#FFFFFF','text_wrap':True,'border':True})
        bold2.set_center_across()

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
        
        sheet.merge_range('B1:I1', ' ', bold)
        sheet.merge_range('A2:I2', 'REPORTE DE PROSPECTOS DEL '+str(dia_start)+' DE '+str(mesesDic[str(mes_start)])+' DEL '+str(year)+' AL '+str(dia_end)+' DE '+str(mesesDic[str(mes_end)])+' DEL '+str(year), bold)
        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 40)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:I', 10)


        sheet.write(4, 0, 'FECHA DE GESTION', bold2)
        sheet.write(4, 1, 'SEMANA', bold2)
        sheet.write(4, 2, 'ASESOR', bold2)
        sheet.write(4, 3, 'PRESUPUESTO', bold2)
        sheet.write(4, 4, 'PROSPECTOS', bold2)
        sheet.write(4, 5, 'LLAMADAS', bold2)
        sheet.write(4, 6, 'CITAS', bold2)
        sheet.write(4, 7, 'VENTAS', bold2)
        sheet.write(4, 8, '% CUMPLIMIENTO', bold2)

        row=5
        crm = self.env['crm.lead'].search([('create_date','>=',self.date_start),('create_date','<=',self.date_end)])
        lista_asesores=[]
        lista_final=[]
        for l in crm:
            semana=l.create_date.date().isocalendar()[1]
            if l.cerrador:
                if l.cerrador.id not in lista_asesores:
                    llamada=0
                    cita=0
                    venta=0
                    for m in l.activity_ids:
                        if m.activity_type_id.name=='Llamada':
                            llamada=1
                        elif m.activity_type_id.name=='Reunión':
                            cita=1
                    if l.colocar_venta_como_ganada:
                        venta=1
                    lista_asesores.append(l.cerrador.id)
                    dct={'fecha_gestion':l.create_date,
                        'semana':semana,
                        'id_asesor':l.cerrador.id,
                        'asesor':l.cerrador.name,
                        'cliente':l.partner_id.name,
                        'presupuesto':100,
                        'prospectos':1,
                        'llamadas':llamada,
                        'citas':cita,
                        'ventas':venta}
                    lista_final.append(dct)
                else:
                    for x in lista_final:
                        if x['id_asesor']==l.cerrador.id:
                            for m in l.activity_ids:
                                if m.activity_type_id.name=='Llamada':
                                    x['llamadas']+=1
                                elif m.activity_type_id.name=='Reunión':
                                    x['citas']+=1
                            x['prospectos']+=1
                            if l.colocar_venta_como_ganada:
                                x['ventas']+=1
            else:
                llamada=0
                cita=0
                venta=0
                for m in l.activity_ids:
                    if m.activity_type_id.name=='Llamada':
                        llamada=1
                    elif m.activity_type_id.name=='Reunión':
                        cita=1
                if l.colocar_venta_como_ganada:
                    venta=1

                dct={'fecha_gestion':l.create_date,
                        'semana':semana,
                        'id_asesor':'',
                        'asesor':'',
                        'cliente':l.partner_id.name,
                        'presupuesto':100,
                        'prospectos':1,
                        'llamadas':llamada,
                        'citas':cita,
                        'ventas':venta}
                lista_final.append(dct)

        for line in lista_final:
            if line['presupuesto']:
                cumplimiento=(line['ventas']/line['presupuesto'])*100
            else:
                cumplimiento=0
            if cumplimiento<=25:
                formato_fecha = workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                                'border':True,'bg_color':'#f5051d','color':'#FFFFFF','num_format': 'dd/mm/yy'})
                formato_numero = workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                                'border':True,'bg_color':'#f5051d','color':'#FFFFFF','num_format': '#,##0.00'})
                registros_tabla= workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                                'border':True,'bg_color':'#f5051d','color':'#FFFFFF'})
            

            elif cumplimiento>25 and cumplimiento<=50:
                formato_fecha = workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                                'border':True,'bg_color':'#e9f50f','color':'#0f0000','num_format': 'dd/mm/yy'})
                formato_numero = workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                                'border':True,'bg_color':'#e9f50f','color':'#0f0000','num_format': '#,##0.00'})
                registros_tabla= workbook.add_format({'align':'center','valign':'vcenter','font_size': 13,'text_wrap':True,
                                                'border':True,'bg_color':'#e9f50f','color':'#0f0000'})

            sheet.write(row,0, line['fecha_gestion'], formato_fecha)
            sheet.write(row, 1, 'Semana '+str(line['semana']), registros_tabla)
            sheet.write(row, 2,line['asesor'] or '', registros_tabla)
            sheet.write(row, 3, line['presupuesto'] or 0, registros_tabla)
            sheet.write(row, 4, line['prospectos'] or 0, registros_tabla)
            sheet.write(row, 5, line['llamadas'] or 0, registros_tabla)
            sheet.write(row, 6,line['citas']  or 0, registros_tabla)
            sheet.write(row, 7, line['ventas'] or 0, registros_tabla)
            sheet.write(row, 8, cumplimiento, registros_tabla)

            row+=1


