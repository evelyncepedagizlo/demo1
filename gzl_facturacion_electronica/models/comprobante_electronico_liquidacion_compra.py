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


    def validarComprobanteLiquidacionCompra(self):
        objValidarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_validar_liquidacion')
        url_validarFactura=objValidarFactura.ip_address+objValidarFactura.link
        dias=datetime.now(pytz.timezone('America/Guayaquil'))
        fecha = dias.strftime('%Y-%m-%d %H:%M:%S')
        
        body_vf = {
                      "liquidacionesCompras": [
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






    def procesarDocumentoLiquidacionCompra(self):


        dctCodDoc={
            'in_invoice':self.env.ref('l10n_ec_tree.ec_06').code,
            'out_invoice':self.env.ref('l10n_ec_tree.ec_04').code,
            'in_refund':self.env.ref('l10n_ec_tree.ec_09').code,
            'out_refund':self.env.ref('l10n_ec_tree.ec_10').code,
            'in_debit':self.env.ref('l10n_ec_tree.ec_53').code,
            'out_debit':self.env.ref('l10n_ec_tree.ec_54').code,
            'liq_purchase':self.env.ref('l10n_ec_tree.ec_08').code

            }



        objProcesarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_procesar_liquidacion')
        url_procesarFactura=objProcesarFactura.ip_address+objProcesarFactura.link


        headers =json.loads(objProcesarFactura.header)

        if objProcesarFactura.oauth:
            token=self.token_autorizacion(objProcesarFactura)
            headers['Authorization']='Bearer '+ token





        body_pf={}

        dctFactura={}


##############DETALLES 
        listaDetalle=[]
        listaTipoImpuestos=[]
        for detalle in self.invoice_line_ids:
            dctDetalle={}
            impuestos=detalle.tax_ids.mapped("id")
        
            listaTipoImpuestos= listaTipoImpuestos +impuestos

            dctDetalle['cantidad']=detalle.quantity 
            dctDetalle['codigoAuxiliar']=str(detalle.product_id.id)
            dctDetalle['codigoPrincipal']=str(detalle.product_id.id)
            dctDetalle['descripcion']=funciones.elimina_tildes(detalle.name) or ""
            dctDetalle['descuento']=(detalle.discount*detalle.price_unit/100) 


            listaImpuesto=[]
            for impuesto in detalle.tax_ids:
                dctImpuesto={}
                dctImpuesto['baseImponible']=round(detalle.price_subtotal,2)
                dctImpuesto['codigo']=impuesto.l10n_ec_code_base or ""
                dctImpuesto['codigoPorcentaje']=impuesto.l10n_ec_code_applied or ""
                dctImpuesto['tarifa']=float(impuesto.tarifa)
                dctImpuesto['valor']=round(detalle.price_subtotal*impuesto.amount/100,2)

                listaImpuesto.append(dctImpuesto)


            if len(listaImpuesto)==0:
                dctListaImpuesto={
                "baseImponible":self.amount_untaxed,
                "codigo":'2',
                "codigoPorcentaje":'0',
                "tarifa":0,
                "valor":0.0
                }
                listaImpuesto.append(dctListaImpuesto)


            dctDetalle['impuestos']=listaImpuesto
            dctDetalle['precioSinSubsidio']=round(detalle.price_subtotal,2)
            dctDetalle['precioTotalSinImpuesto']=round(detalle.price_subtotal,2)
            dctDetalle['precioUnitario']=round(detalle.price_unit ,2)
            dctDetalle['unidadMedida']=detalle.product_id.uom_id.name



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
            dctTotalConImpuestos['codigo']=str(obj_impuesto.l10n_ec_code_base)
            dctTotalConImpuestos['codigoPorcentaje']=str(obj_impuesto.l10n_ec_code_applied)

            dctTotalConImpuestos['descuentoAdicional']=0
            dctTotalConImpuestos['tarifa']= round(float(obj_impuesto.tarifa),2)
            dctTotalConImpuestos['valor']=round(valor,2)

            listaTotalConImpuestos.append(dctTotalConImpuestos)

        if len(listaTotalConImpuestos)==0:
            dctListaImpuesto={
            "baseImponible":self.amount_untaxed,
            "codigo":'2',
            "codigoPorcentaje":'0',
            "tarifa":0,
            "valor":0.0,
            }
            listaTotalConImpuestos.append(dctListaImpuesto)


        listaAdicionales=[]
        for campo in self.campos_adicionales_facturacion:
            dctAdicional={'nombre':campo.nombre,'value':campo.valor}
            listaAdicionales.append(dctAdicional)
        


        listaDetalleFormaPago=[]
        dctFormaPago={}
        dctFormaPago['formaPago']=str(self.method_payment.code or '')


        if self.invoice_payment_term_id.id:
            dctFormaPago['plazo']=max(self.invoice_payment_term_id.line_ids.mapped('days'))
        else:
            dctFormaPago['plazo']=(self.invoice_date_due  - self.invoice_date ).days
        dctFormaPago['total']=round(self.amount_total,2)
        dctFormaPago['unidadTiempo']='dias'

        listaDetalleFormaPago.append(dctFormaPago)



        listaReembolso=[]
        facturaReembolso=self.documento_reembolso_id
        dctReembolso={}




##############DETALLES 
        listaImpuesto=[]
        for detalle in facturaReembolso.invoice_line_ids:
            impuestos=detalle.tax_ids.filtered(lambda l: l.tax_group_id.code not in ['ret_vat_b', 'ret_vat_srv', 'ret_ir','no_ret_ir']).mapped("id")
            listaImpuesto= listaImpuesto +impuestos

        listaImpuesto=list(set(listaImpuesto))


        listaImpuestoDct=[]
        for impuesto in listaImpuesto:
            dctImpuesto={}

            baseImponible=sum(facturaReembolso.invoice_line_ids.filtered(lambda l: impuesto in  l.tax_ids.ids).mapped('price_subtotal'))
            obj_impuesto=self.env['account.tax'].browse(impuesto)
            valor=obj_impuesto._compute_amount(round(baseImponible,2),0)
              

            dctImpuesto['baseImponibleReembolso']=round(baseImponible,2)
            dctImpuesto['codigo']=obj_impuesto.l10n_ec_code_base or ""
            dctImpuesto['codigoPorcentaje']=obj_impuesto.l10n_ec_code_applied or ""
            dctImpuesto['impuestoReembolso']=round(valor,2)
            dctImpuesto['tarifa']=obj_impuesto.tarifa
            listaImpuestoDct.append(dctImpuesto)


        if len(listaImpuestoDct)==0:
            dctImpuesto={}

            baseImponible=sum(facturaReembolso.invoice_line_ids.filtered(lambda l: impuesto in  l.tax_ids.ids).mapped('price_subtotal'))
            obj_impuesto=self.env['account.tax'].browse(impuesto)
            valor=obj_impuesto._compute_amount(round(baseImponible,2),0)
              

            dctImpuesto['baseImponibleReembolso']=round(baseImponible,2)
            dctImpuesto['codigo']='2'
            dctImpuesto['codigoPorcentaje']='0'
            dctImpuesto['impuestoReembolso']=0.0
            dctImpuesto['tarifa']='0'
            listaImpuestoDct.append(dctImpuesto)



        dctReembolso['codDocReembolso']=facturaReembolso.l10n_latam_document_type_id.code
        dctReembolso['codPaisPagoProveedorReembolso']='593'
        dctReembolso['detalleImpuestos']=listaImpuestoDct
        dctReembolso['estabDocReembolso']=facturaReembolso.l10n_latam_document_number[0:3]
        dctReembolso['fechaEmisionDocReembolso']='%s/%s/%s' % (str(facturaReembolso.invoice_date.day).zfill(2), str(facturaReembolso.invoice_date.month).zfill(2),facturaReembolso.invoice_date.year)
        dctReembolso['identificacionProveedorReembolso']=facturaReembolso.partner_id.vat
        dctReembolso['numeroautorizacionDocReemb']=facturaReembolso.auth_number

        dctReembolso['ptoEmiDocReembolso']=facturaReembolso.l10n_latam_document_number[3:6]
        dctReembolso['secuencialDocReembolso']=facturaReembolso.l10n_latam_document_number[6:]
        dctReembolso['tipoIdentificacionProveedorReembolso']=facturaReembolso.partner_id.l10n_latam_identification_type_id.code_venta
        tipoProveedorReembolso=facturaReembolso.partner_id.tipo_proveedor_reembolso_id.id
        if not tipoProveedorReembolso:
            if facturaReembolso.partner_id.company_type=='company':
                tipoProveedorReembolso=self.env.ref('gzl_facturacion_electronica.tipo_proveedor_reembolso_sociedad').code
            else:
                tipoProveedorReembolso=self.env.ref('gzl_facturacion_electronica.tipo_proveedor_reembolso_persona').code
        else:
            tipoProveedorReembolso=facturaReembolso.partner_id.tipo_proveedor_reembolso_id.code



        dctReembolso['tipoProveedorReembolso']=tipoProveedorReembolso


        listaReembolso.append(dctReembolso)

        totalComprobantesReembolso=0
        if facturaReembolso.l10n_latam_document_type_id.code=='41':
            totalComprobantesReembolso=1




        dctFactura['codDocReembolso']=facturaReembolso.l10n_latam_document_type_id.code
        dctFactura['codigoExterno']= self.l10n_latam_document_number or ""

        dctFactura['correoNotificacion']=self.env.user.email or ""
        dctFactura['detalles']=listaDetalle
        dctFactura['dirEstablecimiento']=funciones.elimina_tildes(self.env.user.company_id.street) or ""
        dctFactura['direccionProveedor']=funciones.elimina_tildes(self.partner_id.street )or ""
        dctFactura['estab']=self.l10n_latam_document_number[0:3]

        dctFactura['fechaEmision']='%s-%s-%s 00:00' % (self.invoice_date.year, str(self.invoice_date.month).zfill(2),str(self.invoice_date.day).zfill(2))


        dctFactura['identificacionProveedor']=self.partner_id.vat or ""
        dctFactura['importeTotal']=  round(self.amount_total,2)
        dctFactura['infoAdicional']= listaAdicionales
        dctFactura['maquinaFiscal']= {}
        dctFactura['maquinaFiscal']['marca']= self.marca or "No está definido"
        dctFactura['maquinaFiscal']['modelo']= self.modelo or "No está definido"       
        dctFactura['maquinaFiscal']['serie']= self.serie  or "No está definido"

        dctFactura['moneda']= 'DOLAR'
        dctFactura['pagos']= listaDetalleFormaPago

        dctFactura['ptoEmi']= self.l10n_latam_document_number[3:6]



        dctFactura['razonSocialProveedor']= funciones.elimina_tildes(self.partner_id.name)
        if facturaReembolso.l10n_latam_document_type_id.code=='41':
            dctFactura['reembolsos']=listaReembolso


        dctFactura['ruc']= self.env.user.company_id.vat
        dctFactura['secuencial']=self.l10n_latam_document_number[6:]

        dctFactura['tipoIdentificacionProveedor']=self.partner_id.l10n_latam_identification_type_id.code_venta


        #dctFactura['tipoNegociable']=""

        dctFactura['totalBaseImponibleReembolso']=self.documento_reembolso_id.amount_untaxed
        dctFactura['totalComprobantesReembolso']=totalComprobantesReembolso


        dctFactura['totalConImpuestos']=listaTotalConImpuestos




        listaDescuento=[]
        for detalle in self.invoice_line_ids:
            dctDetalle={}
            dctDetalle['descuento']=(detalle.discount*detalle.price_unit/100) 
            listaDescuento.append(dctDetalle)

        dctFactura['totalDescuento']=sum(map(lambda x: x['descuento'], listaDescuento))
        dctFactura['totalImpuestoReembolso']=(sum(map(lambda x: x['impuestoReembolso'], listaImpuestoDct)))

        dctFactura['totalSinImpuestos']=  self.amount_untaxed


        body_pf={'liquidacionesCompras':[dctFactura]}

        return url_procesarFactura,headers,body_pf


        
    def descargarXMLLiquidacionCompra(self, encoding='utf-8'):
        objdescargarXML=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_xml_liquidacion')
        urlDescargarXML=objdescargarXML.ip_address+objdescargarXML.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarXML.header)

        if objdescargarXML.oauth:
            token=self.token_autorizacion(objdescargarXML)
            headers['Authorization']='Bearer '+ token
        return urlDescargarXML,headers



    def descargarRideLiquidacionCompra(self, encoding='utf-8'):
        objdescargarRide=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_ride_liquidacion')
        urlDescargarRide=objdescargarRide.ip_address+objdescargarRide.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarRide.header)

        if objdescargarRide.oauth:
            token=self.token_autorizacion(objdescargarRide)
            headers['Authorization']='Bearer '+ token
        return urlDescargarRide,headers



