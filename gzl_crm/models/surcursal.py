# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models




class Surcursal(models.Model):

    _name = "surcursal"


    name = fields.Char('Nombre de Surcursal', required=True, index=True)
    codigo = fields.Char('Codigo', required=True, index=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    provincia_id= fields.Many2one(
        'res.country.state', string='Provincia', track_visibility='onchange' )

    ciudad_id = fields.Many2one(
        'res.country.city', string='Ciudad', domain="[('provincia_id','=',provincia_id)]", track_visibility='onchange')




    delegado_id = fields.Many2one('crm.team' , string="Delegado",track_visibility='onchange' )
    postventa_id = fields.Many2one('crm.team' , string="PostVenta",track_visibility='onchange' )

    grupo_id = fields.Many2one('res.groups', string='Grupo')




    def name_get(self):
        res = []
        for surcursal in self:
            name = "%s (%s)" % (surcursal.name, surcursal.codigo)
            res += [(surcursal.id, name)]
        return res