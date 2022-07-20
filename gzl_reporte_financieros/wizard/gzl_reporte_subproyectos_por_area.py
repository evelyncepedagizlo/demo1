# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import AccessError, UserError, ValidationError

class ReporteSubproyectoMes(models.TransientModel):
    _inherit = "reporte.subproyecto.mes"



    def obtener_posicion_presupuestaria_agrupadas_por_unidad(self,tipo_presupuesto,areas_instanciadas):

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


            lista_unidades=[]
            

            
            
            for area in areas_instanciadas:
                dct_unidad={}

                planned_amount_linea=sum(list(consulta_crossovered_budget_linea.search([('analytic_account_id.business_area_id','=',area.id),('general_budget_id','=',linea.id)]).mapped('planned_amount')))
                practical_amount_linea=sum(list(consulta_crossovered_budget_linea.search([('analytic_account_id.business_area_id','=',area.id),('general_budget_id','=',linea.id)]).mapped('practical_amount')))

                dif_amount=planned_amount_linea-practical_amount_linea

                dct_unidad['posicion_practical_amount']=planned_amount_linea
                dct_unidad['posicion_planned_amount']=practical_amount_linea
                dct_unidad['posicion_diferencia']=dif_amount
                dct_unidad['nombre_unidad']=area.name
                lista_unidades.append(dct_unidad)


            dct['unidades']=lista_unidades
            lista_budget.append(dct)
        return(lista_budget)







        return lis



    def xslx_body_area(self,workbook,name,head):
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

        if len(self.area_ids)==0:
            areas_instanciadas=self.env['business.area'].search([]).sorted(key=lambda record: record.sequence, reverse=False)
                
        else:
            areas_instanciadas=self.area_ids.sorted(key=lambda record: record.sequence, reverse=False)




        json_ingresos=self.obtener_posicion_presupuestaria_agrupadas_por_unidad('ingresos',areas_instanciadas)
        json_costo=self.obtener_posicion_presupuestaria_agrupadas_por_unidad('costos',areas_instanciadas)
        json_no_operacionales=self.obtener_posicion_presupuestaria_agrupadas_por_unidad('no_operacionales',areas_instanciadas)
        json_gastos=self.obtener_posicion_presupuestaria_agrupadas_por_unidad('gastos',areas_instanciadas)



                
        
        
        sheet.write(10, 2, 'Unidad', format_title4)
        columna=3
        for l in range(1,4):
            
            
            
            for area in areas_instanciadas:

                sheet.write(10, columna, area.name, format_title)

                columna+=1
                
                
                
                
            sheet.write(10, columna, 'Total', format_title)
            columna+=2

        fila=self.crear_reglon_tipo_presupuesto_en_excel_area(workbook,sheet,'Ingresos',11,json_ingresos,areas_instanciadas)
        
        fila2=self.crear_reglon_tipo_presupuesto_en_excel_area(workbook,sheet,'Costos',fila+2,json_costo,areas_instanciadas)

        fila3=self.crear_reglon_resultado_area(workbook,sheet,'Bruto',fila,fila2,fila2+2,areas_instanciadas)
        
        fila4=self.crear_reglon_tipo_presupuesto_en_excel_area(workbook,sheet,'Gastos',fila3+2,json_gastos,areas_instanciadas)

        fila5=self.crear_reglon_resultado_area(workbook,sheet,'Operativa',fila3,fila4,fila4+2,areas_instanciadas)

        fila6=self.crear_reglon_tipo_presupuesto_en_excel_area(workbook,sheet,'No Operativos',fila5+2,json_no_operacionales,areas_instanciadas)

        fila7=self.crear_reglon_resultado_area(workbook,sheet,'neto',fila5,fila6,fila6+2,areas_instanciadas)
        
        
        sheet.merge_range('C5:{0}5'.format(chr(65 +columna-2)), name.upper(), format_title2)
        sheet.merge_range('C5:{0}5'.format(chr(65 +columna-2)), name.upper(), format_title2)

        sheet.set_column('C:C', 23)

        sheet.set_column('D:{0}'.format(chr(65 +columna-2)), 15)
        
        
        for i in range(1,4):

            sheet.set_column('{0}:{1}'.format(chr(65 +2+(len(areas_instanciadas)+2)*i),chr(65 +2+(len(areas_instanciadas)+2)*(i))), 3)

        
        
        
        
        
        
        
        
        
        
        
    def crear_reglon_resultado_area(self,workbook,sheet,tipo_resultado,fila1,fila2,fila3,areas_instanciadas):

        format_title = workbook.add_format({'bold':True,'border':1})
        format_title.set_center_across()
        body_right = workbook.add_format({'align': 'right', 'border':1 })
        body_left = workbook.add_format({'align': 'left','border':1})
        format_title2 = workbook.add_format({'align': 'right', 'bold':True,'border':0 ,'italic':True,'size':14})
        format_title3 = workbook.add_format({'align': 'right', 'bold':False,'border':0 })
        format_title4 = workbook.add_format({'align': 'left', 'bold':True,'border':0,'italic':True,'size':14 })



        format_title4.set_bg_color('dadada')
        format_title2.set_bg_color('dadada')   
        sheet.write(fila3, 2, 'Resultado {0}'.format(tipo_resultado), format_title4)
        columna=3
        

        
        for l in range(0,3):

            for i in range(0,len(areas_instanciadas)+1):

                cell_formula = {
                    'col': chr(65 +columna),
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


        
        
        
        

    def crear_reglon_tipo_presupuesto_en_excel_area(self,workbook,sheet,tipo_presupuesto,fila,json,areas_instanciadas):

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
                        'col1': chr(65 +columna),
                        'col2': chr(65 +columna+len(areas_instanciadas)),
                        'row1': 10,

                    }
                    
                    
                sheet.merge_range('{col1}{row1}:{col2}{row1}'.format(**cell_formula), '    '+  tipo_analisis['nombre'],format_title5)
                    

                    
                for unidad in ingreso['unidades']:
                    sheet.write(fila, columna, unidad[tipo_analisis['clave']], format_title6)
                    columna+=1


                col_formula = {
                    'from_col': chr(65 +columna-len(areas_instanciadas)),
                    'to_col': chr(65 + columna-1),
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
            
            
            
            
            
            
            
            
        if tipo_presupuesto=='Ingresos':
            formato=format_title9
        else:
            formato=format_title10
        formato.set_bg_color('b4c6e7')
            
        format_title8.set_bg_color('b4c6e7')

            
        sheet.write(fila, 2, 'Total {0}'.format(tipo_presupuesto), format_title8)
        columna=3
        
        for l in range(1,4):
            for area in areas_instanciadas:
                col_formula = {
                    'from_col': chr(65 +columna),
                    'to_col': chr(65 + columna),
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
                    'from_col': chr(65 +columna),
                    'to_col': chr(65 + columna),
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



