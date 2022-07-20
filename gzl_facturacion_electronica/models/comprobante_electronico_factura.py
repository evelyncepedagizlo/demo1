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

    xls_filename1 = fields.Char('Nombre Archivo excel')
    archivo_xls1 = fields.Binary('Archivo excel')
    bitacora_id = fields.Many2one('bitacora.consumo.servicios')

    def procesoComprobanteElectronico(self):
        dctCodDoc={
            'in_invoice':self.env.ref('l10n_ec_tree.ec_06').name,
            'out_invoice':self.env.ref('l10n_ec_tree.ec_04').name,
            'in_refund':self.env.ref('l10n_ec_tree.ec_09').name,
            'out_refund':self.env.ref('l10n_ec_tree.ec_10').name,
            'in_debit':self.env.ref('l10n_ec_tree.ec_53').name,
            'out_debit':self.env.ref('l10n_ec_tree.ec_54').name,
            'liq_purchase':self.env.ref('l10n_ec_tree.ec_08').name

            }      
        #Proceso de Comprobante Electrónico
        dct={
        'name':dctCodDoc[self.type] +' - '+self.l10n_latam_document_number,
        'invoice_id':self.id
        }

        self.env.cr.execute("""select count(*) contador from bitacora_consumo_servicios where invoice_id={0}  """.format(self.id))
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
        if self.type=='out_invoice':
            url,headers,requestDct=self.validarComprobanteFactura()
        elif self.type=='out_refund':
            url,headers,requestDct=self.validarComprobanteNotaCredito()
        elif self.type=='out_debit':
            url,headers,requestDct=self.validarComprobanteNotaDebito()
        elif self.type=='liq_purchase':
            url,headers,requestDct=self.validarComprobanteLiquidacionCompra()
        return url,headers,requestDct


    
    def validarComprobanteFactura(self):
        objValidarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_validar_factura')
        url_validarFactura=objValidarFactura.ip_address+objValidarFactura.link
        dias=datetime.now(pytz.timezone('America/Guayaquil'))
        fecha = dias.strftime('%Y-%m-%d %H:%M:%S')
        
        body_vf = {
                      "facturas": [
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






    def procesarComprobante(self):
        if self.type=='out_invoice':
            url,headers,requestDct=self.procesarDocumentoFactura()
        elif self.type=='out_refund':
            url,headers,requestDct=self.procesarDocumentoNotaCredito()
        elif self.type=='out_debit':
            url,headers,requestDct=self.procesarDocumentoNotaDebito()
        elif self.type=='liq_purchase':
            url,headers,requestDct=self.procesarDocumentoLiquidacionCompra()
        return url,headers,requestDct








    def procesarDocumentoFactura(self):
        dctCodDoc={
            'in_invoice':self.env.ref('l10n_ec_tree.ec_06').code,
            'out_invoice':self.env.ref('l10n_ec_tree.ec_04').code,
            'in_refund':self.env.ref('l10n_ec_tree.ec_09').code,
            'out_refund':self.env.ref('l10n_ec_tree.ec_10').code,
            'in_debit':self.env.ref('l10n_ec_tree.ec_53').code,
            'out_debit':self.env.ref('l10n_ec_tree.ec_54').code,
            'liq_purchase':self.env.ref('l10n_ec_tree.ec_08').code

            }



        objProcesarFactura=self.env.ref('gzl_facturacion_electronica.url_servicio_procesar_factura')
        url_procesarFactura=objProcesarFactura.ip_address+objProcesarFactura.link
        

        headers =json.loads(objProcesarFactura.header)

        if objProcesarFactura.oauth:
            token=self.token_autorizacion(objProcesarFactura)
            headers['Authorization']='Bearer '+ token


        if len(self.guia_ids.mapped('name')):
            guia_remision=self.guia_ids.mapped('name')[0]
        else:
            guia_remision='000-000-000000000'

        estadoPago=''
        if self.amount_residual<=0:
            estadoPago='Pendiente'
        else:
            estadoPago='Pagada'
        listaDescuento=self.invoice_line_ids.mapped('discount')
        listaCantidad=self.invoice_line_ids.mapped('quantity')
        listaPrecios=self.invoice_line_ids.mapped('price_unit')

        descuento = round(sum([a * b*c/100 for a, b ,c in zip(listaPrecios,listaDescuento,listaCantidad)]),2)



        body_pf={}

        dctFactura={}

##############ABONOS

# {'title': 'Menos pagos', "outstanding": false, 
# "content": [{"name": "Pago de cliente: FACFI/2021/0062", 
# "journal_name": "Banco Pacifico", "amount": 12121.0, 
# "currency": "$", "digits": [69, 2], "position": "before",
#  "date": "2021-09-10", "payment_id": 11922, "account_payment_id": 941,
#   "payment_method_name": "Efectivo", "move_id": 3206, 
#   "ref": "BDP/2021/0274 (FACFI/2021/0062)"}, 


#   {"name": "Pago de cliente: FACFI/2021/0062",
#    "journal_name": "Banco Pacifico", "amount": 1319.0, 
#    "currency": "$", "digits": [69, 2], "position": "before", 
#    "date": "2021-09-10", "payment_id": 11928, "account_payment_id": 943,
#     "payment_method_name": "Efectivo", "move_id": 3209, 
#     "ref": "BDP/2021/0276 (FACFI/2021/0062)"}]}
        if self.invoice_payments_widget != 'false':
            jsonPayment = json.loads(self.invoice_payments_widget)
            pagos=jsonPayment['content']


            pagos = sorted(pagos, key=lambda k: k['date'])
            saldo=self.amount_total
            listaPagos=[]


            for pago in pagos:
                pago['saldo']=round(saldo-pago['amount'],2)
                saldo=pago['saldo']
                obj_account_payment=self.env['account.payment'].browse(pago['account_payment_id'])


                dctPago={}
                dctPago['banco']=funciones.elimina_tildes(obj_account_payment.journal_id.bank_id.name)or ''
                fechaDate=datetime.strptime(pago['date'], '%Y-%m-%d')
                dctPago['fechaAbono']='%s-%s-%s 00:00' % (fechaDate.year, str(fechaDate.month).zfill(2),str(fechaDate.day).zfill(2))
                dctPago['formaPago']=self.method_payment.code  or ''
                dctPago['numeroCheque']=obj_account_payment.check_number or ''
                dctPago['saldo']=round(pago['saldo'],2)
                listaPagos.append(dctPago)
        else:
            listaPagos=[]

        if len(listaPagos)>0:
            dctFactura['abonos']=listaPagos


        listaDetalleFormaPago=[]
        dctFormaPago={}
        dctFormaPago['formaPago']=str(self.method_payment.code or '')


        if self.invoice_payment_term_id.id:
            dctFormaPago['plazo']=max(self.invoice_payment_term_id.line_ids.mapped('days'))
        else:
            dctFormaPago['plazo']=(self.invoice_date_due  - self.invoice_date ).days

        dctFormaPago['sucursal']=''
        dctFormaPago['tiempo']='dias'
        dctFormaPago['total']=round(self.amount_total,2)

        listaDetalleFormaPago.append(dctFormaPago)

##############DETALLES 
        listaDetalle=[]
        listaTipoImpuestos=[]
        for detalle in self.invoice_line_ids:
            dctDetalle={}
            impuestos=detalle.tax_ids.mapped("id")
        
            listaTipoImpuestos= listaTipoImpuestos +impuestos

            dctDetalle['cantidad']=detalle.quantity 
            dctDetalle['codigoAuxiliar']=str(detalle.id)
            dctDetalle['codigoPrincipal']=str(detalle.id)
            dctDetalle['descripcion']=funciones.elimina_tildes(detalle.name) or ""
            dctDetalle['descuento']=(detalle.discount*detalle.price_unit/100) 



            listadctDetalleAdicional=[]
            dctDetalleAdicional={}

            listaImpuesto=[]
            for impuesto in detalle.tax_ids:
                dctImpuesto={}
                dctImpuesto['baseImponible']=round(detalle.price_subtotal,2)
                dctImpuesto['codigoImpuesto']=impuesto.l10n_ec_code_base or ""
                dctImpuesto['codigoPorcentaje']=impuesto.l10n_ec_code_applied or ""
                dctImpuesto['tarifa']=impuesto.tarifa
                obj_impuesto=self.env['account.tax'].browse(impuesto.id)
                valor=obj_impuesto._compute_amount(round(detalle.price_subtotal,2),0)        
                dctImpuesto['valor']=round(valor,2)

                listaImpuesto.append(dctImpuesto)



            if len(listaImpuesto)==0:
                dctListaImpuesto={
                "baseImponible":self.amount_untaxed,
                "codigoImpuesto":'2',
                "codigoPorcentaje":'0',
                "tarifa":'0',
                "valor":0.0,
                }
                listaImpuesto.append(dctListaImpuesto)








            dctDetalle['detallesImpuesto']=listaImpuesto
            dctDetalle['iva']=''
            dctDetalle['precioTotalSinImpuesto']=round(detalle.price_subtotal,2)
            dctDetalle['precioUnitario']=round(detalle.price_unit ,2)
            dctDetalle['valorIce']=round(sum(map(lambda x:x['valor'],list(filter(lambda x: x['codigoImpuesto']=='3', listaImpuesto)))),2)
            dctDetalle['valorIrbpnr']=round(sum(map(lambda x:x['valor'],list(filter(lambda x: x['codigoImpuesto']=='5', listaImpuesto)))),2)
            dctDetalle['valorIva']=round(sum(map(lambda x:x['valor'],list(filter(lambda x: x['codigoImpuesto']=='2', listaImpuesto)))),2)
            dctDetalle['valorTotal']=dctDetalle['precioTotalSinImpuesto']+dctDetalle['valorIce']+dctDetalle['valorIrbpnr']+dctDetalle['valorIva']



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


        if len(listaTipoImpuestos)==0:
            impuesto_cero=self.env['account.tax'].search([('description','=','403')],limit=1)
            listaTipoImpuestos.append(impuesto_cero.id)

            for impuesto in listaTipoImpuestos:
                dctTotalConImpuestos={}
                dctTotalConImpuestos['baseImponible']=self.amount_untaxed
                dctTotalConImpuestos['codigoImpuesto']='2'
                dctTotalConImpuestos['codigoPorcentaje']='0'
                dctTotalConImpuestos['tarifa']='0'
                dctTotalConImpuestos['valor']=0.0
                dctTotalConImpuestos['valorDevolucionIva']=0

                listaTotalConImpuestos.append(dctTotalConImpuestos)






        listaAdicionales=[]
        for campo in self.campos_adicionales_facturacion:
            dctAdicional={'nombre':campo.nombre,'value':campo.valor}
            listaAdicionales.append(dctAdicional)
        


        dctFactura['adicionales']=listaAdicionales
        dctFactura['agencia']=""
        dctFactura['cliente']={}
        dctFactura['codPuntoEmision']=self.journal_id.auth_out_invoice_id.serie_emision
        dctFactura['codigoExterno']= self.l10n_latam_document_number or ""
        dctFactura['correoNotificacion']=self.env.user.email or ""
        dctFactura['detalleFormaPagoFacturas']=listaDetalleFormaPago
        dctFactura['detalles']=listaDetalle
        dctFactura['dirEstablecimiento']=funciones.elimina_tildes(self.env.user.company_id.street) or ""
        dctFactura['direccionComprodar']=funciones.elimina_tildes(self.partner_id.street )or ""
        dctFactura['establecimiento']=self.l10n_latam_document_number[0:3]
        dctFactura['estadoPago']= estadoPago
        dctFactura['fechaEmisionBase']='%s-%s-%s 00:00' % (self.invoice_date.year, str(self.invoice_date.month).zfill(2),str(self.invoice_date.day).zfill(2))
        
        if not self.invoice_payment_term_id.id:

            dctFactura['fechaRealPago']='%s-%s-%s 00:00' % (self.invoice_date_due.year, str(self.invoice_date_due.month).zfill(2),str(self.invoice_date_due.day).zfill(2))
            dctFactura['fechaTentativaPago']='%s-%s-%s 00:00' % (self.invoice_date_due.year, str(self.invoice_date_due.month).zfill(2),str(self.invoice_date_due.day).zfill(2))
        else:
            dias=max(self.invoice_payment_term_id.line_ids.mapped('days'))
            fechaPago=self.invoice_date + timedelta(days=dias)

            dctFactura['fechaRealPago']='%s-%s-%s 00:00' % (fechaPago.year, str(fechaPago.month).zfill(2),str(fechaPago.day).zfill(2))
            dctFactura['fechaTentativaPago']='%s-%s-%s 00:00' % (fechaPago.year, str(fechaPago.month).zfill(2),str(fechaPago.day).zfill(2))




        dctFactura['guiaRemision']=guia_remision
        dctFactura['identificacionComprador']=self.partner_id.vat or ""
        dctFactura['identificadorUsuario']= self.env.user.partner_id.vat or ""
        dctFactura['importeTotal']=round(self.amount_total,2)
        dctFactura['moneda']= 'DOLAR'
        dctFactura['propina']=0
        dctFactura['puntoEmision']= self.l10n_latam_document_number[3:6]
        dctFactura['razonSocialComprador']= funciones.elimina_tildes(self.partner_id.name)
        dctFactura['ruc']= self.env.user.company_id.vat
        dctFactura['secuencial']=self.l10n_latam_document_number[6:]
        dctFactura['telefonoComprodar']=self.partner_id.phone

        dctFactura['tipoIdentificacionComprador']=self.partner_id.l10n_latam_identification_type_id.code_venta
        dctFactura['tipoOperacion']="COM"
        dctFactura['totalConImpuestos']=listaTotalConImpuestos
        dctFactura['totalDescuento']=descuento
        dctFactura['totalSinImpuestos']=round(self.amount_untaxed,2)
        dctFactura['valorPagar']=  round(self.amount_total,0)
        dctFactura['valorRetencion']=  round(self.ret_amount_total,2)








        body_pf={'facturas':[dctFactura]}

        return url_procesarFactura,headers,body_pf
    

    def postJson(self, url,headers,request):
        #json_factura=json.dumps(dict, ensure_ascii=False)
        json_factura=json.JSONEncoder().encode(request)
        #raise ValidationError(json_factura)        
        procesar_factura_response = requests.post(url, headers = headers, data = json_factura, verify=False)

        return procesar_factura_response


    def getJson(self, url,headers,request={}):
        #json_factura=json.dumps(dict, ensure_ascii=False)
        response = requests.get(url, headers=headers, verify=False)

        return response



    def descargarXML(self):
        if self.type=='out_invoice':
            url,headers=self.descargarXMLFactura()
        elif self.type=='out_refund':
            url,headers=self.descargarXMLNotaCredito()
        elif self.type=='out_debit':
            url,headers=self.descargarXMLNotaDebito()
        elif self.type=='liq_purchase':
            url,headers,requestDct=self.descargarXMLLiquidacionCompra()
        return url,headers




        
    def descargarXMLFactura(self, encoding='utf-8'):
        objdescargarXML=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_xml_factura')
        urlDescargarXML=objdescargarXML.ip_address+objdescargarXML.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarXML.header)

        if objdescargarXML.oauth:
            token=self.token_autorizacion(objdescargarXML)
            headers['Authorization']='Bearer '+ token
        return urlDescargarXML,headers



    def descargarRide(self):
        if self.type=='out_invoice':
            url,headers=self.descargarRideFactura()
        elif self.type=='out_refund':
            url,headers=self.descargarRideNotaCredito()
        elif self.type=='out_debit':
            url,headers=self.descargarRideNotaDebito()
        elif self.type=='liq_purchase':
            url,headers,requestDct=self.descargarRideLiquidacionCompra()
        return url,headers




    def descargarRideFactura(self, encoding='utf-8'):
        objdescargarRide=self.env.ref('gzl_facturacion_electronica.url_servicio_descargar_ride_factura')
        urlDescargarRide=objdescargarRide.ip_address+objdescargarRide.link+'/'+self.clave_acceso_sri

        headers=json.loads(objdescargarRide.header)

        if objdescargarRide.oauth:
            token=self.token_autorizacion(objdescargarRide)
            headers['Authorization']='Bearer '+ token
        return urlDescargarRide,headers



