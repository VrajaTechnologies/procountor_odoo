from odoo import models, fields
from datetime import timedelta


class ProcountorOperations(models.TransientModel):
    _name = 'procountor.operations'
    _description = 'Procountor Import Export'

    def _get_default_instance(self):
        instance_id = self._context.get('active_id')
        return instance_id

    def _get_default_to_date(self):
        to_date = fields.Datetime.now()
        to_date = fields.Datetime.to_string(to_date)
        return to_date

    def _get_default_from_date_product(self):
        instance_id = self.env.context.get('active_id')
        instance_id = self.env['procountor.instance'].search([('id', '=', instance_id)], limit=1)
        from_date = instance_id.last_product_synced_date if instance_id.last_product_synced_date else fields.Datetime.now() - timedelta(
            30)
        from_date = fields.Datetime.to_string(from_date)
        return from_date

    instance_id = fields.Many2one('procountor.instance', string='Instance', default=_get_default_instance)
    procountor_operation = fields.Selection([('import', 'Import')],
                                            string='Procountor Operations', default='import')
    import_operations = fields.Selection(
        selection=[("import_product", "Import Product"), ("import_customers", "Import Customer"),
                   ('import_vats', 'Import Vats')],
        string='Import Operations', default='import_product'
    )

    # Import Product fields
    from_date_product = fields.Datetime(string='From Date', default=_get_default_from_date_product)
    to_date_product = fields.Datetime(string='To Date', default=_get_default_to_date)
    procountor_product_ids = fields.Char(string='Product IDs')

    def execute_process_of_procountor(self):
        instance = self.instance_id

        if self.import_operations == "import_product":
            self.env['procountor.product.listing'].procountor_import_product_list(instance,
                                                                                  self.from_date_product,
                                                                                  self.to_date_product,
                                                                                  self.procountor_product_ids)
        if self.import_operations == "import_customers":
            response = self.env['res.partner'].import_customer_procountor_to_odoo(instance)
        if self.import_operations =='import_vats':
            response = self.env['procountor.vat.status'].import_vat_settings_procountor_to_odoo(instance)
