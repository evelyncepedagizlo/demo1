# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import datetime
import time
from odoo.exceptions import ValidationError, except_orm
from odoo.exceptions import UserError
from io import StringIO
import base64
from base64 import urlsafe_b64decode
import os
import io 
from  . import formato_documento_entregable_hito
import unicodedata
import subprocess
from subprocess import getoutput

from datetime import datetime,timedelta,date
import pytz
import calendar
from dateutil.relativedelta import relativedelta



class ReporteEntregable(models.TransientModel):
	_name="reporte.entregable.hito"
	_description = "Reporte Hitos"

	name=fields.Char(String='Name',default="Reporte de Entrega Hito")

	project_id=fields.Many2one('project.project' , string='Proyecto')

	hito_id=fields.Many2one('project.task', string='Hito')


	descripcion = fields.Text(string="Descripcion")


	observaciones= fields.Text(string="Observaciones")

	elaborado_por=fields.Many2one('res.users', string='Elaborador por',default=lambda self: self._uid, store=True)
	compania_id=fields.Many2one('res.partner')
	cargo=fields.Char(string="Cargo")



	revisado_por=fields.Many2one('res.partner', string='Revisado por', )
	compania_revisado_por_id=fields.Many2one('res.partner')
	cargo_revisado_por=fields.Char(string="Cargo")


	docx_filename = fields.Char('Nombre Archivo Word')
	archivo_docx = fields.Binary('Archivo Word')


	@api.onchange('project_id')
	def onchange_project_id(self):
		if self.project_id:
			self.descripcion=self.hito_id.description
			self.revisado_por=self.project_id.representante.id
			self.compania_revisado_por_id=self.project_id.partner_id.id

	@api.constrains('project_id')
	def constrains_project_id(self):
		if self.project_id:
			self.compania_revisado_por_id=self.project_id.partner_id.id














	@api.onchange('hito_id')
	def onchange_ingresar_descripcion_hito(self):
		if self.hito_id:
			self.descripcion=self.hito_id.description
			self.observaciones=self.hito_id.observaciones


	@api.onchange('elaborado_por')
	def onchange_elaborado_por(self):
		if self.elaborado_por:
			self.compania_id=self.elaborado_por.partner_id.parent_id.id
			self.cargo=self.elaborado_por.partner_id.function




	@api.constrains('compania_id','cargo')
	def constrains_elaborado_por(self):
		if self.cargo or self.compania_id :
			#self.elaborado_por.partner_id.parent_id=self.compania_id.id
			self.elaborado_por.partner_id.function=self.cargo







	@api.onchange('revisado_por')
	def onchange_revisado_por(self):
		if self.revisado_por:
			self.cargo_revisado_por=self.revisado_por.function


	@api.constrains('cargo_revisado_por')
	def constrains_revisado_por(self):
		if self.cargo_revisado_por :
			self.revisado_por.function=self.cargo_revisado_por






	@api.constrains('observaciones','descripcion')
	def ingresar_descripcion_hito(self):
		if self.descripcion:
			self.hito_id.description=self.descripcion
			self.hito_id.observaciones=self.observaciones





	
	# def generar_word_hito(self):
	# 	dct=self.crear_informe_entrega_hito()

	# 	self.env.cr.execute("""select * from ir_attachment where res_id='{0}' and res_model='{1}'   """.format(self.id,'reporte.entregable.hito'))
	# 	res=self.env.cr.dictfetchall()	



	# 	obj=self.env['reporte.entregable.hito'].browse(self.id)
	# 	if len(res) == 0:
	# 		obj_attach=self.env['ir.attachment']
	# 		obj_xls_attach=obj_attach.create({'name':dct['docx_filename'],
	# 									'res_model':'reporte.entregable.hito',
	# 									'res_id':self.id,
	# 									'datas':dct['archivo_docx'],
	# 									'type':'binary',
	# 									'datas_fname':dct['docx_filename']})

	# 	else:
	# 		obj_attach=self.env['ir.attachment'].browse(res[0]['id'])
	# 		obj_attach.write({'name':dct['docx_filename'],
	# 				'res_model':'reporte.entregable.hito',
	# 				'res_id':self.id,
	# 				'datas':dct['archivo_docx'],
	# 				'type':'binary',
	# 				'datas_fname':dct['docx_filename']})
	# 		obj_xls_attach=obj_attach

	# 	if not self.env['project.project'].IP_servidor() or not self.env['project.project'].Puerto_servidor():

	# 		raise ValidationError(_('AVISO! \n \n No se ha registrado la ip del servidor ni el puerto para generar el documento \n \n Vaya al menu Facturacion/Configuraciones/Ip Reportes/Registro Ip \n \n Registre la Ip y el Puerto para descargar el Documento'))

	# 	else:

	# 		enlace="""http://{0}:{1}/web/content/{2}?download=true""".format(self.env['project.project'].IP_servidor(),self.env['project.project'].Puerto_servidor(),obj_xls_attach.id)
	# 		return{
	# 			"type": "ir.actions.act_url",
	# 			"url": enlace,
	# 			"target": "new",
	# 			}









	def crear_informe_entrega_hito(self,):
		#Instancia la plantilla
		obj_plantilla=self.env['plantillas.dinamicas.informes'].search([('identificador_clave','=','informe_reporte_hitos')],limit=1)
		if obj_plantilla:

			plantilla=obj_plantilla.archivos_ids.filtered(lambda l: l.company_id.id==self.project_id.project_company.id)
			if len(plantilla):
				lista=[]
				#Crea el documento en la muk_dms.file para poderlo instanciar
				dct={

				'name':'Informes_Entregable_hito.docx',			
				'content':plantilla.plantilla,
				'directory':int(obj_plantilla.directorio.id),
				}

				obj_file=self.env['muk_dms.file'].create(dct)


				#Se captura la ruta del documento duplicado
				ruta_del_documento=obj_file.path



				#####Se sacan los campos de la plantilla del objeto plantillas.dinamicas.informes
				campos=obj_plantilla.campos_ids.filtered(lambda l: len(l.child_ids)==0)

				lista_campos=[]
				for campo in campos:

					dct={}
					resultado=self.mapped(campo.name)
					if len(resultado)>0:
						dct['valor']=resultado[0]
					else:
						dct['valor']=''

					dct['identificar_docx']=campo.identificar_docx
					lista_campos.append(dct)



				contador=0
				lista_detalle=[]
				dct_caracteristica={}
				dct_final={}






				for caracteristica in self.hito_id.epica_id:
					contador+=1

					dct_caracteristica={
						'item':'ARD'+' '+str(contador),
						'name':caracteristica.name,
						'reporte_ram_ids':self.id
					}
					self.env['consultar.historias'].create(dct_caracteristica)

					lista_historias=[]
					contador_historia=1
					for historia in caracteristica.id_historia:
						dct={
						'item':str(contador_historia),
						'name':historia.name,
						'estado':historia.estado_histora_id.name or "",
						'observaciones':historia.observaciones or ""
						}
						lista_historias.append(dct)
						contador_historia+=1


					dct_caracteristica['detalle_historias']=lista_historias

					lista_detalle.append(dct_caracteristica)















				#Llamo al word del reporte
				formato_documento_entregable_hito.crear_reporte_entregable_hito(obj_plantilla.directorio.settings.complete_base_path+ruta_del_documento,lista_campos,lista_detalle)


				with open(obj_plantilla.directorio.settings.complete_base_path+ruta_del_documento, "rb") as f:
					data = f.read()
					file=bytes(base64.b64encode(data))  
					


				dct={'docx_filename':'Informes_Entregable_hito.docx','archivo_docx':file}

				self.write({'docx_filename':'Informes_Entregable_hito.docx','archivo_docx':file})

				obj_file.unlink()


			return dct











































	#			dct={

	#			'name':obj.datas_fname,			
	#			'content':obj.datas,
	#			'directory':directory.id,
	#			}

	#			obj_file=self.env['muk_dms.file'].create(dct)


	#			ruta_del_documento=obj_file.path

	#			#####Campos de Cabecera
	#			campos=self.plantilla_dinamica.campos_ids.filtered(lambda l: len(l.child_ids)==0)

	#			lista_campos=[]
	#			for campo in campos:

	#				print(campo.name, campo.fila)
	#				dct={}
	#				resultado=self.mapped(campo.name)
	#				if len(resultado)>0:
	#					dct['valor']=resultado[0]
	#				else:
	#					dct['valor']=''

	#				dct['fila']=campo.fila
	#				dct['columna']=campo.columna
	#				lista_campos.append(dct)



	# ########Checklist Habilitacion
	#			lista_checklist=[]
	#			dvr_ids=self.mapped('x_detalle_checklist_habilitacion')

	#			for dvr in dvr_ids:

	#				campos_dvr=self.plantilla_dinamica.campos_ids.filtered(lambda l: 'x_detalle_checklist_habilitacion' in l.name )
	#				dct_dvr={}
	#				lista_campos_detalle=[]
	#				for campo in campos_dvr.child_ids:
	#					dct_campos_dvr={}
	#					resultado=dvr.mapped(campo.name)
	#					if len(resultado)>0:
	#						dct_campos_dvr['valor']=resultado[0]
	#					else:
	#						dct_campos_dvr['valor']=''

	#					dct_campos_dvr['fila']=campo.fila
	#					dct_campos_dvr['columna']=campo.columna
	#					lista_campos_detalle.append(dct_campos_dvr)
	#				dct_dvr['nombre']=dvr.mapped('x_parametro.x_name')[0]
	#				dct_dvr['campos']=lista_campos_detalle
	#				lista_checklist.append(dct_dvr)
	#			print(lista_checklist)

	#			informe_excel.informe_formato_checklist_habilitacion(ruta_del_documento,lista_campos,lista_checklist)



	#		with open('/mnt/extra-addons/muk_dms/static/src/php/Gestor_Informes'+ruta_del_documento, "rb") as f:
	#			data = f.read()
	#			file=bytes(base64.b64encode(data))
			  


	#		#except:
	#		 #   raise ValidationError(_('No existe informacion para generar el informe'))
	#		obj_file.unlink()

	#		dct={

	#		'name':obj.datas_fname,			
	#		'content':file,
	#		'directory':int(self.id),
	#		}

	#		obj_file_nuevo=self.env['muk_dms.file'].create(dct)







