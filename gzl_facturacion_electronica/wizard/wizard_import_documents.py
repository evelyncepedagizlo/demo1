# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import date, datetime
import base64
import json
import xmltodict 
import dateutil.parser
from odoo.exceptions import ValidationError

class WizardImportDocuments(models.TransientModel):
    _name = "wizard.import.documents"
    _description = 'Importación de Documentos en formato XML'
    
    name=fields.Char('')
    type_document = fields.Selection([('in_invoice', 'Factura'),
                                        ('in_credit', 'Nota de Crédito'),
                                        ('in_debit', 'Nota de Debito'),
                                        ('out_withholdings', 'Retención'),
                                     ],string='Tipo de Documento')
    file_xml = fields.Binary('Archivo')

    
    def format_authorization_date(self, date): 
        date_conv = dateutil.parser.parse(date)

        return date_conv.strftime('%Y-%m-%d %H:%M:%S')
    
    def format_date(self, date):    
        date_conv = dateutil.parser.parse(date)
        return date_conv.strftime('%Y-%m-%d')
    
    
    def import_xml(self):
        if self.type_document=='out_withholdings':
            self.import_xml_out_withholdings()
        elif self.type_document=='in_debit':
            self.import_xml_debit_note()
        else:
            self.import_xml_credit_note_and_invoice()


    
    def import_xml_debit_note(self):
        
        decoded_data = base64.b64decode(self.file_xml)#tranformo el archivo a base 64
       
        autorizacion_xml = xmltodict.parse(decoded_data)
        autorizacion_str = json.dumps(autorizacion_xml, indent=4)
        autorizacion = json.loads(autorizacion_str)

        comprobante_xml = xmltodict.parse(autorizacion["autorizacion"]["comprobante"])
        comprobante_str = json.dumps(comprobante_xml, indent=4)
        comp = json.loads(comprobante_str)
        ###### Tablas a enviar los datos
        invoice = self.env['account.move']
        line_invoice = self.env['account.move.line']
        products = self.env['product.template']
        product_product = self.env['product.product']
        journal = self.env['account.journal']
        partner = self.env['res.partner']
        

        if self.type_document=='in_debit':
            tipo_documento='in_debit'
            clave_xml_tipo_documento='notaDebito'
            clave_xml_info_documento='infoNotaDebito'




        ###### encabezados del xml

        aut = autorizacion['autorizacion']
        infoTrib = comp[clave_xml_tipo_documento]['infoTributaria']
        infoFact = comp[clave_xml_tipo_documento][clave_xml_info_documento]
        
        
        
        payment_method_id=False

        ###### Objetos relacionales
        partner_id = self.env['res.partner'].search([('vat','=',infoTrib['ruc'])],limit=1)
        
        if partner_id.id == False:
            raise ValidationError("El proveedor {1} con el RUC {0} no esta ingresado en la aplicacion, proceda a ingresarlo.".format(infoTrib['ruc'],infoTrib['razonSocial']))
            
        
        
        
        
        journal_id = journal.search([('type','=','purchase')],limit=1)
        

        invoice_id = {
            'type':tipo_documento,
            'is_electronic':True,
            'partner_id':partner_id.id,
            'type_environment':infoTrib['ambiente'],
            'numero_autorizacion_sri':aut['numeroAutorizacion'],
            'fecha_autorizacion_sri':self.format_authorization_date(aut['fechaAutorizacion']['#text']),
            'estado_autorizacion_sri':'AUT' if aut['estado']=='AUTORIZADO' else 'NAT',
            'clave_acceso_sri':infoTrib['claveAcceso'],
            'manual_establishment':infoTrib['estab'],
            'manual_referral_guide':infoTrib['ptoEmi'],
            'manual_sequence':infoTrib['secuencial'],
            'l10n_latam_document_number':infoTrib['estab']+infoTrib['ptoEmi']+infoTrib['secuencial'],
            'invoice_date':self.format_date(infoFact['fechaEmision']),
            'date':self.format_date(infoFact['fechaEmision']),
            'journal_id':journal_id.id,



        }
        
        if self.type_document=='in_invoice':
            invoice_id['method_payment']=payment_method_id.id
        
        
        
        
        tot_debit=0
        lines=[]
        product_template=self.env.ref('gzl_facturacion_electronica.generic_product_template')
        product = product_product.search([('product_tmpl_id','=',product_template.id)])


        dct_line={
                'partner_id':partner_id.id,
                'product_id':product.id,
                'name': '['+product.default_code+']'+product.product_tmpl_id.name,
                'account_id':product.categ_id.property_stock_account_input_categ_id.id,
                'quantity':1,
                'price_unit':float(comp['notaDebito'][clave_xml_info_documento]['impuestos']['impuesto']['baseImponible']),
                'discount':0,
                'account_internal_type':'other',
                'debit':float(comp['notaDebito'][clave_xml_info_documento]['totalSinImpuestos']),
                'credit':0.00,
            }
        #if clave_xml_info_documento:
        #    raise ValidationError(str( comp['notaDebito'][clave_xml_info_documento]['impuestos']))
        impuestos=comp['notaDebito'][clave_xml_info_documento]['impuestos']
        if not isinstance(impuestos, list):
            impuestos=[]
            impuestos.append(comp['notaDebito'][clave_xml_info_documento]['impuestos']['impuesto'])
        impuesto_ids=[]
        for impuesto in impuestos:
            obj_impuesto = self.env['account.tax'].search([('l10n_ec_code_base','=',impuesto['codigo'])],limit=1)
            for obj in obj_impuesto:
                if obj.id:
                    impuesto_ids.append(obj.id)
                else:
                    raise ValidationError('El impuesto con codigo {0} no esta ingresado en la aplicacion'.format(impuesto['codigo']))

        
        dct_line['tax_ids']=[(6,0,impuesto_ids)]
        
        lines.append((0, 0, dct_line))

        tot_debit += float(comp['notaDebito'][clave_xml_info_documento]['totalSinImpuestos'])
        
        lines.append((0, 0, {
        'partner_id':partner_id.id,
        'account_id':partner_id.property_account_payable_id.id,
        'account_internal_type':'payable',
        'debit':0.00,
        'credit':tot_debit,
        'exclude_from_invoice_tab':True
        }))
    
        invoice_id.update({'line_ids': lines})
        move = self.env['account.move'].create(invoice_id)
        
            
        if self.type_document=='in_debit':
            factura_relacionada=self.env['account.move'].search([('l10n_latam_document_number','=',infoFact['numDocModificado']),('type','=','in_invoice')],limit=1)

            factura_relacionada.reverse_entry_id=move.id       
    
    
    def import_xml_credit_note_and_invoice(self):
        
        decoded_data = base64.b64decode(self.file_xml)#tranformo el archivo a base 64
        #raise ValidationError("ESTO ES UNA PRUEBA{1}{0}".format(file_xml,decoded_data))       
        
        #import xml.etree.ElementTree as ET


        #tree = ET.parse(decoded_data)
        #decode_data = tree.getroot()
        #here you can change the encoding type to be able to set it to the one you need
        #xmlstr = ET.tostring(xml_data, encoding='utf-8', method='xml')

#data_dict = dict(xmltodict.parse(xmlstr))





        #raise ValidationError(decoded_data)

        autorizacion_xml = xmltodict.parse(decoded_data)
        autorizacion_str = json.dumps(autorizacion_xml, indent=4)
        autorizacion = json.loads(autorizacion_str)

        comprobante_xml = xmltodict.parse(autorizacion["autorizacion"]["comprobante"])
        comprobante_str = json.dumps(comprobante_xml, indent=4)
        comp = json.loads(comprobante_str)
        ###### Tablas a enviar los datos
        invoice = self.env['account.move']
        line_invoice = self.env['account.move.line']
        products = self.env['product.template']
        product_product = self.env['product.product']
        journal = self.env['account.journal']
        partner = self.env['res.partner']
        


        tipo_documento='in_invoice'
        clave_xml_tipo_documento='factura'
        clave_xml_info_documento='infoFactura'

        #Valores para Facturas Rectificativas:
        if self.type_document=='in_credit':
            tipo_documento='in_refund'
            clave_xml_tipo_documento='notaCredito'
            clave_xml_info_documento='infoNotaCredito'
        if self.type_document=='in_debit':
            tipo_documento='in_debit'
            clave_xml_tipo_documento='notaDebito'
            clave_xml_info_documento='infoNotaDebito'




        ###### encabezados del xml

        aut = autorizacion['autorizacion']
        infoTrib = comp[clave_xml_tipo_documento]['infoTributaria']
        infoFact = comp[clave_xml_tipo_documento][clave_xml_info_documento]
        if  self.type_document in ('in_credit','in_invoice'):
            detalles = comp[clave_xml_tipo_documento]['detalles']['detalle']
        
        
        
        payment_method_id=False

        if self.type_document=='in_invoice':
            infoPag = infoFact['pagos']['pago']
            payment_method_id = self.env['account.epayment'].search([('code','=',infoPag['formaPago'])])


        #Busqueda de Factura relacionada a Nota de Credito






        ###### Objetos relacionales
        partner_id = self.env['res.partner'].search([('vat','=',infoTrib['ruc'])],limit=1)
        
        if partner_id.id == False:
            raise ValidationError("El proveedor {1} con el RUC {0} no esta ingresado en la aplicacion, proceda a ingresarlo.".format(infoTrib['ruc'],infoTrib['razonSocial']))
            
        
        
        
        
        journal_id = journal.search([('type','=','purchase')],limit=1)
        





        invoice_id = {
            'type':tipo_documento,
            'is_electronic':True,
            'partner_id':partner_id.id,
            'type_environment':infoTrib['ambiente'],
            'numero_autorizacion_sri':aut['numeroAutorizacion'],
            'fecha_autorizacion_sri':self.format_authorization_date(aut['fechaAutorizacion']['#text']),
            'estado_autorizacion_sri':'AUT' if aut['estado']=='AUTORIZADO' else 'NAT',
            'clave_acceso_sri':infoTrib['claveAcceso'],
            'manual_establishment':infoTrib['estab'],
            'manual_referral_guide':infoTrib['ptoEmi'],
            'manual_sequence':infoTrib['secuencial'],
            'l10n_latam_document_number':infoTrib['estab']+infoTrib['ptoEmi']+infoTrib['secuencial'],
            'invoice_date':self.format_date(infoFact['fechaEmision']),
            'date':self.format_date(infoFact['fechaEmision']),
            'journal_id':journal_id.id,



        }
        
        if self.type_document=='in_invoice':
            invoice_id['method_payment']=payment_method_id.id
        
        
        
        
        tot_debit=0
        lines=[]
        
        
        
        #if  self.type_document in ('in_credit','in_invoice'):
        if not isinstance(detalles, list):
            detalles=[]
            detalles.append(comp[clave_xml_tipo_documento]['detalles']['detalle'])
        
        
        
    
        for l in detalles:
            product_template=self.env.ref('gzl_facturacion_electronica.generic_product_template')
            product = product_product.search([('product_tmpl_id','=',product_template.id)])


            dct_line={
                    'partner_id':partner_id.id,
                    'product_id':product.id,
                    'name': '['+product.default_code+']'+product.product_tmpl_id.name,
                    'account_id':product.categ_id.property_stock_account_input_categ_id.id,
                    'quantity':float(l['cantidad']),
                    'price_unit':float(l['precioUnitario']),
                    'discount':float(l['descuento'])*100,
                    'account_internal_type':'other',
                    'debit':float(l['precioTotalSinImpuesto']),
                    'credit':0.00,
                }
            impuestos=l['impuestos']
            if not isinstance(impuestos, list):
                impuestos=[]
                impuestos.append(l['impuestos']['impuesto'])



            impuesto_ids=[]
            for impuesto in impuestos:
                obj_impuesto = self.env['account.tax'].search([('l10n_ec_code_base','=',impuesto['codigo'])],limit=1)
                for obj in obj_impuesto:
                    if obj.id:
                        impuesto_ids.append(obj.id)
                    else:
                        raise ValidationError('El impuesto con codigo {0} no esta ingresado en la aplicacion'.format(impuesto['codigo']))


            dct_line['tax_ids']=[(6,0,impuesto_ids)]

            lines.append((0, 0, dct_line))

            tot_debit += float(l['precioTotalSinImpuesto'])
        lines.append((0, 0, {
        'partner_id':partner_id.id,
        'account_id':partner_id.property_account_payable_id.id,
        'account_internal_type':'payable',
        'debit':0.00,
        'credit':tot_debit,
        'exclude_from_invoice_tab':True
        }))
    
        invoice_id.update({'line_ids': lines})
        move = self.env['account.move'].create(invoice_id)



        if self.type_document=='in_credit':
            factura_relacionada=self.env['account.move'].search([('l10n_latam_document_number','=',infoFact['numDocModificado']),('type','=','in_invoice')],limit=1)

            factura_relacionada.reverse_entry_id=move.id

            
        

            

            
        







    def import_xml_out_withholdings(self):
        
        decoded_data = base64.b64decode(self.file_xml)#tranformo el archivo a base 64
       
        autorizacion_xml = xmltodict.parse(decoded_data)
        autorizacion_str = json.dumps(autorizacion_xml, indent=4)
        autorizacion = json.loads(autorizacion_str)

        comprobante_xml = xmltodict.parse(autorizacion["autorizacion"]["comprobante"])
        comprobante_str = json.dumps(comprobante_xml, indent=4)
        comp = json.loads(comprobante_str)
        ###### Tablas a enviar los datos
        retention = self.env['account.retention']
        line_retention = self.env['account.retention.line']
        partner = self.env['res.partner']
        account_tax_group = self.env['account.tax.group']


        clave_xml_tipo_documento='comprobanteRetencion'
        clave_xml_info_documento='infoCompRetencion'




        ###### encabezados del xml

        aut = autorizacion['autorizacion']
        infoTrib = comp[clave_xml_tipo_documento]['infoTributaria']
        infoRetencion = comp[clave_xml_tipo_documento][clave_xml_info_documento]
        impuestos = comp[clave_xml_tipo_documento]['impuestos']['impuesto']
        


        ###### Objetos relacionales
        partner_id = self.env['res.partner'].search([('vat','=',infoTrib['ruc'])],limit=1)
        
        if partner_id.id == False:
            raise ValidationError("El proveedor {1} con el RUC {0} no esta ingresado en la aplicacion, proceda a ingresarlo.".format(infoTrib['ruc'],infoTrib['razonSocial']))
            

        retention_id = {
            'partner_id':partner_id.id,
            'auth_number':aut['numeroAutorizacion'],
            'manual_establishment':infoTrib['estab'],
            'manual_referral_guide':infoTrib['ptoEmi'],
            'manual_sequence':infoTrib['secuencial'],
             'date':self.format_date(infoRetencion['fechaEmision']),
 
        }

        
        lines=[]
        
        
        
        if not isinstance(impuestos, list):
            impuestos=[]
            impuestos.append(comp[clave_xml_tipo_documento]['impuestos']['impuesto'])
            
        num_documento_asociado_retencion=''
        tipo_documento_asociado_retencion=''
        for l in impuestos:

            
            obj_impuesto = self.env['account.tax'].search([('l10n_ec_code_base','=',l['codigo'])],limit=1)
            if obj_impuesto:
                for imp in obj_impuesto:
                    dct_line={
                            'fiscal_year':infoRetencion['periodoFiscal'],
                            'tax_id':imp.id,
                            'base_ret':float(l['baseImponible']),
                            'base':float(l['baseImponible']),
                            'amount':float(l['valorRetenido']),

                        }
                    num_documento_asociado_retencion=l['numDocSustento']
                    tipo_documento_asociado_retencion=l['codDocSustento']


                    lines.append((0, 0, dct_line))



        retention_id.update({'tax_ids': lines})
        retention = self.env['account.retention'].create(retention_id)
        
        
    ####Agregar Factura a Retencion
        if tipo_documento_asociado_retencion=='01':
            factura_relacionada=self.env['account.move'].search([('l10n_latam_document_number','=',num_documento_asociado_retencion),('type','=','in_invoice')],limit=1)

        else:
            factura_relacionada=self.env['account.move'].search([('l10n_latam_document_number','=',num_documento_asociado_retencion),('type','=','out_invoice')],limit=1)


        retention.invoice_id=factura_relacionada.id
