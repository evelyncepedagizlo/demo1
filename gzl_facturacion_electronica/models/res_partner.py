# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ats_regimen_fiscal = fields.Many2one('ats.regimen.fiscal', string="Regimen Fiscal")
    ats_regimen_fiscal_code = fields.Char(related='ats_regimen_fiscal.code') 
    ats_residente = fields.Many2one('ats.pago.residente' ,string="Tipo de pago")
    ats_residente_code = fields.Char(related='ats_residente.code') 
    is_aduana = fields.Boolean('Es Aduanas', default=False)
    is_transporter = fields.Boolean('Transportista', default=False)
    license_number = fields.Char(string='Número de Licencia')
    is_cont_especial = fields.Boolean('Codigo Contribuyente Especial')
    is_rise = fields.Boolean('Contribuyente Negocio Popular Regimen RIMPE')


    ats_country = fields.Many2one('ats.country', string='Pais')
    ats_country_efec_gen = fields.Many2one('ats.country', string='Pais Efec')
    ats_country_efec_parfic = fields.Many2one('ats.country', string='Pais Efec ParFis')
    ats_doble_trib = fields.Boolean('Aplica doble tributacion', default=False)
    denopago = fields.Char('Denominacion', help='Denominación del régimen fiscal preferente o jurisdicción de menor imposición.')
    pag_ext_suj_ret_nor_leg = fields.Boolean('Sujeto a retencion', help='Pago al exterior sujeto a retención en aplicación a la norma legal', default=False)
    pago_reg_fis = fields.Boolean('Regimen Fiscal Preferente', help='El pago es a un régimen fiscal preferente o de menor imposición?', default=False)
    method_payment = fields.Many2one('account.epayment', string="Forma de Pago")
    ats_country = fields.Many2one('ats.country', string='Pais')
    tipo_proveedor_reembolso_id = fields.Many2one('tipo.proveedor.reembolso', string='Tipo de Proveedor de Reembolso')
    type_identifier = fields.Selection(
        [
            ('cedula', 'CEDULA'),
            ('ruc', 'RUC'),
        ],
        'Tipo ID')
    """@api.onchange('l10n_latam_identification_type_id')
    def act_ident(self):
        for s in self:
            if s.l10n_latam_identification_type_id.name  == 'Ced':
                s.type_identifier=='ruc'
            if s.l10n_latam_identification_type_id.name   == 'RUC':
                s.type_identifier=='cedula'  """

    @api.constrains('company_type')
    def ingresar_tipo_proveedor_reembolso(self,):
        if self.company_type=='company':
            self.tipo_proveedor_reembolso_id=self.env.ref('gzl_facturacion_electronica.tipo_proveedor_reembolso_sociedad').id
        else:
            self.tipo_proveedor_reembolso_id=self.env.ref('gzl_facturacion_electronica.tipo_proveedor_reembolso_persona').id
