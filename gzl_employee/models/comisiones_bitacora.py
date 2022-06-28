# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import *
import calendar

class ComisionesBitacora(models.Model):
    _name = 'comision.bitacora'

    user_id = fields.Many2one('res.users',string="Usuario")
    supervisor_id = fields.Many2one('res.users',string="Supervisor")
    lead_id = fields.Many2one('crm.lead',string="Oportunidad")
    valor_inscripcion = fields.Float('Valor de inscripción')

    bono = fields.Float('Bono')
    porcentaje_comision = fields.Float('porcentaje comision')
    comision = fields.Float('Comisión')
    cargo = fields.Many2one('hr.job',string="Cargo")
    empleado_id = fields.Many2one('hr.employee',string="Empleado")


    active = fields.Boolean('Bono',default=True)





