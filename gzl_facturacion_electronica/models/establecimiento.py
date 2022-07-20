# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class Establecimiento(models.Model):
    _name = 'establecimiento'
    _rec_name = 'name'
    _description = 'Configuraciones de secuencia'

    name = fields.Char('Nombre')
    authorization_number = fields.Char('Num. de Autorización', size=10)
    serie_establecimiento = fields.Char('Serie Establecimiento', size=3)
    serie_emision = fields.Char('Serie Emision', size=3)
    num_start = fields.Integer('Desde', default=1)
    num_end = fields.Integer('Hasta')
    is_electronic = fields.Boolean('Documento Electrónico ?')
    active = fields.Boolean(string='Activo',default=True)
    type_id = fields.Many2one('l10n_latam.document.type','Tipo de Comprobante',required=True)
    sequence_id = fields.Many2one('ir.sequence','Secuencia',ondelete='cascade',
        help='Secuencia Alfanumerica para el documento, se debe registrar cuando pertenece a la compañia',
        )
    expiration_date = fields.Date('Fecha de Vencimiento')
    is_manual_sequence = fields.Boolean(string='Es Secuencia Manual?', default=False)

    _sql_constraints = [
        ('number_unique',
         'unique(authorization_number,serie_emision,serie_establecimiento,type_id,is_electronic)',
         u'La relación de autorización, serie establecimiento, serie emisor y tipo, debe ser única.'),
        ]

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, values):
        tipo = self.env['l10n_latam.document.type'].browse(values['type_id'])
        if values['is_manual_sequence']!=True:
            vals = self.search([
                               ('type_id', '=', values['type_id']),
                               ('serie_establecimiento', '=', values['serie_establecimiento']),
                               ('serie_emision', '=', values['serie_emision']),
                               ('active', '=', True),
                               ('is_electronic', '=', True)
                               ])

            if vals:
                raise ValidationError('Ya existe un secuencial activo para '+tipo.name)
            if values['authorization_number']:
                name_type = '{0}'.format(values['authorization_number'])
            else:
                name_type = '{0}_{1}'.format(values['serie_establecimiento'], values['serie_emision'])
            sequence_data = {
                'code': (tipo.name.replace(' ','.')).lower()+'.'+name_type,
                'name': (tipo.name.replace(' ','_')).lower()+'_'+name_type,
                'implementation':'standard',
                'padding': 9,
                'number_next': values['num_start'],
            }
            seq = self.env['ir.sequence'].create(sequence_data)
            values.update({'sequence_id': seq.id, 'name':seq.name})
        else:
            values['name']= (tipo.name.replace(' ','_')).lower()+'_'+values['authorization_number']
        
        return super(Establecimiento, self).create(values)
    
    @api.depends('expiration_date', 'is_electronic')
    def _compute_active(self):
        """
        Check the due_date to give the value active field
        """
        for s in self:
            if s.is_electronic:
                s.active = True
                return
            if not s.expiration_date:
                return
            now = date.today()
            due_date = s.expiration_date #datetime.strptime(s.expiration_date, '%Y-%m-%d')
            s.active = now < due_date