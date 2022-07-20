
# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from datetime import date, timedelta,datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import AccessError, UserError, ValidationError
#from . import l10n_ec_check_printing.amount_to_text_es
from . import amount_to_text_es
from datetime import datetime
import calendar
import datetime as tiempo
import itertools
from . import crear_documento_contrato_reserva
import shutil



class ContratoResrva(models.TransientModel):
    _name = "contrato.reserva"
    
    contrato_id = fields.Many2one('contrato',string='Contrato')
    clave =  fields.Char( default="contrato_reserva")
    vehiculo_id = fields.Many2one('entrega.vehiculo',string='entrega.vehiculo')


    def print_report_xls(self):

        if self.clave=='contrato_reserva':
            dct=self.crear_plantilla_contrato_reserva()
            return dct


    def convierte_cifra(self,numero,sw):
        lista_centana = ["",("CIEN","CIENTO"),"DOSCIENTOS","TRESCIENTOS","CUATROCIENTOS","QUINIENTOS","SEISCIENTOS","SETECIENTOS","OCHOCIENTOS","NOVECIENTOS"]
        lista_decena = ["",("DIEZ","ONCE","DOCE","TRECE","CATORCE","QUINCE","DIECISEIS","DIECISIETE","DIECIOCHO","DIECINUEVE"),
                        ("VEINTE","VEINTI"),("TREINTA","TREINTA Y "),("CUARENTA" , "CUARENTA Y "),
                        ("CINCUENTA" , "CINCUENTA Y "),("SESENTA" , "SESENTA Y "),
                        ("SETENTA" , "SETENTA Y "),("OCHENTA" , "OCHENTA Y "),
                        ("NOVENTA" , "NOVENTA Y ")
                    ]
        lista_unidad = ["",("UN" , "UNO"),"DOS","TRES","CUATRO","CINCO","SEIS","SIETE","OCHO","NUEVE"]
        centena = int (numero / 100)
        decena = int((numero -(centena * 100))/10)
        unidad = int(numero - (centena * 100 + decena * 10))
        #print "centena: ",centena, "decena: ",decena,'unidad: ',unidad
     
        texto_centena = ""
        texto_decena = ""
        texto_unidad = ""
     
        #Validad las centenas
        texto_centena = lista_centana[centena]
        if centena == 1:
            if (decena + unidad)!=0:
                texto_centena = texto_centena[1]
            else :
                texto_centena = texto_centena[0]
     
        #Valida las decenas
        texto_decena = lista_decena[decena]
        if decena == 1 :
             texto_decena = texto_decena[unidad]
        elif decena > 1 :
            if unidad != 0 :
                texto_decena = texto_decena[1]
            else:
                texto_decena = texto_decena[0]
        #Validar las unidades
        #print "texto_unidad: ",texto_unidad
        if decena != 1:
            texto_unidad = lista_unidad[unidad]
            if unidad == 1:
                texto_unidad = texto_unidad[sw]
     
        return "%s %s %s" %(texto_centena,texto_decena,texto_unidad)

    def numero_to_letras(self,numero):
        indicador = [("",""),("MIL","MIL"),("MILLON","MILLONES"),("MIL","MIL"),("BILLON","BILLONES")]
        entero = int(numero)
        decimal = int(round((numero - entero)*100))
        #print 'decimal : ',decimal 
        contador = 0
        numero_letras = ""
        while entero >0:
            a = entero % 1000
            if contador == 0:
                en_letras = self.convierte_cifra(a,1).strip()
            else :
                en_letras = self.convierte_cifra(a,0).strip()
            if a==0:
                numero_letras = en_letras+" "+numero_letras
            elif a==1:
                if contador in (1,3):
                    numero_letras = indicador[contador][0]+" "+numero_letras
                else:
                    numero_letras = en_letras+" "+indicador[contador][0]+" "+numero_letras
            else:
                numero_letras = en_letras+" "+indicador[contador][1]+" "+numero_letras
            numero_letras = numero_letras.strip()
            contador = contador + 1
            entero = int(entero / 1000)
        numero_letras = numero_letras+" con " + str(decimal) +"/100"

        return numero_letras

    def crear_plantilla_contrato_reserva(self,):        
        obj_plantilla=self.env['plantillas.dinamicas.informes'].search([('identificador_clave','=','contrato_reserva')],limit=1)
        if self.contrato_id.garante:
            obj_plantilla=self.env['plantillas.dinamicas.informes'].search([('identificador_clave','=','contrato_reserva_garante')],limit=1)
        if obj_plantilla:
            shutil.copy2(obj_plantilla.directorio,obj_plantilla.directorio_out)
            campos=obj_plantilla.campos_ids.filtered(lambda l: len(l.child_ids)==0)
            lista_campos=[]
            estado_cuenta=[]
            mesesDic = {
                "1":'Enero',
                "2":'Febrero',
                "3":'Marzo',
                "4":'Abril',
                "5":'Mayo',
                "6":'Junio',
                "7":'Julio',
                "8":'Agosto',
                "9":'Septiembre',
                "10":'Octubre',
                "11":'Noviembre',
                "12":'Diciembre'
            }
            enteraletras=""
            if self.contrato_id.monto_financiamiento:
                enteraletras=self.numero_to_letras(self.contrato_id.monto_financiamiento)
            lista_campos.append({'identificar_docx':'enteraletras',
                                'valor':enteraletras})
            lista_campos.append({'identificar_docx':'montofinanciamiento',
                                'valor':str(round(self.contrato_id.monto_financiamiento,2))})
            for campo in campos:
                dct={}
                if campo.name == 'vehiculo_id.tipoVehiculo':
                    obj_veh=self.env['entrega.vehiculo'].search([])
                    for l in obj_veh :
                        if l.nombreSocioAdjudicado.id == self.contrato_id.cliente.id: #vehiculo_clase 238
                            fechaasamblea=' '
                            if l.asamblea:
                                year = resultado[0].year
                                mes = resultado[0].month
                                dia = resultado[0].day
                                fechaasamblea = str(dia)+' de '+str(mesesDic[str(mes)])+' del '+str(year)
                            lista_vehiculos=[{'identificar_docx':'vehiculo_tipo',
                                            'valor':l.tipoVehiculo},
                                            {'identificar_docx':'vehiculoclase',
                                            'valor':l.claseVehiculo},
                                            {'identificar_docx':'vehiculomarca',
                                            'valor':l.marcaVehiculo},
                                            {'identificar_docx':'modeloregistsri',
                                            'valor':l.modeloVehiculoSRI},
                                            {'identificar_docx':'modelohomologadoant',
                                            'valor':l.modeloHomologado},
                                            {'identificar_docx':'vehiculoserie',
                                            'valor':l.serieVehiculo},
                                            {'identificar_docx':'vehiculomotor',
                                            'valor':l.motorVehiculo},
                                            {'identificar_docx':'vehiculocolor',
                                            'valor':l.colorVehiculo},
                                            {'identificar_docx':'vehiculoanio',
                                            'valor':l.anioVehiculo},
                                            {'identificar_docx':'vehiculopaisorigen',
                                            'valor':l.paisOrigenVehiculo.name},
                                            {'identificar_docx':'vehiculocombustible',
                                            'valor':l.conbustibleVehiculo},
                                            {'identificar_docx':'vehiculopasajeros',
                                            'valor':str(l.numPasajeros)},
                                            {'identificar_docx':'valorcpn',
                                            'valor':''},
                                            {'identificar_docx':'vehiculotonelaje',
                                            'valor':l.tonelajeVehiculo},
                                            {'identificar_docx':'numeroeje',
                                            'valor':str(l.numEjesVehiculo)},
                                            {'identificar_docx':'plazomeses',
                                            'valor':str(self.contrato_id.plazo_meses.numero)},
                                            {'identificar_docx':'fechaasamblea',
                                            'valor':fechaasamblea}]
  
                            lista_campos+=lista_vehiculos
                else:
                    resultado=self.mapped(campo.name)
                    if campo.name!=False:
                        if len(resultado)>0:
                            if resultado[0]==False:
                                dct['valor']=''
                            else:    
                                dct['valor']=str(resultado[0])
                        else:
                            dct['valor']=''
                    dct['identificar_docx']=campo.identificar_docx
                    lista_campos.append(dct)            
            year = datetime.now().year
            mes = datetime.now().month
            dia = datetime.now().day
            valordia = amount_to_text_es.amount_to_text(dia)
            valordia = valordia.split()
            valordia = valordia[0]
            fechacontr = 'a los '+valordia.lower()+' dias del mes de '+str(mesesDic[str(mes)])+' del Año '+str(year)
            lista_fecha=[{'identificar_docx':'txt_factual','valor':fechacontr}]
            lista_campos+=lista_fecha
            estado_cuenta.append(self.contrato_id.estado_de_cuenta_ids)
            crear_documento_contrato_reserva.crear_documento_reserva(obj_plantilla.directorio_out,lista_campos,estado_cuenta)
            with open(obj_plantilla.directorio_out, "rb") as f:
                data = f.read()
                file=bytes(base64.b64encode(data))
        obj_attch=self.env['ir.attachment'].create({
                                                    'name':'Contrato_Reserva.docx',
                                                    'datas':file,
                                                    'type':'binary', 
                                                    'store_fname':'Contrato_Reserva.docx'
                                                    })

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += "/web/content/%s?download=true" %(obj_attch.id)
        return{
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }