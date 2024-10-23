from odoo import fields, models
from datetime import timedelta
import logging
import re

_logger = logging.getLogger("Procountor Product:")


class ProcountorProductListing(models.Model):
    _name = 'procountor.product.listing'
    _description = 'Procountor Product'
    _rec_name = 'procountor_product_name'

    procountor_product_id = fields.Char(
        string="Zoho Product ID",
        help="This is just a reference of Procountor Product identifier"
    )
    procountor_product_name = fields.Char(
        string="Name"
    )
    procountor_product_unit = fields.Char(
        string="Unit"
    )
    procountor_product_status = fields.Char(
        string="Status"
    )
    procountor_product_rate = fields.Char(
        string="Rate"
    )
    procountor_product_sku = fields.Char(
        string="SKU"
    )
    procountor_hs_code = fields.Char(
        string="HS Code"
    )
    procountor_product_description = fields.Char(
        string="description"
    )
    instance_id = fields.Many2one(
        comodel_name='procountor.instance',
        string='Instance',
        help='Select Instance Id'
    )
    is_product_list = fields.Boolean(
        string="Is Product List"
    )
    product_template_id = fields.Many2one(
        comodel_name='product.template'
    )

    def procountor_import_product_list(self, procountor_instance, from_date=False, to_date=False, procountor_product_ids=False):
        """
        This method is used to import Products from procountor to odoo.
        """
        queue_id_list, product_list = [], []

        from_date = fields.Datetime.now() - timedelta(10) if not from_date else from_date
        to_date = fields.Datetime.now() if not to_date else to_date
        last_synced_date = fields.Datetime.now()

        log_id = self.env['procountor.log'].generate_procountor_logs('product', 'import', procountor_instance,
                                                                     'Process Started')

        if procountor_product_ids:
            procountor_product_list = []
            product_ids_list = list(set(re.findall(re.compile(r"(\d+)"), procountor_product_ids)))
            headers = {
                'accept': 'application/json',
                'Authorization': 'Bearer {0}'.format(procountor_instance.procountor_api_access_token),
                'Content-Type': 'application/json'
            }
            for product_id in product_ids_list:
                api_url = "{0}/products/{1}".format(procountor_instance.procountor_api_url, product_id)
                try:
                    response_status, response_data = procountor_instance.procountor_api_calling('GET', api_url,
                                                                                                '', headers)
                    if response_status and response_data.get('id'):

                        ### Create product code, for odoo product & product listing table both ###

                        message = 'Product successfully created in Odoo from Procountor : {}'.format(response_data.get('name'))
                        self.env['procountor.log.line'].generate_procountor_process_line('product', 'import',
                                                                                         procountor_instance,
                                                                                         message, False, response_data,
                                                                                         log_id, False)
                    else:
                        is_error = True
                        error_msg = 'Getting some error when try to import product {} => {}'.format(product_id,
                                                                                                    response_data)
                        self.env['procountor.log.line'].generate_procountor_process_line('product', 'import',
                                                                                         procountor_instance, error_msg,
                                                                                         False, response_data, log_id,
                                                                                         True)
                except Exception as error:
                    is_error = True
                    error_msg = 'Getting some error when try to import product from odoo to procountor.'
                    self.env['procountor.log.line'].generate_procountor_process_line('product', 'import',
                                                                                     procountor_instance, error_msg,
                                                                                     False, error, log_id, True)
        else:
            pass
            # CODE for fetch product date wise

        if is_error:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Getting some issue while import product!',
                    'message': 'Please Check Following Log : {0}'.format(log_id.name),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        log_id.procountor_operation_message = 'Process Has Been Finished'
        if not log_id.procountor_operation_line_ids:
            log_id.unlink()
        return queue_id_list
