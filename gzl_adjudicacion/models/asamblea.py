from odoo import api, fields, models
import json
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
import datetime


class Asamblea(models.Model):
    _name = 'asamblea'
    _description = 'Proceso de Asamblea'
    _rec_name = 'secuencia'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    secuencia = fields.Char(index=True)
    descripcion = fields.Text('Descripcion',  required=True,track_visibility='onchange')
    active = fields.Boolean(default=True,track_visibility='onchange')
    integrantes = fields.One2many(
        'integrante.grupo.adjudicado.asamblea', 'asamblea_id',track_visibility='onchange')
    # integrantes = fields.Many2many('integrante.grupo.adjudicado')
    codigo_tipo_contrato = fields.Char(related="tipo_asamblea.code", string='Tipo de Asamblea' )
    #fecha_asamblea = fields.Date(String='Fecha de Asamblea')
    
    junta = fields.One2many('junta.grupo.asamblea', 'asamblea_id',track_visibility='onchange')
    ganadores = fields.One2many('gana.grupo.adjudicado.asamblea.clientes', 'grupo_id',track_visibility='onchange')
    fecha_inicio = fields.Datetime(String='Fecha Inicio',track_visibility='onchange')
    fecha_fin = fields.Datetime(String='Fecha Fin',track_visibility='onchange')
    tipo_asamblea = fields.Many2one(
        'tipo.contrato.adjudicado', string='Tipo de Asamblea',track_visibility='onchange')
    state = fields.Selection(selection=[
            ('borrador', 'Borrador'),
            ('inicio', 'Ingreso de Socios'),
            ('en_curso', 'En Curso'),
            ('pre_cierre', 'Pre cierre'),
            ('cerrado', 'Cerrado')
            ], string='Estado', copy=False, tracking=True, default='inicio',track_visibility='onchange')


    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    licitaciones=fields.Monetary(string='Licitaciones', currency_field='currency_id', track_visibility='onchange')
    evaluacion=fields.Monetary(string='Evaluación', currency_field='currency_id', track_visibility='onchange')
    programo=fields.Monetary(string='Plan Programo', currency_field='currency_id', track_visibility='onchange')
    monto_financiamiento=fields.Monetary(string='Monto', currency_field='currency_id', track_visibility='onchange')

    recuperacionCartera = fields.Monetary(string='Recuperación de Cartera', currency_field='currency_id', track_visibility='onchange')
    adjudicados = fields.Monetary(string='Adjudicados', currency_field='currency_id', track_visibility='onchange')
    fondos_mes=fields.Monetary(string='Fondos del Mes', currency_field='currency_id', track_visibility='onchange')
    invertir_licitacion=fields.Monetary(string='Invertir-Licitacion', currency_field='currency_id', track_visibility='onchange')
    saldo=fields.Monetary(string='Saldo', compute="obtener_saldo",currency_field='currency_id', track_visibility='onchange')

    @api.depends('fondos_mes','invertir_licitacion','programo','evaluacion')
    def obtener_saldo(self):
        for l in self:
            l.saldo=l.fondos_mes-l.invertir_licitacion-l.programo-l.evaluacion


    @api.constrains('integrantes')
    @api.onchange('integrantes')
    @api.depends('integrantes')
    def obtener_valores(self):
        for l in self:
            fondos_mes=0
            recuperacionCartera=0
            adjudicados=0
            for x in l.integrantes:
                fondos_mes+=x.fondos_mes
                recuperacionCartera+=x.recuperacionCartera
                adjudicados+=x.adjudicados
            l.fondos_mes=fondos_mes
            l.recuperacionCartera=recuperacionCartera
            l.adjudicados=adjudicados


    @api.constrains('ganadores')
    @api.onchange('ganadores')
    @api.depends('ganadores')
    def obtener_valores_contrato(self):
        for l in self:
            monto_financiamiento=0
            licitaciones=0
            invertir_licitacion=0
            evaluacion=0
            programo=0
            for x in l.ganadores:
                if l.codigo_tipo_contrato=='ahorro':
                    monto_financiamiento+=x.monto_financiamiento
                    licitaciones+=x.total_or
                    invertir_licitacion=monto_financiamiento-licitaciones
                elif l.codigo_tipo_contrato=='evaluacion':
                    evaluacion+=x.monto_financiamiento
                elif l.codigo_tipo_contrato=='programo':
                    programo+=(x.monto_financiamiento-x.monto_programado)
            l.monto_financiamiento=monto_financiamiento
            l.licitaciones=licitaciones
            l.invertir_licitacion=invertir_licitacion
            l.evaluacion=evaluacion
            l.programo=programo



    @api.model
    def create(self, vals):
        vals['secuencia'] = self.env['ir.sequence'].next_by_code('asamblea')
        res = self.env['res.config.settings'].sudo(1).search([], limit=1, order="id desc")
        return super(Asamblea, self).create(vals)

    @api.constrains('secuencia')
    def constrains_valor_por_defecto(self): 
        res = self.env['res.config.settings'].sudo(1).search([], limit=1, order="id desc")




    def cambio_estado_boton_precierre(self):
        self.write({"state": "pre_cierre"})
        if self.tipo_asamblea.code in ['ahorro']:
            listaGanadores=[]
            for grupo in self.integrantes:
                for integrante in grupo.integrantes_g:
                    dct={}

                    contrato = self.env['contrato'].search(
                        [('cliente', '=', integrante.adjudicado_id.id)], limit=1)
                    dct['contrato_id']=contrato.id
                    dct['adjudicado_id']=integrante.adjudicado_id.id
                    dct['grupo_adjudicado_id']=contrato.grupo.id
                    dct['puntos']=integrante.nro_cuota_licitar
                    listaGanadores.append(dct)


            # This changes the list a

            # This returns a new list (a is not modified)
            #raise ValidationError(str(listaGanadores))
            
            listaGanadores=sorted(listaGanadores, key=lambda k : k['puntos'],reverse=True) 


            numero_ganadores=self.tipo_asamblea.numero_ganadores*2
            for ganador in listaGanadores[:numero_ganadores]:
                ganador['grupo_id']=self.id
                self.env['gana.grupo.adjudicado.asamblea.clientes'].create(ganador)

            
        elif self.tipo_asamblea.code in ['evaluacion']:
            listaGanadores=[]
            for grupo in self.integrantes:
                for integrante in grupo.integrantes_g:
                    dct={}

                    contrato = self.env['contrato'].search(
                        [('cliente', '=', integrante.adjudicado_id.id)], limit=1)
                    dct['contrato_id']=contrato.id
                    dct['adjudicado_id']=integrante.adjudicado_id.id
                    dct['grupo_adjudicado_id']=contrato.grupo.id
                    listaGanadores.append(dct)


            # This changes the list a

            # This returns a new list (a is not modified)
            #raise ValidationError(str(listaGanadores))
            
            #listaGanadores=sorted(listaGanadores, key=lambda k : k['grupo_adjudicado_id'],reverse=True) 

            numero_ganadores=self.tipo_asamblea.numero_ganadores*2
            for ganador in listaGanadores[:numero_ganadores]:
                ganador['grupo_id']=self.id
                self.env['gana.grupo.adjudicado.asamblea.clientes'].create(ganador)
      
            
        elif self.tipo_asamblea.code in ['programo']:
            listaGanadores=[]
            for grupo in self.integrantes:
                for integrante in grupo.integrantes_g:
                    dct={}

                    contrato = self.env['contrato'].search(
                        [('cliente', '=', integrante.adjudicado_id.id)], limit=1)

                    dct['adjudicado_id']=integrante.adjudicado_id.id
                    dct['grupo_adjudicado_id']=contrato.grupo.id
                    dct['contrato_id']=contrato.id
                    listaGanadores.append(dct)


            # This changes the list a

            # This returns a new list (a is not modified)
            #listaGanadores=sorted(listaGanadores, key=lambda k : k['grupo_adjudicado_id'],reverse=True)            
            numero_ganadores=self.tipo_asamblea.numero_ganadores*2


            for ganador in listaGanadores[:numero_ganadores]:
                ganador['grupo_id']=self.id
                self.env['gana.grupo.adjudicado.asamblea.clientes'].create(ganador)

            



    def cambio_estado_boton_cerrado(self):
        entrega_vehiculo=self.env['entrega.vehiculo']
        listaGanadores=[]


        for l in self.ganadores:
            dct={}
            dct['adjudicado_id']=l.adjudicado_id.id
            dct['puntos']=l.puntos
            dct['contrato_id']=l.contrato_id.id
            dct['monto']=l.monto_adjudicar
            listaGanadores.append(dct)

        listaGanadores=sorted(listaGanadores, key=lambda k : k['puntos'],reverse=True) 
        numero_ganadores=self.tipo_asamblea.numero_ganadores

        for l in  listaGanadores[:numero_ganadores]:
            rol_asignado=self.env.ref('gzl_adjudicacion.tipo_rol3')
            entrega=entrega_vehiculo.create({'asamblea_id':self.id,'nombreSocioAdjudicado':l['adjudicado_id'],'rolAsignado':rol_asignado.id ,'montoEnviadoAsamblea':l['monto']  })

            transacciones=self.env['transaccion.grupo.adjudicado']
            contrato_id=self.env['contrato'].browse(l['contrato_id'])

            contrato_id.entrega_vehiculo=entrega.id

            dct={
            'grupo_id':contrato_id.grupo.id,
            'debe':l['monto'],
            'adjudicado_id':l['adjudicado_id'],
            'contrato_id':l['contrato_id'],
            'state':contrato_id.state
            }


            transacciones.create(dct)


        self.write({"state": "cerrado"})




class GrupoAsamblea(models.Model):
    _name = 'integrante.grupo.adjudicado.asamblea'
    _description = 'Grupo Participante en asamblea'

    asamblea_id = fields.Many2one('asamblea')
    grupo_adjudicado_id = fields.Many2one('grupo.adjudicado')
    tipo_contrato = fields.Many2one(
        'tipo.contrato.adjudicado', string='Tipo de Asamblea',track_visibility='onchange')

    codigo_tipo_contrato = fields.Char(related="tipo_contrato.code", string='Tipo de Asamblea' )


    integrantes_g = fields.One2many('integrante.grupo.adjudicado.asamblea.clientes','grupo_id')
    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)


    recuperacionCartera = fields.Monetary(compute='calculo_recuperacion_cartera',string='Recuperación de Cartera', currency_field='currency_id', track_visibility='onchange')
    adjudicados = fields.Monetary(compute='calculo_recuperacion_cartera',string='Adjudicados', currency_field='currency_id', track_visibility='onchange')
    fondos_mes=fields.Monetary(compute='calculo_recuperacion_cartera',string='Fondos del Mes', currency_field='currency_id', track_visibility='onchange')


    @api.depends('grupo_adjudicado_id')
    def calculo_recuperacion_cartera(self):
        for l in self:
            hoy=date.today()
            grupoParticipante=l.grupo_adjudicado_id.transacciones_ids.filtered(lambda l: l.create_date.month==hoy.month and l.create_date.year==hoy.year)
            l.recuperacionCartera= sum(grupoParticipante.mapped('haber'))
            l.adjudicados= sum(grupoParticipante.mapped('debe'))
            l.fondos_mes=l.recuperacionCartera-l.adjudicados
            




    @api.onchange('grupo_adjudicado_id')
    def onchange_grupo_adjudicado_id(self):
        self.integrantes_g=()


class IntegrantesGrupoAsamblea(models.Model):
    _name = 'integrante.grupo.adjudicado.asamblea.clientes'
    _description = 'Integrantes de Grupo Participante en asamblea'
  


    adjudicado_id = fields.Many2one('res.partner', string="Nombre")
    descripcion=fields.Char('Descripcion',  )
    grupo_id = fields.Many2one('integrante.grupo.adjudicado.asamblea')
    grupo_cliente = fields.Many2one('grupo.adjudicado')
    nro_cuota_licitar = fields.Integer(string='Nro de Cuotas a Licitar',default=1)
    carta_licitacion = fields.Selection([('si', 'Si'), ('no', 'No')], string='Carta Licitación')
    carta_doc = fields.Binary(string='Carta Licitación')




    dominio  = fields.Char(store=False, compute="_filtro_partner",readonly=True)

    #@api.onchange('nro_cuota_licitar')
    def ingresar_cuota(self):
        if self.nro_cuota_licitar==0:
            raise ValidationError("Por favor Ingrese el número de Cuotas.")



    @api.depends('grupo_cliente')
    def _filtro_partner(self):
        numero_cuotas_pagadas_limite =  int(self.env['ir.config_parameter'].sudo().get_param('gzl_adjudicacion.numero_cuotas_pagadas'))
        for rec in self:

            integrantes=rec.grupo_id.grupo_adjudicado_id.integrantes.filtered(lambda l: l.contrato_id.tipo_de_contrato.id==rec.grupo_id.tipo_contrato.id and l.contrato_id.numero_cuotas_pagadas>=numero_cuotas_pagadas_limite and l.contrato_id.state=='activo').mapped('adjudicado_id').ids
            integrantes_res=rec.grupo_id.integrantes_g.mapped("adjudicado_id").ids
            if len(integrantes)>0:
                rec.dominio=json.dumps( [('id','in',integrantes),('id','not in',integrantes_res)] )
            else:
                rec.dominio=json.dumps([])




class GanadoresAsamblea(models.Model):
    _name = 'gana.grupo.adjudicado.asamblea.clientes'
    _description = 'Ganadores de la Asamblea'


    grupo_id = fields.Many2one('asamblea')
    adjudicado_id = fields.Many2one('res.partner', string="Nombre")
    contrato_id = fields.Many2one('contrato', string="Nombre")
    fecha_antiguedad = fields.Datetime(related='contrato_id.create_date', string="Fecha de Antiguedad")
    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)

    monto_financiamiento = fields.Monetary(related='contrato_id.monto_financiamiento',string='Monto Financiamiento', currency_field='currency_id', track_visibility='onchange')
    monto_adjudicar = fields.Float( string="Monto a Adjudicar")
    grupo_adjudicado_id = fields.Many2one('grupo.adjudicado',string="Grupo")
    puntos = fields.Integer(string='Nro de Cuotas a Licitar')
    calificacion = fields.Integer(related='puntos',string='Calificación')
    plazo_meses = fields.Many2one('numero.meses',related="contrato_id.plazo_meses")
    cuota=fields.Float("Cuota")
    cuota_capital=fields.Monetary("Cuota Capital", currency_field='currency_id',related="contrato_id.cuota_capital")
    total_or=fields.Float("O.R",compute="calcular_cuotas")
    nro_cuotas_adelantadas = fields.Integer(string='Cuotas Pagadas', related="contrato_id.numero_cuotas_pagadas")
    total_cuotas = fields.Integer(string='Total de Cuotas',compute="calcular_cuotas")
    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    cuota_pago = fields.Integer( related="contrato_id.cuota_pago")
    monto_programado = fields.Monetary(
        string='Entrada', related="contrato_id.monto_programado", currency_field='currency_id')

    @api.constrains('contrato_id')
    def actualizar_monto_financiamiento(self):
        self.cuota=self.contrato_id.cuota_adm+self.contrato_id.cuota_capital+self.contrato_id.iva_administrativo
        self.cuota_adm=self.contrato_id.cuota_capital
        self.monto_adjudicar=self.cuota*self.puntos
        self.grupo_id.obtener_valores_contrato()

    @api.depends('contrato_id')
    def calcular_cuotas(self):
        for l in self:
            l.total_cuotas=l.nro_cuotas_adelantadas+ l.puntos
            l.total_or=l.cuota_capital*l.puntos
            l.grupo_id.obtener_valores_contrato()

class JuntaGrupoAsamblea(models.Model):
    _name = 'junta.grupo.asamblea'
    _description = 'Comité que realiza la asamblea'

    asamblea_id = fields.Many2one('asamblea', string='Asamblea')
    empleado_id = fields.Many2one('hr.employee', string="Empleado")