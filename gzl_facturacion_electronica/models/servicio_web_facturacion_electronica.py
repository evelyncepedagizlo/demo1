import zeep
from zeep import Client
from lxml import etree
import requests
from zeep.transports import Transport


def validarFactura(url,codigo_factura):
	result={}

	transport = Transport(timeout=30)

	client = Client(url,transport=transport)




	return result
