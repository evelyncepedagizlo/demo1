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


class Retenciones(models.Model):
    _inherit = 'account.retention'

    bitacora_id = fields.Many2one('bitacora.consumo.servicios')

    def procesoComprobanteElectronico(self):
        dctCodDoc={
            'ret_in_invoice':self.env.ref('l10n_ec_tree.ec_11').name,

            }      
        #Proceso de Comprobante Electrónico
        dct={
        'name':dctCodDoc[self.in_type] +' - '+self.name,
        'retention_id':self.id
        }

        self.env.cr.execute("""select count(*) contador from bitacora_consumo_servicios where retention_id={0}  """.format(self.id))
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




    def token_autorizacion(self,obj_servicio):
        #Credenciales de cliente (aplicación) 
        objTokenUrl=obj_servicio.idtoken


        client_id = objTokenUrl.idCliente
        client_secret = objTokenUrl.clientSecret
        token_url = objTokenUrl.ip_address

        data=json.loads(objTokenUrl.data)
        
        access_token_response = requests.post(token_url, data=data, verify=False, allow_redirects=False, auth=(client_id, client_secret))
        tokens = json.loads(access_token_response.text)
        # api_call_headers = {'Content-Type':'application/json',
        #                     'Authorization':'Bearer '+ tokens['access_token']}
        # api_call_headers = {'Content-Type':'application/json',
        # 'Accept':'application/json'
        #                     }
        
        return tokens['access_token']
    


    
    def validarComprobante(self):
        objValidarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_validar_retencion')
        url_validarFactura=objValidarFactura.ip_address+objValidarFactura.link
        dias=datetime.now(pytz.timezone('America/Guayaquil'))
        fecha = dias.strftime('%Y-%m-%d %H:%M:%S')
        
        body_vf = {
                      "retenciones": [
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
            'ret_in_invoice':self.env.ref('l10n_ec_tree.ec_11').code
            }  

        dctCodDocSustento={
            'in_invoice':self.env.ref('l10n_ec_tree.ec_06').code,
            'out_invoice':self.env.ref('l10n_ec_tree.ec_04').code,
            'in_refund':self.env.ref('l10n_ec_tree.ec_09').code,
            'out_refund':self.env.ref('l10n_ec_tree.ec_10').code,
            'in_debit':self.env.ref('l10n_ec_tree.ec_53').code,
            'out_debit':self.env.ref('l10n_ec_tree.ec_54').code,
            'liq_purchase':self.env.ref('l10n_ec_tree.ec_08').code

            }


        objProcesarRetencion=self.env.ref('gzl_facturacion_electronica.url_servicio_procesar_retencion')
        url_procesarRetencion=objProcesarRetencion.ip_address+objProcesarRetencion.link

        headers =json.loads(objProcesarRetencion.header)

        if objProcesarRetencion.oauth:
            token=self.token_autorizacion(objProcesarRetencion)
            headers['Authorization']='Bearer '+ token



        body_pf={}

        dctFactura={}

##############DETALLES 
        listaDetalle=[]
        for detalle in self.tax_ids:
            dctDetalle={}


            dctDetalle['baseImponible']=detalle.base_ret
            dctDetalle['codDocSustento']=dctCodDocSustento[self.invoice_id.type]
            dctDetalle['codigoImpuesto']=detalle.tax_id.l10n_ec_code_base
            dctDetalle['codigoRetencion']=detalle.tax_id.l10n_ec_code_applied
            dctDetalle['fechaEmisionDocSustento']='%s-%s-%s 00:00' % (self.invoice_id.invoice_date.year, str(self.invoice_id.invoice_date.month).zfill(2),str(self.invoice_id.invoice_date.day).zfill(2))


            dctDetalle['numDocSustento']=self.invoice_id.manual_establishment.zfill(3) + self.invoice_id.manual_referral_guide.zfill(3) + self.invoice_id.manual_sequence.zfill(9)
            dctDetalle['porcentajeRetener']=float(detalle.tax_id.tarifa)
            dctDetalle['tarifa']=detalle.tax_id.tarifa
            dctDetalle['valorRetenido']=abs(round(detalle.amount,2))



            listaDetalle.append(dctDetalle)


###################################################

        dctFactura['codigoExterno']= self.name or ""

        dctFactura['correoNotificacion']=self.env.user.email or ""
        #dctFactura['detalles']=listaDetalle
        dctFactura['dirEstablecimiento']=funciones.elimina_tildes(self.env.user.company_id.street) or ""
        dctFactura['establecimiento']=self.name[0:3]
        dctFactura['fechaAutorizacion']='%s-%s-%s 00:00' % (self.date.year, str(self.date.month).zfill(2),str(self.date.day).zfill(2))

        dctFactura['fechaEmision']='%s-%s-%s 00:00' % (self.date.year, str(self.date.month).zfill(2),str(self.date.day).zfill(2))


        dctFactura['identificacionSujetoRetenido']=self.partner_id.vat or ""



        
        dctFactura['impuestos']=listaDetalle

        listaAdicionales=[]
        for campo in self.campos_adicionales_facturacion:
            dctAdicional={'nombre':campo.nombre,'value':campo.valor}
            listaAdicionales.append(dctAdicional)
        


        dctFactura['infoAdicional']=listaAdicionales



        dctFactura['periodoFiscal']= str(self.date.month).zfill(2)+'/'+str(self.date.year)


        dctFactura['puntoEmision']= self.name[3:6]
        dctFactura['razonSocialSujetoRetenido']= funciones.elimina_tildes(self.partner_id.name)
        dctFactura['ruc']= self.env.user.company_id.vat
        dctFactura['secuencial']=self.name[6:]

        dctFactura['tipoIdentificacionSujetoRetenido']=self.partner_id.l10n_latam_identification_type_id.code_venta





        body_pf={'retenciones':[dctFactura]}

        return url_procesarRetencion,headers,body_pf



    def postJson(self, url,headers,request):
        procesar_factura_response=self.env['account.move'].postJson(url,headers,request)

        return procesar_factura_response


    def getJson(self, url,headers,request={}):
        response=self.env['account.move'].getJson(url,headers,request)

        return response






        
    def descargarXML(self, encoding='utf-8'):
        objdescargarXML=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_xml_retencion')
        urlDescargarXML=objdescargarXML.ip_address+objdescargarXML.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarXML.header)

        if objdescargarXML.oauth:
            token=self.token_autorizacion(objdescargarXML)
            headers['Authorization']='Bearer '+ token
        return urlDescargarXML,headers



    def descargarRide(self, encoding='utf-8'):
        objdescargarRide=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_ride_retencion')
        urlDescargarRide=objdescargarRide.ip_address+objdescargarRide.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarRide.header)

        if objdescargarRide.oauth:
            token=self.token_autorizacion(objdescargarRide)
            headers['Authorization']='Bearer '+ token
        return urlDescargarRide,headers


