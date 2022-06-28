# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
import re
import json
import base64
import logging
import mimetypes
import odoo.tools
import hashlib
from odoo import api, fields, models, tools, SUPERUSER_ID
from datetime import datetime,timedelta,date
import time
from odoo import _
from odoo.exceptions import ValidationError, except_orm
from dateutil.relativedelta import *

import base64
from base64 import urlsafe_b64decode

import shutil



#class Nomina_mensual(models.Model):
class Nomina_mensual(models.TransientModel):
    _name = "correo.nomina.mensual"
    #_inherit ="hr.employee"
    def _get_available_contracts_domain(self):
        payslip = self.env['hr.payslip'].search([('date_from','>=',self.fecha_inicio),('date_to','<=',self.fecha_fin)])
        #raise ValidationError(str(list(payslip.employee_id.ids))+' payslip')
        return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id),('id', 'in', list(payslip.employee_id.ids))]

    def _get_employees(self):
        # YTI check dates too
        return self.env['hr.employee'].search(self._get_available_contracts_domain())

    employee_ids_correo = fields.Many2many('hr.employee',
                                    default=lambda self: self._get_employees(), required=True)

    fecha_inicio = fields.Date(string="Desde")
    fecha_fin = fields.Date(string="Hasta")

    work_email = fields.Char('Work Email')
    url_doc = fields.Char('Url doc')


    def actualizar_empleados_payroll(self):   
        self.employee_ids_correo=self._get_employees()
        self.ensure_one()
        self.name = "New name"
        #return {
        #    "type": "ir.actions.do_nothing",
        #}
        #self.send_mail_payrol()
        #self.ensure_one()
        #self.name = "New name"
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'correo.nomina.mensual',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        #raise ValidationError(str(self.employee_ids_correo)+' result')
    def send_mail_payrol(self):
        lis=[]
        #result = self.env['hr.payslip']
        #raise ValidationError(str(self.employee_ids_correo)+' result')
        for l in self.employee_ids_correo:
            
            #result = self.env['hr.payslip'].search([('employee_id', '=', l.id)])
            payslip = self.env['hr.payslip'].search([('employee_id','=',l.id),('date_from','>=',self.fecha_inicio),('date_to','<=',self.fecha_fin)])
            #url='/print/payslips?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in payslip.ids)}
            
            if len(payslip) > 0:
            #    url='/print/payslips?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in payslip.ids)}
                
                #payslip.update({'url_doc': url})
                for a in payslip:
                    url={
                    'name': 'Payslip',
                    'type': 'ir.actions.act_url',
                    'url': '/print/payslips?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in a.ids)},
                    }
                    #url='/print/payslips?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in a.ids)}
                    a.update({'url_doc': url['url']})
                    self.envio_correos_plantilla('email_rol_nomina',a.id)
                #lis.append(url)
        #if lis:
        #    raise ValidationError(str(lis)+'   -- ')
        #    self.envio_correos_plantilla('correo_nomina_mensual',l.id)
    
    
    def envio_correos_plantilla(self, plantilla,id_envio):

        try:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data.get_object_reference('gzl_reporte', plantilla)[1]
        except ValueError:
            template_id = False
#Si existe capturo el template
        if template_id:
            obj_template=self.env['mail.template'].browse(template_id)

            email_id=obj_template.send_mail(id_envio)  
class NominaRolmensualModelo(models.Model):
    _inherit = 'hr.payslip'
#    _name = 'correo.nomina.mensual.modelo'
#    work_email = fields.Char('Work Email')
    url_doc = fields.Char('Url doc')
#    employee_id = fields.One2many(
#        'hr.employee', track_visibility='onchange')