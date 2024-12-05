from odoo.exceptions import ValidationError
from odoo import fields, models
from datetime import datetime, timedelta
import json

from odoo.tools import date_range


class AccountMove(models.Model):
    _inherit = 'account.move'

    def default_vat_status(self):
        """This method is used for get vat status and set that status as a default in every invoice"""
        default_vat_status = self.env['procountor.vat.status'].search([('procountor_vat_description', '=', 'Domestic')],
                                                                      limit=1)
        return default_vat_status

    procountor_instance_id = fields.Many2one(
        comodel_name='procountor.instance',
        string='Procountor Instance', copy=False
    )
    export_invoice_to_procountor = fields.Boolean(string='Invoice Export', copy=False,
                                                  help="If this boolean field is mark then consider as a exported to procountor")
    procountor_invoice_id = fields.Char(string='Procountor Invoice ID', copy=False)
    procountor_bank_reference_code_type = fields.Selection(
        [('RF', 'RF'), ('FI', 'FI'), ('OCR', 'OCR'), ('KID', 'KID'), ('GIK01', 'GIK01'), ('GIK04', 'GIK04'),
         ('GIK15', 'GIK15'),
         ('FIK71', 'FIK71'), ('FIK73', 'FIK73'), ('FIK75', 'FIK75')], copy=False, default="FI",
        help="Reference code generation type.")
    procountor_clearing_code = fields.Char(string="Clearing Code", copy=False,
                                           help="Receiver bank's clearing code for foreign payments.")
    procountor_accounting_by_row = fields.Boolean(string="Accounting By Row", copy=False, default=False,
                                                  help="Indicates if accounting by row is used (true) or not (false). Accounting by row means that a separate ledger transaction is created for each invoice row.")
    procountor_unit_prices_include_vat = fields.Boolean(string="Unit Prices Include Vat", copy=False, default=False,
                                                        help="Indicates if the unit prices on invoice rows include VAT (true) or not (false).")
    procountor_vat_status_id = fields.Many2one(comodel_name='procountor.vat.status', string="Vat Status", copy=False,
                                               default=default_vat_status)
    procountor_delivery_method = fields.Selection(
        [('MAILING', 'MAILING'), ('ONLINE', 'ONLINE'), ('COURIER', 'COURIER'), ('VRCARGO', 'VRCARGO'), ('BUS', 'BUS'),
         ('FREIGHT', 'FREIGHT'), ('RETRIEVABLE', 'RETRIEVABLE'), ('OTHER', 'OTHER')], copy="False", default="MAILING", )
    procountor_invoice_channel = fields.Selection(
        [('EMAIL', 'EMAIL'), ('MAIL', 'MAIL'), ('ELECTRONIC_INVOICE', 'ELECTRONIC_INVOICE'),
         ('NO_SENDING', 'NO_SENDING')], copy=False, default="EMAIL")

    def prepare_invoice_line_data(self, invoice_id):
        invoice_lines = []
        units = {'mm': 'MILLIMETER', 'g': 'GRAM', 'cm': 'CM', 'in': 'INCH', 'oz': 'OUNCE', 'Hours': 'HOUR',
                 'ft': 'FOOT', 'lb': 'POUND', 'yd': 'YARD', 'Days': 'DAY', 'm': 'METER', 'm²': 'SQUARE_METER',
                 'L': 'LITER', 'kg': 'KILOGRAM', 'Dozens': 'DOZEN', 'km': 'KILOMETER', 'm³': 'CUBIC_METER',
                 'mi': 'MILE'}

        for invoice_line_id in invoice_id.invoice_line_ids:
            
            invoice_lines.append({
                "productId": invoice_line_id.product_id.code or '',
                "product": invoice_line_id.product_id.name or '',
                "productCode": invoice_line_id.product_id.default_code or '',
                "quantity": invoice_line_id.quantity or 0,
                "unit": units.get(invoice_line_id.product_id.uom_id.name, ''),
                "unitPrice": invoice_line_id.price_unit or 0.0,
                "discountPercent": invoice_line_id.discount or 0.0,
                "vatPercent": invoice_line_id.tax_ids[0].procountor_vat_percent_id and invoice_line_id.tax_ids[
                    0].procountor_vat_percent_id.procountor_vat_percent or '' if len(
                    invoice_line_id.tax_ids) >= 1 else '',
                "vatStatus": str(invoice_line_id.tax_ids[0].procountor_vat_status_id and invoice_line_id.tax_ids[
                    0].procountor_vat_status_id.procountor_vat_status or '' if len(
                    invoice_line_id.tax_ids) >= 1 else 1),
                # "comment": "string",
                # "startDate": "2024-10-21",
                # "endDate": "2024-10-21",
                # "headerText": "string",
                # "explanationText": "string"
            })
        return invoice_lines

    def prepare_customer_address_info(self, customer_id):
        """This method use for prepare customer address info
            author - mithilesh lathiya"""
        return {
            "name": customer_id.name or '',
            "specifier": "",
            "street": "{} {}".format(customer_id.street,
                                     customer_id.street2) if customer_id.street2 else customer_id.street,
            "zip": customer_id.zip or '',
            "city": customer_id.city or '',
            "country": (customer_id.country_id and customer_id.country_id.name).replace(' ', '_').upper() or '',
            "subdivision": ""
        }

    def prepare_invoice_api_request_data(self, invoice_id):
        """This method used for prepare api request data of export invoice.
            author - mithilesh lathiya """
        customer_id = invoice_id.partner_id
        customer_delivery_address = customer_id.child_ids and customer_id.child_ids.filtered(
            lambda x: x.type == 'delivery')
        customer_invoice_address = customer_id.child_ids and customer_id.child_ids.filtered(
            lambda x: x.type == 'invoice')

        company_currency = invoice_id.company_id.currency_id
        customer_currency = invoice_id.currency_id
        date = invoice_id.invoice_date or datetime.today().date()

        payload = {
            "partnerId": customer_id.procountor_customer_id or 0,
            "type": "SALES_INVOICE",
            "status": "UNFINISHED",
            "date": invoice_id.invoice_date.strftime("%Y-%m-%d"),
            "counterParty": {
                "contactPersonName": customer_id.name or '',
                "identifier": "SALES_INVOICE",
                # "customerNumber": customer_id.procountor_customer_id or '',
                "email": customer_id.email or self.env.company.partner_id.email or '',
                "counterPartyAddress": self.prepare_customer_address_info(customer_id),
                "bankAccount": {
                    "accountNumber": customer_id.bank_ids and customer_id.bank_ids.mapped('acc_number')[0] or '',
                    "bic": ""
                },
                # "einvoiceAddress": {
                #     "operator": "string",
                #     "address": "string",
                #     "ediId": "string"
                # }
            },
            "billingAddress": self.prepare_customer_address_info(
                customer_invoice_address[0] if customer_invoice_address else customer_id),
            "deliveryAddress": self.prepare_customer_address_info(
                customer_delivery_address[0] if customer_delivery_address else customer_id),
            "paymentInfo": {
                "paymentMethod": customer_id.procountor_payment_method or '',
                "currency": customer_id.currency_id.name if customer_id.currency_id else customer_id.property_product_pricelist.currency_id.name,
                "bankAccount": {
                    "accountNumber": "FI7099899900012946",  # Need to discuss with jigarbhai
                    "bic": ""
                },
                "dueDate": invoice_id.invoice_date_due.strftime("%Y-%m-%d"),
                "currencyRate": customer_currency._get_conversion_rate(company_currency, customer_currency,
                                                                       invoice_id.company_id, date),
                "paymentTermPercentage": 0,
                "bankReferenceCode": "",
                "bankReferenceCodeType": invoice_id.procountor_bank_reference_code_type or '',
                "clearingCode": invoice_id.procountor_clearing_code or ''
            },
            "extraInfo": {
                "accountingByRow": invoice_id.procountor_accounting_by_row,
                "unitPricesIncludeVat": invoice_id.procountor_unit_prices_include_vat
            },
            "discountPercent": 8,  # Invoice discount percentage. Scale: 4.
            "orderReference": invoice_id.name,
            "invoiceRows": self.prepare_invoice_line_data(invoice_id),
            "vatStatus": invoice_id.procountor_vat_status_id and invoice_id.procountor_vat_status_id.procountor_vat_status or '',
            "originalInvoiceNumber": invoice_id.invoice_origin or invoice_id.name or '',

            # "deliveryStartDate": "2024-10-21",
            # "deliveryEndDate": "2024-10-21",
            "deliveryMethod": invoice_id.procountor_delivery_method,
            # "deliveryInstructions": "string",
            "invoiceChannel": invoice_id.procountor_invoice_channel,
            # "penaltyPercent": 0,
            "language": "ENGLISH",
            # "invoiceTemplateId": 0,
            # "additionalInformation": "string",
            "vatCountry": "FINLAND",
            # "notes": "string",
        }
        request_data = json.dumps(payload)
        return request_data

    def export_invoice_data_odoo_to_procountor(self, procountor_instance=False, active_invoice_ids=False, log_id=False):
        log_id = log_id if log_id else self.env['procountor.log'].generate_procountor_logs('invoice', 'export',
                                                                                           procountor_instance,
                                                                                           'Process Started')
        is_error = False
        for invoice_id in active_invoice_ids:
            try:
                procountor_customer_id = invoice_id.partner_id and invoice_id.partner_id.procountor_customer_id
                if not procountor_customer_id:
                    error = self.env['export.customer.to.procountor'].export_or_update_customer_to_procountor(
                        procountor_instance, invoice_id.partner_id, log_id)
                    if error:
                        is_error = True
                        error_msg = 'Getting some error when try to export invoice {} from odoo to procountor.'.format(
                            invoice_id.name)
                        self.env['procountor.log.line'].generate_procountor_process_line('invoice', 'export',
                                                                                         procountor_instance,
                                                                                         error_msg,
                                                                                         'Customer {0} not available in procountor,please check customer details properly.Invoice No : {1}'.format(
                                                                                             invoice_id.partner_id.name,
                                                                                             invoice_id.name),
                                                                                         '', log_id,
                                                                                         True)
                        continue
                invoice_api_request_data = self.prepare_invoice_api_request_data(invoice_id)
                headers = {
                    'accept': 'application/json',
                    'Authorization': 'Bearer {0}'.format(procountor_instance.procountor_api_access_token),
                    'Content-Type': 'application/json'
                }
                api_url = "{0}/invoices".format(
                    procountor_instance.procountor_api_url)
                response_status, response_data = procountor_instance.procountor_api_calling("POST", api_url,
                                                                                            invoice_api_request_data,
                                                                                            headers)

                if response_status and response_data.get('id'):
                    invoice_id.export_invoice_to_procountor = True
                    invoice_id.procountor_instance_id = procountor_instance
                    invoice_id.procountor_invoice_id = response_data.get('id')
                    message = 'Successfully Export Invoice To Procountor : {}'.format(
                        invoice_id.name)
                    self.env['procountor.log.line'].generate_procountor_process_line('invoice', 'export',
                                                                                     procountor_instance,
                                                                                     message,
                                                                                     invoice_api_request_data,
                                                                                     response_data, log_id,
                                                                                     False)
                else:
                    is_error = True
                    error_msg = 'Getting some error when try to export invoice {} from odoo to procountor.'.format(
                        invoice_id.name)
                    self.env['procountor.log.line'].generate_procountor_process_line('invoice', 'export',
                                                                                     procountor_instance,
                                                                                     error_msg,
                                                                                     invoice_api_request_data,
                                                                                     response_data, log_id,
                                                                                     True)
            except Exception as error:
                is_error = True
                error_msg = 'Getting some error when try to export invoice from odoo to procountor.'
                self.env['procountor.log.line'].generate_procountor_process_line('invoice', 'export',
                                                                                 procountor_instance,
                                                                                 error_msg,
                                                                                 invoice_api_request_data, error,
                                                                                 log_id,
                                                                                 True)
        return is_error
        # if is_error:
        #     return {
        #         'type': 'ir.actions.client',
        #         'tag': 'display_notification',
        #         'params': {
        #             'title': 'Getting some issue while export invoice!',
        #             'message': 'Please Check Following Log : {0}'.format(log_id.name),
        #             'type': 'warning',
        #             'sticky': False,
        #             'next': {'type': 'ir.actions.act_window_close'},
        #         }
        #     }
        # log_id.procountor_operation_message = 'Process Has Been Finished'
        # if not log_id.procountor_operation_line_ids:
        #     log_id.unlink()

    def fetch_invoice_payment_procountor_to_odoo(self, procountor_instance=False, previous_payment_id=False,log_id=False):
        try:
            procountor_instance = self.env['procountor.instance'].browse(
                procountor_instance) if procountor_instance else self.procountor_instance_id
            log_id =log_id if log_id else self.env['procountor.log'].generate_procountor_logs('payment', 'import', procountor_instance,
                                                                         'Process Started')
            procountor_invoice_ids = self.search(
                [('export_invoice_to_procountor', '=', True), ('procountor_invoice_id', '!=', False),
                 ('payment_state', 'in', ['not_paid', 'partial']),
                 ('procountor_instance_id', '=', procountor_instance.id)]).mapped('procountor_invoice_id')
            is_error = False
            if procountor_invoice_ids:
                print("123")
                base_url = "{0}/payments/".format(procountor_instance.procountor_api_url)
                headers = {
                    'accept': 'application/json',
                    'Authorization': 'Bearer {0}'.format(procountor_instance.procountor_api_access_token)
                }
                days = procountor_instance.invoice_payment_days_limit or 1
                start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                end_date = datetime.today().strftime("%Y-%m-%d")
                query_params = "&".join([f"invoiceId={id}" for id in procountor_invoice_ids])
                import_payment_api_url = (
                    f"{base_url}?startDate={start_date}&endDate={end_date}&{query_params}&orderById=ASC&size=25")
                updated_payment_api_url = (
                    f"{import_payment_api_url}&previousId={previous_payment_id}"
                    if self._context.get('check_pagination') else import_payment_api_url)
                response_status, response_data = procountor_instance.procountor_api_calling("GET",
                                                                                            updated_payment_api_url,
                                                                                            {}, headers)
                if response_status and response_data.get('results'):
                # if response_status:
                #     response_data = {
                #         "results": [
                #             {
                #                 "id": 0,
                #                 "invoiceId": 8464298,
                #                 "paymentDate": "2024-12-04",
                #                 "amount": 80,
                #                 "receiverName": "123",
                #                 "status": "APPROVED",
                #                 "serviceCharge": "BOTH_PAY_OWN_FEES"
                #             }
                #         ],
                #         "meta": {
                #             "pageNumber": 0,
                #             "pageSize": 0,
                #             "resultCount": 0,
                #             "totalCount": 0
                #         }
                #     }
                    procountor_invoice_payments = response_data.get('results')
                    for procountor_invoice_payment in procountor_invoice_payments:
                        procountor_invoice_id = procountor_invoice_payment.get('invoiceId')
                        invoice_id = self.search([('procountor_invoice_id', '=', procountor_invoice_id)])
                        if invoice_id:
                            payment_amount = procountor_invoice_payment.get('amount')
                            payment_date = procountor_invoice_payment.get('paymentDate')
                            if procountor_instance.journal_id:
                                journal_id = procountor_instance.journal_id
                            else:
                                journal_id = self.env['account.journal'].search([('type', 'in', ['cash','bank'])], limit=1)
                            payment_method_line = journal_id.inbound_payment_method_line_ids.filtered(
                                lambda x: x.name.lower() == 'manual')
                            pmt_wizard = self.env['account.payment.register'].with_context(
                                active_model='account.move',
                                active_ids=invoice_id.ids).create(
                                {'payment_date': payment_date,
                                 'journal_id': journal_id and journal_id.id or '',
                                 'payment_method_line_id': payment_method_line.id,
                                 'currency_id': invoice_id.currency_id and invoice_id.currency_id.id,
                                 'amount': payment_amount,
                                 'group_payment': True,
                                 'communication': invoice_id.name or invoice_id.display_name or ' '})
                            pmt_wizard._create_payments()
                            message = 'Payment {0} Created Successfully In Odoo for invoice : .'.format(procountor_invoice_payment.get('invoiceId'))
                            self.env['procountor.log.line'].generate_procountor_process_line('payment', 'import',
                                                                                             procountor_instance,
                                                                                             message,
                                                                                             False, response_data,
                                                                                             log_id,
                                                                                             False)
                        else:
                            is_error = True
                            error_msg = 'We are not find this invoice : {0} in odoo for payment'.format(procountor_invoice_id)
                            self.env['procountor.log.line'].generate_procountor_process_line('payment', 'import',
                                                                                             procountor_instance,
                                                                                             error_msg,
                                                                                             base_url,
                                                                                             response_data, log_id,
                                                                                             True)
                    previous_payment_id = procountor_invoice_payments[-1].get('id')
                    self.with_context(check_pagination=True).fetch_invoice_payment_procountor_to_odoo(procountor_instance.id,
                                                                                                previous_payment_id,
                                                                                                log_id)
                else:
                    if response_status:
                        return True
                    else:
                        is_error = True
                        error_msg = 'Getting some error when try to import invoice payments from procountor to odoo.'
                        self.env['procountor.log.line'].generate_procountor_process_line('payment', 'import',
                                                                                         procountor_instance,
                                                                                         error_msg,
                                                                                         base_url,
                                                                                         response_data, log_id,
                                                                                         True)
            else:
                is_error = True
                error_msg = 'We are not Found Any Invoice For Import Payments'
                self.env['procountor.log.line'].generate_procountor_process_line('payment', 'payment',
                                                                                 procountor_instance,
                                                                                 error_msg,
                                                                                 False,
                                                                                 error_msg, log_id,
                                                                                 True)
        except Exception as e:
            error_msg = 'Something Went Wrong : {}'.format(e)
            self.env['procountor.log.line'].generate_procountor_process_line('payment', 'import',
                                                                             procountor_instance,
                                                                             error_msg,
                                                                             False,
                                                                             error_msg, log_id,
                                                                             True)

        log_id.procountor_operation_message = 'Process Has Been Finished'
        if not log_id.procountor_operation_line_ids:
            log_id.unlink()
