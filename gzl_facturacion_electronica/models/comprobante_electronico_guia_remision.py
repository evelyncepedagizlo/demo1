# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta,date
from datetime import date
import requests
import json
import subprocess
import sys
import pytz
from io import StringIO
import base64
from base64 import urlsafe_b64decode
import unicodedata
import io 
from . import funciones
from odoo.tools.safe_eval import safe_eval


class AccountGuiaRemision(models.Model):
    _inherit = 'account.guia.remision'

    bitacora_id = fields.Many2one('bitacora.consumo.servicios')


    def procesoComprobanteElectronico(self):
        dctCodDoc={
            'guia_remision':self.env.ref('l10n_ec_tree.ec_07').name,

            }      
        #Proceso de Comprobante Electrónico
        dct={
        'name':dctCodDoc['guia_remision'] +' - '+self.name,
        'guia_remision_id':self.id
        }

        self.env.cr.execute("""select count(*) contador from bitacora_consumo_servicios where guia_remision_id={0}  """.format(self.id))
        contador = self.env.cr.dictfetchall()

        if contador[0]['contador']>0:
            raise ValidationError('El Comprobante Electrónico está en proceso')
        else:
            instanciaBitacora=self.env['bitacora.consumo.servicios'].create(dct)
            self.bitacora_id=instanciaBitacora.id

            
            try:
                instanciaBitacora.procesarComprobante()
            except json.decoder.JSONDecodeError:
                instanciaBitacora.response='Error 500 al consumir el servicio'




    def validarComprobante(self):
        objValidarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_validar_guia_remision')
        url_validarFactura=objValidarFactura.ip_address+objValidarFactura.link
        dias=datetime.now(pytz.timezone('America/Guayaquil'))
        fecha = dias.strftime('%Y-%m-%d %H:%M:%S')
        
        body_vf = {
                      "guiasRemision": [
                        {
                          "codigoExterno": self.name[0:3]+self.name[3:6]+self.name[6:],
                          "ruc": self.env.user.company_id.vat,

                        }
                      ]
                    }

        headers=json.loads(objValidarFactura.header)


        if objValidarFactura.oauth:
            token=self.token_autorizacion(objValidarFactura)
            headers['Authorization']='Bearer '+ token

        return url_validarFactura,headers,body_vf






    def procesarComprobante(self):
        dctCodDoc={
            'in_invoice':self.env.ref('l10n_ec_tree.ec_06').code,
            'out_invoice':self.env.ref('l10n_ec_tree.ec_04').code,
            'in_refund':self.env.ref('l10n_ec_tree.ec_09').code,
            'out_refund':self.env.ref('l10n_ec_tree.ec_10').code,
            'in_debit':self.env.ref('l10n_ec_tree.ec_53').code,
            'out_debit':self.env.ref('l10n_ec_tree.ec_54').code,
            'liq_purchase':self.env.ref('l10n_ec_tree.ec_08').code,
            'guia_remision':self.env.ref('l10n_ec_tree.ec_07').code,

            }


        objProcesarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_procesar_guia_remision')
        url_procesarFactura=objProcesarFactura.ip_address+objProcesarFactura.link
        

        headers =json.loads(objProcesarFactura.header)

        if objProcesarFactura.oauth:
            token=self.token_autorizacion(objProcesarFactura)
            headers['Authorization']='Bearer '+ token

        body_pf={}

        dctFactura={}


##############DETALLES 
        listaDetalle=[]
        for detalle in self.guia_remision_line_ids:
            dctDetalle={}


            dctDetalle['codDocSustento']=dctCodDoc[detalle.invoice_id.type]
            dctDetalle['codEstabDestino']=detalle.cod_establecimiento_destino.zfill(3)
            listaDetalleFactura=[]
            for lineas_cantidad in detalle.guia_remision_line_quantity_ids:
                dctDetalleLinea={}
                dctDetalleLinea['cantidad']=lineas_cantidad.cantidad
                dctDetalleLinea['codigoAdicional']=lineas_cantidad.product_id.id
                dctDetalleLinea['codigoInterno']=lineas_cantidad.product_id.id
                dctDetalleLinea['descripcion']=lineas_cantidad.product_id.name
                dctDetalleLinea['cantidad']=lineas_cantidad.cantidad
                listaDetalleFactura.append(dctDetalleLinea)

            dctDetalle['detalles']=listaDetalleFactura

            dctDetalle['dirDestinatario']= funciones.elimina_tildes(detalle.picking_id.partner_id.street) or ""  
            dctDetalle['docAduaneroUnico']=detalle.documento_aduanero
            dctDetalle['fechaEmisionDocSustento']='%s-%s-%s 00:00' % (detalle.invoice_id.invoice_date.year, str(detalle.invoice_id.invoice_date.month).zfill(2),str(detalle.invoice_id.invoice_date.day).zfill(2))


            dctDetalle['identificacionDestinatario']=detalle.picking_id.partner_id.vat
            dctDetalle['motivoTraslado']=detalle.motivo_id.name
            dctDetalle['numAutDocSustento']=detalle.invoice_id.numero_autorizacion_sri
            dctDetalle['numDocSustento']=detalle.invoice_id.l10n_latam_document_number[0:3]+'-'+detalle.invoice_id.l10n_latam_document_number[3:6]+'-'+detalle.invoice_id.l10n_latam_document_number[6:]
            dctDetalle['razonSocialDestinatario']=detalle.picking_id.partner_id.name
            dctDetalle['ruta']=(detalle.exit_route or '' ) +' -  '+(detalle.arrival_route or '')


            listaDetalle.append(dctDetalle)

        listaAdicionales=[]
        for campo in self.campos_adicionales_facturacion:
            dctAdicional={'nombre':campo.nombre,'value':campo.valor}
            listaAdicionales.append(dctAdicional)
        


        dctFactura['adicionales']=listaAdicionales
        dctFactura['agencia']= ""
        dctFactura['codigoExterno']= self.name or ""

        dctFactura['correoNotificacion']=self.env.user.email or ""
        dctFactura['destinatarios']=listaDetalle
        dctFactura['dirEstablecimiento']=funciones.elimina_tildes(self.env.user.company_id.street) or ""
        dctFactura['dirPartida']= self.direccion_partida
        dctFactura['documentosRelaciondos']= ""


        dctFactura['establecimiento']=self.name[:3]
        #dctFactura['fechaAutorizacion']='%s-%s-%s 00:00' % (self.invoice_date.year, str(self.invoice_date.month).zfill(2),str(self.invoice_date.day).zfill(2))
        dctFactura['fechaFinTransporte']='%s-%s-%s 00:00' % (self.date_end.year, str(self.date_end.month).zfill(2),str(self.date_end.day).zfill(2))
        dctFactura['fechaIniTransporte']='%s-%s-%s 00:00' % (self.date_start.year, str(self.date_start.month).zfill(2),str(self.date_start.day).zfill(2))

        dctFactura['placa']= self.placa

        dctFactura['puntoEmision']=self.name[3:6]


        dctFactura['razonSocialTransportista']= self.transporter_id.name
        #dctFactura['rise']= ""
        dctFactura['ruc']= self.env.user.company_id.vat
        dctFactura['rucTransportista']= self.transporter_id.vat
        dctFactura['secuencial']=self.name[6:]

        dctFactura['tipoIdentificacionTransportista']=self.transporter_id.l10n_latam_identification_type_id.code_venta
        dctFactura['tipoOperacion']="COM"



        body_pf={'guiasRemision':[dctFactura]}

        return url_procesarFactura,headers,body_pf



        
    def descargarXML(self, encoding='utf-8'):
        objdescargarXML=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_xml_guia_remision')
        urlDescargarXML=objdescargarXML.ip_address+objdescargarXML.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarXML.header)

        if objdescargarXML.oauth:
            token=self.token_autorizacion(objdescargarXML)
            headers['Authorization']='Bearer '+ token
        return urlDescargarXML,headers



    def descargarRide(self, encoding='utf-8'):
        objdescargarRide=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_ride_guia_remision')
        urlDescargarRide=objdescargarRide.ip_address+objdescargarRide.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarRide.header)

        if objdescargarRide.oauth:
            token=self.token_autorizacion(objdescargarRide)
            headers['Authorization']='Bearer '+ token
        return urlDescargarRide,headers


    def postJson(self, url,headers,request):
        procesar_factura_response=self.env['account.move'].postJson(url,headers,request)

        return procesar_factura_response








    def getJson(self, url,headers,request={}):
        response=self.env['account.move'].getJson(url,headers,request)

        return response

