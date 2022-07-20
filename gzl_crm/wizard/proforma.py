# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProformaCuotas(models.TransientModel):
    _name = 'proforma.cuotas'
    _description = 'Proforma de cuota exacta'

    name = fields.Char(string='Nombre',default='Proforma')
    monto_fijo = fields.Monetary(string='Monto Fijo', currency_field='company_currency_id')
    porcentaje_ce = fields.Float(string='Porcentaje de C.E')
    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)



    def print_proforma(self):
        return self.env.ref('gzl_crm.reporte_proforma_cuota').report_action(self)