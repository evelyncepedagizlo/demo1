# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from datetime import date, timedelta
from odoo.fields import Datetime, Date
from datetime import datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import AccessError, UserError, ValidationError

class ReporteSubproyectoMes(models.TransientModel):
    _inherit = "reporte.subproyecto.mes"



    def obtener_posicion_presupuestaria_agrupadas_por_unidad_v(self,tipo_presupuesto,areas_instanciadas,date_f,date_t):

        filtro=[('date_from','>=',date_f),
            ('date_to','<=',date_t),
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



    def xslx_body_variacion(self,workbook,name,head):
        bold = workbook.add_format({'bold':True,'border':1, 'bg_color':'#CFC8C6'})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':0,'align': 'center'})
        format_title.set_center_across()
        porcentaje_format = workbook.add_format({'num_format': '00.00%','border':1 })
        body_right = workbook.add_format({'align': 'right', 'border':1 })
        body_left = workbook.add_format({'align': 'left','border':1})
        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        sheet = workbook.add_worksheet(name)
        
        
        

        format_title3 = workbook.add_format({'align': 'center', 'bold':False,'border':0 })
        format_title4 = workbook.add_format({'align': 'center', 'bold':True,'border':0 })
        format_titlec = workbook.add_format({'align': 'center', 'bold':False,'border':0 })
        format_titlec.set_bg_color('b4c6e7')

        if len(self.area_ids)==0:
            areas_instanciadas=self.env['business.area'].search([]).sorted(key=lambda record: record.sequence, reverse=False)
                
        else:
            areas_instanciadas=self.area_ids.sorted(key=lambda record: record.sequence, reverse=False)



        year = self.date_from.year #-1
            
        
        date_f = Date.to_date(str(year)+'-01-'+'01')
        date_t = Date.to_date(str(year)+'-12-'+'31')
        json_ingresos=self.obtener_posicion_presupuestaria_agrupadas_por_unidad_v('ingresos',areas_instanciadas,date_f,date_t)
        json_costo=self.obtener_posicion_presupuestaria_agrupadas_por_unidad_v('costos',areas_instanciadas,date_f,date_t)
        json_no_operacionales=self.obtener_posicion_presupuestaria_agrupadas_por_unidad_v('no_operacionales',areas_instanciadas,date_f,date_t)
        json_gastos=self.obtener_posicion_presupuestaria_agrupadas_por_unidad_v('gastos',areas_instanciadas,date_f,date_t)
        #raise ValidationError((str(json_gastos)))

        
                
        
        sheet.write('D9:I9', 'VARIACION DE PRESUPUESTO vs EJECUTADO '+str(self.date_from.year), format_title4)
        sheet.write(10, 3, 'PRESU', format_title4)
        sheet.write(10, 5, 'EJECUTADO', format_title4)
        sheet.write(10, 7, 'DIFERENCIAS', format_title4)
        columna=2
        fila = 12
        fila_1=0
        fila_2=0
        fila_3=0
        fila_4=0
        fila_5=0
        fila_6=0
        ing_j=[]
        ing_aut=[]
        ing_adm=[]
        c_j=[]
        c_aut=[]
        c_adm=[]
        g_j=[]
        g_aut=[]
        g_adm=[]
        fingresos1=0
        fingresos2=0
        fingresos3=0
        valor=0
        anterior =False
        for area in areas_instanciadas:
            #fila+=1
            
            for ingreso in json_ingresos:
                for unidad in ingreso['unidades']:
                    if unidad['nombre_unidad']==area.name:
                        if area.name == 'PROYECTOS':
                            ing_j = unidad
                        elif area.name == 'ADMINISTRACIÓN':
                            ing_adm = unidad
                        else:
                           ing_aut = unidad 
            for cost in json_costo:
                for unidad_cost in cost['unidades']:
                    if unidad_cost['nombre_unidad']==area.name:
                        if area.name == 'PROYECTOS':
                            c_j = unidad_cost
                        elif area.name == 'ADMINISTRACIÓN':
                            c_adm = unidad_cost
                        else:
                           c_aut = unidad_cost 
            for gast in json_gastos:
                for unidad_gast in gast['unidades']:
                    if unidad_gast['nombre_unidad']==area.name:
                        if area.name == 'PROYECTOS':
                            g_j = unidad_gast
                        elif area.name == 'ADMINISTRACIÓN':
                            g_adm = unidad_gast
                        else:
                           g_aut = unidad_gast                         
            
            if area.name== 'PROYECTOS':
                sheet.merge_range('C'+str(fila)+':I'+str(fila),area.name, format_title)
               #raise ValidationError((str(ing_j)+' '+str(c_j))) crear_reglon_margen_op
                fila_1=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Ingresos',area.name,fila,ing_j,areas_instanciadas,fila+2)
                valor = fila_1+1
                fingresos1 = fila_1
                fila_2=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Costo',area.name,fila_1,c_j,areas_instanciadas,valor)
                fila_m=self.crear_reglon_margen_op(workbook,sheet,'Margen Op',area.name,fila_2,c_j,areas_instanciadas,valor,anterior)
                fila_g=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Gastos',area.name,fila_m,g_j,areas_instanciadas,valor)
                fila_mn=self.crear_reglon_margen_op(workbook,sheet,'(=)Margen neto',area.name,fila_g,c_j,areas_instanciadas,valor,anterior)
                fila = fila_mn +1
            
            
            if area.name== 'ADMINISTRACIÓN':
                fila +=1
                sheet.merge_range('C'+str(fila)+':I'+str(fila),area.name, format_title)
                fila +=1
                #raise ValidationError((str(fila)))
                fila_3=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Ingresos',area.name,fila,ing_adm,areas_instanciadas,fila+2)
                valor = fila_3 +1
                fingresos2 = fila_3
                fila_4=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Costo',area.name,fila_3,c_adm,areas_instanciadas,valor)
                fila_m1=self.crear_reglon_margen_op(workbook,sheet,'(=)Margen Op',area.name,fila_4,c_j,areas_instanciadas,valor,anterior)
                fila_g1=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Gastos',area.name,fila_m1,g_adm,areas_instanciadas,valor)
                fila_mn1=self.crear_reglon_margen_op(workbook,sheet,'(=)Margen neto',area.name,fila_g1,c_j,areas_instanciadas,valor,anterior)
                fila = fila_mn1 +1
                #raise ValidationError((str(fila_4)))
            
            
            if area.name== 'AUTOGESTIÓN':
                fila +=1
                sheet.merge_range('C'+str(fila)+':I'+str(fila),area.name, format_title)
                fila +=1
                #raise ValidationError((str(fila)+' '+str(c_aut)))
                fila_5=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Ingresos',area.name,fila,ing_aut,areas_instanciadas,fila+2)
                valor = fila_5+1
                fingresos3 = fila_5
                fila_6=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Costo',area.name,fila_5,c_aut,areas_instanciadas,valor)
                fila_m2=self.crear_reglon_margen_op(workbook,sheet,'Margen Op',area.name,fila_6,c_j,areas_instanciadas,valor,anterior)
                fila_g2=self.crear_reglon_tipo_presupuesto_en_excel_area2(workbook,sheet,'Gastos',area.name,fila_m2,g_aut,areas_instanciadas,valor)
                fila_mn2=self.crear_reglon_margen_op(workbook,sheet,'(=)Margen neto',area.name,fila_g2,c_j,areas_instanciadas,valor,anterior)
                fila = fila_mn2 +1
            
            fila +=1
            #fila = fila +1
        totales=self.crear_reglon_resultados(workbook,sheet,'in totales',area.name,fila,c_j,areas_instanciadas,fingresos1+1,fingresos2+1,fingresos3+1,valor,anterior)
        ##########################YEAR ANTERIORRRRRRR#############333
        year = self.date_from.year -1
            
        anterior =True
        date_f = Date.to_date(str(year)+'-01-'+'01')
        date_t = Date.to_date(str(year)+'-12-'+'31')
        json_ingresos=[]
        json_costo=[]
        json_no_operacionales=[]
        json_gastos=[]
        json_ingresos=self.obtener_posicion_presupuestaria_agrupadas_por_unidad_v('ingresos',areas_instanciadas,date_f,date_t)
        json_costo=self.obtener_posicion_presupuestaria_agrupadas_por_unidad_v('costos',areas_instanciadas,date_f,date_t)
        json_no_operacionales=self.obtener_posicion_presupuestaria_agrupadas_por_unidad_v('no_operacionales',areas_instanciadas,date_f,date_t)
        json_gastos=self.obtener_posicion_presupuestaria_agrupadas_por_unidad_v('gastos',areas_instanciadas,date_f,date_t)
       

        
                
        
        sheet.write('N9:T9', 'VARIACION DE PRESUPUESTO vs EJECUTADO '+str(self.date_from.year-1)+'-'+str(self.date_from.year), format_title4)
        sheet.write(10, 15, str(self.date_from.year), format_title4)
        sheet.write(10, 17, str(self.date_from.year-1), format_title4)
        sheet.write(10, 19, 'DIFERENCIAS', format_title4)
        columna=2
        fila = 12
        fila_1=0
        fila_2=0
        fila_3=0
        fila_4=0
        fila_5=0
        fila_6=0
        ing_j=[]
        ing_aut=[]
        ing_adm=[]
        c_j=[]
        c_aut=[]
        c_adm=[]
        g_j=[]
        g_aut=[]
        g_adm=[]
        fingresos1=0
        fingresos2=0
        fingresos3=0
        valor=0
        for area in areas_instanciadas:
            #fila+=1
            
            for ingreso in json_ingresos:
                for unidad in ingreso['unidades']:
                    if unidad['nombre_unidad']==area.name:
                        if area.name == 'PROYECTOS':
                            ing_j = unidad
                        elif area.name == 'ADMINISTRACIÓN':
                            ing_adm = unidad
                        else:
                           ing_aut = unidad 
            for cost in json_costo:
                for unidad_cost in cost['unidades']:
                    if unidad_cost['nombre_unidad']==area.name:
                        if area.name == 'PROYECTOS':
                            c_j = unidad_cost
                        elif area.name == 'ADMINISTRACIÓN':
                            c_adm = unidad_cost
                        else:
                           c_aut = unidad_cost 
            for gast in json_gastos:
                for unidad_gast in gast['unidades']:
                    if unidad_gast['nombre_unidad']==area.name:
                        if area.name == 'PROYECTOS':
                            g_j = unidad_gast
                        elif area.name == 'ADMINISTRACIÓN':
                            g_adm = unidad_gast
                        else:
                           g_aut = unidad_gast                         
            
            if area.name== 'PROYECTOS':
                sheet.merge_range('N'+str(fila)+':T'+str(fila),area.name, format_title)
               #raise ValidationError((str(ing_j)+' '+str(c_j))) crear_reglon_margen_op
                fila_1=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Ingresos',area.name,fila,ing_j,areas_instanciadas,fila+2)
                valor = fila_1+1
                fingresos1 = fila_1
                fila_2=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Costo',area.name,fila_1,c_j,areas_instanciadas,valor)
                fila_m=self.crear_reglon_margen_op(workbook,sheet,'Margen Op',area.name,fila_2,c_j,areas_instanciadas,valor,anterior)
                fila_g=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Gastos',area.name,fila_m,g_j,areas_instanciadas,valor)
                fila_mn=self.crear_reglon_margen_op(workbook,sheet,'(=)Margen neto',area.name,fila_g,c_j,areas_instanciadas,valor,anterior)
                fila = fila_mn +1
            
            
            if area.name== 'ADMINISTRACIÓN':
                fila +=1
                sheet.merge_range('N'+str(fila)+':T'+str(fila),area.name, format_title)
                fila +=1
                #raise ValidationError((str(fila)))
                fila_3=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Ingresos',area.name,fila,ing_adm,areas_instanciadas,fila+2)
                valor = fila_3 +1
                fingresos2 = fila_3
                fila_4=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Costo',area.name,fila_3,c_adm,areas_instanciadas,valor)
                fila_m1=self.crear_reglon_margen_op(workbook,sheet,'(=)Margen Op',area.name,fila_4,c_j,areas_instanciadas,valor,anterior)
                fila_g1=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Gastos',area.name,fila_m1,g_adm,areas_instanciadas,valor)
                fila_mn1=self.crear_reglon_margen_op(workbook,sheet,'(=)Margen neto',area.name,fila_g1,c_j,areas_instanciadas,valor,anterior)
                fila = fila_mn1 +1
                #raise ValidationError((str(fila_4)))
            
            
            if area.name== 'AUTOGESTIÓN':
                fila +=1
                sheet.merge_range('N'+str(fila)+':T'+str(fila),area.name, format_title)
                fila +=1
                #raise ValidationError((str(fila)+' '+str(c_aut)))
                fila_5=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Ingresos',area.name,fila,ing_aut,areas_instanciadas,fila+2)
                valor = fila_5+1
                fingresos3 = fila_5
                fila_6=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Costo',area.name,fila_5,c_aut,areas_instanciadas,valor)
                fila_m2=self.crear_reglon_margen_op(workbook,sheet,'Margen Op',area.name,fila_6,c_j,areas_instanciadas,valor,anterior)
                fila_g2=self.crear_reglon_tipo_presupuesto_en_excel_area3(workbook,sheet,'Gastos',area.name,fila_m2,g_aut,areas_instanciadas,valor)
                fila_mn2=self.crear_reglon_margen_op(workbook,sheet,'(=)Margen neto',area.name,fila_g2,c_j,areas_instanciadas,valor,anterior)
                fila = fila_mn2 +1
            
            fila +=1
            #fila = fila +1
        totales=self.crear_reglon_resultados(workbook,sheet,'in totales',area.name,fila,c_j,areas_instanciadas,fingresos1+1,fingresos2+1,fingresos3+1,valor,anterior)        
        
        
        
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

    def crear_reglon_tipo_presupuesto_en_excel_area3(self,workbook,sheet,tipo_presupuesto,n_area,fila,json,areas_instanciadas,anterior):

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
        
        valor=anterior
        format_title.set_center_across()


        fila+=1
        columna=14
        #raise ValidationError((str(fila)))
        sheet.write(fila, 13, tipo_presupuesto, format_title7)
       
        if json:
            """sheet.write(fila, columna, json['posicion_practical_amount'] or '0.00', format_title6)
            col_formula = {
                        'from_col': 'N',
                        'to_col': 'N',
                        'to_row': valor ,
                        'row': fila+1,
            }
            sheet.write_formula(
            fila ,columna+1 ,
            '=(({from_col}{row}/{to_col}{to_row})*100)'.format(
                **col_formula
            ) or '0.0%', format_title6
            )
            columna+=2"""
            
            for l in range(1,4):
                col_formula = {
                            'from_col':chr(65 +(columna-7)),
                            'to_col': chr(65 +columna),
                            'to_row': valor,
                            'row': fila+1,
                }
                sheet.write_formula(
                fila ,columna+1 ,
                '=+({from_col}{row})'.format(
                    **col_formula
                ) or '0.0', format_title6
                )
                col_formula = {
                            'from_col':chr(65 +(columna-7)),
                            'to_col': chr(65 +columna),
                            'to_row': valor,
                            'row': fila+1,
                }
                sheet.write_formula(
                fila ,columna+1 ,
                '=+({from_col}{row})'.format(
                    **col_formula
                ) or '0.0%', format_title6
                )
                columna+=2
                sheet.write(fila, columna, json['posicion_planned_amount'] or '0.00', format_title6)
                col_formula = {
                            'from_col': 'R',
                            'to_col': 'R',
                            'to_row': valor,
                            'row': fila+1,
                }
                sheet.write_formula(
                fila ,columna+1 ,
                '=(({from_col}{row}/{to_col}{to_row}*100))'.format(
                    **col_formula
                ) or '0.0%', format_title6
                )
                if l==3:
                    col_formula = {
                            'from_col':chr(65 +(columna-4)),
                            'to_col': chr(65 +(columna-2)),
                            'to_row': valor,
                            'row': fila+1,
                    }
                    sheet.write_formula(
                    fila ,columna+1 ,
                    '=({from_col}{row}-{to_col}{to_row})'.format(
                        **col_formula
                    ) or '0.0%', format_title6
                    )
                    col_formula = {
                                'from_col': chr(65 +(columna)),
                                'to_col': chr(65 +(columna-3)),
                                'to_row': fila+1,
                                'row': fila+1,
                    }
                    sheet.write_formula(
                    fila ,columna+1 ,
                    '=(({from_col}{row}/{to_col}{to_row}*100))'.format(
                        **col_formula
                    ) or '0.0%', format_title6
                    )
        else:
            sheet.write(fila, columna,  '0.00', format_title6)
            sheet.write(fila, columna+1,  '0%', format_title6)
            columna+=2
            sheet.write(fila, columna, '0.00', format_title6)
            sheet.write(fila, columna+1,  '0%', format_title6)
            columna+=2
            sheet.write(fila, columna,  '0.00', format_title6)   
            sheet.write(fila, columna+1,  '0%', format_title6)
            
            
            
            
            
            
        if tipo_presupuesto=='Ingresos':
            formato=format_title9
        else:
            formato=format_title10
        formato.set_bg_color('b4c6e7')
            
        format_title8.set_bg_color('b4c6e7')


        return fila           
        
        

    def crear_reglon_tipo_presupuesto_en_excel_area2(self,workbook,sheet,tipo_presupuesto,n_area,fila,json,areas_instanciadas,valor):

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


        fila+=1
        columna=3
        #raise ValidationError((str(fila)))
        sheet.write(fila, 2, tipo_presupuesto, format_title7)
       
        if json:
            sheet.write(fila, columna, json['posicion_practical_amount'] or '0.00', format_title6)
            col_formula = {
                        'from_col': 'D',
                        'to_col': 'D',
                        'to_row': valor ,
                        'row': fila+1,
            }
            sheet.write_formula(
            fila ,columna+1 ,
            '=(({from_col}{row}/{to_col}{to_row})*100)'.format(
                **col_formula
            ) or '0.0%', format_title6
            )
            columna+=2
            sheet.write(fila, columna, json['posicion_planned_amount'] or '0.00', format_title6)
            col_formula = {
                        'from_col': 'F',
                        'to_col': 'F',
                        'to_row': valor,
                        'row': fila+1,
            }
            sheet.write_formula(
            fila ,columna+1 ,
            '=(({from_col}{row}/{to_col}{to_row}*100))'.format(
                **col_formula
            ) or '0.0%', format_title6
            )
            columna+=2
            sheet.write(fila, columna, json['posicion_diferencia'] or '0.00', format_title6)
            col_formula = {
                        'from_col': 'H',
                        'to_col': 'D',
                        'to_row': fila+1,
                        'row': fila+1,
            }
            sheet.write_formula(
            fila ,columna+1 ,
            '=(({from_col}{row}/{to_col}{to_row}*100))'.format(
                **col_formula
            ) or '0.0%', format_title6
            )
        else:
            sheet.write(fila, columna,  '0.00', format_title6)
            sheet.write(fila, columna+1,  '0%', format_title6)
            columna+=2
            sheet.write(fila, columna, '0.00', format_title6)
            sheet.write(fila, columna+1,  '0%', format_title6)
            columna+=2
            sheet.write(fila, columna,  '0.00', format_title6)   
            sheet.write(fila, columna+1,  '0%', format_title6)
            
            
            
            
            
            
        if tipo_presupuesto=='Ingresos':
            formato=format_title9
        else:
            formato=format_title10
        formato.set_bg_color('b4c6e7')
            
        format_title8.set_bg_color('b4c6e7')


        return fila

    def crear_reglon_margen_op(self,workbook,sheet,tipo_presupuesto,n_area,fila,json,areas_instanciadas,valor,anterior):

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


        fila+=1
        if anterior:
            columna=14
        else:
            columna=3
        #raise ValidationError((str(fila)))
        format_title7.set_bg_color('b4c6e7')
        #if anterior:
        sheet.write(fila, 13, tipo_presupuesto, format_title7)
        #else:
        sheet.write(fila, 2, tipo_presupuesto, format_title7)
        format_title6.set_bg_color('b4c6e7')
        for l in range(1,4):
            
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila-1,
                                'to_row': fila,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=({from_col}{from_row}-{to_col}{to_row})'.format(
                    **col_formula
                ), format_title6
            )
            columna+=1
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila+1,
                                'to_row': valor,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                    **col_formula
                ), format_title6
            )
            if l==3:
                col_formula = {
                                    'from_col': chr(65 +(columna-1)),
                                    'to_col': chr(65 + (columna-4)),
                                    'from_row': fila+1,
                                    'to_row': fila+1,


                                }            

                sheet.write_formula(
                    fila ,columna ,
                    '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                        **col_formula
                    ), format_title6
                )                
            columna+=1
            
        if tipo_presupuesto=='Ingresos':
            formato=format_title9
        else:
            formato=format_title10
        formato.set_bg_color('b4c6e7')
            
        format_title8.set_bg_color('b4c6e7')

        return fila


    def crear_reglon_resultados(self,workbook,sheet,tipo_presupuesto,n_area,fila,json,areas_instanciadas,fila1,fila2,fila3,valor,anterior):

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


        fila+=1
        if anterior:
            columna=14
        else:
            columna=3
        #raise ValidationError((str(fila)))
        #format_title7.set_bg_color('b4c6e7')
        if anterior:
            sheet.write(fila, 13, 'ING TOT', format_title7)
        else:
            sheet.write(fila, 2, 'ING TOT', format_title7)
        for l in range(1,4):
            
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila1,
                                'to_row': fila2,
                                'to_row2': fila3,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=({from_col}{from_row}+{to_col}{to_row}+{to_col}{to_row2})'.format(
                    **col_formula
                ), format_title6
            )
            columna+=1
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila+1,
                                'to_row': fila+1,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                    **col_formula
                ), format_title6
            )
            if l ==3:
                col_formula = {
                                    'from_col': chr(65 +(columna-1)),
                                    'to_col': chr(65 + (columna-5)),
                                    'from_row': fila+1,
                                    'to_row': fila+1,


                                }            

                sheet.write_formula(
                    fila ,columna ,
                    '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                        **col_formula
                    ), format_title6
                ) 
            columna+=1
            
#########costos
        fila+=1
        fila1+=1
        fila2+=1
        fila3+=1
        if anterior:
            columna=14
        else:
            columna=3
        if anterior:
            sheet.write(fila, 13, '(-)COSTOS  OPE TOT', format_title7)
        else:
            sheet.write(fila, 2, '(-)COSTOS  OPE TOT', format_title7)
        for l in range(1,4):
            
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila1,
                                'to_row': fila2,
                                'to_row2': fila3,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=({from_col}{from_row}+{to_col}{to_row}+{to_col}{to_row2})'.format(
                    **col_formula
                ), format_title6
            )
            columna+=1
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila+1,
                                'to_row': fila,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                    **col_formula
                ), format_title6
            )
            if l ==3:
                col_formula = {
                                    'from_col': chr(65 +(columna-1)),
                                    'to_col': chr(65 + (columna-5)),
                                    'from_row': fila+1,
                                    'to_row': fila+1,


                                }            

                sheet.write_formula(
                    fila ,columna ,
                    '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                        **col_formula
                    ), format_title6
                ) 
            columna+=1
            
#########gastos
        fila+=1
        fila1+=1
        fila2+=1
        fila3+=1
        if anterior:
            columna=14
        else:
            columna=3
        if anterior:
            sheet.write(fila, 13, '(-) GASTOS FIJOS TOT', format_title7)
        else:
            sheet.write(fila, 2, '(-) GASTOS FIJOS TOT', format_title7)
        for l in range(1,4):
            
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila1,
                                'to_row': fila2,
                                'to_row2': fila3,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=({from_col}{from_row}+{to_col}{to_row}+{to_col}{to_row2})'.format(
                    **col_formula
                ), format_title6
            )
            columna+=1
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila+1,
                                'to_row': fila-1,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                    **col_formula
                ), format_title6
            )
            if l ==3:
                col_formula = {
                                    'from_col': chr(65 +(columna-1)),
                                    'to_col': chr(65 + (columna-5)),
                                    'from_row': fila+1,
                                    'to_row': fila+1,


                                }            

                sheet.write_formula(
                    fila ,columna ,
                    '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                        **col_formula
                    ), format_title6
                )             
            columna+=1
            
#########margen
        fila1+=1
        fila2+=1
        fila3+=1
        fila+=1
        if anterior:
            columna=14
        else:
            columna=3
        #format_title7.set_bg_color('b4c6e7')
        if anterior:
            sheet.write(fila, 13, '(=)MARGEN NETO TOT', format_title7)
        else:
            sheet.write(fila, 2, '(=)MARGEN NETO TOT', format_title7)
        for l in range(1,4):
            #format_title6.set_bg_color('b4c6e7')
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila1,
                                'to_row': fila2,
                                'to_row2': fila3,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=({from_col}{from_row}+{to_col}{to_row}+{to_col}{to_row2})'.format(
                    **col_formula
                ), format_title6
            )
            columna+=1
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila+1,
                                'to_row': fila-2,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                    **col_formula
                ), format_title6
            )
            if l ==3:
                col_formula = {
                                    'from_col': chr(65 +(columna-1)),
                                    'to_col': chr(65 + (columna-5)),
                                    'from_row': fila+1,
                                    'to_row': fila+1,


                                }            

                sheet.write_formula(
                    fila ,columna ,
                    '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                        **col_formula
                    ), format_title6
                )                
            columna+=1
        fila+=1
        sheet.write(fila, 2, '(-)GASTOS ADM', format_title7)
        sheet.write(fila, 13, '(-)GASTOS ADM', format_title7)
        fila+=1
        format_title2.set_bg_color('b4c6e7')
        sheet.write(fila, 2, 'RESULTADO', format_title2)
        sheet.write(fila, 13, 'RESULTADO', format_title2)
###RESULTADO
        fila1+=1
        fila2+=1
        fila3+=1
       
        if anterior:
            columna=14
        else:
            columna=3
        for l in range(1,4):
            #format_title6.set_bg_color('b4c6e7')
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila-1,
                                'to_row': fila2,
                                'to_row2': fila3,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=+({from_col}{from_row})'.format(
                    **col_formula
                ), format_title2
            )
            columna+=1
            col_formula = {
                                'from_col': chr(65 +columna),
                                'to_col': chr(65 + columna),
                                'from_row': fila+1,
                                'to_row': fila-2,


                            }            
            
            sheet.write_formula(
                fila ,columna ,
                '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                    **col_formula
                ), format_title2
            )
            if l ==3:
                col_formula = {
                                    'from_col': chr(65 +(columna-1)),
                                    'to_col': chr(65 + (columna-5)),
                                    'from_row': fila+1,
                                    'to_row': fila+1,


                                }            

                sheet.write_formula(
                    fila ,columna ,
                    '=(({from_col}{from_row}/{to_col}{to_row})*100)'.format(
                        **col_formula
                    ), format_title2
                )                
            columna+=1
        return fila




