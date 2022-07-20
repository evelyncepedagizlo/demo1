# -*- coding: utf-8 -*-

import base64
import io
import os
import logging
from itertools import groupby
from operator import itemgetter

from lxml import etree
from lxml.etree import DocumentInvalid
from jinja2 import Environment, FileSystemLoader

from openerp import fields, models, api

from .utils import convertir_fecha, get_date_value
from odoo.exceptions import ValidationError

tpIdProv = {
    'ruc': '01',
    'cedula': '02',
    'pasaporte': '03',
}

tpIdCliente = {
    'ruc': '04',
    'cedula': '05',
    'pasaporte': '06',
    'final': '07',
    'nit': '08'
    }


class AccountAts(dict):
    """
    representacion del ATS
    >>> ats.campo = 'valor'
    >>> ats['campo']
    'valor'
    """

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, item, value):
        if item in self.__dict__:
            dict.__setattr__(self, item, value)
        else:
            self.__setitem__(item, value)


class WizardAts(models.TransientModel):

    _name = 'wizard.ats'
    _description = 'Anexo Transaccional Simplificado'
    __logger = logging.getLogger(_name)

    
    def _get_period(self):
        return None #self.env['account.period'].search([])

    
    def _get_company(self):
        return self.env.company.id

    def act_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
    def _get_iva_types(self, invoice):
        iva12 = 0
        iva0 = 0
        novat = 0
        for line in invoice.invoice_line_ids:
            for tax in line.tax_ids:
                if tax.tax_group_id.code == 'vat':
                    iva12 += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))
                if tax.tax_group_id.code == 'vat0':
                    iva0 += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))
                if tax.tax_group_id.code == 'novat':
                    novat += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))
        
        return iva12, iva0, novat
    """def process_lines(self, lines):
        
        data_air = []
        temp = {}
        for line in lines:
            if line.group_id.code in ['ret_ir', 'no_ret_ir']:
                if not temp.get(line.tax_id.description):
                    temp[line.tax_id.description] = {
                        'baseImpAir': 0,
                        'valRetAir': 0
                    }
                temp[line.tax_id.description]['baseImpAir'] += line.base
                temp[line.tax_id.description]['codRetAir'] = line.tax_id.description  # noqa
                temp[line.tax_id.description]['porcentajeAir'] = abs(int(line.tax_id.amount))  # noqa
                temp[line.tax_id.description]['valRetAir'] += abs(float(line.amount))
        for k, v in temp.items():
            data_air.append(v)
        return data_air"""
    def process_lines(self, invoice):
        """
        @temp: {'332': {baseImpAir: 0,}}
        @data_air: [{baseImpAir: 0, ...}]
        """
        data_air = []
        temp = {}
        for line in invoice.invoice_line_ids:
            for tax in line.tax_ids:
        #for line in lines:
                if tax.tax_group_id.code in ['ret_ir', 'no_ret_ir']:
                    if not temp.get(tax.description):
                        temp[tax.description] = {
                            'baseImpAir': 0,
                            'valRetAir': 0
                        }
                    temp[tax.description]['baseImpAir'] += line.price_subtotal
                    temp[tax.description]['codRetAir'] = tax.description # noqa
                    temp[tax.description]['porcentajeAir'] = abs(float(tax.tarifa))  # noqa
                    temp[tax.description]['valRetAir'] += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))
        for k, v in temp.items():
            data_air.append(v)
        return data_air
    @api.model
    def _get_ventas(self, start, end):
        sql_ventas = "SELECT inv.type, sum(amount_untaxed) AS base \
                      FROM account_move AS inv\
                      LEFT JOIN establecimiento AS auth ON inv.establecimiento=auth.id \
                      WHERE inv.type IN ('out_invoice', 'out_refund') \
                      AND inv.state IN ('posted') \
                      AND inv.invoice_date >= '%s' \
                      AND inv.invoice_date <= '%s' \
                      AND inv.is_electronic != true \
                      AND inv.company_id = %d \
                      " % (start, end, self.company_id.id) 

        sql_ventas += " GROUP BY inv.type"
        self.env.cr.execute(sql_ventas)
        res = self.env.cr.fetchall()
        resultado = sum(map(lambda x: x[0] == 'out_refund' and x[1] * -1 or x[1], res))  # noqa
        return resultado

    #def _get_ret_iva(self, invoice):
    #    """
    #    Return (valRetBien10, valRetServ20,
    #    valorRetBienes,
    #    valorRetServicios, valorRetServ100)
    #    """
    #    retBien10 = 0
    #    retServ20 = 0
    #    retBien = 0
    #    retServ = 0
    #    retServ100 = 0
    #    for line in invoice.invoice_line_ids:
    #        for tax in line.tax_ids:
    #            if tax.tax_group_id.code == 'ret_vat_b':
    #                if abs(tax.amount) == 10:
    #                    retBien10 += abs(tax.amount)
    #                else:
    #                    retBien += abs(tax.amount)
    #            if tax.tax_group_id == 'ret_vat_srv':
    #                if abs(tax.amount) == 100:
    #                    retServ100 += abs(tax.amount)
    #                elif abs(tax.amount) == 20:
    #                    retServ20 += abs(tax.amount)
    #                else:
    #                    retServ += abs(tax.amount)
    #    return retBien10, retServ20, retBien, retServ, retServ100
    def _get_ret_iva(self, invoice):
        """
        Return (valRetBien10, valRetServ20,
        valorRetBienes,
        valorRetServicios, valorRetServ100)
        """
        retBien10 = 0
        retServ20 = 0
        retBien = 0
        retServ = 0
        retServ100 = 0
        for line in invoice.invoice_line_ids:
            for tax in line.tax_ids:
                if tax.tax_group_id.code == 'ret_vat_b':
                    if abs(tax.amount) == 10:
                        retBien10 += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))*0.12
                    else:
                        retBien += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))*0.12
                if tax.tax_group_id.code == 'ret_vat_srv':
                    if abs(tax.amount) == 100:
                        retServ100 += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))*0.12
                    elif abs(tax.amount) == 20:
                        retServ20 += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))*0.12
                    else:
                        retServ += abs(tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id))*0.12
        return retBien10, retServ20, retBien, retServ, retServ100
    def get_withholding(self, wh):
        if wh.id:
        
            authRetencion=''
            if wh.auth_id.is_electronic:
                authRetencion = wh.auth_number
            #else:
            #    authRetencion = wh.auth_number
            secret=''
            
            if not wh.name:
                
                secret='000000001'
            else:
                #raise ValidationError((str((wh.name)[6:15])+'kdkd'))
                secret=wh.name[6:15]
            return {
                'estabRetencion1': wh.auth_id.serie_establecimiento,
                'ptoEmiRetencion1': wh.auth_id.serie_emision,
                'secRetencion1': secret,#(wh.name )[6:15] or '000000000000000000',
                'autRetencion1': authRetencion or '000',
                'fechaEmiRet1': convertir_fecha(wh.date)
            }
        else:
            return {
                'estabRetencion1': '000',
                'ptoEmiRetencion1':'000',
                'secRetencion1': '000000001',
                'autRetencion1': '000',
                'fechaEmiRet1': False,
            }
    def get_refund(self, invoice):
        refund = self.env['account.move'].search([
            ('reversed_entry_id', '=', invoice.id),('state','not in',('draft','cancel'))
        ])
        if refund:
            auth = refund.establecimiento
            return {
                'docModificado': '01',
                'estabModificado': refund.l10n_latam_document_number[0:3],
                'ptoEmiModificado': refund.l10n_latam_document_number[3:6],
                'secModificado': refund.supplier_invoice_number,
                'autModificado': refund.reference,
            }
        else:
            return {}
            # auth = refund.establecimiento
            # return {
            #     'docModificado': auth.type_id.code,
            #     'estabModificado': auth.serie_entidad,
            #     'ptoEmiModificado': auth.serie_emision,
            #     'secModificado': refund.invoice_number[6:15],
            #     'autModificado': refund.reference
            # }

            
    def _get_iva_bases(self, invoice):
        iva12 = 0
        iva0 = 0
        novat = 0
        for line in invoice.invoice_line_ids:
            
            cont_vats=0
            for tax in line.tax_ids:
                if tax.tax_group_id.code == 'vat':
                    cont_vats+=1
                    iva12 += abs(line.price_subtotal)
                if tax.tax_group_id.code == 'vat0':
                    cont_vats+=1
                    iva0 += abs(line.price_subtotal)
                if tax.tax_group_id.code == 'novat':
                    cont_vats+=1
                    novat += abs(line.price_subtotal)
            #raise ValidationError((str(len(line.tax_ids))+'kdkd'))
            if cont_vats==0:
                iva0 += abs(line.price_subtotal)
        
        return iva12, iva0, novat
                            
            
  
            
            
            
    def get_reembolsos(self, invoice):
        if not invoice.establecimiento.type_id.code == '41':
            return False
        res = []
        for r in invoice.refund_ids:
            res.append({
                'tipoComprobanteReemb': r.doc_id.code,
                'tpIdProvReemb': tpIdProv[r.partner_id.l10n_latam_document_type_id],
                'idProvReemb': r.partner_id.vat,
                'establecimientoReemb': r.auth_id.serie_establecimiento,
                'puntoEmisionReemb': r.auth_id.serie_emision,
                'secuencialReemb': r.secuencial,
                'fechaEmisionReemb': convertir_fecha(r.date),
                'autorizacionReemb': r.auth_id.name,
                'baseImponibleReemb': '0.00',
                'baseImpGravReemb': '0.00',
                'baseNoGravReemb': '%.2f' % r.amount,
                'baseImpExeReemb': '0.00',
                'montoIceRemb': '0.00',
                'montoIvaRemb': '%.2f' % r.tax
            })
        return res

    def si_no(self, condition):
        if condition:
             return 'SI'
        return 'NO'

    def read_compras(self, start, end):
        """
        Procesa:
          * facturas de proveedor
          * liquidaciones de compra
        """
        inv_obj = self.env['account.move']
        dmn_purchase = [
            ('state', 'in', ['posted']),
            ('invoice_date', '>=', '{0:%Y-%m-%d}'.format(start)),
            ('invoice_date', '<=',  '{0:%Y-%m-%d}'.format(end)),
            ('type', 'in', ['in_invoice', 'liq_purchase', 'in_refund', 'id_debit'])  # noqa
        ]
        compras = []
        for inv in inv_obj.search(dmn_purchase):
            if inv.partner_id.type_identifier not in ['pasaporte','final']:
                detallecompras = {}
                auth = inv.establecimiento
                valRetBien10, valRetServ20, valorRetBienes, valorRetServicios, valRetServ100 = self._get_ret_iva(inv)  # noqa
                baseiva12, baseiva0, basenovat= self._get_iva_bases(inv)
                iva12, iva0, novat = self._get_iva_types(inv)
                
                t_reeb = 0.0
                if not inv.establecimiento.type_id.code == '41':
                    t_reeb = 0.00
                else:
                    if inv.type == 'liq_purchase':
                        t_reeb = 0.0
                    else:
                        t_reeb = inv.amount_untaxed
                secu =''
                if len (inv.l10n_latam_document_number[6:15])==9:
                    secu =inv.l10n_latam_document_number[6:15]
                else:
                    secu ='0'+inv.l10n_latam_document_number[6:15]
                #if secu == '`00000355':
                #    raise ValidationError((str(len(secu))+'=='+str(inv.invoice_date)+'=='+str(inv.name)))
                detallecompras.update({
                    'codSustento': inv.sustento_del_comprobante.code or '00',
                    'tpIdProv': inv.partner_id.l10n_latam_identification_type_id.code_compra,
                    'idProv': inv.partner_id.vat,
                    'tipoComprobante': inv.type == 'liq_purchase' and '03' or auth.type_id.code or inv.l10n_latam_document_type_id.code,  # noqa
                    'parteRel': 'NO',
                    'fechaRegistro': convertir_fecha(inv.invoice_date),
                    'establecimiento': inv.l10n_latam_document_number[:3],
                    'puntoEmision': inv.l10n_latam_document_number[3:6],
                    'secuencial':secu,# inv.l10n_latam_document_number[6:15],
                    'fechaEmision': convertir_fecha(inv.invoice_date),
                    'autorizacion': inv.auth_number or '000000',
                    'baseNoGraIva':'%.2f' % basenovat,
                    'baseImponible': '%.2f' % baseiva0,
                    'baseImpGrav': '%.2f' % baseiva12,#  (inv.amount_total - inv.amount_untaxed),
                    'baseImpExe': '0.00',
                    'total': inv.amount_total,
                    'montoIce': '0.00',
                    'montoIva': '%.2f' %( iva12),
                    'valRetBien10': '%.2f' % valRetBien10,
                    'valRetServ20': '%.2f' % valRetServ20,
                    'valorRetBienes': '%.2f' % valorRetBienes,
                    'valRetServ50': '0.00',
                    'valorRetServicios': '%.2f' % valorRetServicios,
                    'valRetServ100': '%.2f' % valRetServ100,
                    'totbasesImpReemb': '%.2f' % t_reeb,
                    'pagoExterior': {
                        'pagoLocExt':'01',# inv.partner_id.ats_residente,
                        'paisEfecPago': 'NA',#inv.partner_id.ats_country ,
                        'aplicConvDobTrib': 'NA',#self.si_no(inv.partner_id.ats_doble_trib),
                        'pagExtSujRetNorLeg': 'NA',#self._pagExtSujRetNorLeg(inv),
                    },
                    #'pagoExterior': {
                    #    'pagoLocExt': inv.partner_id.ats_residente,
                    #    'tipoRegi': inv.partner_id.ats_regimen_fiscal,
                    #    'pais': inv.partner_id.ats_country,
                    #    'pais_efec_gen': inv.partner_id.ats_country_efec_gen,
                    #    'pais_efec_par_fic': inv.partner_id.ats_country_efec_parfic,
                    #    'aplicConvDobTrib': self.si_no(inv.partner_id.ats_doble_trib),
                    #    'denopago': inv.partner_id.denopago,
                    #    'pagExtSujRetNorLeg': self._pagExtSujRetNorLeg(inv),
                    #    'pagoRegFis': self.si_no(inv.partner_id.pago_reg_fis)
                    #},
                    'formaPago': inv.method_payment.code or '20',
                    'detalleAir': self.process_lines(inv)
                  #  'detalleAir': self.process_lines(inv.l10n_latam_tax_ids)
                })
                if inv.retention_id:
                    detallecompras.update({'retencion': True})
                    detallecompras.update(self.get_withholding(inv.retention_id))  # noqa
                if inv.type in ['out_refund', 'in_refund']:
                    refund = self.get_refund(inv)
                    if refund:
                        detallecompras.update({'es_nc': True})
                        detallecompras.update(refund)
                detallecompras.update({
                    'reembolsos': self.get_reembolsos(inv)
                })
                compras.append(detallecompras)
        logging.error(compras)
        return compras

    def _pagExtSujRetNorLeg(self, inv):
        if inv.partner_id.ats_doble_trib:
            return self.si_no(inv.partner_id.pag_ext_suj_ret_nor_leg)
        else:
            return 'NA'

    
    def read_ventas(self, start, end):
        dmn = [
            ('state', '=', 'posted'),
            ('invoice_date','>=', '%s'%start),
            ('invoice_date', '<=', '%s'%end),
            ('type', '=', 'out_invoice'),
            ('establecimiento.is_electronic', '!=', True)
        ]
        ventas = []
        for inv in self.env['account.move'].search(dmn):
            valRetBien10, valRetServ20, valorRetBienes, valorRetServicios, valRetServ100 = self._get_ret_iva(inv)
            baseiva12, baseiva0, basenovat= self._get_iva_bases(inv)
            iva12, iva0, novat = self._get_iva_types(inv)
            detalleventas = {
                'tpIdCliente': inv.partner_id.l10n_latam_identification_type_id.code_compra,
                'idCliente': inv.partner_id.vat,
                'parteRelVtas': 'NO',
                'partner': inv.partner_id,
                'auth': inv.auth_number,#inv.establecimiento,
                'tipoComprobante': inv.l10n_latam_document_type_id.code, # inv.sustento_del_comprobante.code or 
                'tipoEmision': inv.journal_id.auth_out_invoice_id.is_electronic and 'E' or 'F',
                'numeroComprobantes': 1,
                'baseNoGraIva': basenovat,# inv.amount_untaxed,
                'baseImponible': baseiva0,#inv.amount_untaxed,
                'baseImpGrav':  baseiva12,#(inv.amount_total - inv.amount_untaxed),
                'montoIva':iva12,# baseiva12,#inv.amount_tax,
                'montoIce': '0.00',
                'valorRetIva': (abs(valorRetBienes) + abs(valorRetServicios)),  # noqa
                'valorRetRenta': abs(valRetBien10)+abs(valRetServ20)+abs(valRetServ100),#,#0,#abs(inv.taxed_ret_ir),
                'formasDePago': {
                    'formaPago': inv.method_payment.id
                }
            }
            ventas.append(detalleventas)
        ventas = sorted(ventas, key=itemgetter('idCliente'))
        ventas_end = []
        for ruc, grupo in groupby(ventas, key=itemgetter('idCliente')):
            baseimp = 0
            nograviva = 0.00
            montoiva = 0
            retiva = 0
            impgrav = 0
            retrenta = 0
            numComp = 0
            partner_temp = False
            auth_temp = False
            for i in grupo:
                nograviva += i['baseNoGraIva']
                baseimp += i['baseImponible']
                impgrav += i['baseImpGrav']
                montoiva += i['montoIva']
                retiva += i['valorRetIva']
                retrenta += i['valorRetRenta']
                numComp += 1
                partner_temp = i['partner']
                auth_temp = i['auth']
            #if inv.partner_id.l10n_latam_identification_type_id.code_venta =='04':
            #    raise ValidationError((str((inv.partner_id.l10n_latam_identification_type_id.code_compra)+'====')))
            detalle = {
                'tpIdCliente': inv.partner_id.l10n_latam_identification_type_id.code_venta,
                'idCliente': ruc,
                'parteRelVtas': 'NO',
                'tipoComprobante': inv.l10n_latam_document_type_id.code, # inv.sustento_del_comprobante.code or 
                'tipoEmision': inv.journal_id.auth_out_invoice_id.is_electronic and 'E' or 'F',
                'numeroComprobantes': numComp,
                'baseNoGraIva': '%.2f' % nograviva,
                'baseImponible': '%.2f' % baseimp,
                'baseImpGrav': '%.2f' % impgrav,
                'montoIva': '%.2f' % montoiva,
                'montoIce': '0.00',
                'valorRetIva': '%.2f' % retiva,
                'valorRetRenta': '%.2f' % retrenta,
                'formasDePago': {
                    'formaPago': '20'
                }
            }
            ventas_end.append(detalle)
        return ventas_end

    
    def read_anulados(self, start, end):
        dmn = [
            ('state', '=', 'cancel'),
            ('invoice_date', '>=', '%s'%start),
            ('invoice_date', '<=', '%s'%end),
            ('type', 'in', ['out_invoice', 'liq_purchase'])
        ]
        anulados = []
        for inv in self.env['account.move'].search(dmn):
            auth = inv.establecimiento
            aut = auth.is_electronic and inv.numero_autorizacion or auth.name
            detalleanulados = {
                'tipoComprobante': auth.type_id.code or '00',
                'establecimiento': auth.serie_establecimiento,
                'ptoEmision': auth.serie_emision,
                'secuencialInicio': inv.l10n_latam_document_number[6:].rstrip("0"),
                'secuencialFin': inv.l10n_latam_document_number[6:].rstrip("0"),
                'autorizacion': aut or '000000'
            }
            anulados.append(detalleanulados)

        dmn_ret = [
            ('state', '=', 'cancel'),
            ('date', '>=', '%s'%start),
            ('date', '<=', '%s'%end),
            ('in_type', '=', 'ret_in_invoice')
        ]
        for ret in self.env['account.retention'].search(dmn_ret):
            auth = ret.auth_id
            aut = auth.is_electronic and inv.numero_autorizacion or auth.name
            detalleanulados = {
                'tipoComprobante': auth.type_id.code or '00',
                'establecimiento': auth.serie_entidad,
                'ptoEmision': auth.serie_emision,
                'secuencialInicio': ret.name[6:9],
                'secuencialFin': ret.name[6:9],
                'autorizacion': aut
            }
            anulados.append(detalleanulados)
        return anulados

    
    def render_xml(self, ats):
        tmpl_path = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(tmpl_path))
        ats_tmpl = env.get_template('ats.xml')
        return ats_tmpl.render(ats)

    
    def validate_document(self, ats, error_log=False):
        file_path = os.path.join(os.path.dirname(__file__), 'XSD/ats.xsd')
        schema_file = open(file_path)
        xmlschema_doc = etree.parse(schema_file)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        root = etree.fromstring(ats.encode())
        ok = True
        if not self.no_validate:
            try:
                xmlschema.assertValid(root)
            except DocumentInvalid:
                ok = False
        return ok, xmlschema

    
    def act_export_ats(self):
        ats = AccountAts()
        period = self.period_id
        ruc = self.company_id.partner_id.vat
        ats.TipoIDInformante = 'R'
        ats.IdInformante = ruc
        ats.razonSocial = self.company_id.name.upper()
        ats.Anio = get_date_value(self.period_start, '%Y')
        ats.Mes = get_date_value(self.period_start, '%m')
        ats.numEstabRuc = self.num_estab_ruc.zfill(3)
        ats.AtstotalVentas = '%.2f' % self._get_ventas(self.period_start, self.period_end)
        ats.totalVentas = '%.2f' % self._get_ventas(self.period_start, self.period_end)
        ats.codigoOperativo = 'IVA'
        ats.compras = self.read_compras(self.period_start, self.period_end)
        ats.ventas = self.read_ventas(self.period_start, self.period_end)
        ats.codEstab = self.num_estab_ruc
        ats.ventasEstab = '%.2f' % self._get_ventas(self.period_start, self.period_end)
        ats.ivaComp = '0.00'
        ats.anulados = self.read_anulados(self.period_start, self.period_end)
        ats_rendered = self.render_xml(ats)
        ok, schema = self.validate_document(ats_rendered)
        buf = io.StringIO()
        buf.write(ats_rendered)
        out = base64.encodestring(buf.getvalue().encode('utf-8')).decode()
        logging.error(out)
        buf.close()
        buf_erro = io.StringIO()
        for err in schema.error_log:
            buf_erro.write(err.message+'\n')
        #buf_erro.write(schema.error_log)
        out_erro = base64.encodestring(buf_erro.getvalue().encode())
        buf_erro.close()
        name = "%s%s%s.XML" % (
            "AT",
            ats.Mes,
            ats.Anio
        )
        data2save = {
            'state': ok and 'export' or 'export_error',
            'data': out,
            'fcname': name
        }
        if not ok:
            data2save.update({
                'error_data': out_erro,
                'fcname_errores': 'ERRORES.txt'
            })
        self.write(data2save)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.ats',
            'view_mode': ' form',
            'view_type': ' form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    fcname = fields.Char('Nombre de Archivo', size=50, readonly=True)
    fcname_errores = fields.Char('Archivo Errores', size=50, readonly=True)
    period_id = fields.Many2one(
        'account.period',
        'Periodo',
        #default=_get_period
    )
    period_start = fields.Date('Inicio de periodo')
    period_end = fields.Date('Fin de periodo')
    company_id = fields.Many2one(
        'res.company',
        'Compania',
        default=_get_company
    )
    num_estab_ruc = fields.Char(
        'Num. de Establecimientos',
        size=3,
        required=True,
        default='001'
    )
    pay_limit = fields.Float('Limite de Pago', default=1000)
    data = fields.Binary('Archivo XML')
    error_data = fields.Binary('Archivo de Errores')
    no_validate = fields.Boolean('No Validar', default=True)
    state = fields.Selection(
        (
            ('choose', 'Elegir'),
            ('export', 'Generado'),
            ('export_error', 'Error')
        ),
        string='Estado',
        default='choose'
    )
