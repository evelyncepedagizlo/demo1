# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError
import calendar
#import numpy_financial as npf

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    is_won = fields.Boolean(related='stage_id.is_won',track_visibility='onchange')
    contacto_name = fields.Char(string='Nombre Completo',track_visibility='onchange')
    contacto_cedula = fields.Char(string='Cédula',track_visibility='onchange')
    contacto_correo = fields.Char(string='Correo Electrónico',track_visibility='onchange')
    contacto_telefono = fields.Char(string='Teléfono',track_visibility='onchange')
    contacto_domicilio = fields.Char(string='Domicilio',track_visibility='onchange')
    tasa_interes = fields.Integer(string='Tasa de Interés',track_visibility='onchange')
    numero_cuotas = fields.Many2one('numero.meses',default=lambda self: self.env.ref('gzl_adjudicacion.{0}'.format('numero_meses60')).id ,track_visibility='onchange' )
    grupo_adjudicado_id = fields.Many2one('grupo.adjudicado', string='Grupo', track_visibility='onchange')

    supervisor = fields.Many2one('res.users',string="Supervisor",track_visibility='onchange' )
    surcursal_id = fields.Many2one('surcursal',string="Surcursal",track_visibility='onchange' )
    fecha_ganada = fields.Date(string='Fecha Ganada',track_visibility='onchange')
    provincia_id= fields.Many2one(
        'res.country.state', string='Provincia', track_visibility='onchange'  )

    ciudad_id = fields.Many2one(
        'res.country.city', string='Ciudad', domain="[('provincia_id','=',provincia_id)]", track_visibility='onchange')

    delegado_id = fields.Many2one('crm.team',string="Delegado",track_visibility='onchange' )
    postventa_id = fields.Many2one('crm.team',string="PostVenta",track_visibility='onchange' )


    valor_inscripcion = fields.Float(string='Valor de inscripción',track_visibility='onchange')

    contrato_id= fields.Many2one('contrato',string="Contrato Asociado",track_visibility='onchange' )




    equipo_asigando = fields.Many2one('crm.team',string="Equipo Asignado",track_visibility='onchange' )

    #campo nuevo
    cerrador = fields.Many2one('res.partner',string="Cerrador")
    porcent_asesor = fields.Float('Porcentaje Asesor')
    factura_requerida = fields.Boolean('Factura Requerida')
    #asesor_premium = fields.Many2one('res.partner',string="Cerrador")




    def action_new_quotation(self):
        action = self.env.ref("sale_crm.sale_action_quotations_new").read()[0]
        action['context'] = {
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.team_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_tag_ids': self.tag_ids.ids,
            'default_user_id': self.user_id.id,



        }
        return action










    
    @api.constrains("stage_id")
    def actualizar_equipo_asignado_por_estado(self, ):
        if self.stage_id.notificar_facturacion:
            self.factura_requerida=True




        if self.stage_id.rol=='comercial':
            self.equipo_asigando=self.team_id

        if self.stage_id.rol=='delegado':
            self.equipo_asigando=self.delegado_id


        if self.stage_id.rol=='postventa':
            self.equipo_asigando=self.postventa_id



        if self.stage_id.crear_factura:
            self.equipo_asigando=self.postventa_id
            impuesto_iva12=self.env['account.tax'].search([('description','=','401')],limit=1)
            hoy=date.today()
            
            journal_id = self.env['account.journal'].search([('type','=','sale')],limit=1)
            product = self.env['product.product'].search([('default_code','=','I01')])

            factura = self.env['account.move'].create({
                        'type': 'out_invoice',
                        'partner_id': self.partner_id.id,
                        'invoice_user_id': self.user_id.id,
                        'team_id': self.team_id.id,
                        'journal_id':journal_id.id,
                
                        'invoice_line_ids': [(0, 0, {
                            'tax_ids':  impuesto_iva12,
                            'product_id':product.id,
                            'quantity': 1,
                            'price_unit': self.valor_inscripcion ,
                            'name': 'Valor de Inscripción',
                        })],
                        'invoice_date':hoy,
                    })
            self.factura_inscripcion_id=factura.id



            self.envio_correos_plantilla('email_financiero_promoauto',factura.id)




    def envio_correos_plantilla(self, plantilla,id_envio):

        try:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data.get_object_reference('gzl_crm', plantilla)[1]
        except ValueError:
            template_id = False
#Si existe capturo el template
        if template_id:
            obj_template=self.env['mail.template'].browse(template_id)

            email_id=obj_template.send_mail(id_envio)











    @api.constrains("stage_id")
    def guardar_fecha_como_ganada(self, ):
        hoy=date.today()

        if self.stage_id.is_won==True:
            hoy=date.today()
            self.fecha_ganada=hoy
           # raise ValidationError(self.user_id.id)
            self.crear_comision_ganada(self.user_id.id)




    def crear_comision_ganada(self,user_id ):

        hoy=date.today()
        comisiones=self.env['comision'].search([('active','=',True)])


 
        fecha_actual="%s-%s-01" % (hoy.year, hoy.month)
        fecha_fin="%s-%s-%s" %(hoy.year, hoy.month,(calendar.monthrange(hoy.year, hoy.month)[1]))

        
        listaComision=[]
        
        #Comision de Asesor
        bono = 0.00
        porcentaje_comision = 0.00
        empleado=self.env['hr.employee'].search([('user_id','=',user_id)])
        monto_ganado= self.factura_inscripcion_id.amount_untaxed
        comision_tabla=self.env['comision'].search([('cargo_id','=',empleado.job_id.id),('valor_min','<=',monto_ganado),('valor_max','>=',monto_ganado)],limit=1)
        
        if len(comision_tabla)>0:
          #  raise ValidationError(str(comision_tabla.comision) + str(comision_tabla.valor_min)+ str(comision_tabla.valor_max))

            monto_comision=(comision_tabla.comision*monto_ganado/100) + comision_tabla.bono
            porcentaje_comision=comision_tabla.comision
            bono =comision_tabla.bono

            listaComision.append({'empleado_id':empleado.id,'nombre':empleado.name,'comision':monto_comision,'cargo':empleado.job_id.id,'tipo_comision':'asesor','porcentaje_comision':porcentaje_comision,'bono':bono})



        tipo_comision=self.env['hr.payslip.input.type'].search([('code','=','COMI')])


        for empleado in listaComision:
            dct={
            'date':  hoy  ,
            'input_type_id': tipo_comision.id   ,
            'employee_id':empleado['empleado_id']  ,
            'amount':empleado['comision']   ,

            }
            comision_input=self.env['hr.input'].create(dct)
            dct2={
                'user_id':  user_id  ,
                'supervisor_id':  self.supervisor.id  ,
                'lead_id':  self.id  ,
                'valor_inscripcion':   self.factura_inscripcion_id.amount_untaxed  ,
                'comision': empleado['comision']   ,
                'cargo':   empleado['cargo']  ,
                'empleado_id':   empleado['empleado_id'],
                'porcentaje_comision':   empleado['porcentaje_comision'],
                'bono':   empleado['bono'] }


            comision_bitacora=self.env['comision.bitacora'].create(dct2)







    @api.onchange("team_id")
    @api.constrains("team_id")
    def guardar_supervisor_actual(self, ):

        self.surcursal_id=self.team_id.surcursal_id.id
        self.provincia_id=self.team_id.surcursal_id.provincia_id.id
        self.ciudad_id=self.team_id.surcursal_id.ciudad_id.id
        self.supervisor=self.team_id.user_id
        self.delegado_id=self.surcursal_id.delegado_id
        self.postventa_id=self.surcursal_id.postventa_id



    dia_pago = fields.Integer(string='Día de Pagos', default=lambda self: self._capturar_dia_pago(),track_visibility='onchange')

    def _capturar_dia_pago(self):
        dia_corte =  self.env['ir.config_parameter'].sudo().get_param('gzl_adjudicacion.dia_corte')
        return dia_corte



    colocar_venta_como_ganada = fields.Boolean( string='Colocar Venta Como Ganada')




    @api.constrains("stage_id")
    def cambio_colocar_venta_como_ganada(self, ):
        self.colocar_venta_como_ganada=self.stage_id.colocar_venta_como_ganada






    tipo_contrato = fields.Many2one('tipo.contrato.adjudicado', string='Tipo de Contrato', required=True)
    tabla_amortizacion = fields.One2many('tabla.amortizacion', 'oportunidad_id' )
    cotizaciones_ids = fields.One2many('sale.order', 'oportunidad_id')
    cuota_capital = fields.Monetary(string='Cuota Capital', currency_field='currency_id')
    iva = fields.Monetary(string='Iva', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.company.currency_id)


    factura_inscripcion_id = fields.Many2one('account.move',string='Factura de inscripción')












    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve team_id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        team_id = self._context.get('default_team_id')

        search_domain = [ ('id', '!=', 0)]

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)






    def modificar_contrato(self):

        usuario_logeado=self.env.user.id
        equipos=self.env['crm.team'].search([])

        team=0
        for equipo in equipos:
            if usuario_logeado in equipo.miembros.ids :
                team=equipo

        rol=team.rol

        if rol != self.stage_id.rol:
            raise ValidationError("Usted no puede editar la oportunidad está asignado al rol {0}".format(self.stage_id.rol))







    @api.constrains("planned_revenue")
    def validar_monto_contrato(self):
        if self.planned_revenue==0:
            raise ValidationError("Ingrese el monto de la oportunidad")





    def detalle_tabla_amortizacion(self):


        self._cr.execute(""" delete from tabla_amortizacion where oportunidad_id={0}""".format(self.id))
        dia_corte = datetime.now()
        try:
            dia_corte = ahora.replace(day = self.dia_pago)
        except:
            raise ValidationError('La fecha no existe, por favor ingrese otro día de pago.')
        
        tasa_administrativa =  self.env['ir.config_parameter'].sudo().get_param('gzl_adjudicacion.tasa_administrativa')



        for rec in self:
            for i in range(0, int(rec.numero_cuotas.numero)):
                cuota_capital = rec.planned_revenue/int(rec.numero_cuotas.numero)
                cuota_adm = rec.planned_revenue *tasa_administrativa / 100 / 12
                iva = cuota_adm * 0.12

                cuota_administrativa_neto= cuota_adm + iva
                saldo = cuota_capital+cuota_adm+iva
                self.env['tabla.amortizacion'].create({
                                                    'numero_cuota':i+1,
                                                    'fecha':rec.fecha_inicio_pago + relativedelta(months=i),
                                                    'cuota_capital':cuota_capital,
                                                    'cuota_adm':cuota_adm,
                                                    'iva_adm':iva,
                                                    'saldo':saldo,
                                                    'oportunidad_id':self.id,                                                    
                                                        })
        vls=[]                                                
        monto_finan_contrato = sum(self.tabla_amortizacion.mapped('cuota_capital'))
        monto_finan_contrato = round(monto_finan_contrato,2)
        #raise ValidationError(str(monto_finan_contrato))
        if  monto_finan_contrato  > self.monto_financiamiento:
            valor_sobrante = monto_finan_contrato - self.monto_financiamiento 
            valor_sobrante = round(valor_sobrante,2)
            parte_decimal, parte_entera = math.modf(valor_sobrante)
            if parte_decimal >=1:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.1
            else:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.01

            obj_contrato=self.env['tabla.amortizacion'].search([('oportunidad_id','=',self.id)] , order ='fecha desc')
            for c in obj_contrato:
                if valor_sobrante != 0.00 or valor_sobrante != 0 or valor_sobrante != 0.0:

                    c.update({
                        'cuota_capital': c.cuota_capital - valor_a_restar,
                        'oportunidad_id':self.id,
                    })
                    vls.append(valor_sobrante)
                    valor_sobrante = valor_sobrante -valor_a_restar
                    valor_sobrante = round(valor_sobrante,2)
                            
                            
        if  monto_finan_contrato  < self.monto_financiamiento:
            valor_sobrante = self.monto_financiamiento  - monto_finan_contrato 
            valor_sobrante = round(valor_sobrante,2)
            parte_decimal, parte_entera = math.modf(valor_sobrante)
            if parte_decimal >=1:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.1
            else:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.01

            obj_contrato=self.env['tabla.amortizacion'].search([('oportunidad_id','=',self.id)] , order ='fecha desc')

            for c in obj_contrato:

                if valor_sobrante != 0.00 or valor_sobrante != 0 or valor_sobrante != 0.0:
                    #raise ValidationError(str(valor_sobrante)+'--'+str(parte_decimal)+'----'+str(valor_a_restar))
                    c.update({
                        'cuota_capital': c.cuota_capital + valor_a_restar,
                        'oportunidad_id':self.id,
                    })  
                    vls.append(valor_sobrante)
                    valor_sobrante = valor_sobrante -valor_a_restar
                    valor_sobrante = round(valor_sobrante,2)
        self.cuota_capital = cuota_capital
        self.iva =  iva  


    def write(self, vals):
     #   if self.fecha_ganada and not(vals.get('date_action_last',False)):
       #     raise ValidationError("No se puede editar en estado ganado")
        if vals.get('stage_id',False) and self.stage_id.restringir_movimiento:
            estados_habilitados=[]
            estados_habilitados.append(self.stage_id.stage_anterior_id.id)
            estados_habilitados.append(self.stage_id.stage_siguiente_id.id)

            if not (vals['stage_id'] in estados_habilitados):
                raise ValidationError("No se puede cambiar a ese estado.")

            if self.stage_id.modificacion_solo_equipo:
                self.modificar_contrato()

        crm = super(CrmLead, self).write(vals)

        if  vals.get('stage_id',False):
            stage_id = self.env['crm.stage'].browse(vals['stage_id'])
            if stage_id.crear_contrato:
                contrato = self.env['contrato'].create({
                                            'cliente':self.partner_id.id,
                                            'dia_corte':self.dia_pago,
                                            'monto_financiamiento':self.planned_revenue,
                                            'tipo_de_contrato':self.tipo_contrato.id,
                                            'provincias':self.partner_id.state_id.id,
                                            'plazo_meses':self.numero_cuotas.id,
                                            'cuota_capital':self.cuota_capital,
                                            'iva_administrativo':self.iva,
                                            'factura_inscripcion':self.factura_inscripcion_id.id,
                                            'grupo':self.grupo_adjudicado_id.id,
                                        })
                self.contrato_id=contrato.id

            if stage_id.is_won:
                if not (self.factura_inscripcion_id ):
                    raise ValidationError("Ingrese la factura de inscripción")
                
                if not (self.factura_inscripcion_id.amount_residual==0 ):
                    raise ValidationError("Se debe ingresar la factura como Factura de inscripción y La factura debe registrarse como pagada.")

                obj_partner=self.partner_id
                obj_partner.tipo='preAdjudicado'


            if stage_id.crear_reunion_en_calendar:
                now=datetime.now()
                calendar=self.crear_calendar_event('Reunión Socio {0}'.format(self.partner_id.name),now,1,'Reunión para evidenciar Calidad de la Venta')
        
            stage_cotizacion = self.env['crm.stage'].search([('generar_cotizacion','=',True)], limit=1).id
            if self.stage_id != stage_cotizacion and self.quotation_count==0 and self.sale_order_count ==0:
                raise ValidationError("Para pasar a la siguiente etapa, debe crear mínimo una cotización")
        




        return crm


    def crear_calendar_event(self,name,fecha,duracion,descripcion):


        stop= fecha + timedelta(hours=duracion)

        
        self.env.cr.execute("insert into calendar_event (name,start_datetime,duration,start,stop,description,allday,active) values('{0}','{1}',{2},'{3}','{4}','{5}',{6},{7})".format(name,fecha,duracion,fecha,stop,descripcion,False,True))
        
        self.env.cr.execute("""select id from calendar_event order by id desc limit 1""")
        calendar = self.env.cr.dictfetchall()
        if len(calendar)>0:
            obj=self.env['calendar.event'].browse(calendar[0]['id'])
            obj.partner_ids=self.env['res.users'].browse(self._uid).partner_id








    def crear_contrato(self):
        plantillas = self.env['sign.template'].search([('attachment_id.tipo_plantilla','=','adjudicacion')])
        for l in plantillas:
            def create_request(self, send=True, without_mail=False):
                template_id = l.id
                signers = [{'partner_id': self.partner_id.id, 'role': False}]
                followers = []
                reference = l.attachment_id.name
                subject = 'Contrato'
                message = 'Contrato'
                return self.env['sign.request'].initialize_new(l.id, signers, followers, reference, subject, message, send, without_mail)
            a=create_request(self)
            sign_request=self.env['sign.request'].search([('id','=',a['id'])])
            def sign_directly_without_mail(self):
                #res = create_request(False, True)
                request = self.env['sign.request'].browse(sign_request.id)
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
                        'token_list': [item.access_token for item in request.request_item_ids[1:]],
                        'current_signor_name': user_item.partner_id.name,
                        'name_list': [item.partner_id.name for item in request.request_item_ids[1:]],
                    },
                }
            
            def send_completed_document(self):
                self.ensure_one()
                self.contacto_cedula = "entra a send_completed_document"
                if len(sign_request.request_item_ids) <= 0 or self.state != 'signed':
                    self.contacto_correo = 'linea 107'
                    return False
                    

                if not sign_request.completed_document:
                    sign_request.generate_completed_document()

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                attachment = self.env['ir.attachment'].create({
                    'name': "%s.pdf" % sign_request.reference if sign_request.reference.split('.')[-1] != 'pdf' else sign_request.reference,
                    'datas': sign_request.completed_document,
                    'type': 'binary',
                    'res_model': sign_request._name,
                    'res_id': sign_request.id,
                })
                self.contacto_name= attachment
                report_action = self.env.ref('sign.action_sign_request_print_logs')
                # print the report with the public user in a sudoed env
                # public user because we don't want groups to pollute the result
                # (e.g. if the current user has the group Sign Manager,
                # some private information will be sent to *all* signers)
                # sudoed env because we have checked access higher up the stack
                public_user = self.env.ref('base.public_user', raise_if_not_found=False)
                if not public_user:
                    # public user was deleted, fallback to avoid crash (info may leak)
                    public_user = self.env.user
                pdf_content, __ = report_action.with_user(public_user).sudo().render_qweb_pdf(self.id)
                attachment_log = self.env['ir.attachment'].create({
                    'name': "Activity Logs - %s.pdf" % time.strftime('%Y-%m-%d - %H:%M:%S'),
                    'datas': base64.b64encode(pdf_content),
                    'type': 'binary',
                    'res_model': sign_request._name,
                    'res_id': sign_request.id,
                })
                tpl = self.env.ref('sign.sign_template_mail_completed')
                for signer in sign_request.request_item_ids:
                    if not signer.signer_email:
                        continue
                    signer_lang = get_lang(self.env, lang_code=signer.partner_id.lang).code
                    tpl = tpl.with_context(lang=signer_lang)
                    body = tpl.render({
                        'record': self,
                        'link': url_join(base_url, 'sign/document/%s/%s' % (sign_request.id, signer.access_token)),
                        'subject': '%s signed' % self.reference,
                        'body': False,
                    }, engine='ir.qweb', minimal_qcontext=True)
                return True




class TablaAmortizacion(models.Model):
    _name = 'tabla.amortizacion'
    _description = 'Tabla de Amortización'

    oportunidad_id = fields.Many2one('crm.lead')
    numero_cuota = fields.Char(String='Número de Cuota')
    fecha = fields.Date(String='Fecha Pago')
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    cuota_capital = fields.Monetary(string='Cuota Capital', currency_field='currency_id')
    cuota_adm = fields.Monetary(string='Cuota Adm', currency_field='currency_id')
    iva = fields.Monetary(string='Iva', currency_field='currency_id')
    seguro = fields.Monetary(string='Seguro', currency_field='currency_id')
    saldo = fields.Monetary(string='Saldo', currency_field='currency_id')
    rastreo = fields.Monetary(string='Rastreo', currency_field='currency_id')
    otro = fields.Monetary(string='Otro', currency_field='currency_id')
    estado_pago = fields.Selection([('pendiente', 'Pendiente'), 
                                      ('pagado', 'Pagado')
                                    ],string='Estado de Pago', default='pendiente') 
    factura_id = fields.Many2one('account.move')
    pago_id = fields.Many2one('account.payment')
    
    def pagar_cuota(self):
        view_id = self.env.ref('gzl_crm.wizard_pago_cuota_amortizaciones').id
        return {'type': 'ir.actions.act_window',
                'name': 'Validar Pago',
                'res_model': 'wizard.pago.cuota.amortizacion',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': {
                    'default_tabla_amortizacion_id': self.id,
                }
        }
            
        
    def accion_planificada_crear_factura_borrador(self):
        fecha_actual= date.today()
        pagos_pendientes = self.env['tabla.amortizacion'].search([('estado_pago','=','pendiente')])
        if pagos_pendientes:
            for l in pagos_pendientes:
                fecha_borrador = l.fecha + timedelta(days=-5)
                if fecha_actual >= fecha_borrador and not l.factura_id:
                    factura = self.env['account.move'].create({
                                'type': 'out_invoice',
                                'partner_id': l.oportunidad_id.partner_id.id,
                                'invoice_line_ids': [(0, 0, {
                                    'quantity': 1,
                                    'price_unit': l.cuota,
                                    'name': l.oportunidad_id.name+' - Cuota '+l.numero_cuota,
                                })],
                            })
                    l.factura_id=factura

                    pago = self.env['account.payment'].create({
                            'payment_date': l.fecha,
                            'communication': l.oportunidad_id.name+' - Cuota '+l.numero_cuota,
                            'invoice_ids': [(6, 0, [factura.id])],
                            'payment_type': 'inbound',
                            'amount': l.cuota,
                            'partner_id': l.oportunidad_id.partner_id.id,
                            'partner_type': 'customer',
                            'payment_method_id': self.env['account.payment.method'].search([('payment_type', '=', 'inbound')], limit=1).id,
                            'journal_id': self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1).id
                            })
                    l.pago_id = pago
    
    


    def enviar_correos_contrato(self,):


        rolCredito=self.env.ref('gzl_adjudicacion.tipo_rol3').correos
        rolGerenciaAdmin=self.env.ref('gzl_adjudicacion.tipo_rol1').correos
        rolGerenciaFin=self.env.ref('gzl_adjudicacion.tipo_rol4').correos
        rolAdjudicacion=self.env.ref('gzl_adjudicacion.tipo_rol2').correos

        

        correos=rolCredito+','+rolGerenciaAdmin+','+rolGerenciaFin+','+rolAdjudicacion

        return correos















class SaleOrder(models.Model):
    _inherit = 'sale.order'

    oportunidad_id = fields.Many2one('crm.lead')
    
    
class WizardPagoCuotaAmortizacion(models.TransientModel):
    _name = 'wizard.pago.cuota.amortizacion'
    
    tabla_amortizacion_id = fields.Many2one('tabla.amortizacion')
    payment_date = fields.Date(required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', required=True, string='Diario', domain=[('type', 'in', ('bank', 'cash'))])
    payment_method_id = fields.Many2one('account.payment.method', string='Método de Pago', required=True)
    
    @api.onchange('journal_id')
    def onchange_payment_method(self):
        if self.journal_id:
            self.env.cr.execute("""select inbound_payment_method from account_journal_inbound_payment_method_rel where journal_id={0}""".format(self.journal_id.id))
            res = self.env.cr.dictfetchall()
            if res:
                list_method=[]
                for l in res:
                    list_method.append(l['inbound_payment_method'])
                return {'domain': {'payment_method_id': [('id', 'in', list_method)]}}

    
    def validar_pago(self):
        factura = self.tabla_amortizacion_id.factura_id
        pago = self.tabla_amortizacion_id.pago_id
        if factura:
            factura.write({
                'journal_id':self.journal_id,
                'invoice_date':self.payment_date,
            })
            
            pago.write({
                'journal_id':self.journal_id,
                'invoice_id':factura,
                'payment_date':self.payment_date,
                'payment_method_id':self.payment_method_id,
                'communication':factura.name
            })
            
        else:
            factura = self.env['account.move'].create({
                        'type': 'out_invoice',
                        'partner_id': self.tabla_amortizacion_id.oportunidad_id.partner_id.id,
                        'invoice_line_ids': [(0, 0, {
                            'quantity': 1,
                            'price_unit': self.tabla_amortizacion_id.cuota,
                            'name': self.tabla_amortizacion_id.oportunidad_id.name+' - Cuota '+self.tabla_amortizacion_id.numero_cuota,
                        })],
                        'journal_id':self.journal_id,
                        'invoice_date':self.payment_date,
                    })
            self.tabla_amortizacion_id.factura_id=factura

            pago = self.env['account.payment'].create({
                    'payment_date': self.payment_date,
                    'communication': l.oportunidad_id.name+' - Cuota '+l.numero_cuota,
                    'invoice_ids': [(6, 0, [factura.id])],
                    'payment_type': 'inbound',
                    'amount': l.cuota,
                    'partner_id': l.oportunidad_id.partner_id.id,
                    'partner_type': 'customer',
                    'payment_method_id': self.payment_method_id,
                    'journal_id': self.journal_id,
                    'invoice_id':factura,
                    'communication':factura.name
                    })
            self.tabla_amortizacion_id.pago_id = pago
            
        factura.action_post()
        pago.post()
        self.tabla_amortizacion_id.estado_pago='pagado'