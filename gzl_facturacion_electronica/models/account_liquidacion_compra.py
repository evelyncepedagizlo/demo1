# -*- coding: utf-8 -*-
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import itertools
import logging
from itertools import groupby
import json

_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
    _inherit = 'account.move'



    documento_reembolso_id = fields.Many2one('account.move', 'Documento Reembolso',copy=False)

    marca= fields.Char(string="Máquina")
    modelo= fields.Char(string="Modelo")
    serie= fields.Char(string="Serie")
