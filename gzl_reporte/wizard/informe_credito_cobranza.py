# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
import re
import json
import base64
import logging
import mimetypes
import odoo.tools
import hashlib
from odoo import api, fields, models, tools, SUPERUSER_ID
from datetime import datetime,timedelta,date
import time
from odoo import _
from odoo.exceptions import ValidationError, except_orm
from dateutil.relativedelta import *
from . import informe_excel

import base64
from base64 import urlsafe_b64decode

import shutil



class InformeCreditoCrobranza(models.TransientModel):
    _name = "informe.credito.cobranza"

    entrega_vehiculo_id =  fields.Many2one('entrega.vehiculo',string='Entrega Vehiculo',)
    clave =  fields.Char( default="informe_credito_cobranza")



    def print_report_xls(self):

        if self.clave=='informe_credito_cobranza':
            dct=self.crear_plantilla_informe_credito_cobranza()
            return dct




    def crear_plantilla_informe_credito_cobranza(self,):
        #Instancia la plantilla
        obj_plantilla=self.env['plantillas.dinamicas.informes'].search([('identificador_clave','=','informe_credito_cobranza')],limit=1)
        if obj_plantilla:


            shutil.copy2(obj_plantilla.directorio,obj_plantilla.directorio_out)


            #####Campos de Cabecera
            campos=obj_plantilla.campos_ids.filtered(lambda l: len(l.child_ids)==0)



            lista_campos=[]
            for campo in campos:

                print(campo.name, campo.fila)
                dct={}
                resultado=self.entrega_vehiculo_id.mapped(campo.name)
                if len(resultado)>0:
                    dct['valor']=resultado[0]
                else:
                    dct['valor']=''

                dct['fila']=campo.fila
                dct['columna']=campo.columna
                dct['hoja']=campo.hoja_excel
                lista_campos.append(dct)
            #{"valor":"value", "fila": "value", "columna": "value", "hoja": "value"}
            
          #  raise ValidationError(str(lista_campos))




            objetos_patrimonio=self.entrega_vehiculo_id.montoAhorroInversiones

            lista_patrimonio= self.obtenerTablas(obj_plantilla,objetos_patrimonio,'montoAhorroInversiones','patrimonio_id.nombre')

            objetos_paginas_de_control=self.entrega_vehiculo_id.paginasDeControl

            lista_paginas= self.obtenerTablas(obj_plantilla,objetos_paginas_de_control,'paginasDeControl','pagina_id.nombre')
            
            objetos_puntos_bienes=self.entrega_vehiculo_id.tablaPuntosBienes

            lista_puntos_bienes= self.obtenerTablas(obj_plantilla,objetos_puntos_bienes,'tablaPuntosBienes','bien_id.nombre')
            
            informe_excel.informe_credito_cobranza(obj_plantilla.directorio_out,lista_campos,lista_patrimonio, lista_paginas, lista_puntos_bienes)

            


            with open(obj_plantilla.directorio_out, "rb") as f:
                data = f.read()
                file=bytes(base64.b64encode(data))


        obj_attch=self.env['ir.attachment'].create({
                                                    'name':'Informe_Credito_Cobranza.xlsx',
                                                    'datas':file,
                                                    'type':'binary', 
                                                    'store_fname':'Informe_Credito_Cobranza.xlsx'
                                                    })

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += "/web/content/%s?download=true" %(obj_attch.id)
        return{
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }




    def obtenerTablas(self, obj_plantilla, objetos,parametro,campoReferencia):
        lista_patrimonio=[]
        for dvr in objetos:

            campos_dvr=obj_plantilla.campos_ids.filtered(lambda l: parametro in l.name )
            dct_dvr={}
            lista_campos_detalle=[]
            for campo in campos_dvr.child_ids:
                dct_campos_dvr={}
                resultado=dvr.mapped(campo.name)
                if len(resultado)>0:
                    dct_campos_dvr['valor']=resultado[0]
                else:
                    dct_campos_dvr['valor']=''

                dct_campos_dvr['fila']=campo.fila
                dct_campos_dvr['columna']=campo.columna
                lista_campos_detalle.append(dct_campos_dvr)
            dct_dvr['nombre']=dvr.mapped(campoReferencia)[0]
            dct_dvr['campos']=lista_campos_detalle
            lista_patrimonio.append(dct_dvr)
        return lista_patrimonio

