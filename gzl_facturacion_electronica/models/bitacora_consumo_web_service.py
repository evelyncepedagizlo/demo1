# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, tools,  _
from odoo.exceptions import AccessError, UserError, ValidationError
from .servicio_web_facturacion_electronica import *
from datetime import datetime
import json
import pytz
from base64 import b64decode,b64encode


class BitacoraConsumoServicios(models.Model):   
     
    _name = 'bitacora.consumo.servicios'    
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order= 'id desc'

    name = fields.Char( string='Comprobante',)
    invoice_id = fields.Many2one( 'account.move',string='Factura')
    retention_id = fields.Many2one( 'account.retention',string='Retencion')
    guia_remision_id = fields.Many2one( 'account.guia.remision',string='Guia de Remisión')
    state = fields.Selection([('pendiente', 'Pendiente'),('proceso', 'Proceso'),('validar', 'Validada'),('generada','XMl y Ride')
                                 ], string='Estado', required=True, default='pendiente',track_visibility='onchange')

    codigo_respuesta_web_service = fields.Char( string='Codigo Respueta',track_visibility='onchange')

    url = fields.Char( string='URL',track_visibility='onchange')
    header = fields.Char( string='Header',track_visibility='onchange')
    request = fields.Char( string='Petición',track_visibility='onchange')
    response = fields.Char( string='Response',track_visibility='onchange')
    respuesta = fields.Char( string='Mensaje de SRI',track_visibility='onchange')
    etapa = fields.Char( string='Etapa',track_visibility='onchange')

    clave_acceso_sri = fields.Char( string='Clave de Acceso',track_visibility='onchange')
    numero_autorizacion_sri = fields.Char( string='Número de Autorización SRI',track_visibility='onchange')
    fecha_autorizacion_sri = fields.Datetime( string='Fecha de Autorización',track_visibility='onchange')
    estado_autorizacion_sri = fields.Selection([('PPR', 'En procesamiento'), 
                                                ('AUT', 'Autorizado'),
                                                ('NAT', 'No Autorizado'),],
                                    string='Estado de Autorización del Sri',track_visibility='onchange')




    def reenvioComprobante(self):
        url,header,diccionarioRequest=self.invoice_id.procesarComprobante()
        diccionarioRequest['facturas'][0]['claveAcceso']=self.clave_acceso_sri
        diccionarioRequest['facturas'][0]['numeroAutorizacion']=self.numero_autorizacion_sri
        diccionarioRequest['facturas'][0]['estado']=self.estado_autorizacion_sri

        response=self.invoice_id.postJson(url,header,diccionarioRequest)


        self.codigo_respuesta_web_service=str(response.status_code)
        self.response=str(json.loads(response.text))
        if response.status_code==200 :
            response = json.loads(response.text)
            dias=datetime.now(pytz.timezone('America/Guayaquil'))
            self.invoice_id.estado_autorizacion_sri=response['estado']
            self.state='proceso'
            self.invoice_id.numero_autorizacion_sri='321231231'



    def token_autorizacion(self):
        objTokenUrl=self.env.ref('gzl_facturacion_electronica.url_servicio_validar_factura')
        dct=self.invoice_id.token_autorizacion(objTokenUrl)
        self.response=str( dct)


    def seleccionComprobante(self):
        comprobante=False
        model=''
        nombreComprobante=''
        responseKey=''
        template_id = 0


        if self.invoice_id.id:
            comprobante=self.invoice_id
            model='account.move'
            dctCodDoc={
                'out_invoice':'facturas',
                'out_refund':'notasCredito',
                'out_debit':'notasDebito',
                'liq_purchase':'liquidacionesCompras',
                }
            dctCodNombre={
                'out_invoice':'Factura',
                'out_refund':'Nota de Credito',
                'out_debit':'Nota de Debito',
                'liq_purchase':'Liquidación de Compra',
                }


            nombreComprobante='{0}-{1}'.format(dctCodNombre[self.invoice_id.type],self.invoice_id.l10n_latam_document_number)





            responseKey=dctCodDoc[self.invoice_id.type]
            template_id = self.env.ref('gzl_facturacion_electronica.facturacion_electronica_email_template').id



        if self.guia_remision_id.id:
            comprobante=self.guia_remision_id
            model='account.guia.remision'
            nombreComprobante='Guia-{0}'.format(self.guia_remision_id.name)
            responseKey='guiasRemision'
            template_id = self.env.ref('gzl_facturacion_electronica.guia_remision_email_template').id
        if self.retention_id.id:
            comprobante=self.retention_id
            model='account.retention'
            nombreComprobante='Retencion-{0}'.format(self.retention_id.name)
            responseKey='retenciones'
            template_id = self.env.ref('gzl_facturacion_electronica.retencion_electronica_email_template').id
        return comprobante,model,nombreComprobante,responseKey,template_id



    def procesarComprobante(self):
        comprobante,model,nombreComprobante,responseKey,template_id=self.seleccionComprobante()


        self.etapa='Procesar Comprobante'
        if not self.numero_autorizacion_sri:
            url,header,diccionarioRequest=comprobante.procesarComprobante()
            self.url=url
            self.header=header
            self.request=diccionarioRequest
            response=comprobante.postJson(url,header,diccionarioRequest)


            self.codigo_respuesta_web_service=str(response.status_code)
            self.response=str(json.loads(response.text))
            if response.status_code==200 :
                response = json.loads(response.text)
                facturas=response['respuestas']

                for factura in facturas:                    
                    self.codigo_respuesta_web_service=factura['codigo']
                    dias=datetime.now(pytz.timezone('America/Guayaquil'))
                    comprobante.estado_autorizacion_sri='PPR'
                    self.state='proceso'
                    comprobante.numero_autorizacion_sri=''
                    self.respuesta=factura['respuesta']

                    self.estado_autorizacion_sri='PPR'

                    self.numero_autorizacion_sri=''




        else:
            raise ValidationError('La factura ya fue procesada, si desea cambiarla use Reenvio de Factura')






    def validarComprobante(self):
        comprobante,model,nombreComprobante,responseKey,template_id=self.seleccionComprobante()

        self.etapa='Validar Comprobante'


        url,header,diccionarioRequest=comprobante.validarComprobante()
        self.url=url
        self.header=header
        self.request=diccionarioRequest
        response=comprobante.postJson(url,header,diccionarioRequest)
        self.codigo_respuesta_web_service=str(response.status_code)
        self.response=str(json.loads(response.text))
        if response.status_code==200:
            response = json.loads(response.text)
            facturas=response[responseKey]




            for factura in facturas:                    
                if factura['estado']=='AUTORIZADO':
                    dias=datetime.now(pytz.timezone('America/Guayaquil'))
                    fecha = dias.strftime('%Y-%m-%d %H:%M:%S')
                    comprobante.fecha_autorizacion_sri=datetime.strptime(factura['fechaAutorizacion'],'%Y-%m-%d %H:%M')
                    comprobante.clave_acceso_sri=factura['claveAcceso']
                    comprobante.numero_autorizacion_sri=factura['numeroAutorizacion']
                    comprobante.estado_autorizacion_sri='AUT'

                    self.fecha_autorizacion_sri=datetime.strptime(factura['fechaAutorizacion'],'%Y-%m-%d %H:%M')
                    self.clave_acceso_sri=factura['claveAcceso']
                    self.numero_autorizacion_sri=factura['numeroAutorizacion']
                    self.estado_autorizacion_sri='AUT'


                    self.state='validar'
                    self.respuesta=factura['mensajeSRI']

    def descargarXML(self):

        comprobante,model,nombreComprobante,responseKey,template_id=self.seleccionComprobante()


        self.etapa='Descargar XML'

        if comprobante.estado_autorizacion_sri=='AUT':

            url,header=comprobante.descargarXML()
            self.url=url
            self.header=header
            response=comprobante.getJson(url,header)
            self.codigo_respuesta_web_service=str(response.status_code)
            self.response=str(json.loads(response.text))
            if response.status_code==200:




                b64 = json.loads(response.text)['archivo']
                binario = b64decode(b64)
                f = open('file.xml', 'wb')
                f.write(binario)
                f.close()

                self.state='generada'

                with open('file.xml', "rb") as f:
                    data = f.read()
                    file=bytes(b64encode(data))



                self.env['ir.attachment'].create({
                                                         'res_id':comprobante.id,
                                                         'res_model':model,
                                                         'name':'{0}.xml'.format(nombreComprobante),
                                                          'datas':file,
                                                          'type':'binary', 
                                                          'store_fname':'{0}.xml'.format(nombreComprobante)})

                self.env['ir.attachment'].create({
                                                         'res_id':self.id,
                                                         'res_model':'bitacora.consumo.servicios',
                                                         'name':'{0}.xml'.format(nombreComprobante),
                                                          'datas':file,
                                                          'type':'binary', 
                                                          'store_fname':'{0}.xml'.format(nombreComprobante)})



                
    def descargarRide(self):
        comprobante,model,nombreComprobante,responseKey,template_id=self.seleccionComprobante()
        self.etapa='Descargar Ride'

        if comprobante.estado_autorizacion_sri=='AUT':


            url,header=comprobante.descargarRide()
            self.url=url
            self.header=header
            
            response=comprobante.getJson(url,header)
            self.codigo_respuesta_web_service=str(response.status_code)
            self.response=str(json.loads(response.text))


            if response.status_code==200:
            
            
            
            
                b64 = json.loads(response.text)['archivo']
                binario = b64decode(b64)
                f = open('file.pdf', 'wb')
                f.write(binario)
                f.close()


                with open('file.pdf', "rb") as f:
                    data = f.read()
                    file=bytes(b64encode(data))

                self.state='generada'


                self.env['ir.attachment'].create({
                                                         'res_id':comprobante.id,
                                                         'res_model':model,
                                                         'name':'{0}.pdf'.format(nombreComprobante),
                                                          'datas':file,
                                                          'type':'binary', 
                                                          'store_fname':'{0}.pdf'.format(nombreComprobante)
                                                          })

                self.env['ir.attachment'].create({
                                                         'res_id':self.id,
                                                         'res_model':'bitacora.consumo.servicios',
                                                         'name':'{0}.pdf'.format(nombreComprobante),
                                                          'datas':file,
                                                          'type':'binary', 
                                                          'store_fname':'{0}.pdf'.format(nombreComprobante)
                                                          })
    def jobEnvioServicioProcesarFactura(self,):
        
        self.env.cr.execute("""select * from bitacora_consumo_servicios where state='pendiente'  """)
        registros = self.env.cr.dictfetchall()
        hoy = datetime.now()

        for registro in registros:
            bitacora=self.env['bitacora.consumo.servicios'].browse(registro['id'])
            bitacora.procesarComprobante()




    def jobEnvioServicioValidarFactura(self,):
        
        self.env.cr.execute("""select * from bitacora_consumo_servicios where state='proceso'  """)
        registros = self.env.cr.dictfetchall()
        hoy = datetime.now()

        for registro in registros:
            bitacora=self.env['bitacora.consumo.servicios'].browse(registro['id'])
            bitacora.validarComprobante()
            if bitacora.estado_autorizacion_sri=='AUT':
                bitacora.state='generada'
                bitacora.descargarXML()
                bitacora.descargarRide()
                comprobante,model,nombreComprobante,responseKey,template_id=bitacora.seleccionComprobante()

                template = self.env['mail.template'].browse(template_id)

                email_id=template.send_mail(registro['id'])
                
                obj_mail=self.env['mail.mail'].browse(email_id)
                obj_attach_pdf=self.env['ir.attachment'].search([('res_model','=','bitacora.consumo.servicios'),('res_id','=',registro['id']),('mimetype','=','application/pdf')],limit=1)
                obj_attach_xml=self.env['ir.attachment'].search([('res_model','=','bitacora.consumo.servicios'),('res_id','=',registro['id']),('mimetype','=','application/xml')],limit=1)
                obj_mail.attachment_ids=self.env['ir.attachment'].browse([obj_attach_pdf.id,obj_attach_xml.id])
                

                obj_mail_invoice=obj_mail.copy({'state':'cancel'})
                obj_mail_invoice.model=model
                obj_mail_invoice.res_id=comprobante.id

                try:
                    obj_mail.send()
                except:
                    pass







    def jobEnvioServicioDescargarRideXML(self,):
        
        self.env.cr.execute("""select * from bitacora_consumo_servicios where state='validar'  """)
        registros = self.env.cr.dictfetchall()
        hoy = datetime.now()

        for registro in registros:
            bitacora=self.env['bitacora.consumo.servicios'].browse(registro['id'])
            bitacora.state='generada'
            bitacora.descargarXML()
            bitacora.descargarRide()
            comprobante,model,nombreComprobante,responseKey,template_id=bitacora.seleccionComprobante()

            template = self.env['mail.template'].browse(template_id)

            email_id=template.send_mail(registro['id'])
            
            obj_mail=self.env['mail.mail'].browse(email_id)
            obj_attach_pdf=self.env['ir.attachment'].search([('res_model','=','bitacora.consumo.servicios'),('res_id','=',registro['id']),('mimetype','=','application/pdf')],limit=1)
            obj_attach_xml=self.env['ir.attachment'].search([('res_model','=','bitacora.consumo.servicios'),('res_id','=',registro['id']),('mimetype','=','application/xml')],limit=1)
            obj_mail.attachment_ids=self.env['ir.attachment'].browse([obj_attach_pdf.id,obj_attach_xml.id])
            

            obj_mail_invoice=obj_mail.copy({'state':'cancel'})
            obj_mail_invoice.model=model
            obj_mail_invoice.res_id=comprobante.id

            try:
                obj_mail.send()
            except:
                pass