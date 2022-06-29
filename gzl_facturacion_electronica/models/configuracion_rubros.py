# # -*- coding: utf-8 -*-
 

# import time
# from datetime import datetime, date
# from odoo import api, fields, models

# class RubrosContratos(models.Model):
#     _name = 'rubros.contratos'


#     cuenta_id = fields.Many2one('account.account','Cuenta')
#     journal_id = fields.Many2one('account.journal','Diario')
#     name = fields.Selection([('cuota_capital','Cuota Capital'),
#                                         ('seguro','Seguro'),
#                                         ('otros','Otros'),
#                                         ('rastreo','Rastreo')
#                                         ],string='Rubros')
