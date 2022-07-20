# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
import re
import os
import datetime, unicodedata,base64


def elimina_tildes(s):
    if s:
        return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
    else:
        return ''



def validar_letras(campo):
	if campo != False:
		propiet2 = campo.replace(' ','')
		if propiet2.isalpha() == False:
			return True
		else:
			return False


def validar_numero(campo):

	if campo != False:
		if campo.isdigit() == False:
			return True
		else:
			return False
			

def validate_ip(name):
    ip = name
    res = True
    
    if (ip != False):
        addr = ip.split('/')
        if len(addr) == 2:
            validate_ipv4_cdr(addr[0])
            if  int(addr[0].split('.')[3])==0 :
                if  not(int(addr[1])>0 and  int(addr[1])<=32):
                    raise ValidationError(('Verifique su direccion de ip de red %s  ') %addr[1])
            else:
                raise ValidationError(('La Direccion de IP de Red %s es invalida') %ip)

        else:
            dato=0
            if len (addr[0].split('.'))==4 :
                dato = int(addr[0].split('.')[0])
                if dato!=0:
                    if int(addr[0].split('.')[3])==0:
                        raise ValidationError(('Debe Ingresar una  Direccion IP %s ') %ip)
                    validate_ipv4_cdr(ip)
                else:
                   raise ValidationError(('La direccion IP %s es invalida.') % ip)


    else:
        raise ValidationError(('Ingrese direccion IP'))


def validate_ipv4_cdr(ip):


    array_ip = ip.split(".")
    for i in array_ip:
        if len(i.strip()) != len(i):
            raise ValidationError(('La direccion IP %s contiene espacios en blanco.') % ip)
    res = validate_ipv4(ip)
    if res == False:
        raise ValidationError(('La direccion IP %s es invalida.') % ip)




def validate_ipv4(ip):
    res = True
    array_ip = ip.split(".")
    if(len(array_ip)!=4):
        res = False
    else:
        for i in array_ip:
            if not i.isdigit():
                return False
            if int(i)>=256:
                return False
    return res

def is_valid_ipv6(ip):
    """Validates IPv6 addresses.
    """
    pattern = re.compile(r"""
        ^
        \s*                         # Leading whitespace
        (?!.*::.*::)                # Only a single whildcard allowed
        (?:(?!:)|:(?=:))            # Colon iff it would be part of a wildcard
        (?:                         # Repeat 6 times:
            [0-9a-f]{0,4}           #   A group of at most four hexadecimal digits
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
        ){6}                        #
        (?:                         # Either
            [0-9a-f]{0,4}           #   Another group
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
            [0-9a-f]{0,4}           #   Last group
            (?: (?<=::)             #   Colon iff preceeded by exacly one colon
             |  (?<!:)              #
             |  (?<=:) (?<!::) :    #
             )                      # OR
         |                          #   A v4 address with NO leading zeros 
            (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            (?: \.
                (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            ){3}
        )
        \s*                         # Trailing whitespace
        $
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL)
    return pattern.match(ip) is not None


def do_ping(ip):
    response = os.system("ping -c 1 " + ip)
    if response == 0:
        #print &quot;HOST CONECTADO&quot;
        return True
    else:
        #print &quot;HOST NO CONECTADO&quot;
        return False