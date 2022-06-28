# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'
    _description = 'Departure Wizard'


    fecha_salida =  fields.Date('Fecha de Salida')
    monto_liquidacion =  fields.Float('Monto de Liquidación')


    def action_register_departure(self):
        employee = self.employee_id
        employee.departure_reason = self.departure_reason
        employee.departure_description = self.departure_description
        employee.fecha_salida = self.fecha_salida
        employee.monto_liquidacion = self.monto_liquidacion

        if not employee.user_id.partner_id:
            return

        for activity_type in self.plan_id.plan_activity_type_ids:
            self.env['mail.activity'].create({
                'res_id': employee.user_id.partner_id.id,
                'res_model_id': self.env['ir.model']._get('res.partner').id,
                'activity_type_id': activity_type.activity_type_id.id,
                'summary': activity_type.summary,
                'user_id': activity_type.get_responsible_id(employee).id,
            })
