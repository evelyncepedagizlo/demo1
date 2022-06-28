
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




class ReporteSubproyectoMes(models.TransientModel):
    _name = "reporte.subproyecto.mes"


    cuenta_analitica_ids = fields.Many2many('account.analytic.account',string='Cuenta')
    proyectos = fields.Many2many('parent.project',string='Grupo')
    eje_ids = fields.Many2many('axis',string='Eje')
    area_ids = fields.Many2many('business.area',string='Area/Unidad')
    date_from = fields.Date('Fecha de Inicio')
    date_to = fields.Date('Fecha Fin')



    @api.constrains('date_from','date_to' )
    def verificar_primer_dia_del_mes(self):
        start_date =self.date_from
        fecha_inicio="%s-%s-01" % (start_date.year, str(start_date.month).zfill(2))
        

        
        if str(self.date_from)!=fecha_inicio:
            raise ValidationError(("La fecha de Inicio debe ser el primer dia del mes"))

            

        end_date = self.date_to
        fecha_fin="%s-%s-%s" % (end_date.year, str(end_date.month).zfill(2),str(calendar.monthrange(end_date.year, end_date.month)[1]).zfill(2))
        if str(self.date_to)!=fecha_fin:
            raise ValidationError(("La fecha de Fin debe ser el ultimo dia del mes"))

        if self.date_to.year != self.date_from.year:
            raise ValidationError(("Las fechas deben corresponder al mismo periodo fiscal"))

        
            
            
    def fix_date(self, date):
        repaired_date = date.strftime("%d/%m/%Y")
        return repaired_date




    ##nueva funcionalidad por ver 


    def obtener_posicion_presupuestaria_agrupadas_por_mes(self,tipo_presupuesto,lista_mes):

        filtro=[('date_from','>=',self.date_from),
            ('date_to','<=',self.date_to),
            ('tipo_presupuesto','=',tipo_presupuesto)]


        
        if len(self.cuenta_analitica_ids.mapped("id"))!=0:
            filtro.append(('analytic_account_id','=',self.cuenta_analitica_ids.mapped("id")))
        


        if  len(self.proyectos.mapped("id"))!=0:   
            filtro.append(('analytic_account_id.project_id','in',self.proyectos.mapped("id")))

        if  len(self.eje_ids.mapped("id"))!=0:   
            filtro.append(('analytic_account_id.axis_id','in',self.eje_ids.mapped("id")))

        if  len(self.area_ids.mapped("id"))!=0:   
            filtro.append(('analytic_account_id.business_area_id','in',self.area_ids.mapped("id")))


#######Ingresos
        consulta_crossovered_budget_linea=self.env['crossovered.budget.lines'].search(filtro)
        lista_budget=[]
        
        lista_crossovered_budget_linea_instancia_ids=list(set(consulta_crossovered_budget_linea.mapped("general_budget_id").mapped("id")))
        lista_crossovered_budget_linea_instancia=self.env['account.budget.post'].browse(lista_crossovered_budget_linea_instancia_ids)
        

        for linea in lista_crossovered_budget_linea_instancia:
            dct={}
            dct['posicion_presupuestaria']=linea.name


            lista_posicion_mes=[]
            

            
            
            for mes in lista_mes:
                dct_mes={}

                planned_amount_linea=sum(list(consulta_crossovered_budget_linea.search([('date_from','=',mes['fecha_inicio']),('date_to','=',mes['fecha_fin']),('general_budget_id','=',linea.id)]).mapped('planned_amount')))
                practical_amount_linea=sum(list(consulta_crossovered_budget_linea.search([('date_from','=',mes['fecha_inicio']),('date_to','=',mes['fecha_fin']),('general_budget_id','=',linea.id)]).mapped('practical_amount')))

                dif_amount=planned_amount_linea-practical_amount_linea

                dct_mes['posicion_practical_amount']=planned_amount_linea
                dct_mes['posicion_planned_amount']=practical_amount_linea
                dct_mes['posicion_diferencia']=dif_amount
                dct_mes['nombre_mes']=mes['nombre_mes']
                lista_posicion_mes.append(dct_mes)


            dct['meses']=lista_posicion_mes
            lista_budget.append(dct)
        return(lista_budget)







        return lis

    def head_info(self):
        return [
            ({'value': ''}, {'value': ''})
            for i in self
        ]

    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        head = self.head_info()
        name = 'Presupuestos por Mes'
        self.xslx_body(workbook, name, head)
        
        name = 'Presupuestos por Unidad/Area'

        self.xslx_body_area(workbook, name, head)
        #workbook.close()
        #file_data.seek(0)
        #acunalema presupuesto variante
        name = 'Variacion'

        self.xslx_body_variacion(workbook, name, head)
        workbook.close()
        file_data.seek(0)
        name = 'Reporte Presupuestario'
        
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
        porcentaje_format = workbook.add_format({'num_format': '00.00%','border':1 })
        body_right = workbook.add_format({'align': 'right', 'border':1 })
        body_left = workbook.add_format({'align': 'left','border':1})
        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        sheet = workbook.add_worksheet(name)
        
        
        

        format_title3 = workbook.add_format({'align': 'right', 'bold':False,'border':0 })
        format_title4 = workbook.add_format({'align': 'left', 'bold':False,'border':0 })





        start_date = datetime(self.date_from.year, self.date_from.month, self.date_from.day)


        end_date = datetime(self.date_to.year, self.date_to.month, self.date_to.day)
        num_months = [i-12 if i>12 else i for i in range(start_date.month, monthdelta(start_date, end_date)+start_date.month+1)]



        monthly_daterange = [datetime(start_date.year,i, start_date.day, start_date.hour) for i in num_months]

        lista_mes=[]
        dct_nombre_mes={
            1:'ENE',
            2:'FEB',
            3:'MAR',
            4:'ABR',
            5:'MAY',
            6:'JUN',
            7:'JUL',
            8:'AGO',
            9:'SEP',
            10:'OCT',
            11:'NOV',
            12:'DIC',



        }

        for mes in monthly_daterange:
            dct_mes={}


            dct_mes['nombre_mes']=dct_nombre_mes[mes.month]

            fecha_actual="%s-%s-01" % (mes.year, mes.month)
            fecha_fin_tarea="%s-%s-%s" % (mes.year, mes.month,(calendar.monthrange(mes.year, mes.month)[1]))


            dct_mes['fecha_inicio']=fecha_actual
            dct_mes['fecha_fin']=fecha_fin_tarea

            lista_mes.append(dct_mes)


        json_ingresos=self.obtener_posicion_presupuestaria_agrupadas_por_mes('ingresos',lista_mes)
        json_costo=self.obtener_posicion_presupuestaria_agrupadas_por_mes('costos',lista_mes)
        json_no_operacionales=self.obtener_posicion_presupuestaria_agrupadas_por_mes('no_operacionales',lista_mes)
        json_gastos=self.obtener_posicion_presupuestaria_agrupadas_por_mes('gastos',lista_mes)



                
        
        
        sheet.write(10, 2, 'Unidad', format_title4)
        columna=3
        for l in range(1,4):
            
            
            
            for mes in lista_mes:

                sheet.write(10, columna, mes['nombre_mes'], format_title)

                columna+=1
                
                
                
                
            sheet.write(10, columna, 'Total', format_title)
            columna+=2

        fila=self.crear_reglon_tipo_presupuesto_en_excel(workbook,sheet,'Ingresos',11,json_ingresos,lista_mes)
        
        fila2=self.crear_reglon_tipo_presupuesto_en_excel(workbook,sheet,'Costos',fila+2,json_costo,lista_mes)

        fila3=self.crear_reglon_resultado(workbook,sheet,'Bruto',fila,fila2,fila2+2,lista_mes)
        
        fila4=self.crear_reglon_tipo_presupuesto_en_excel(workbook,sheet,'Gastos',fila3+2,json_gastos,lista_mes)

        fila5=self.crear_reglon_resultado(workbook,sheet,'Operativa',fila3,fila4,fila4+2,lista_mes)

        fila6=self.crear_reglon_tipo_presupuesto_en_excel(workbook,sheet,'No Operativos',fila5+2,json_no_operacionales,lista_mes)

        fila7=self.crear_reglon_resultado(workbook,sheet,'neto',fila5,fila6,fila6+2,lista_mes)
        
        

        
        
        sheet.merge_range('C5:{0}5'.format(chr(65 +columna-2) if columna-2 <= 25 else 'A'+chr(65 +columna-2-26)), name.upper(), format_title2)

        sheet.set_column('C:C', 38.70)

        sheet.set_column('D:{0}'.format(chr(65 +columna-2) if columna-2 <= 25 else 'A'+chr(65 +columna-2-26)), 9.80)
        for i in range(1,4):
            columna_secuencial= chr(65 +2+(len(lista_mes)+2)*i) if 2+(len(lista_mes)+2)*i <= 25 else 'A'+chr(65 +2+(len(lista_mes)+2)*i-26)
            sheet.set_column('{0}:{1}'.format(columna_secuencial,columna_secuencial, 0.90))

        
        
        
        
        
        
        
        
        
        
        
    def crear_reglon_resultado(self,workbook,sheet,tipo_resultado,fila1,fila2,fila3,lista_mes):

        format_title = workbook.add_format({'bold':True,'border':1})
        format_title.set_center_across()
        body_right = workbook.add_format({'align': 'right', 'border':1 })
        body_left = workbook.add_format({'align': 'left','border':1})
        format_title2 = workbook.add_format({'align': 'right', 'bold':True,'border':0 ,'italic':True,'size':14})
        format_title3 = workbook.add_format({'align': 'right', 'bold':False,'border':0 })
        format_title4 = workbook.add_format({'align': 'left', 'bold':True,'border':0,'italic':True,'size':14 })


        format_title4.set_bg_color('dadada')
        format_title2.set_bg_color('dadada')

        format_title4.set_bg_color('dadada')
        format_title2.set_bg_color('dadada')

        
        
        
        sheet.write(fila3, 2, 'Resultado {0}'.format(tipo_resultado), format_title4)
        
        
        
        
        columna=3
        

        
        for l in range(0,3):

            for i in range(0,len(lista_mes)+1):

                cell_formula = {
                    'col': chr(65 +columna) if columna <= 25 else 'A'+chr(65 +columna-26),
                    'row1': fila1+1,
                    'row2': fila2+1,
                    
                }
                sheet.write_formula(
                    fila3 ,columna ,
                    '=+{col}{row1}-{col}{row2}'.format(
                        **cell_formula
                    ), format_title2
                )
                columna+=1
            columna+=1
        return fila3


        
        
        
        

    def crear_reglon_tipo_presupuesto_en_excel(self,workbook,sheet,tipo_presupuesto,fila,json,lista_mes):

        body_right = workbook.add_format({'align': 'right', 'border':1 })
        body_left = workbook.add_format({'align': 'left','border':1})
        
        format_title = workbook.add_format({'bold':True,'border':0})

        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        format_title3 = workbook.add_format({'align': 'left', 'bold':False,'border':0 })
        format_title4 = workbook.add_format({'align': 'right', 'bold':True,'border':0 })
        format_title5 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        format_title6 = workbook.add_format({'align': 'right', 'bold':False,'border':0 })
        format_title7 = workbook.add_format({'align': 'left', 'bold':True,'border':0 })
        format_title8 = workbook.add_format({'align': 'left', 'bold':True,'border':0,'underline':True })
        format_title9 = workbook.add_format({'align': 'right', 'bold':True,'border':0,'underline':True })
        format_title10 = workbook.add_format({'align': 'right', 'bold':False,'border':0 })

        format_title.set_center_across()



        sheet.write(fila, 2, tipo_presupuesto, format_title7)
        fila_inicial=fila
        fila+=1
        for ingreso in json:
            sheet.write(fila, 2, ingreso['posicion_presupuestaria'], format_title3)
            columna=3

            lista_analisis=[{'nombre':'PRESUPUESTO  UNIDADES','clave':'posicion_practical_amount'},{'nombre':'EJECUTADO  UNIDADES','clave':'posicion_planned_amount'},{'nombre':'DIFERENCIA  UNIDADES','clave':'posicion_diferencia'}]

            for tipo_analisis in lista_analisis:

                    
                cell_formula = {
                        'col1': chr(65 +columna) if columna <= 25 else 'A'+chr(65 +columna-26),
                        'col2': chr(65 +columna+len(lista_mes)) if columna+len(lista_mes) <= 25 else 'A'+chr(65 +columna+len(lista_mes)-26),
                        'row1': 10,

                    }
                    
                    
                sheet.merge_range('{col1}{row1}:{col2}{row1}'.format(**cell_formula), '    '+  tipo_analisis['nombre'],format_title5)
                    

                    
                for unidad in ingreso['meses']:
                    sheet.write(fila, columna, unidad[tipo_analisis['clave']], format_title6)
                    columna+=1


                             
                             

                col_formula = {
                    'from_col': chr(65 + columna-len(lista_mes)) if  columna-len(lista_mes) <= 25 else 'A'+chr(65 + columna-len(lista_mes)-26),
                    'to_col': chr(65 + columna-1) if  columna-1 <= 25 else 'A'+chr(65 + columna-1-26),
                    'row': fila+1,
                }
                sheet.write_formula(
                    fila ,columna ,
                    '=SUM({from_col}{row}:{to_col}{row})'.format(
                        **col_formula
                    ), format_title6
                )
                
                
                columna+=2
            fila+=1
            
            
        format_title8.set_bg_color('b4c6e7')
        sheet.write(fila, 2, 'Total {0}'.format(tipo_presupuesto), format_title8)
        columna=3
        
        if tipo_presupuesto=='Ingresos':
            formato=format_title9
        else:
            formato=format_title10
        formato.set_bg_color('b4c6e7')

        
        for l in range(1,4):
            for mes in lista_mes:
                             
                             
                             
                             
                             
                col_formula = {
                    'from_col': chr(65 +columna) if columna <= 25 else 'A'+chr(65 +columna-26),
                    'to_col': chr(65 +columna) if columna <= 25 else 'A'+chr(65 +columna-26),
                    'from_row': fila_inicial+2,
                    'to_row': fila,
                    
                    
                }

                
                if len(json)>0:
                    sheet.write_formula(
                        fila ,columna ,
                        '=SUM({from_col}{from_row}:{to_col}{to_row})'.format(
                            **col_formula
                        ), formato
                    )
                else:
                    sheet.write(fila, columna, 0, formato)
                
                
                
                
                
                
                
                
                columna+=1
            col_formula = {
                    'from_col': chr(65 +columna) if columna <= 25 else 'A'+chr(65 +columna-26),
                    'to_col': chr(65 +columna) if columna <= 25 else 'A'+chr(65 +columna-26),
                    'from_row': fila_inicial+2,
                    'to_row': fila,                
                
                }
                
                


            if len(json)>0:
                sheet.write_formula(
                    fila ,columna ,
                    '=SUM({from_col}{from_row}:{to_col}{to_row})'.format(
                        **col_formula
                    ), formato
                )
            else:
                sheet.write(fila, columna, 0, formato)
                
                
                
            
            
            
            
            
            columna+=2
        return fila


