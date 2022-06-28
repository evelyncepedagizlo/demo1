# -*- coding: utf-8 -*-
from odoo import fields, models,  _

class SignSendRequest(models.TransientModel):
    _inherit = 'sign.send.request'

    contrato = fields.Many2one('contrato', string='Contrato')
    grupo = fields.Many2one('grupo.adjudicado', string='Grupo')

    def sign_directly_without_mail(self):
        grupo_contrato = self.grupo.codigo +" - "+ self.contrato.secuencia
        self.env.cr.execute("""update res_partner set contrato={0},grupo={1},grupo_contrato='{2}' where id={3}""".format(self.contrato.id,self.grupo.id,grupo_contrato,self.signer_ids.partner_id.id))
        self.env.cr.commit()

        #    def sign_directly_without_mail(self):
        res = self.create_request(False, True)
        request = self.env['sign.request'].browse(res['id'])

        user_item = request.request_item_ids[0]

        return {
            'type': 'ir.actions.client',
            'tag': 'sign.SignableDocument',
            'name': _('Sign'),
            'context': {
                'id': request.id,
                'token': user_item.access_token,
                'sign_token': user_item.access_token,
                'create_uid': request.create_uid.id,
                'state': request.state,
                # Don't use mapped to avoid ignoring duplicated signatories
                'token_list': [item.access_token for item in request.request_item_ids[1:]],
                'current_signor_name': user_item.partner_id.name,
                'name_list': [item.partner_id.name for item in request.request_item_ids[1:]],
            },
        }