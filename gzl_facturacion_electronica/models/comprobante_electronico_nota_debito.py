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


class FacturacionElectronica(models.Model):
    _inherit = 'account.move'


    def validarComprobanteNotaDebito(self):
        objValidarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_validar_nota_debito')
        url_validarFactura=objValidarFactura.ip_address+objValidarFactura.link
        dias=datetime.now(pytz.timezone('America/Guayaquil'))
        fecha = dias.strftime('%Y-%m-%d %H:%M:%S')
        
        body_vf = {
                      "notasDebito": [
                        {
                          "codigoExterno": self.l10n_latam_document_number[0:3]+self.l10n_latam_document_number[3:6]+self.l10n_latam_document_number[6:],
                          "ruc": self.env.user.company_id.vat,

                        }
                      ]
                    }

        headers=json.loads(objValidarFactura.header)


        if objValidarFactura.oauth:
            token=self.token_autorizacion(objValidarFactura)
            headers['Authorization']='Bearer '+ token

        return url_validarFactura,headers,body_vf






    def procesarDocumentoNotaDebito(self):


        dctCodDoc={
            'in_invoice':self.env.ref('l10n_ec_tree.ec_06').code,
            'out_invoice':self.env.ref('l10n_ec_tree.ec_04').code,
            'in_refund':self.env.ref('l10n_ec_tree.ec_09').code,
            'out_refund':self.env.ref('l10n_ec_tree.ec_10').code,
            'in_debit':self.env.ref('l10n_ec_tree.ec_53').code,
            'out_debit':self.env.ref('l10n_ec_tree.ec_54').code,
            'liq_purchase':self.env.ref('l10n_ec_tree.ec_08').code

            }



        objProcesarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_procesar_nota_debito')
        url_procesarFactura=objProcesarFactura.ip_address+objProcesarFactura.link
        

        headers =json.loads(objProcesarFactura.header)

        if objProcesarFactura.oauth:
            token=self.token_autorizacion(objProcesarFactura)
            headers['Authorization']='Bearer '+ token



        facturaReferenciada=self.debit_origin_id


        body_pf={}

        dctFactura={}


##############DETALLES 
        listaDetalle=[]
        listaTipoImpuestos=[]
        listaImpuestosDetalle=[]
        for detalle in self.invoice_line_ids:
            dctDetalle={}
            impuestos=detalle.tax_ids.mapped("id")
        
            listaTipoImpuestos= listaTipoImpuestos +impuestos

            dctDetalle['cantidad']=detalle.quantity 
            dctDetalle['codigoAdicional']=str(detalle.id)
            dctDetalle['codigoInterno']=str(detalle.id)
            dctDetalle['descripcion']=funciones.elimina_tildes(detalle.name) or ""
            dctDetalle['descuento']=(detalle.discount*detalle.price_unit/100) 



            listadctDetalleAdicional=[]
            dctDetalleAdicional={}

            listaImpuesto=[]
            for impuesto in detalle.tax_ids:
                obj_impuesto=self.env['account.tax'].browse(impuesto.id)
                valor=obj_impuesto._compute_amount(round(detalle.price_subtotal,2),0)
                  

                dctImpuesto={}
                dctImpuesto['baseImponible']=round(detalle.price_subtotal,2)
                dctImpuesto['codigoImpuesto']=impuesto.l10n_ec_code_base or ""
                dctImpuesto['codigoPorcentaje']=impuesto.l10n_ec_code_applied or ""
                dctImpuesto['tarifa']=str(impuesto.tarifa)
                dctImpuesto['valor']=round(valor,2)

                listaImpuesto.append(dctImpuesto)
                listaImpuestosDetalle.append(dctImpuesto)

            if len(listaImpuesto)==0:
                dctListaImpuesto={
                "baseImponible":self.amount_untaxed,
                "codigoImpuesto":'2',
                "codigoPorcentaje":'0',
                "tarifa":'0',
                "valor":0.0
                }
                listaImpuesto.append(dctListaImpuesto)
                listaImpuestosDetalle.append(dctListaImpuesto)

            dctDetalle['detallesImpuesto']=listaImpuesto
            dctDetalle['iva']=''
            dctDetalle['precioTotalSinImpuesto']=round(detalle.price_subtotal,2)
            dctDetalle['precioUnitario']=round(detalle.price_unit ,2)



            listaDetalle.append(dctDetalle)


###################################################

        listaTipoImpuestos=list(set(listaTipoImpuestos))

        listaTotalConImpuestos=[]
        for impuesto in listaTipoImpuestos:
            lines=self.invoice_line_ids.filtered(lambda l: impuesto in l.tax_ids.ids)

            subtotal=sum(lines.mapped('price_subtotal'))
            obj_impuesto=self.env['account.tax'].browse(impuesto)
            valor=obj_impuesto._compute_amount(subtotal,0)

            dctTotalConImpuestos={}
            dctTotalConImpuestos['baseImponible']=round(subtotal,2)
            dctTotalConImpuestos['codigoImpuesto']=str(obj_impuesto.l10n_ec_code_base)
            dctTotalConImpuestos['codigoPorcentaje']=str(obj_impuesto.l10n_ec_code_applied)
            dctTotalConImpuestos['tarifa']= round(float(obj_impuesto.tarifa),2)
            dctTotalConImpuestos['valor']=round(valor,2)
            dctTotalConImpuestos['valorDevolucionIva']=0

            listaTotalConImpuestos.append(dctTotalConImpuestos)




        listaAdicionales=[]
        for campo in self.campos_adicionales_facturacion:
            dctAdicional={'nombre':campo.nombre,'value':campo.valor}
            listaAdicionales.append(dctAdicional)
        


        dctFactura['adicionales']=listaAdicionales
        dctFactura['claveInterna']=""
        dctFactura['codDocModificado']=dctCodDoc[facturaReferenciada.type]
        dctFactura['codigoExterno']= self.l10n_latam_document_number or ""

        dctFactura['correoNotificacion']=self.env.user.email or ""
        #dctFactura['detalles']=listaDetalle
        dctFactura['dirEstablecimiento']=funciones.elimina_tildes(self.env.user.company_id.street) or ""
        dctFactura['direccionComprodar']=funciones.elimina_tildes(self.partner_id.street )or ""
        dctFactura['establecimiento']=self.l10n_latam_document_number[0:3]
        dctFactura['fechaAutorizacion']='%s-%s-%s 00:00' % (self.invoice_date.year, str(self.invoice_date.month).zfill(2),str(self.invoice_date.day).zfill(2))

        dctFactura['fechaEmision']='%s-%s-%s 00:00' % (self.invoice_date.year, str(self.invoice_date.month).zfill(2),str(self.invoice_date.day).zfill(2))
        dctFactura['fechaEmisionDocSustentoDb']='%s-%s-%s 00:00' % (self.debit_origin_id.invoice_date.year, str(self.debit_origin_id.invoice_date.month).zfill(2),str(self.debit_origin_id.invoice_date.day).zfill(2))







        dctFactura['identificacionComprador']=self.partner_id.vat or ""
        dctFactura['impuestos']=listaImpuestosDetalle

        dctFactura['infoAdicional']=""

        dctFactura['motivos']=[{ "razon": self.narration or "No especifica" ,"valor": abs(round(self.amount_untaxed,2))}]

        dctFactura['numDocModificado']=facturaReferenciada.l10n_latam_document_number[0:3]+'-'+facturaReferenciada.l10n_latam_document_number[3:6]+'-'+facturaReferenciada.l10n_latam_document_number[6:]


        dctFactura['puntoEmision']= self.journal_id.auth_out_invoice_id.serie_emision
        dctFactura['razonSocialComprador']= funciones.elimina_tildes(self.partner_id.name)
        #dctFactura['rise']= ""
        dctFactura['ruc']= self.env.user.company_id.vat
        dctFactura['secuencial']=self.l10n_latam_document_number[6:]
        dctFactura['telefonoComprodar']=self.partner_id.phone

        dctFactura['tipoIdentificacionComprador']=self.partner_id.l10n_latam_identification_type_id.code_venta
        dctFactura['tipoOperacion']="COM"
      #  dctFactura['totalConImpuestos']=listaTotalConImpuestos
        dctFactura['totalSinImpuestos']=round(self.amount_untaxed,2)
        dctFactura['valorTotal']=  abs(round(self.amount_total,2))








        body_pf={'notasDebito':[dctFactura]}

        return url_procesarFactura,headers,body_pf






































        
    def descargarXMLNotaDebito(self, encoding='utf-8'):
        objdescargarXML=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_xml_nota_debito')
        urlDescargarXML=objdescargarXML.ip_address+objdescargarXML.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarXML.header)

        if objdescargarXML.oauth:
            token=self.token_autorizacion(objdescargarXML)
            headers['Authorization']='Bearer '+ token
        return urlDescargarXML,headers



    def descargarRideNotaDebito(self, encoding='utf-8'):
        objdescargarRide=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_ride_nota_debito')
        urlDescargarRide=objdescargarRide.ip_address+objdescargarRide.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarRide.header)

        if objdescargarRide.oauth:
            token=self.token_autorizacion(objdescargarRide)
            headers['Authorization']='Bearer '+ token
        return urlDescargarRide,headers



