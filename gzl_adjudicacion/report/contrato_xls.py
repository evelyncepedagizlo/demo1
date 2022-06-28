# -*- coding: utf-8 -*-

from odoo import models



class ContratoXls(models.AbstractModel):
    _name = 'report.gzl_adjudicacion.report_contrato_id_card_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, contrato):
        for obj in contrato:
            report_name = obj.name
            # One sheet by partner
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'bold': True})
            sheet.write(0, 0, obj.name, bold)