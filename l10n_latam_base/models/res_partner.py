# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, tools,  _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime,timedelta,date
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type',
        string="Identification Type", index=True, auto_join=True,
        default=lambda self: self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False),
        help="The type of identification")
    vat = fields.Char(string='Identification Number', help="Identification Number for selected type")

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ['l10n_latam_identification_type_id']

    @api.constrains('vat', 'l10n_latam_identification_type_id')
    def check_vat(self):
        with_vat = self.filtered(lambda x: x.l10n_latam_identification_type_id.is_vat)
        return super(ResPartner, with_vat).check_vat()

    @api.onchange('country_id')
    def _onchange_country(self):
        country = self.country_id or self.company_id.country_id or self.env.company.country_id
        self.l10n_latam_identification_type_id = self.env['l10n_latam.identification.type'].search(
            [('country_id', '=', country.id), ('is_vat', '=', True)], limit=1) or self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False)


    val_iden=fields.Boolean(string='Valida identificación',default=True)

    def valida_identificacionci(self,idnt,sigla):
        numero_provincias = int(self.env['ir.config_parameter'].get_param('numero_provincias'))

        #Provincia
        result = re.sub(r"[0-9]", "", idnt, flags=re.I)  

        if len(result)>0:
            raise ValidationError('No se permiten Caractéres') 




        cp = int(idnt[0:2])
        if not (cp >= 1 and cp <= numero_provincias): # verificar codigo de provincia

            raise ValidationError('Código de provincia incorrecto') 





        val = 1
        if str(sigla).lstrip().rstrip().upper() =='C':

            mlti = 2 
            acmu = 0
            cont = 1 
            for i in str(idnt):
                if cont >= 10 : 
                    break
                if mlti ==  3 : 
                    mlti = 1
                mult =  int(i) * mlti
                if mult >= 10 : 
                    mult = mult - 9
                acmu += mult 
                cont += 1
                mlti += 1
            digito = int(str(int(str(acmu)[0:1]) + 1)+'0') - acmu
            if int(str(idnt)[9:10]) != digito:
                val = 1
            else:
                val = 2
            if digito == 10:
                if int(str(idnt)[9:10]) != 0 :
                    val = 1
                else:
                    val = 2



        elif str(sigla).lstrip().rstrip().upper() == 'R':
            
            #PERSONA NATURAL 3ER DIGITO <= 6



            nn = int(idnt[2:3])
            val = 2
            if nn < 6:
                mlti = 2 ; acmu = 0 ; cont = 1  
                for i in str(idnt):
                    if cont >= 10 : break
                    if mlti ==  3 : mlti = 1
                    mult =  int(i) * mlti
                    if mult >= 10 : mult = mult - 9
                    acmu += mult ; cont += 1 ; mlti += 1
                digito = int(str(int(str(acmu)[0:1]) + 1)+'0') - acmu
                if int(str(idnt)[9:10]) != digito:
                    val = 1
                else:
                    val = 2
                if digito == 10:
                    if int(str(idnt)[9:10]) != 0 :
                        val = 1
                    else:
                        val = 2
            elif nn == 9:
                ind = 0 ; acmu = 0 ; cont = 0
                lst=[4,3,2,7,6,5,4,3,2]
                for i in str(idnt):
                    if cont >= 9 : 
                        break
                    mult =  int(i) * lst[ind]
                    acmu += mult
                    ind += 1
                    cont += 1
                if int(acmu % 11) > 0:
                    digito = 11 - int(acmu % 11)
                else:
                    digito = int(acmu % 11) 
                if int(str(idnt)[9:10]) != digito:
                    val = 1
                else:
                    val = 2
                    
            elif nn == 6:
                ind = 0 ; acmu = 0 ; cont = 0
                lst=[3,2,7,6,5,4,3,2]
                for i in str(idnt):
                    if cont >= 8 : 
                        break
                    mult =  int(i) * lst[ind]
                    acmu += mult
                    ind += 1
                    cont += 1
                if int(acmu % 11) > 0:
                    digito = 11 - int(acmu % 11)
                else:
                    digito = int(acmu % 11)
                if int(str(idnt)[8:9]) != digito:
                    val = 1
                else:
                    val = 2

            else:
                raise ValidationError('Tercer digito invalido') 


        else:
            val = 1            
        return val
                    


    @api.constrains("vat")
    def validar_digitos_vat(self,):
        for obj in self:
            if obj.active == True and obj.val_iden == True:
                if  obj.l10n_latam_identification_type_id.sigla != False: 
                    if len(obj.vat) == 10 and obj.l10n_latam_identification_type_id.sigla == 'C':
                        res = self.valida_identificacionci(obj.vat, obj.l10n_latam_identification_type_id.sigla)
                        if res == 1:
                            raise ValidationError('ERROR!, Cedula ingresada incorrecta.')
                        else:
                            return True                
                    elif len(obj.vat) == 13 and obj.l10n_latam_identification_type_id.sigla == 'R' :
                        res = self.valida_identificacionci(obj.vat, obj.l10n_latam_identification_type_id.sigla)
                        if res == 1:
                            raise ValidationError('ERROR!, RUC ingresado incorrecto.')
                        else:
                            return True
                    else:
                        raise ValidationError("ERROR!, Numero de identificación incorrecto.")                