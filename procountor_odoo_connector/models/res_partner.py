from odoo import models, fields


class SalesOrder(models.Model):
    _inherit = 'res.partner'

    procountor_customer_id = fields.Char(string="Procountor Customer ID",
                                         help="This is just a reference of procountor customer identifier",
                                         tracking=True, copy=False)
    procountor_instance_id = fields.Many2one('procountor.instance', string="Procountor Instance", copy=False,
                                             help="This field show the instance details of Procountor", tracking=True)
    procountor_payment_method = fields.Selection([('BANK_TRANSFER', 'BANK_TRANSFER'),
                                                  ('DIRECT_DEBIT', 'DIRECT_DEBIT'),
                                                  ('DIRECT_PAYMENT', 'DIRECT_PAYMENT'),
                                                  ('CLEARING', 'CLEARING'),
                                                  ('CREDIT_CARD_CHARGE', 'CREDIT_CARD_CHARGE'),
                                                  ('FOREIGN_PAYMENT', 'FOREIGN_PAYMENT'),
                                                  ('OTHER', 'OTHER'),
                                                  ('CASH', 'CASH'),
                                                  ('DOMESTIC_PAYMENT_PLUSGIRO', 'DOMESTIC_PAYMENT_PLUSGIRO'),
                                                  ('DOMESTIC_PAYMENT_BANKGIRO', 'DOMESTIC_PAYMENT_BANKGIRO'),
                                                  ('DOMESTIC_PAYMENT_CREDITOR', 'DOMESTIC_PAYMENT_CREDITOR'),
                                                  ('NETS', 'NETS')], string="Procountor Payment Method", copy=False,
                                                 tracking=True,
                                                 default="BANK_TRANSFER", help="Payment method of the partner")
    procountor_customer_type = fields.Selection([('CUSTOMER', 'CUSTOMER'),
                                                 ('PERSON', 'PERSON')], copy=False, default="CUSTOMER", tracking=True,
                                                help="Type of partner / customer")

    def prepare_vals_for_customer(self, instance, response_data, address):
        """This method use for prepare customer address info
        author - Mithilesh Lathiya"""
        return {'name': address.get('name') or response_data.get('name') or '',
                'street': address.get('street') or '',
                'city': address.get('city') or '',
                'zip': address.get('zip') or '',
                'country_id': self.env['res.country'].search(
                    [('name', '=', (address.get('country') or '').replace('_', ' ').title())],
                    limit=1).id,
                'procountor_instance_id': instance.id
                }

    def import_customer_procountor_to_odoo(self, instance, previous_customer_id=False, log_id=False):
        """This method use for import customer from procountor to odoo
        author : mithilesh lathiya"""

        base_url = "{0}/businesspartners/".format(instance.procountor_api_url)
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {0}'.format(instance.procountor_api_access_token)
        }
        log_id = log_id if log_id else self.env['procountor.log'].generate_procountor_logs('customer', 'import',
                                                                                           instance,
                                                                                           'Process Started')
        is_error = False
        try:
            import_customers_api_url = f"{base_url}?size=25&type=CUSTOMER"
            updated_url = f"{import_customers_api_url}&previousId={previous_customer_id}" if self._context.get(
                'check_pagination') else import_customers_api_url
            response_status, response_data = instance.procountor_api_calling("GET",
                                                                             updated_url,
                                                                             {}, headers)
            if response_status and response_data.get('results'):
                partner_obj = self.env["res.partner"]
                procountor_customers = response_data.get('results')
                for customer in procountor_customers:
                    import_customer_api_url = base_url + "{0}".format(customer.get('id'))
                    response_status, response_data = instance.procountor_api_calling("GET",
                                                                                     import_customer_api_url,
                                                                                     {}, headers)
                    if response_status and response_data.get('id'):
                        existing_customer_id = partner_obj.search(
                            [('procountor_customer_id', '=', response_data.get('id'))], limit=1)
                        if not existing_customer_id:
                            invoicing_info = response_data.get('invoicingInfo', {})
                            email = invoicing_info.get('email', False)
                            if email:
                                existing_customer_id = partner_obj.search([('email', '=', email)], limit=1)
                        if existing_customer_id:
                            message = 'Customer {0} Already Exist In Odoo.'.format(customer.get('name'))
                            self.env['procountor.log.line'].generate_procountor_process_line('customer', 'import',
                                                                                             instance,
                                                                                             message,
                                                                                             False, response_data,
                                                                                             log_id,
                                                                                             False)
                            continue
                        else:
                            customer_address_vals = self.prepare_vals_for_customer(instance, response_data,
                                                                                   response_data.get('address'))
                            customer_address_vals.update({'procountor_customer_id': response_data.get('id'),
                                                          'email': response_data.get(
                                                              'invoicingInfo') and response_data.get(
                                                              'invoicingInfo').get('email') or '',
                                                          'phone': response_data.get(
                                                              'registryInfo') and response_data.get(
                                                              'registryInfo').get('phone') or '',
                                                          'mobile': response_data.get(
                                                              'registryInfo') and response_data.get(
                                                              'registryInfo').get('mobilePhone') or '',
                                                          'company_type': 'company'})
                            parent_customer_id = partner_obj.create(customer_address_vals)
                            if response_data.get('billingAddress'):
                                billing_address_vals = self.prepare_vals_for_customer(instance, response_data,
                                                                                      response_data.get(
                                                                                          'billingAddress'))
                                billing_address_vals.update({'type': 'invoice', 'parent_id': parent_customer_id.id})
                                partner_obj.create(billing_address_vals)
                            if response_data.get('deliveryAddress'):
                                delivery_address_vals = self.prepare_vals_for_customer(instance, response_data,
                                                                                       response_data.get(
                                                                                           'billingAddress'))
                                delivery_address_vals.update({'type': 'delivery', 'parent_id': parent_customer_id.id})
                                partner_obj.create(delivery_address_vals)
                            if response_data.get('contactPersons'):
                                contact_person_address = response_data.get('contactPersons')
                                for contact_person in contact_person_address:
                                    partner_obj.create({'name': contact_person.get('name') or '',
                                                        'email': contact_person.get('email') or '',
                                                        'phone': contact_person.get('phone') or '',
                                                        'type': 'contact',
                                                        'parent_id': parent_customer_id.id})
                            message = 'Customer {0} Created Successfully In Odoo.'.format(customer.get('name'))
                            self.env['procountor.log.line'].generate_procountor_process_line('customer', 'import',
                                                                                             instance,
                                                                                             message,
                                                                                             False, response_data,
                                                                                             log_id,
                                                                                             False)

                    else:
                        is_error = True
                        error_msg = 'Getting some error when try to import customer {} from procountor to odoo.'.format(
                            customer.get('name'))
                        self.env['procountor.log.line'].generate_procountor_process_line('customer', 'import',
                                                                                         instance, error_msg,
                                                                                         import_customer_api_url,
                                                                                         response_data, log_id, True)
                previous_customer_id = procountor_customers[-1].get('id')
                self.with_context(check_pagination=True).import_customer_procountor_to_odoo(instance,
                                                                                            previous_customer_id,
                                                                                            log_id)
            else:
                if response_status:
                    return True
                else:
                    is_error = True
                    error_msg = 'Getting some error when try to import customer from procountor to odoo.'
                    self.env['procountor.log.line'].generate_procountor_process_line('customer', 'import',
                                                                                     instance,
                                                                                     error_msg,
                                                                                     base_url,
                                                                                     response_data, log_id,
                                                                                     True)
        except Exception as error:
            is_error = True
            error_msg = 'Getting some error when try to import customer from procountor to odoo.'
            self.env['procountor.log.line'].generate_procountor_process_line('customer', 'import',
                                                                             instance,
                                                                             error_msg,
                                                                             base_url,
                                                                             error, log_id,
                                                                             True)
        log_id.procountor_operation_message = 'Process Has Been Finished'
        if not log_id.procountor_operation_line_ids:
            log_id.unlink()
        if is_error:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Getting some issue while import customer!',
                    'message': 'Please Check Following Log : {0}'.format(log_id.name),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
