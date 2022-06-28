# -*-  coding: utf-8 -*-
from odoo import api, models,_, fields
from odoo.exceptions import ValidationError, UserError
from io import BytesIO
import xlsxwriter
import base64
import itertools
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

class bankStatementReport(models.TransientModel):
    _name = 'bank.statement.report'
    _description = _('Report Bank Statement')
    _rec_name = 'journal_id'
    _inherit = "reporte.proveedor.cliente"


    extracto_saldo= fields.Many2one('account.bank.statement', string="Extracto")


    journal_id = fields.Many2one('account.journal', string="Diario", domain="[('type','=','bank')]")
    date = fields.Date(string="Corte",default=fields.Date.context_today)
    fecha_inicio = fields.Date(string="Desde")
    fecha_fin = fields.Date(string="Hasta")
    date_reporte = fields.Char(string="Corte")
    saldo_cuenta = fields.Float(string="Saldo Segun Estado de cuenta")
    saldo_libros = fields.Float(string="Saldo Contable")
    total_conciliado = fields.Float(string="Total Conciliado")
    total_no_conciliado = fields.Float(string="Total no conciliado")

    diferencia = fields.Float(string="Diferencia")
    diferencia_libros = fields.Float(string="Diferencia Libros")
    diferencia_total = fields.Float(string="Diferencia total")
    diferencia_no_conciliada = fields.Float(string="Diferencia No conciliada")
    subtotal_cheques_no_cobrados = fields.Float(string="Subtotal Cheques")
    subtotal_depositos_no_cobrados = fields.Float(string="Subtotal depositos")
    subtotal_debitos_no_cobrados = fields.Float(string="Subtotal debitos")
    subtotal_creditos_no_cobrados = fields.Float(string="Subtotal creditos")


    subtotal_cheques_no_cobrados_no_cont = fields.Float(string="Subtotal Cheques No Contabilizado")
    subtotal_depositos_no_cobrados_no_cont = fields.Float(string="Subtotal depositos No Contabilizado")
    subtotal_debitos_no_cobrados_no_cont = fields.Float(string="Subtotal debitos No Contabilizado")
    subtotal_creditos_no_cobrados_no_cont = fields.Float(string="Subtotal creditos No Contabilizado")

    month = fields.Selection([('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'), ('4', 'Abril'),
                          ('5', 'Mayo'), ('6', 'Junio'), ('7', 'Julio'), ('8', 'Agosto'), 
                          ('9', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'), ], 
                         string='Mes')
    
    def capturar_anio(self):
        dct={

        '1':'Enero',
        '2':'Febrero',
        '3':'Marzo',
        '4':'Abril',
        '5':'Mayo',
        '6':'Junio',
        '7':'Julio',
        '8':'Agosto',
        '9':'Septiembre',
        '10':'Octubre',
        '11':'Noviembre',
        '12':'Diciembre'

        }
        return dct[self.month]






    @api.model
    def year_selection(self):
        year = 2000 # replace 2000 with your a start year
        year_list = []
        today = date.today()
        actual_year= today.year
        while year != actual_year: # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        
        return year_list

    # year_date = fields.Selection(
       # year_selection,
        #string="Year",
         # as a default value it would be 2019)
    year_date = fields.Selection([
                        ('2020','2020'),
                        ('2021','2021'),
                        ('2022','2022'),
                        ('2023','2023'),
                        ('2024','2024'),
                        ('2025','2025'),
                        ('2026','2026'),
                        ('2027','2027'),
                        ('2028','2028'),
                        ('2029','2029'),
                        ('2030','2030'),
                        ('2031','2031'),
                        ('2032','2032'),
                        ('2033','2033'),
                        ('2034','2034'),
                        ('2035','2035'),
                        ('2036','2036'),
                        ('2037','2037'),
                        ('2038','2038'),
                        ('2039','2039'),
                        ('2040','2040'),
                        ('2041','2041'),
                        ('2042','2042'),
                        ('2043','2043'),
                        ('2044','2044'),
                        ('2045','2045'),
                        ('2046','2046'),
                        ('2047','2047'),
                        ('2048','2048'),
                        ('2049','2049'),
                        ('2050','2050'),


                        ],string="Año",default="2022")
    def print_report(self):
        self.saldo_cuenta_calculo()


        return self.env.ref('gzl_reporte_financiero.bank_statement_report').report_action(self)


    @api.onchange("extracto_saldo")
    def onchange_saldo_estado_cuenta_contable(self):
        if self.extracto_saldo.id:

            self.saldo_cuenta=self.extracto_saldo.balance_end_real



    @api.onchange("year_date","month")
    def onchange_dates(self):
        if self.year_date and self.month:
            dateMonthStart = "%s-%s-01" % (self.year_date, self.month)
            dateMonthStart = datetime.strptime(dateMonthStart,'%Y-%m-%d')
            dateMonthEnd=dateMonthStart+relativedelta(months=1, day=1, days=-1)
            self.date_reporte = str(dateMonthStart)+'-'+str(dateMonthEnd)
            self.fecha_inicio = dateMonthStart.strftime("%Y-%m-%d")
            self.fecha_fin = dateMonthEnd.strftime("%Y-%m-%d")


            obj_statement=self.env['account.bank.statement'].search([('date','>=',self.fecha_inicio),('date','<=',self.fecha_fin),('journal_id','=',self.journal_id.id)],order="date desc",limit=1)
            

            if len(obj_statement)>0:
                self.saldo_cuenta=obj_statement.balance_end_real
            else:
                self.saldo_cuenta=0

    def saldo_cuenta_calculo(self):

        self.subtotal_depositos_no_cobrados=round(self.body_report('deposito',True),2)
        self.subtotal_debitos_no_cobrados=round(self.body_report('debito',True),2)
        self.subtotal_cheques_no_cobrados=round(self.body_report('cheque',True),2)
        self.subtotal_creditos_no_cobrados=round(self.body_report('credito',True),2)

        self.subtotal_cheques_no_cobrados_no_cont = round(self.body_report('cheque',True,False),2)
        self.subtotal_depositos_no_cobrados_no_cont = round(self.body_report('deposito',True,False),2)
        self.subtotal_debitos_no_cobrados_no_cont = round(self.body_report('debito',True,False),2)
        self.subtotal_creditos_no_cobrados_no_cont = round(self.body_report('credito',True,False),2)


        
        self.diferencia= round(self.saldo_cuenta + self.subtotal_depositos_no_cobrados + self.subtotal_creditos_no_cobrados - self.subtotal_cheques_no_cobrados - self.subtotal_debitos_no_cobrados,2)
 
        self.saldo_libros=self.obtener_saldo_inicial_cuenta_bancaria(self.fecha_fin)

        self.diferencia_libros= round(self.saldo_libros + self.subtotal_depositos_no_cobrados_no_cont + self.subtotal_creditos_no_cobrados_no_cont - self.subtotal_cheques_no_cobrados_no_cont - self.subtotal_debitos_no_cobrados_no_cont,2)
        self.diferencia_total=round(self.saldo_cuenta - self.saldo_libros,2)

        self.diferencia_no_conciliada= self.diferencia_total + (self.subtotal_depositos_no_cobrados + self.subtotal_creditos_no_cobrados - self.subtotal_cheques_no_cobrados - self.subtotal_debitos_no_cobrados) #+ (self.subtotal_depositos_no_cobrados_no_cont + self.subtotal_creditos_no_cobrados_no_cont - self.subtotal_cheques_no_cobrados_no_cont - self.subtotal_debitos_no_cobrados_no_cont)




    def body_report(self, ref=False,valores=False,contabilizado=True):

        if contabilizado:
            state_deposito=state_debito=state_credito='posted'
            state_cheque='registered'
        else:
            state_deposito=state_debito=state_credito='draft'
            state_cheque='draft'

        #finicio mes ffinmes 
        dateMonthStart = "%s-%s-01" % (self.year_date, self.month)
        dateMonthStart = datetime.strptime(dateMonthStart,'%Y-%m-%d')
        dateMonthEnd=dateMonthStart+relativedelta(months=1, day=1, days=-1)
        self.date_reporte = str(dateMonthStart)+'-'+str(dateMonthEnd)
        dateMonthStart = dateMonthStart.strftime("%Y-%m-%d")
        dateMonthEnd = dateMonthEnd.strftime("%Y-%m-%d")
        
        #Depositos No registrados en estado de cuenta
        if ref=='deposito':

            filtro=[('journal_id','=',self.journal_id.id),('payment_date','<=',dateMonthEnd),('es_nota_credito','=',False),('payment_type','=','inbound'),('state','=',state_deposito),('check_number','=',False)]

            depositos=self.env['account.payment'].search(filtro)
            if not valores:
                lista_obj=[]
                for deposito in depositos:
                    dct={}
                    dct['numero_documento']=deposito.name or '-'
                    dct['fecha_emision']=deposito.payment_date or '-'
                    dct['referencia']=deposito.communication or '-'
                    dct['empresa']=deposito.partner_id.name 

                    dct['monto']=deposito.amount 

                    obj=self.env['reporte.conciliacion.bancaria.detalle'].create(dct)

                    lista_obj.append(obj)


        #Cheques Girados y no cobrados (Cheques ingresados en el sistema pero que no ha aparecen en el estado de cuenta del banco)


        if ref=='cheque':
            filtro=[]
            if self.journal_id.id:
                filtro=[('journal_id','=',self.journal_id.id),('cheque_date','<=',dateMonthEnd),('status','=',state_cheque)]
    #######filtro de cheques
            cheques=self.env['account.cheque'].search(filtro)
            
            lista_cheques=[]

            for cheque in cheques:
                dct={}
                dct['numero_cheque']=cheque.cheque_number
                dct['banco']=cheque.journal_id.bank_id.name
                dct['monto']=cheque.amount
                dct['fecha_cheque']=cheque.cheque_date
                dct['empresa']=cheque.payee_user_id.name
                dct['terceros']=cheque.third_party_name

                paymments=self.env['account.payment'].search([('payment_method_id.code','=','check_printing'),('check_number','=',cheque.cheque_number)],limit=1)
                dct['numero_documento_pago']=paymments.name or '-'
                dct['fecha_pago']=paymments.date_to or '-'
                dct['descripcion']=paymments.communication or '-'

                if paymments.id and  paymments.state=='reconciled':
                    dct['conciliado']='Si'
                else:
                    dct['conciliado']='No'

                lista_cheques.append(dct)

            lista_cheques = filter(lambda x: x['conciliado']=='No', lista_cheques)
            lista_obj=[]
            if not valores:

                for cheque in lista_cheques:
                    dct={
                    'numero_documento':cheque['numero_cheque'],
                    'fecha_emision':cheque['fecha_cheque'],
                    'empresa':cheque['empresa'],
                    'referencia':cheque['descripcion'],
                    'monto':cheque['monto'],
                    }
                    obj=self.env['reporte.conciliacion.bancaria.detalle'].create(dct)

                    lista_obj.append(obj)


        #Notas de Debito  No registrados en estado de cuenta
        if ref=='debito':

            filtro=[('journal_id','=',self.journal_id.id),('payment_date','<=',dateMonthEnd),('payment_type','in',['outbound','transfer']),('state','=',state_deposito),('check_number','=',False)]

            debitos=self.env['account.payment'].search(filtro)
            lista_obj=[]

            if not valores:
                for debito in debitos:
                    dct={}
                    dct['numero_documento']=debito.name or '-'
                    dct['fecha_emision']=debito.payment_date or '-'
                    dct['referencia']=debito.communication or '-'
                    dct['empresa']=debito.partner_id.name 

                    dct['monto']=debito.amount 

                    obj=self.env['reporte.conciliacion.bancaria.detalle'].create(dct)

                    lista_obj.append(obj)




        #Notas de Credito  No registrados en estado de cuenta
        if ref=='credito' :

            filtro=[('journal_id','=',self.journal_id.id),('es_nota_credito','=',True),('payment_date','<=',dateMonthEnd),('payment_type','in',['inbound']),('state','=',state_credito),('check_number','=',False)]

            creditos=self.env['account.payment'].search(filtro)
            lista_obj=[]
            if not valores:     
                for credito in creditos:
                    dct={}
                    dct['numero_documento']=credito.name or '-'
                    dct['fecha_emision']=credito.payment_date or '-'
                    dct['referencia']=credito.communication or '-'
                    dct['empresa']=credito.partner_id.name 

                    dct['monto']=credito.amount 

                    obj=self.env['reporte.conciliacion.bancaria.detalle'].create(dct)

                    lista_obj.append(obj)


        if valores:
            if ref=='deposito':
                return float(sum(depositos.mapped('amount')))
            if ref=='debito':
                return float(sum(debitos.mapped('amount')))
            if ref=='cheque':
                return float(sum(map(lambda x: x['monto'],lista_cheques)))
            if ref=='credito':
                return float(sum(creditos.mapped('amount')))
        else:
            return lista_obj



    @api.model
    def _get_bank_rec_report_data(self, options, journal):
        # General data + setup
        rslt = {}

        accounts = journal.default_debit_account_id + journal.default_credit_account_id
        company = journal.company_id
        amount_field = 'balance' if (not journal.currency_id or journal.currency_id == journal.company_id.currency_id) else 'amount_currency'
        states = ['posted']
        states += options.get('all_entries') and ['draft'] or []
        #fechas
        #finicio mes ffinmes  self.env.context['date']
        
        dates = "%s-%s-01" % (self.env.context['year_date'], self.env.context['month'])
        dateMonthStart = self.fecha_inicio
        dateMonthEnd=self.fecha_fin



        # Get total already accounted.
        self._cr.execute('''
            SELECT SUM(aml.''' + amount_field + ''')
            FROM account_move_line aml
            LEFT JOIN account_move am ON aml.move_id = am.id
            WHERE aml.date >= %s AND aml.date <= %s AND aml.company_id = %s AND aml.account_id IN %s
            AND am.state in %s
        ''', [dateMonthStart,dateMonthEnd, journal.company_id.id, tuple(accounts.ids), tuple(states)])
        rslt['total_already_accounted'] = self._cr.fetchone()[0] or 0.0

        # Payments not reconciled with a bank statement line
        self._cr.execute('''
            SELECT
                aml.id,
                aml.name,
                aml.ref,
                aml.date,
                aml.''' + amount_field + '''                    AS balance
            FROM account_move_line aml
            LEFT JOIN res_company company                       ON company.id = aml.company_id
            LEFT JOIN account_account account                   ON account.id = aml.account_id
            LEFT JOIN account_account_type account_type         ON account_type.id = account.user_type_id
            LEFT JOIN account_bank_statement_line st_line       ON st_line.id = aml.statement_line_id
            LEFT JOIN account_payment payment                   ON payment.id = aml.payment_id
            LEFT JOIN account_journal journal                   ON journal.id = aml.journal_id
            LEFT JOIN account_move move                         ON move.id = aml.move_id
            WHERE aml.date >= %s and aml.date <= %s
            AND aml.company_id = %s
            AND CASE WHEN journal.type NOT IN ('cash', 'bank')
                     THEN payment.journal_id
                     ELSE aml.journal_id
                 END = %s
            AND account_type.type = 'liquidity'
            AND full_reconcile_id IS NULL
            AND (aml.statement_line_id IS NULL OR st_line.date > %s OR st_line.date < %s)
            AND (company.account_bank_reconciliation_start IS NULL OR aml.date >= company.account_bank_reconciliation_start)
            AND move.state in %s
            ORDER BY aml.date DESC, aml.id DESC
        ''', [dateMonthStart,dateMonthEnd, journal.company_id.id, journal.id, dateMonthStart,dateMonthEnd, tuple(states)])
        rslt['not_reconciled_payments'] = self._cr.dictfetchall()

        # Bank statement lines not reconciled with a payment
        rslt['not_reconciled_st_positive'] = self.env['account.bank.statement.line'].search([
            ('statement_id.journal_id', '=', journal.id),
            ('date', '>=', dateMonthStart),
            ('date', '<=', dateMonthEnd),
            ('journal_entry_ids', '=', False),
            ('amount', '>', 0),
            ('company_id', '=', company.id)
        ])

        rslt['not_reconciled_st_negative'] = self.env['account.bank.statement.line'].search([
            ('statement_id.journal_id', '=', journal.id),
            ('date', '>=', dateMonthStart),
            ('date', '<=', dateMonthEnd),
            ('journal_entry_ids', '=', False),
            ('amount', '<', 0),
            ('company_id', '=', company.id)
        ])

        # Final
        last_statement = self.env['account.bank.statement'].search([
            ('journal_id', '=', journal.id),
            ('date', '>=', dateMonthStart),
            ('date', '<=', dateMonthEnd),
            ('company_id', '=', company.id)
        ], order="date desc, id desc", limit=1)
        rslt['last_st_balance'] = last_statement.balance_end
        rslt['last_st_end_date'] = last_statement.date

        return rslt









    def print_report_xls(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        name = 'Reporte de Conciliacion Bancaria {0}'.format(self.journal_id.name)
        self.xslx_body(workbook, name)
        

        workbook.close()
        file_data.seek(0)
        

        
        attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(file_data.getvalue()),
            'name': name,
            'store_fname': name,
            'type': 'binary',
        })
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += "/web/content/%s?download=true" %(attachment.id)
        return{
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }






        
    def xslx_body(self, workbook, name):
        bold = workbook.add_format({'bold':True,'border':1})
        bold_no_border = workbook.add_format({'bold':True})
        bold.set_center_across()
        format_title = workbook.add_format({'bold':True,'border':1})
        format_title_left = workbook.add_format({'bold':True,'border':1,'align': 'left'})
        format_title_left_14 = workbook.add_format({'bold':True,'border':1,'align': 'left','size': 14})
        format_title_center_14 = workbook.add_format({'bold':True,'border':1,'align': 'center','size': 14})


        format_title.set_center_across()
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00','border':1,'text_wrap': True })
        currency_format.set_align('vcenter')

        
        date_format = workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'right','border':1,'text_wrap': True })
        date_format.set_align('vcenter')
        date_format_day = workbook.add_format({'align': 'right','border':1,'text_wrap': True })
        date_format_day.set_align('vcenter')
        date_format_title = workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'left','text_wrap': True})
        date_format_title.set_align('vcenter')

        body = workbook.add_format({'align': 'center' , 'border':0,'text_wrap': True})
        body.set_align('vcenter')
        body_right = workbook.add_format({'align': 'right', 'border':1 })
        body_left = workbook.add_format({'align': 'left','bold':True})
        format_title2 = workbook.add_format({'align': 'center', 'bold':True,'border':1 })
        sheet = workbook.add_worksheet(name)

        sheet.set_portrait()
        sheet.set_paper(9)  # A4

        sheet.set_margins(left=0.4, right=0.4, top=0.4, bottom=0.2)
        sheet.set_print_scale(100)
        sheet.fit_to_pages(1,2)

        self.saldo_cuenta_calculo()

        
        sheet.insert_image('A1', "any_name.png",
                           {'image_data':  BytesIO(base64.b64decode( self.env.company.logo)), 'x_scale': 0.5, 'y_scale': 0.5,'x_scale': 0.5,
                            'y_scale':     0.5, 'align': 'center'})
        sheet.set_column('A:A', 23)
        sheet.set_column('B:B', 23)
        sheet.set_column('C:C', 23)
        sheet.set_column('D:D', 23)
        sheet.set_column('E:E', 23)
        sheet.merge_range('A4:E4', self.env.company.name.upper(), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A5:E5', self.env.company.street, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A6:E6', self.env.company.city, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A7:G7', self.env.company.country_id.name, workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        valor = self.saldo_cuenta - self.saldo_libros
        sheet.merge_range('A8:E8', 'CONCILIACIÓN BANCARIA', workbook.add_format({'bold':True,'border':0,'align': 'center','size': 14}))
        bold.set_bg_color('b8cce4')
        #finicio mes ffinmes
        dateMonthStart = "%s-%s-01" % (self.year_date, self.month)
        dateMonthStart = datetime.strptime('2021-10-01','%Y-%m-%d')
        dateMonthEnd=dateMonthStart+relativedelta(months=1, day=1, days=-1)
        self.date_reporte = str(dateMonthStart)+'-'+str(dateMonthEnd)



        sheet.merge_range('A9:G9','Periodo: {0} {1}'.format(self.year_date,self.capturar_anio()), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A10:G10', 'Cuenta: {0} {1}'.format(self.journal_id.name,self.journal_id.bank_account_id.acc_number), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A11:G11', 'Saldo Estado de Cuenta Inicial: '+str(self.saldo_cuenta), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A12:G12', 'Saldo Según Libros: '+str(self.saldo_libros), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A13:G13','Diferencia: '+str(round(valor,2)), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A14:G14', 'Cheques No Cobrados: '+str(self.subtotal_cheques_no_cobrados) , workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A15:G15', 'Notas Debito no incluidad: '+str(self.subtotal_debitos_no_cobrados), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A16:G16', 'Depositos No incluidos: '+str(self.subtotal_depositos_no_cobrados), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A17:G17', 'Creditos no incluidos: '+str(self.subtotal_creditos_no_cobrados), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A18:G18', 'Notas Debito (No Contabilizadas): '+str(self.subtotal_debitos_no_cobrados_no_cont), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A19:G19', 'Cheques no Contabilizados: '+str(self.subtotal_cheques_no_cobrados_no_cont), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A20:G20', 'Notas Credito (No Contabilizados): '+str(self.subtotal_creditos_no_cobrados_no_cont), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A21:G21', 'Depositos No Contabilizado: '+str(self.subtotal_depositos_no_cobrados_no_cont), workbook.add_format({'bold':True,'border':0,'align': 'left'}))
        sheet.merge_range('A22:G22','Diferencia No Conciliada: '+str(round(self.diferencia_no_conciliada,2)), workbook.add_format({'bold':True,'border':0,'align': 'left'}))


        format_saldo = workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'})
        
        sheet.merge_range('C23:D23', 'SALDO SEGUN ESTADO DE CUENTA: ', format_saldo)
        
        sheet.write('E23', self.saldo_cuenta, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))
        #secciones
        listado_depositos= self.body_report('deposito')
        fila=25
        sheet.write('A24:E24', '(+) Depositos No Incluidos', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        
        sheet.write('A25', 'Nro. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #74a8cf'}))
        sheet.write('B25', 'Fec. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #74a8cf'}))
        sheet.write('C25', 'Empresa', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #74a8cf'}))
        sheet.write('D25', 'Descripcion', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #74a8cf'}))
        sheet.write('E25', 'Monto', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #74a8cf'}))
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00'})
        for ld in listado_depositos:
            if ld:
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                sheet.write(fila,0, ld.numero_documento or "", body)
                sheet.write(fila,1, ld.fecha_emision or "", body)
                sheet.write(fila,2, ld.empresa or "", body)
                sheet.write(fila,3, ld.referencia or "", body)
                sheet.write(fila,4, ld.monto or "", currency_format)
        fila +=1
        sheet.write(fila,3, 'SubTotal  (+) Depositos No Incluidos: ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.subtotal_depositos_no_cobrados, workbook.add_format({'bold':True,'top':1,'align': 'left','num_format': '[$$-409]#,##0.00'}))
        #seccion2
        listado_creditos= self.body_report('credito')
        fila +=2
        sheet.write('A'+str(fila)+':E'+str(fila), '(+) Creditos No Incluidos', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        fila +=1
        sheet.write('A'+str(fila), 'Nro. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('B'+str(fila), 'Fec. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('C'+str(fila), 'Empresa', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('D'+str(fila), 'Descripcion', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('E'+str(fila), 'Monto', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00'})
        
        for ld in listado_creditos:
            if ld:
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                sheet.write(fila,0, ld.numero_documento or "", body)
                sheet.write(fila,1, ld.fecha_emision or "", body)
                sheet.write(fila,2, ld.empresa or "", body)
                sheet.write(fila,3, ld.referencia or "", body)
                sheet.write(fila,4, ld.monto or "", currency_format)
        fila +=1
        sheet.write(fila,3, 'SubTotal  (+) Creditos No Incluidos: ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.subtotal_creditos_no_cobrados, workbook.add_format({'bold':True,'top':1,'align': 'left','num_format': '[$$-409]#,##0.00'}))
        #seccion 3
        listado_cheque= self.body_report('cheque')
        fila +=2
        sheet.write('A'+str(fila)+':E'+str(fila), '(-) Chq Girados y No Cobrados', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        fila +=1
        sheet.write('A'+str(fila), 'Nro. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('B'+str(fila), 'Fec. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('C'+str(fila), 'Empresa', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('D'+str(fila), 'Descripcion', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('E'+str(fila), 'Monto', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00'})
        for ld in listado_cheque:
            if ld:
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                sheet.write(fila,0, ld.numero_documento or "", body)
                sheet.write(fila,1, ld.fecha_emision or "", body)
                sheet.write(fila,2, ld.empresa or "", body)
                sheet.write(fila,3, ld.referencia or "", body)
                sheet.write(fila,4, ld.monto or "", currency_format)
        fila +=1
        sheet.write(fila,3, 'SubTotal  (-) Chq Girados y No Cobrados: ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.subtotal_cheques_no_cobrados, workbook.add_format({'bold':True,'top':1,'align': 'left','num_format': '[$$-409]#,##0.00'}))
        #seccion5
        listado_dbn= self.body_report('debito')
        fila +=2
        sheet.write('A'+str(fila)+':E'+str(fila), '(-) Debitos No Incluidos', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        fila +=1
        sheet.write('A'+str(fila), 'Nro. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('B'+str(fila), 'Fec. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('C'+str(fila), 'Empresa', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('D'+str(fila), 'Descripcion', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('E'+str(fila), 'Monto', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00'})
        
        for ld in listado_dbn:
            
            if ld:
                fila+=1
                sheet.write(fila,0, ld.numero_documento or "", body)
                sheet.write(fila,1, ld.fecha_emision or "", body)
                sheet.write(fila,2, ld.empresa or "", body)
                sheet.write(fila,3, ld.referencia or "", body)
                sheet.write(fila,4, ld.monto or "", currency_format)
        fila +=1
        sheet.write(fila,3, 'SubTotal  (-) Debitos No Incluidos ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.subtotal_debitos_no_cobrados, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))
        fila +=1
        sheet.write(fila,3, 'SALDO ESTADO CUENTA', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.diferencia, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))
        fila +=1
        sheet.write(fila,3, 'SALDO CONTABLE ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.saldo_libros, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))
        #seccion6
        listado_depo= self.body_report('deposito',False,False)
        fila +=2
        sheet.write('A'+str(fila)+':E'+str(fila), '(+) Depositos No Contabilizados', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        fila +=1
        sheet.write('A'+str(fila), 'Nro. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('B'+str(fila), 'Fec. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('C'+str(fila), 'Empresa', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('D'+str(fila), 'Descripcion', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('E'+str(fila), 'Monto', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00'})
        
        for ld in listado_depo:
            if ld:
                fila+=1
                sheet.write(fila,0, ld.numero_documento or "", body)
                sheet.write(fila,1, ld.fecha_emision or "", body)
                sheet.write(fila,2, ld.empresa or "", body)
                sheet.write(fila,3, ld.referencia or "", body)
                sheet.write(fila,4, ld.monto or "", currency_format)
        fila +=1
        sheet.write(fila,3, 'SubTotal  (+) Depositos No Contabilizados ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.subtotal_depositos_no_cobrados_no_cont, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))
       #seccion7
        listado_creditosnc= self.body_report('credito',False,False)
        fila +=2
        sheet.write('A'+str(fila)+':E'+str(fila), '(+) Creditos No Contabilizados', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        fila +=1
        sheet.write('A'+str(fila), 'Nro. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('B'+str(fila), 'Fec. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('C'+str(fila), 'Empresa', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('D'+str(fila), 'Descripcion', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('E'+str(fila), 'Monto', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00'})
        
        for ld in listado_creditosnc:
            if ld:
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                sheet.write(fila,0, ld.numero_documento or "", body)
                sheet.write(fila,1, ld.fecha_emision or "", body)
                sheet.write(fila,2, ld.empresa or "", body)
                sheet.write(fila,3, ld.referencia or "", body)
                sheet.write(fila,4, ld.monto or "", currency_format)
        fila +=1
        sheet.write(fila,3, 'SubTotal  (+) Creditos No Contabilizados ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.subtotal_creditos_no_cobrados_no_cont, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))
        #seccion8
        listado_cheqnc= self.body_report('cheque',False,False)
        fila +=2
        sheet.write('A'+str(fila)+':E'+str(fila), '(-) Chq Girados y  No Contabilizados', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        fila +=1
        sheet.write('A'+str(fila), 'Nro. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('B'+str(fila), 'Fec. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('C'+str(fila), 'Empresa', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('D'+str(fila), 'Descripcion', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('E'+str(fila), 'Monto', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00'})
        
        for ld in listado_cheqnc:
            if ld:
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                sheet.write(fila,0, ld.numero_documento or "", body)
                sheet.write(fila,1, ld.fecha_emision or "", body)
                sheet.write(fila,2, ld.empresa or "", body)
                sheet.write(fila,3, ld.referencia or "", body)
                sheet.write(fila,4, ld.monto or "", currency_format)
        fila +=1
        sheet.write(fila,3, 'SubTotal  (-) Chq Girados y  No Contabilizados ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.subtotal_cheques_no_cobrados_no_cont, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))
       #seccion9
        listado_debnoc= self.body_report('debito',False,False)
        fila +=2
        sheet.write('A'+str(fila)+':E'+str(fila), '(-) Debitos No Contabilizados', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        fila +=1
        sheet.write('A'+str(fila), 'Nro. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('B'+str(fila), 'Fec. Deposito', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('C'+str(fila), 'Empresa', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('D'+str(fila), 'Descripcion', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        sheet.write('E'+str(fila), 'Monto', workbook.add_format({'bold':True,'border':0,'align': 'center','font_color':' #427db7'}))
        currency_format = workbook.add_format({'num_format': '[$$-409]#,##0.00'})
        
        for ld in listado_debnoc:
            if ld:
                fila+=1
                line = itertools.count(start=fila)
                fila_current=0
                sheet.write(fila,0, ld.numero_documento or "", body)
                sheet.write(fila,1, ld.fecha_emision or "", body)
                sheet.write(fila,2, ld.empresa or "", body)
                sheet.write(fila,3, ld.referencia or "", body)
                sheet.write(fila,4, ld.monto or "", currency_format)
        fila +=1
        sheet.write(fila,3, 'SubTotal (-) Debitos No Contabilizados ', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.subtotal_debitos_no_cobrados_no_cont, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))

        fila +=1
        sheet.write(fila,3, 'TOTAL', workbook.add_format({'bold':True,'top':1,'align': 'left','font_color':'#bdaf53'}))
        sheet.write(fila,4, self.diferencia_libros, workbook.add_format({'bold':True,'top':1,'align': 'center','num_format': '[$$-409]#,##0.00'}))


    def obtener_saldo_inicial_cuenta_bancaria(self,fecha_fin):
            
        filtro=""" where fecha<'{0}' """.format(fecha_fin)

        saldo=self.env['reporte.estado.cuenta.bancario'].obtener_saldo_inicial(filtro,self.journal_id.id)
        return saldo






















class ReporteAnticipoDetalle(models.TransientModel):
    _name = "reporte.conciliacion.bancaria.detalle"

    numero_documento = fields.Char('Nro. Documento')
    fecha_emision = fields.Date('Fc. Emision')
    empresa = fields.Char('Empresa')
    referencia = fields.Char('Referencia')
    monto = fields.Float('Monto ')
    observaciones = fields.Char('Observaciones')
    reglon = fields.Char('Reglon')

