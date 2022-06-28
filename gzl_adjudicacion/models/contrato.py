# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.parser import parse
import calendar
from dateutil.relativedelta import relativedelta
import math

class Contrato(models.Model):
    _name = 'contrato'
    _description = 'Contrato'
    _rec_name = 'secuencia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    en_mora = fields.Boolean(stirng="Contrato en Mora")

    entrega_vehiculo_id = fields.Many2one('entrega.vehiculo',string="Solicitud de entrega vehículo" ,track_visibility='onchange')


    porcentaje_programado = fields.Float(
        string='Porcentaje Programado')
    monto_programado = fields.Monetary(
        string='Saldo Programado ', currency_field='currency_id')

    cuota_pago = fields.Integer(
        string='Cuota de Pago Programado', track_visibility='onchange')
    idEstadoContrato = fields.Char("ID Estado Contrato")
    idTipoContrato = fields.Char("ID Tipo Contrato")
    idContrato = fields.Char("ID de Contrato en base")
    idClienteContrato= fields.Char("ID de Cliente en Cotnrato")
    idGrupo = fields.Char("ID de Grupo en Cotnrato")
    numeroContratoOriginal = fields.Char("Numero de Contrato Original")
    fechaInicioPago = fields.Date("Fecha de inicio de Pago")
    numeroCuotasPagadas = fields.Char("Numero de Contrato Original")

    secuencia = fields.Char(index=True)
    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    cliente = fields.Many2one(
        'res.partner', string="Cliente", track_visibility='onchange')
    grupo = fields.Many2one(
        'grupo.adjudicado', string="Grupo", track_visibility='onchange')
    dia_corte = fields.Char(string='Día de Corte', default=lambda self: self.capturar_valores_por_defecto_dia())
    saldo_a_favor_de_capital_por_adendum = fields.Monetary(
        string='Saldo a Favor de Capital por Adendum', currency_field='currency_id', track_visibility='onchange')
    pago = fields.Selection(selection=[
        ('mes_actual', 'Mes Actual'),
        ('siguiente_mes', 'Siguiente Mes'),
        ('personalizado', 'Personalizado')
    ], string='Pago', default='mes_actual', track_visibility='onchange')
    monto_financiamiento = fields.Monetary(
        string='Monto Financiamiento', currency_field='currency_id', track_visibility='onchange')
    tasa_administrativa = fields.Float(
        string='Tasa Administrativa(%)', track_visibility='onchange',default=lambda self: self.capturar_valores_por_defecto_tasa_administrativa())
    valor_inscripcion = fields.Monetary(
        string='Valor Inscripción', currency_field='currency_id', track_visibility='onchange')
    tipo_de_contrato = fields.Many2one(
        'tipo.contrato.adjudicado', string='Tipo de Contrato', track_visibility='onchange')
    codigo_grupo = fields.Char(compute='setear_codigo_grupo', string='Código de Grupo', track_visibility='onchange')
    provincias = fields.Many2one(
        'res.country.state', string='Provincia', track_visibility='onchange')
    archivo = fields.Binary(string='Archivo')
    fecha_contrato = fields.Date(
        string='Fecha Contrato', track_visibility='onchange')

    plazo_meses = fields.Many2one('numero.meses',default=lambda self: self.env.ref('gzl_adjudicacion.{0}'.format('numero_meses60')).id ,track_visibility='onchange' )

    tiene_cuota = fields.Boolean(String='Cuota de Entrada',default=False)
    cuota_adm = fields.Monetary(
        string='Cuota Administrativa',store=True, compute='calcular_valores_contrato', currency_field='currency_id', track_visibility='onchange')
    factura_inscripcion = fields.Many2one(
        'account.move', string='Factura Incripción', track_visibility='onchange')
    active = fields.Boolean(string='Activo', default=True)
    state = fields.Selection(selection=[
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('congelar_contrato', 'Congelado'),
        ('adjudicar', 'Adjudicado'),
        ('adendum', 'Realizar Adendum'),
        ('finalizado', 'Finalizado'),
        ('cedido', 'Cesión de Derecho'),
        ('desistir', 'Desistido'),
    ], string='Estado', default='pendiente', track_visibility='onchange')


    desistido = fields.Boolean(string='Desistido')


# A  Activo        activo    
# C  Congelado     congelar_contrtato
# F  Finalizado    finalizado
# I  Desistido     desistido
# J  Adjudicado    adjudicar
# P  Pendiente     pendiente



    is_group_cobranza = fields.Boolean(string='Es Cobranza',compute="_compute_is_group_cobranza")

    @api.depends("cliente")
    def _compute_is_group_cobranza(self):
        self.is_group_cobranza = self.env['res.users'].has_group('gzl_facturacion_electronica.grupo_cobranza')

    direccion = fields.Char(string='Dirección',
                              track_visibility='onchange')
    descripcion_adjudicaciones = fields.Char(string='Descripción de Adjudicaciones',
                              track_visibility='onchange')
    nota = fields.Char(string='Cesión de Derecho')

    observacion = fields.Char(string='Observación',
                              track_visibility='onchange')
    ciudad = fields.Many2one(
        'res.country.city', string='Ciudad', domain="[('provincia_id','=',provincias)]", track_visibility='onchange')
    archivo_adicional = fields.Binary(
        string='Archivo Adicional', track_visibility='onchange')
    fecha_inicio_pago = fields.Date(
        string='Fecha Inicio de Pago', compute='calcular_fecha_pago', track_visibility='onchange',store=True)
    cuota_capital = fields.Monetary(
        string='Cuota Capital', currency_field='currency_id', compute='calcular_valores_contrato', track_visibility='onchange',store=True)
    iva_administrativo = fields.Monetary(
        string='Iva Administrativo',  compute='calcular_valores_contrato',currency_field='currency_id', track_visibility='onchange',store=True)
    estado_de_cuenta_ids = fields.One2many(
        'contrato.estado.cuenta', 'contrato_id', track_visibility='onchange')
    fecha_adjudicado = fields.Date(
        string='Fecha Adj.', track_visibility='onchange')

    monto_pagado = fields.Float(
        string='Monto Pagado', compute="calcular_monto_pagado", store=True, track_visibility='onchange')

    tabla_amortizacion = fields.One2many(
        'contrato.estado.cuenta', 'contrato_id', track_visibility='onchange')

    congelar_contrato_ids = fields.One2many(
        'contrato.congelamiento', 'contrato_id', track_visibility='onchange')

    adendums_contrato_ids = fields.One2many(
        'contrato.adendum', 'contrato_id', track_visibility='onchange')


    actualizacion_ids=fields.One2many('actualizacion.contrato.valores','contrato_id',track_visibility='onchange')





    numero_cuotas_pagadas = fields.Integer(
        string='Cuotas Pagadas', compute="calcular_cuotas_pagadas", store=True, track_visibility='onchange')

    aplicaGarante  = fields.Boolean(string='Garante',default = False, track_visibility='onchange')
    
    garante =  fields.Many2one('res.partner', string="Garante", track_visibility='onchange')

    ejecutado = fields.Boolean(string="Ejecutado", default = False)
    @api.depends('grupo')
    def setear_codigo_grupo(self):
        for rec in self:
            if rec.grupo.codigo and rec.grupo.name:
                rec.codigo_grupo = "["+rec.grupo.codigo+"] "+ rec.grupo.name or ' '
            else:
                rec.codigo_grupo =' '

    @api.onchange('tipo_de_contrato')
    @api.constrains('tipo_de_contrato')
    def validar_entrada(self):
        for l in self:
            if l.tipo_de_contrato.code in ['exacto','programo']:
                l.tiene_cuota=True
            else:
                l.tiene_cuota=False

    @api.onchange('porcentaje_programado','monto_financiamiento','plazo_meses','tipo_de_contrato')
    def obtener_monto_programo(self):
        for l in self:
            if l.porcentaje_programado:
                l.monto_programado=l.monto_financiamiento*(l.porcentaje_programado/100)
            if l.tipo_de_contrato.code=='programo' and l.plazo_meses:
                l.cuota_pago=self.plazo_meses.numero
            else:
                l.cuota_pago=0
            


#    @api.constrains('state')
    def crear_registro_fondo_grupo(self):
        if self.grupo and self.state!='pendiente':
            self.grupo.calcular_monto_pagado()

            if self.state in ['desistir','inactivo','congelar_contrato']:
                transacciones=self.env['transaccion.grupo.adjudicado']

                dct={
                'grupo_id':self.grupo.id,
                'debe':self.monto_pagado ,
                'adjudicado_id':self.cliente.id,
                'contrato_id':self.id,
                'state':self.state
                }


                transacciones.create(dct)

            if self.state in ['activo']:
                transacciones=self.env['transaccion.grupo.adjudicado']

                dct={
                'grupo_id':self.grupo.id,
                'haber':self.monto_pagado ,
                'adjudicado_id':self.cliente.id,
                'contrato_id':self.id,
                'state':self.state
                }


                transacciones.create(dct)


    @api.depends('tabla_amortizacion.saldo')
    def calcular_cuotas_pagadas(self):
        for rec in self:
            cuotas=rec.tabla_amortizacion.filtered(lambda l: l.saldo==0)
            rec.numero_cuotas_pagadas=len(cuotas)

    def actualizar_calcular_cuotas_pagadas(self):
        for rec in self:
            rec.calcular_cuotas_pagadas()




    def capturar_valores_por_defecto_tasa_administrativa(self):
        tasa_administrativa =  float(self.env['ir.config_parameter'].sudo().get_param('gzl_adjudicacion.tasa_administrativa'))

        return tasa_administrativa


    def capturar_valores_por_defecto_dia(self):
        dia_corte =  self.env['ir.config_parameter'].sudo().get_param('gzl_adjudicacion.dia_corte')

        return dia_corte


    @api.depends('pago')
    def calcular_fecha_pago(self):
        for rec in self:
            if rec.dia_corte:
                if rec.pago == 'mes_actual':
                    anio = str(datetime.today().year)
                    mes = str(datetime.today().month)
                    fechaPago =  anio+"-"+mes+"-{0}".format(rec.dia_corte.zfill(2)) 
                    rec.fecha_inicio_pago = parse(fechaPago).date().strftime('%Y-%m-%d')
                elif rec.pago == 'siguiente_mes':
                    fechaMesSeguiente = datetime.today() + relativedelta(months=1)
                    mesSgte=str(fechaMesSeguiente.month)
                    anioSgte=str(fechaMesSeguiente.year)
                    fechaPago = anioSgte+"-"+mesSgte+"-{0}".format(rec.dia_corte.zfill(2)) 
                    rec.fecha_inicio_pago = parse(fechaPago).date().strftime('%Y-%m-%d')
                else:
                    rec.fecha_inicio_pago =False
    
    @api.depends('plazo_meses', 'monto_financiamiento','monto_programado')
    def calcular_valores_contrato(self):
        for rec in self:

            if int(rec.plazo_meses.numero):
                rec.cuota_capital = rec.monto_financiamiento/int(rec.plazo_meses.numero)
                if rec.tiene_cuota:
                    rec.cuota_capital=(rec.monto_financiamiento-rec.monto_programado)/int(rec.plazo_meses.numero)
                cuotaAdministrativa= rec.monto_financiamiento*((rec.tasa_administrativa/100)/12)
                rec.iva_administrativo = cuotaAdministrativa * 0.12
                rec.cuota_adm = cuotaAdministrativa

    def detalle_tabla_amortizacion(self):
        dia_corte =  self.dia_corte
        tasa_administrativa = self.tasa_administrativa

        self.tabla_amortizacion=()

        for rec in self:
            for i in range(0, int(rec.plazo_meses.numero)):
                
                cuota_capital = rec.monto_financiamiento/int(rec.plazo_meses.numero)
                if self.tiene_cuota:
                    cuota_capital=(rec.monto_financiamiento-rec.monto_programado)/int(rec.plazo_meses.numero)
                cuota_adm = rec.monto_financiamiento *tasa_administrativa / 100 / 12
                iva = cuota_adm * 0.12

                cuota_administrativa_neto= cuota_adm + iva
                saldo = cuota_capital+cuota_adm+iva
                cuota_asignada=i+1
                self.env['contrato.estado.cuenta'].create({
                                                    'numero_cuota':i+1,
                                                    'fecha':rec.fecha_inicio_pago + relativedelta(months=i),
                                                    'cuota_capital':cuota_capital,
                                                    'cuota_adm':cuota_adm,
                                                    'iva_adm':iva,
                                                    'saldo':saldo,
                                                    'saldo_cuota_capital':cuota_capital,
                                                    'saldo_cuota_administrativa':cuota_adm,
                                                    'saldo_iva':iva,
                                                    'contrato_id':self.id,
                                                        })
                if rec.cuota_pago and rec.tiene_cuota:
                    if cuota_asignada==rec.cuota_pago:
                        self.env['contrato.estado.cuenta'].create({'numero_cuota':rec.cuota_pago,
                                                                                'contrato_id':self.id,
                                                                                'cuota_capital':0,
                                                                                'cuota_adm':0,
                                                                                'iva_adm':0,
                                                                                'saldo':rec.monto_programado,
                                                                                'saldo_cuota_capital':0,
                                                                                'saldo_cuota_administrativa':0,
                                                                                'saldo_iva':0,
                                                                                'fecha':rec.fecha_inicio_pago + relativedelta(months=i),
                                                                                'saldo_programado':rec.monto_programado,'programado':rec.monto_programado})



        vls=[]                                                
        monto_finan_contrato = sum(self.tabla_amortizacion.mapped('cuota_capital'))
        monto_finan_contrato = round(monto_finan_contrato,2)
        #raise ValidationError(str(monto_finan_contrato))
        monto_financiamiento_contrato=self.monto_financiamiento
        if self.tiene_cuota:
            monto_financiamiento_contrato=self.monto_financiamiento-self.monto_programado
        if  monto_finan_contrato  > monto_financiamiento_contrato:
            valor_sobrante = monto_finan_contrato - monto_financiamiento_contrato 
            valor_sobrante = round(valor_sobrante,2)
            parte_decimal, parte_entera = math.modf(valor_sobrante)
            if parte_decimal==0:
                valor_a_restar=0
            elif parte_decimal >=1:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.1
            else:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.01

            obj_contrato=self.env['contrato.estado.cuenta'].search([('contrato_id','=',self.id),('estado_pago','=','pendiente')] , order ='fecha desc')
            for c in obj_contrato:
                if valor_sobrante != 0.00 or valor_sobrante != 0 or valor_sobrante != 0.0:
                    if c.programado == 0.00 or c.programado == 0 or c.programado == 0.0:
                        c.update({
                            'cuota_capital': c.cuota_capital - valor_a_restar,
                            'contrato_id':self.id,
                            'saldo_cuota_capital': c.cuota_capital - valor_a_restar,
                        })
                        vls.append(valor_sobrante)
                        valor_sobrante = valor_sobrante -valor_a_restar
                        valor_sobrante = round(valor_sobrante,2)
                            
                            
        if  monto_finan_contrato  < monto_financiamiento_contrato:
            valor_sobrante = monto_financiamiento_contrato  - monto_finan_contrato 
            valor_sobrante = round(valor_sobrante,2)
            parte_decimal, parte_entera = math.modf(valor_sobrante)
            if parte_decimal==0:
                valor_a_restar=0
            elif parte_decimal >=1:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.1
            else:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.01

            obj_contrato=self.env['contrato.estado.cuenta'].search([('contrato_id','=',self.id),('estado_pago','=','pendiente')] , order ='fecha desc')

            for c in obj_contrato:

                if valor_sobrante != 0.00 or valor_sobrante != 0 or valor_sobrante != 0.0:
                    if c.programado == 0.00 or c.programado == 0 or c.programado == 0.0:
                    #raise ValidationError(str(valor_sobrante)+'--'+str(parte_decimal)+'----'+str(valor_a_restar))
                        c.update({
                            'cuota_capital': c.cuota_capital + valor_a_restar,
                            'saldo_cuota_capital': c.cuota_capital + valor_a_restar,
                            'contrato_id':self.id,
                        })  
                        vls.append(valor_sobrante)
                        valor_sobrante = valor_sobrante -valor_a_restar
                        valor_sobrante = round(valor_sobrante,2)
        #raise ValidationError(str(vls)+'--')
    @api.depends("estado_de_cuenta_ids.monto_pagado")
    def calcular_monto_pagado(self,):
        for l in self:
            monto=round(sum(l.estado_de_cuenta_ids.mapped("monto_pagado"),2))
            l.monto_pagado=monto




    @api.model
    def create(self, vals):
        grupo=self.env['grupo.adjudicado'].browse(vals['grupo'])
        obj_secuencia= grupo.secuencia_id

        vals['secuencia'] = obj_secuencia.next_by_code(obj_secuencia.code)
        dia_corte =  self.env['ir.config_parameter'].sudo().get_param('gzl_adjudicacion.dia_corte')
        tasa_administrativa =  self.env['ir.config_parameter'].sudo().get_param('gzl_adjudicacion.tasa_administrativa')

        vals['tasa_administrativa'] = float(tasa_administrativa)
        vals['dia_corte'] = dia_corte

        self.validar_cliente_en_otro_contrato()


        return super(Contrato, self).create(vals)

    @api.onchange('cliente', 'grupo')
    def onchange_provincia(self):
        self.env.cr.execute("""select id from res_country_state where country_id={0}""".format(
            self.env.ref('base.ec').id))
        res = self.env.cr.dictfetchall()
        if res:
            list_res = []
            for l in res:
                list_res.append(l['id'])
            return {'domain': {'provincias': [('id', 'in', list_res)]}}



    def cambio_estado_boton_borrador(self):

        self.detalle_tabla_amortizacion()
        self.write({"state": "activo"})



    def cambio_estado_boton_adendum(self):
        return self.write({"state": "adendum"})

    def cambio_estado_boton_adjudicar(self):
        return self.write({"state": "adjudicar"})


    def cambio_estado_boton_desistir(self):



        # transacciones=self.env['transaccion.grupo.adjudicado']
        # contrato_id=self.env['contrato'].browse(self.id)


        # pago=sum(pagos.mapped("cuota_capital"))+sum(pagos.mapped("cuota_adm"))+sum(pagos.mapped("cuota_adm"))+sum(pagos.mapped("iva_adm"))+sum(pagos.mapped("seguro"))+sum(pagos.mapped("rastreo"))+sum(pagos.mapped("otro"))


        # dct={
        #     'grupo_id':contrato_id.grupo.id,
        #     'debe':pago,
        #     'adjudicado_id':self.cliente.id,
        #     'contrato_id':contrato_id.id,
        #     'state':contrato_id.state


        # }


        # transacciones.create(dct)


        return self.write({"state": "desistir"})


    def cambio_estado_boton_inactivar(self):
        return self.write({"state": "inactivo"})





    def validar_cliente_en_otro_contrato(self, ):
        if self.cliente.id:
            contratos=self.env['contrato'].search([('cliente','=',self.cliente.id)])
            if len(contratos)>0:
                raise ValidationError("El cliente {0} ya está asignado en el contrato {1}".format(self.cliente.name,contratos.secuencia))



    @api.constrains("grupo")
    def validar_cliente_en_grupo(self, ):
        if self.grupo.id:
            obj_cliente_integrante=self.env['integrante.grupo.adjudicado'].search([('adjudicado_id','=',self.cliente.id)])
            obj_cliente_integrante.unlink()

            dctCliente={
            "grupo_id":self.grupo.id,
            "adjudicado_id":self.cliente.id

            }

            obj_cliente_integrante=self.env['integrante.grupo.adjudicado'].create(dctCliente)
            obj_cliente_integrante.agregar_contrato()






####Job que coloca la bandera estado en mora de los contratos se ejecuta cada minuto
    def job_colocar_contratos_en_mora(self, ):

        hoy=date.today()
        contratos=self.env['contrato'].search([('state','in',['adjudicado','activo'])])

        for contrato in contratos:
            mes_estado_cuenta=contrato.tabla_amortizacion.filtered(lambda l: l.fecha.year == hoy.year and l.fecha.month == hoy.month)
            for mes in mes_estado_cuenta:
                if  mes.estado_pago=='pagado':
                    contrato.en_mora=False
                else:
                    contrato.en_mora=True
#Job para registrar calificacion de contratos en mora de acuerdo al job job_colocar_contratos_en_mora se ejecuta el 6 de cada mes

    def job_registrar_calificacion_contratos_en_mora(self, ):

        hoy=date.today()
        contratos=self.env['contrato'].search([('en_mora','=',True)])

        for contrato in contratos:
            obj_calificador=self.env['calificador.cliente']
            motivo=self.env.ref('gzl_adjudicacion.calificacion_2')
            obj_calificador.create({'partner_id': contrato.cliente.id,'motivo':motivo.motivo,'calificacion':motivo.calificacion})


        contratos=self.env['contrato'].search([('en_mora','=',False)])

        for contrato in contratos:

            obj_calificador=self.env['calificador.cliente']
            motivo=self.env.ref('gzl_adjudicacion.calificacion_1')
            obj_calificador.create({'partner_id': contrato.cliente.id,'motivo':motivo.motivo,'calificacion':motivo.calificacion})



###Job que envia correos segun bandera en mora

    def job_enviar_correos_contratos_en_mora(self, ):

        contratos=self.env['contrato'].search([('en_mora','=',True)])

        for contrato in contratos:
                 
            self.envio_correos_plantilla('email_contrato_en_mora',contrato.id)



###  Job para inactivar acorde a cuotas vencidas en el contrato

    def job_para_inactivar_contrato(self, ):

        hoy=date.today()
        dateMonthStart="%s-%s-%s" %(hoy.year, hoy.month,(calendar.monthrange(hoy.year, hoy.month)[1]))

        dateMonthStart=datetime.strptime(dateMonthStart, '%Y-%m-%d').date()

        numeroCuotasMaximo =  int(self.env['ir.config_parameter'].sudo().get_param('gzl_adjudicacion.maximo_cuotas_vencidas'))

        contratos=self.env['contrato'].search([('state','in',['activo'])])

        for contrato in contratos:
                 
            lineas_pendientes=contrato.tabla_amortizacion.filtered(lambda l: l.fecha<dateMonthStart and l.estado_pago=='pendiente')
            if len(lineas_pendientes)>=numeroCuotasMaximo:
                contrato.state='inactivo'







####Jo para enviar correo contrato pago por vencer



    def job_enviar_correos_contratos_pago_por_vencer(self, ):

        hoy=date.today()
        contratos=self.env['contrato'].search([('state','in',['adjudicado','activo'])])

        for contrato in contratos:
            mes_estado_cuenta=contrato.tabla_amortizacion.filtered(lambda l: l.fecha.year == hoy.year and l.fecha.month == hoy.month)
            if len(mes_estado_cuenta)>0:
                self.envio_correos_plantilla('email_contrato_notificacion_de_pago',contrato.id)






    def cambio_estado_congelar_contrato(self):
        #Cambio de estado
        self.state='congelar_contrato'
        #Se obtiene el listado de cuotas pendientes ordenadas de forma ascedente en la fecha de pago.
        tabla=self.env['contrato.estado.cuenta'].search([('estado_pago','=','pendiente'),('contrato_id','=',self.id)],order='fecha asc')

        if len(tabla)>0:
            dct={'contrato_id':self.id,'fecha':tabla[0].fecha}
            self.env['contrato.congelamiento'].create(dct)



    def reactivar_contrato_congelado(self):
        obj_fecha_congelamiento=self.env['contrato.congelamiento'].search([('contrato_id','=',self.id),('pendiente','=',True)],limit=1)

        hoy=date.today()

        fecha_reactivacion="%s-%s-%s" % (hoy.year, hoy.month,(calendar.monthrange(hoy.year, hoy.month)[1]))
        fecha_reactivacion = datetime.strptime(fecha_reactivacion, '%Y-%m-%d').date()
        
      #  raise ValidationError(type(fecha_reactivacion))

        detalle_estado_cuenta_pendiente=self.tabla_amortizacion.filtered(lambda l:  l.fecha>=obj_fecha_congelamiento.fecha  and l.fecha<fecha_reactivacion)
        
        
        nuevo_detalle_estado_cuenta_pendiente=[]
        for detalle in detalle_estado_cuenta_pendiente:
            obj_detalle=detalle.copy()
            nuevo_detalle_estado_cuenta_pendiente.append(obj_detalle.id)
        
        nuevo_detalle_estado_cuenta_pendiente=self.env['contrato.estado.cuenta'].browse(nuevo_detalle_estado_cuenta_pendiente)
        
        
        for detalle in detalle_estado_cuenta_pendiente:

            detalle.cuota_capital=0
            detalle.cuota_adm=0
            detalle.seguro=0
            detalle.rastreo=0
            detalle.otro=0
            detalle.monto_pagado=0
            detalle.saldo=0
            detalle.estado_pago='congelado'

        tabla=self.env['contrato.estado.cuenta'].search([('contrato_id','=',self.id)],order='fecha desc',limit=1)
        
        if len(tabla)==1:

            contador=1
            
            for detalle in nuevo_detalle_estado_cuenta_pendiente:
                detalle.fecha=tabla.fecha +relativedelta(months=contador)
                detalle.numero_cuota= str( int(tabla.numero_cuota) +contador)
                contador+=1

            obj_fecha_congelamiento.pendiente=False

        self.state='activo'



    def envio_correos_plantilla(self, plantilla,id_envio):

        try:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data.get_object_reference('gzl_adjudicacion', plantilla)[1]
        except ValueError:
            template_id = False
#Si existe capturo el template
        if template_id:
            obj_template=self.env['mail.template'].browse(template_id)

            email_id=obj_template.send_mail(id_envio)



    def pagar_cuotas_por_adelantado(self):
        view_id = self.env.ref('gzl_adjudicacion.wizard_adelantar_cuotas_form').id


        return {'type': 'ir.actions.act_window',
                'name': 'Adelantar Pago',
                'res_model': 'wizard.adelantar.cuotas',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': {
                    'default_contrato_id': self.id,
                }
        }


    def modificar_tabla_contrato(self):
        if len(self.actualizacion_ids)>1:
            raise ValidationError("El contrato ya sufrio modificacion con anterioridad")
        view_id = self.env.ref('gzl_adjudicacion.wizard_crear_valores_form').id


        return {'type': 'ir.actions.act_window',
                'name': 'Modificar contrato',
                'res_model': 'actualizacion.contrato.valores',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': {
                    'default_contrato_id': self.id,
                    'default_socio_id': self.cliente.id,
                    'default_monto_financiamiento': self.monto_financiamiento,
                    'default_monto_financiamiento_anterior': self.monto_financiamiento,
                }
        }


    def crear_adendum(self):
        if len(self.adendums_contrato_ids)>1:
            raise ValidationError("El contrato solo puede realizar un adendum")
        elif self.state !='activo':
            raise ValidationError("El contrato solo puede realizar un adendum en estado activo")

        view_id = self.env.ref('gzl_adjudicacion.wizard_crear_adendum_form').id


        return {'type': 'ir.actions.act_window',
                'name': 'Crear Adendum',
                'res_model': 'wizard.contrato.adendum',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': {
                    'default_contrato_id': self.id,
                    'default_socio_id': self.cliente.id,
                    'default_monto_financiamiento': self.monto_financiamiento,
                    'default_plazo_meses': self.plazo_meses.id,
                }
        }



    def obtener_contrato(self):
        for l in self:

            contrato_documento=self.env['sign.request.item'].search([('partner_id','=',l.cliente.id)], limit=1)
            if contrato_documento:
                contrato_documento.ensure_one()
                

                return {
                'name': 'Signed Document',
                'type': 'ir.actions.act_url',
                'url': '/sign/document/%(request_id)s/%(access_token)s' % {'request_id': contrato_documento.sign_request_id.id, 'access_token': contrato_documento.access_token},
                }


    def cesion_derecho(self):


        view_id = self.env.ref('gzl_adjudicacion.wizard_cesion_derecho_form').id

        pagos=self.tabla_amortizacion.filtered(lambda l: l.estado_pago=='pagado')
        pago=sum(pagos.mapped("cuota_capital"))




        return {'type': 'ir.actions.act_window',
                'name': 'Crear Cesión de Derecho',
                'res_model': 'wizard.cesion.derecho',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': {
                    'default_contrato_id': self.id,
                    'default_monto_a_ceder': pago,
                }
        }

    def actualizar_rubros_por_adelantado(self):
        view_id = self.env.ref('gzl_adjudicacion.wizard_actualizar_rubro_form').id


        return {'type': 'ir.actions.act_window',
                'name': 'Actualizar Rubro',
                'res_model': 'wizard.actualizar.rubro',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': {
                    'default_contrato_id': self.id,
                }
        }





    def enviar_correos_contrato(self,):

        obj_rol=self.env['adjudicaciones.team'].search([('active','=',True),('correos','!=',False)]).mapped('correos')
        correos=''
        for correo in obj_rol:
            correos=correos+correo+','

        return correos


#CRUD METHODS

    def write(self, vals):

        crm = super(Contrato, self).write(vals)
        return crm

    
















class ContratoCongelamiento(models.Model):
    _name = 'contrato.congelamiento'
    _description = 'Bitacora de Congelamiento'

    contrato_id = fields.Many2one('contrato')
    fecha = fields.Date(String='Fecha Congelamiento')
    pendiente = fields.Boolean(String='Pendiente de Activación',default=True)






class ContratoEstadoCuenta(models.Model):
    _name = 'contrato.estado.cuenta'
    _description = 'Contrato - Tabla de estado de cuenta de Aporte'
    _rec_name = 'numero_cuota'


    idContrato = fields.Char("ID de Contrato en base")






    contrato_id = fields.Many2one('contrato')
    numero_cuota = fields.Char(String='Número de Cuota')
    fecha = fields.Date(String='Fecha Pago')
    fecha_pagada = fields.Date(String='Fecha Pagada')
    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)


    cuota_capital = fields.Monetary(
        string='Cuota Capital', currency_field='currency_id')
    cuota_adm = fields.Monetary(
        string='Cuota Adm', currency_field='currency_id')

    iva_adm = fields.Monetary(
        string='Iva Adm', currency_field='currency_id')

    factura_id = fields.Many2one('account.move', string='Factura')
    # pago_ids = fields.Many2many('account.payment','contrato_estado_cuenta_payment_rel', 'estado_cuenta_id','payment_id', string='Pagos')
    seguro = fields.Monetary(string='Seguro', currency_field='currency_id')
    rastreo = fields.Monetary(string='Rastreo', currency_field='currency_id')
    otro = fields.Monetary(string='Otro', currency_field='currency_id')
    monto_pagado = fields.Monetary(
        string='Monto Pagado', currency_field='currency_id',compute="calcular_monto_pagado",store=True)
    saldo = fields.Monetary(string='Saldo', currency_field='currency_id' ,compute="calcular_monto_pagado",store=True)
    certificado = fields.Binary(string='Certificado')
    cuotaAdelantada = fields.Boolean(string='Cuota Adelantada')
    estado_pago = fields.Selection([('pendiente', 'Pendiente'),
                                    ('pagado', 'Pagado'),
                                    ('congelado', 'Congelado')
                                    ], string='Estado de Pago', default='pendiente')

    programado=fields.Monetary(string="Cuota Programada", currency_field='currency_id')
    pago_ids = fields.One2many(
        'account.payment', 'pago_id', track_visibility='onchange')
    

    fondo_reserva = fields.Monetary(
        string='Fondo Reserva', currency_field='currency_id')

    iva = fields.Monetary(
        string='Iva ', currency_field='currency_id')
    
    referencia = fields.Char(String='Referencia')

    saldo_cuota_capital = fields.Monetary(
        string='Saldo cuota capital', currency_field='currency_id')
    saldo_cuota_administrativa = fields.Monetary(
        string='Saldo cuota adm ', currency_field='currency_id')
    saldo_fondo_reserva = fields.Monetary(
        string='Saldo fondo de reserva ', currency_field='currency_id')
    
    saldo_iva = fields.Monetary(
        string='Saldo Iva ', currency_field='currency_id')
    
    saldo_programado = fields.Monetary(
        string='Saldo Programado ', currency_field='currency_id')
    
    saldo_seguro = fields.Monetary(
        string='Saldo Seguro ', currency_field='currency_id')
    
    saldo_rastreo = fields.Monetary(
        string='Saldo rastreo ', currency_field='currency_id')
    
    saldo_otros = fields.Monetary(
        string='Saldo Otros ', currency_field='currency_id')
    
    saldo_tabla = fields.Monetary(
        string='Saldo Tabla ', currency_field='currency_id')

    @api.depends("seguro","rastreo","otro","pago_ids")
    def calcular_monto_pagado(self):

        for l in self:
            monto=sum(l.ids_pagos.mapped("valor_asociado"))
            l.monto_pagado=monto

            l.saldo=l.cuota_capital+l.cuota_adm+l.iva_adm + l.seguro+ l.rastreo + l.otro + l.programado - l.monto_pagado




    def pagar_cuota(self):
        view_id = self.env.ref('gzl_adjudicacion.wizard_pago_cuota_amortizaciones_contrato').id

        hoy= date.today()

        pagos_pendientes=self.contrato_id.tabla_amortizacion.filtered(lambda l: l.estado_pago=='pendiente' and l.fecha<self.fecha)
        if len(pagos_pendientes)>0 :
            raise ValidationError('Tengo pagos pendientes a la fecha, por favor realizar los pagos pendientes.')




        return {'type': 'ir.actions.act_window',
                'name': 'Pagar Cuota',
                'res_model': 'wizard.pago.cuota.amortizacion.contrato',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': {
                    'default_tabla_amortizacion_id': self.id,
                    'default_amount': self.saldo,
                    'default_payment_method_id': 2,


                }
        }

class PagoContratoEstadoCuenta(models.Model):
    _inherit = 'account.payment'

    pago_id = fields.Many2one('contrato.estado.cuenta', string="Detalle Estado de Cuenta")
    


    
class ContratoAdendum(models.Model):
    _name = 'contrato.adendum'
    _description = 'Contrato Adendum'


    contrato_id = fields.Many2one('contrato',string="Contrato")
    socio_id = fields.Many2one('res.partner',string="Socio")
    observacion = fields.Char(string='Observacion')
    monto_financiamiento = fields.Monetary(
        string='Monto Financiamiento', currency_field='currency_id', track_visibility='onchange')
    plazo_meses = fields.Many2one('numero.meses',default=lambda self: self.env.ref('gzl_adjudicacion.{0}'.format('numero_meses60')).id ,track_visibility='onchange' )

    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)



class ContratoHistorio(models.Model):
    _name = 'contrato.estado.cuenta.historico.cabecera'
    _description = 'Contrato Historico Tabla de estado de cuenta de Aporte'

    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    contrato_id = fields.Many2one('contrato')
    tabla_amortizacion = fields.One2many(
        'contrato.estado.cuenta.historico.detalle', 'contrato_id', track_visibility='onchange')
    motivo_adendum = fields.Char(String='Motivo Adendum')
    cuota_capital = fields.Monetary(
        string='Cuota Capital', currency_field='currency_id')
    monto_financiamiento = fields.Monetary(
        string='Monto Financiamiento', currency_field='currency_id')
    plazo_meses = fields.Many2one('numero.meses',default=lambda self: self.env.ref('gzl_adjudicacion.{0}'.format('numero_meses60')).id ,track_visibility='onchange' )

    cuota_capital_anterior = fields.Monetary(
        string='Cuota Capital', currency_field='currency_id')
    monto_financiamiento_anterior = fields.Monetary(
        string='Monto Financiamiento', currency_field='currency_id')
    plazo_meses_anterior = fields.Many2one('numero.meses',default=lambda self: self.env.ref('gzl_adjudicacion.{0}'.format('numero_meses60')).id ,track_visibility='onchange' )    
    
class ContratoEstadoCuentaHsitorico(models.Model):
    _name = 'contrato.estado.cuenta.historico.detalle'
    _description = 'Contrato Historico Tabla de estado de cuenta de Aporte'

    contrato_id = fields.Many2one('contrato.estado.cuenta.historico.cabecera')
    numero_cuota = fields.Char(String='Número de Cuota')
    fecha = fields.Date(String='Fecha Pago')
    fecha_pagada = fields.Date(String='Fecha Pagada')
    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    cuota_capital = fields.Monetary(
        string='Cuota Capital', currency_field='currency_id')
    cuota_adm = fields.Monetary(
        string='Cuota Adm', currency_field='currency_id')

    iva_adm = fields.Monetary(
        string='Iva Adm', currency_field='currency_id')

    factura_id = fields.Many2one('account.move', string='Factura')
    # pago_ids = fields.Many2many('account.payment','contrato_estado_cuenta_payment_rel', 'estado_cuenta_id','payment_id', string='Pagos')
    seguro = fields.Monetary(string='Seguro', currency_field='currency_id')
    rastreo = fields.Monetary(string='Rastreo', currency_field='currency_id')
    otro = fields.Monetary(string='Otro', currency_field='currency_id')
    monto_pagado = fields.Monetary(
        string='Monto Pagado', currency_field='currency_id',compute="calcular_monto_pagado",store=True)
    saldo = fields.Monetary(string='Saldo', currency_field='currency_id' ,compute="calcular_monto_pagado",store=True)
    certificado = fields.Binary(string='Certificado')
    cuotaAdelantada = fields.Boolean(string='Cuota Adelantada')
    estado_pago = fields.Selection([('pendiente', 'Pendiente'),
                                    ('pagado', 'Pagado'),
                                    ('congelado', 'Congelado')
                                    ], string='Estado de Pago', default='pendiente')

    pago_ids = fields.One2many(
        'account.payment', 'pago_id', track_visibility='onchange')
    

