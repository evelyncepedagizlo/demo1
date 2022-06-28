from odoo import models,api,fields
from odoo.exceptions import UserError, ValidationError

class ContratoEstadoCuentaPagos(models.Model):
    _name = 'contrato.estado.cuenta.payment'
    _description = 'Contrato - Tabla Relacional de pagos y contratos'
    # _rec_name = 'numero_cuota'



    
    payment_pagos_id = fields.Many2one('account.payment')
    idContrato = fields.Char("ID de Contrato en base")
    contrato_id = fields.Many2one('contrato')
    numero_cuota = fields.Char(String='Número de Cuota', readonly=True)
    fecha = fields.Date(String='Fecha Pago', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    cuota_capital = fields.Monetary(
        string='Cuota Capital', currency_field='currency_id', readonly=True)
    # pago_ids = fields.Many2many('account.payment','contrato_estado_cuenta_payment_rel', 'estado_cuenta_id','payment_id', string='Pagos')
    seguro = fields.Monetary(string='Seguro', currency_field='currency_id', readonly=True)
    rastreo = fields.Monetary(string='Rastreo', currency_field='currency_id', readonly=True)
    otro = fields.Monetary(string='Otro', currency_field='currency_id', readonly=True)
    
    programado = fields.Monetary('Cuota Programada')
    saldo = fields.Monetary(string='Saldo', currency_field='currency_id' , readonly=True)
    cuota_capital_pagar = fields.Monetary('Cuota Capital a Pagar')
    seguro_pagar = fields.Monetary('Seguro a Pagar')
    rastreo_pagar = fields.Monetary('Rastreo a Pagar')
    otro_pagar = fields.Monetary('Otro a Pagar')
    entrada_pagar = fields.Monetary('Programado a pagar')

    monto_pagar = fields.Monetary('Monto a Pagar', compute='_obtener_monto',store=True)

    @api.onchange('cuota_capital_pagar')
    def validar_cuota_capital_pagar(self):
        for l in self:
            if l.cuota_capital_pagar>l.cuota_capital:
                raise ValidationError("El valor a Pagar no puede ser mayor que el permitido")

    @api.onchange('seguro_pagar')
    def validar_seguro_pagar(self):
        for l in self:
            if l.seguro_pagar>l.seguro:
                raise ValidationError("El valor a Pagar no puede ser mayor que el permitido")

    @api.onchange('rastreo_pagar')
    def validar_rastreo_pagar(self):
        for l in self:
            if l.rastreo_pagar>l.rastreo:
                raise ValidationError("El valor a Pagar no puede ser mayor que el permitido")

    @api.onchange('otro_pagar')
    def validar_otro_pagar(self):
        for l in self:
            if l.otro_pagar>l.otro:
                raise ValidationError("El valor a Pagar no puede ser mayor que el permitido")

    @api.depends('cuota_capital_pagar','seguro_pagar','rastreo_pagar','otro_pagar','entrada_pagar')
    def _obtener_monto(self):
        for l in self:
            l.monto_pagar=l.cuota_capital_pagar+l.seguro_pagar+l.rastreo_pagar+l.otro_pagar+l.entrada_pagar
            l.payment_pagos_id._saldo_pagar()




    def crear_detalles(self):
        viewid = self.env.ref('gzl_facturacion_electronica.estado_contrato_form').id
        return {   
            'name':'Valores a Pagar',
            'view_type':'form',
            'views' : [(viewid,'form')],
            'res_model':'contrato.estado.cuenta.payment',
            'res_id':self.id,
            'type':'ir.actions.act_window',
            'target':'new',
            }


    def cerrar_ventana(self):
        self.payment_pagos_id.crear_asientos()
        self.payment_pagos_id.crear_detalles()
