# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    beneficiary_name = fields.Char(string="Nombre Completo")
    beneficiary_ced = fields.Char(string="Cédula")
    beneficiary_birthday = fields.Date(string="Fecha de nacimiento")
    beneficiary_email = fields.Char(string="Correo")
    beneficiary_address = fields.Char(string="Domicilio")
    beneficiary_movil = fields.Char(string="Teléfono")