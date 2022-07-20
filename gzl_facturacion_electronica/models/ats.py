# -*- coding: utf-8 -*-
 
import time
from datetime import datetime, date

from odoo import api, fields, models
from odoo.exceptions import (
    ValidationError,
    Warning as UserError
)

class AtsSustentoComprobante(models.Model):
    _name = 'ats.sustento.comprobante'
    _description = 'Sustento del Comprobante'

   
    @api.depends('code', 'type')
    def name_get(self):
        res = []
        for record in self:
            name = '%s - %s' % (record.code, record.type)
            res.append((record.id, name))
        return res

    _rec_name = 'type'

    code = fields.Char('Código', size=2, required=True)
    type = fields.Char('Tipo de Sustento', size=128, required=True)
    active = fields.Boolean(string="Activo", default=False)


class AtsCountry(models.Model):
    _name = 'ats.country'
    _rec_name = 'name'
    _description = 'Paises'
    
    name = fields.Char('Nombre')
    code = fields.Char('Code')
    is_fiscal_paradise = fields.Boolean("Paraiso Fiscal")



class AtsEarning(models.Model):
    _name = 'ats.earning'
    _rec_name = 'name'
    _description = 'configuraciones ats'

    name = fields.Char('Nombre')
    code = fields.Char('Code')


class AccountEpayment(models.Model):
    _name = 'account.epayment'
    _rec_name = 'name'
    _description = 'Tipo de pago segun el sri'

    code = fields.Char('Código')
    name = fields.Char('Forma de Pago')
    active = fields.Boolean(string="Activo", default=False)


class AtsPagoResidente(models.Model):
    _name = 'ats.pago.residente'
    _rec_name = 'name'
    _description = 'Forma de pago segun el sri'

    name = fields.Char(string="Tipo de Pago")
    code = fields.Char(string="Código")
    active = fields.Boolean(string="Activo", default=False)


class AtsRegimenFiscal(models.Model):
    _name = 'ats.regimen.fiscal'
    _rec_name = 'name'
    _description = 'Regimen Fiscal segun el sri'

    name = fields.Char(string="Regimen Fiscal")
    code = fields.Char(string="Código")
    active = fields.Boolean(string="Activo", default=False)


