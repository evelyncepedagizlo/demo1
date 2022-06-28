from dateutil.relativedelta import relativedelta
from itertools import count, groupby
import tempfile
from functools import lru_cache, partial
import xlsxwriter
from odoo import fields, models, api
from datetime import *
from io import BytesIO
import base64

class ReportDebtsDue (models.TransientModel):
    _name = 'report.debts.due'
    _description = 'Reporte Deudas Vencidas'

    date_at = fields.Date(string='Fecha de Vencimiento', required=True)
    partner_id = fields.Many2one('res.partner', 'Empresa', domain="[('customer_rank', '!=', 0)]")
    supplier_id = fields.Many2one('res.partner', 'Empresa', domain="[('supplier_rank', '!=', 0)]" )
    type = fields.Selection([
        ('receivable', 'Cuenta por cobrar'),
        ('payable', 'Cuenta por pagar'),
    ], default='receivable', required=True, string="Tipo")

    @staticmethod
    def _generate_worksheet():
        """
        Generate worksheet return
        file name, worksheet, function for close worksheet
         concat(am.name, '-', aml.ref) as reference,"""
        file_name = 'Reporte_deuda_vencida_{}.xlsx'.format(fields.Datetime.now().timestamp())
        workbook = xlsxwriter.Workbook(tempfile.gettempdir() + "/" + file_name)
        return workbook, file_name


    def _write_value_col(self, worksheet, periods, row, date_due, residual, format):
        """Generate the columns depends of period"""
        if date_due:
            now = date.today()
            diff_days = (date_due-now)
            diff_days = diff_days.days
            write = lambda index: worksheet.write(row, index, residual, format)
            for index, period in enumerate(periods, 7):
                if diff_days < period.day_to and \
                        (period.day_from and diff_days > period.day_from or True):
                    return write(index)
            return write(index)

    def wirte_title(self, row, worksheet, periods, format_title):
        """write title"""
        worksheet.write(row, 1, ("Empresa"), format_title)
        worksheet.write(row, 2, ("Documento"), format_title)
        worksheet.write(row, 3, ("Nro. Documento"), format_title)
        worksheet.write(row, 4, ("Fecha Vencimiento"), format_title)
        worksheet.write(row, 5, ("Diario"), format_title)
        worksheet.write(row, 6, ("Cuenta"), format_title)
        for i, period in enumerate(periods, 7):
            worksheet.write(row, i, period.name, format_title)
        

    def _get_dataset(self):
        self.env.cr.execute(""" 
            select
                rp.display_name as partner,
                aml.date_maturity  as date_maturity,
                am.invoice_date as invoice_date,
                am.name as name_invoice,
                am.l10n_latam_document_number as document_number,
                concat(aj."name", ' ') journal,
                concat(aa.code ,' ', aa.name) account,
                case 
                when aml.debit!=0 and am.id is null then aml.debit
                when  am.type='out_refund' then am.amount_residual*(-1)
                when  am.amount_residual!=0 then am.amount_residual
                when ap.selected_inv_total>0 then ap.amount
                else COALESCE(ap.amount*(-1),0) end as residual,
                aml.debit
            from account_move_line aml
            join account_move am on am.id=aml.move_id
            join res_partner rp on rp.id=aml.partner_id
            left join account_payment ap on ap.id=aml.payment_id 
            join account_journal  aj on aj.id=aml.journal_id 
            join account_account  aa on aa.id = aml.account_id 
            where  
                aml.reconciled is false and aml.balance <> 0
                and aa.reconcile is true
                and am.state='posted'
                and aml.date_maturity>='{date}'
                and (aa.internal_type ='{internal_type}')
                {partner}
            group by 1,2,3,4,5,6,7,8,9,rp.name
            order by rp.name, am.l10n_latam_document_number, COALESCE(aml.date_maturity)
        """.format(**self._get_params()))
        dataset = self.env.cr.dictfetchall()
        periods = self.env['periods.debts.due'].search(
            [], order='day_to asc'
        )
        return groupby(dataset, lambda x: x['partner']), periods

    def _get_params(self):
        prt = lambda x, arg1: x and "and {arg1}={id}".format(arg1=arg1, id=x.id) or ''
        return {
            "date":self.date_at,
            "internal_type": self.type,
            "partner": prt(self.partner_id or self.supplier_id, "aml.partner_id")
        }
        

    @staticmethod
    def _get_formats(workbook):
        add = workbook.add_format
        return {
            'currency_format': add({'num_format': '[$$-409]#,##0.00'}),
            'date_format': add({'num_format': 'dd/mm/yy', 'align': 'left'}),
            'format_title': add({'bold': True}),
            'head': add({'bold': True, 'font_size': 30})
        }

    def write_head(self, worksheet, format):
        """Create head for report"""
        worksheet.write(0, 0, 'Reporte Deudas Vencidas',format)
        worksheet.write(1, 0, self.env.user.company_id.display_name)
        worksheet.write(2, 0,fields.Datetime.to_string(self.date_at))

    @staticmethod
    def _set_partner_data_row(worksheet, row, doc, date_format, formats):
        worksheet.write(row, 1, doc['partner'])
        worksheet.write(row, 2, doc['name_invoice'])
        worksheet.write(row, 3, doc['document_number'])
        worksheet.write(row, 4, doc['date_maturity'], date_format)
        worksheet.write(row, 5, doc['journal'])
        worksheet.write(row, 6, doc['account'])
        
        worksheet.set_column('A:A', 4)
        worksheet.set_column('B:B', 45)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 21)
        worksheet.set_column('G:G', 25)
        worksheet.set_column('H:H', 11)
        worksheet.set_column('I:I', 11)
        worksheet.set_column('J:J', 11)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 11)
        worksheet.set_column('M:M', 12)


    @staticmethod
    def footer_for_partner(worksheet, row, name, col, total, frmt):
        worksheet.write(row, 0, ('Total '))
        worksheet.write(row, 1, name)
        worksheet.write(row, col, total, frmt)

    def write_line_for_document(self, worksheet, periods, formats, doc, row):
        self._set_partner_data_row(worksheet, row, doc, formats['date_format'], formats['currency_format'])
        self._write_value_col(
            worksheet, periods, row,
            doc['date_maturity'], doc['debit'], formats['currency_format']
        )
        return doc['debit']

    def write_data(self, workbook):
        """ write a data to the worksheet"""
        worksheet = workbook.add_worksheet('FR')
        dataset, periods = self._get_dataset()
        count_row = count(5)
        formats = self._get_formats(workbook)
        self.write_head(worksheet, formats['head'])
        self.wirte_title(next(count_row), worksheet, periods, formats['format_title'])
        write_row = partial(self.write_line_for_document, worksheet, periods, formats)
        for partner, docs in dataset:
            total_for_partner = sum([
                write_row(doc, next(count_row))
                    for doc in docs
            ])
            self.footer_for_partner(
                worksheet, next(count_row), partner, len(periods.ids) + 7,
                total_for_partner, formats['currency_format']
            )

    def action_print(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        self.write_data(workbook)
        workbook.close()
        file_data.seek(0)
        
        name = 'Reporte Deudas Vencidas'
        
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