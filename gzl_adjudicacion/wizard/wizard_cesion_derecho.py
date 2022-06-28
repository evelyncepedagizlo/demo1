# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError

#import numpy_financial as npf


class WizardAdelantarCuotas(models.Model):
    _name = 'wizard.cesion.derecho'
    
    contrato_id = fields.Many2one('contrato')
    monto_a_ceder = fields.Float( string='Monto a Ceder',store=True)
    contrato_a_ceder= fields.Many2one('contrato',string="Contrato a Ceder")
    carta_adjunto = fields.Binary('Carta de Cesión', attachment=True)
    partner_id=fields.Many2one("res.partner", "Cliente a Ceder")
    




    def pagar_cuotas_por_adelantado(self):
        for l in self:
            if l.contrato_id:
                if l.partner_id:
                    l.contrato_id.nota=" "+str(self.contrato_id.cliente.name)+' Cede el contrato a la persona: '+str(self.partner_id.name)
                    l.contrato_id.cliente=self.partner_id.id

        # view_id = self.env.ref('gzl_adjudicacion.wizard_adelantar_cuotas_readonly_form').id


        # return {'type': 'ir.actions.act_window',
        #         'name': 'Validar Pago',
        #         'res_model': 'wizard.adelantar.cuotas',
        #         'target': 'new',
        #         'view_mode': 'form',
        #         'views': [[view_id, 'form']],
        #         'context': {
        #             'default_contrato_id': self.contrato_a_ceder.id,
        #             'default_monto_a_pagar':self.monto_a_ceder
        #         }
        # }


