# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from datetime import date, timedelta,datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import AccessError, UserError, ValidationError
from .funciones import *
import calendar
import datetime as tiempo
import itertools




class ImportarArchivo(models.TransientModel):
    _name = "importar.archivo.cuentas"

    diario  = fields.Char(string="Diario")
    cuenta_origin  = fields.Char(string="Cta. Origen")
    cuenta_destino  = fields.Char(string="Cta. Destino" )
    active  = fields.Boolean(string="Active",default=True )



    def cambio_cuentas(self):



        cuentas_contables=self.env['importar.archivo.cuentas'].search([('active','=',True)])

        for rec in cuentas_contables:


            code_origin=rec.cuenta_origin.split(' ')[0]
            code_dest=rec.cuenta_destino.split(' ')[0]
     
            account_move_line= """select 
                                    aml.id,aml.name 
                                    from 
                                        account_move_line aml, 
                                        account_account aa,    
                                        account_move am    

                                    where 
                                        am.id=aml.move_id and
                                        aml.account_id=aa.id and 
                                        aa.code='{1}' and
                                        am.name ilike '%{0}%'
                                        
                                        
                                        
                                        """.format(rec.diario ,code_origin)



            self.env.cr.execute(account_move_line)

            cuentas=self.env.cr.dictfetchall()
            #raise ValidationError(str(cuentas))
            
            for linea in cuentas:
                account=self.env['account.account'].search([('code','=',code_dest)])
                obj=self.env['account.move.line'].browse(linea['id'])
                obj.account_id=account.id
            rec.active=False