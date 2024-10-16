from odoo import models, fields, api
import pprint


class ProcountorLog(models.Model):
    _name = 'procountor.log'
    _inherit = ['mail.thread']
    _description = 'Logs'
    _order = 'id DESC'

    name = fields.Char(
        string='Name'
    )
    procountor_operation_name = fields.Selection(
        selection=[('product', 'Product'), ('customer', 'Customer'),
                   ('product_attribute', 'Product Attribute'),
                   ('product_variant', 'Product Variant'),
                   ('invoice', 'Invoice')],
        string="Process Name")
    procountor_operation_type = fields.Selection(
        selection=[('export', 'Export'), ('import', 'Import'),
                   ('update', 'Update'), ('delete', 'Cancel / Delete')],
        string="Process Type"
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id
    )
    instance_id = fields.Many2one(
        comodel_name='procountor.instance',
        string='Instance',
        help='Instance'
    )
    procountor_operation_line_ids = fields.One2many(
        comodel_name="procountor.log.line",
        inverse_name="procountor_operation_id",
        string="Operation"
    )
    procountor_operation_message = fields.Char(
        string="Message"
    )
    create_date = fields.Datetime(
        string='Created on'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        In this method auto generated sequence added in log name.
        """
        for vals in vals_list:
            sequence = self.env.ref("procountor_odoo_connector.seq_procountor_log")
            name = sequence and sequence.next_by_id() or '/'
            company_id = self._context.get('company_id', self.env.user.company_id.id)
            if type(vals) == dict:
                vals.update({'name': name, 'company_id': company_id})
        return super(ProcountorLog, self).create(vals_list)

    def unlink(self):
        """
        This method is used for unlink appropriate log and logline both from both log model
        """
        for selected_main_log in self:
            if selected_main_log.procountor_operation_line_ids:
                selected_main_log.procountor_operation_line_ids.unlink()
        return super(ProcountorLog, self).unlink()

    def generate_procountor_logs(self, procountor_operation_name, procountor_operation_type, instance,
                              procountor_operation_message):
        """
        From this method procountor log's record will create.
        """
        log_id = self.create({
            'procountor_operation_name': procountor_operation_name,
            'procountor_operation_type': procountor_operation_type,
            'instance_id': instance.id,
            'procountor_operation_message': procountor_operation_message
        })
        return log_id


class ProcountorLogLine(models.Model):
    _name = 'procountor.log.line'
    _rec_name = 'procountor_operation_id'
    _description = 'Process Details Line'

    _order = 'id DESC'

    procountor_operation_id = fields.Many2one(
        comodel_name='procountor.log',
        string='Log'
    )
    procountor_operation_name = fields.Selection(
        selection=[('product', 'Product'), ('customer', 'Customer'),
                   ('product_attribute', 'Product Attribute'),
                   ('product_variant', 'Product Variant'),
                   ('invoice', 'Invoice')],
        string="Process Name"
    )
    procountor_operation_type = fields.Selection(
        selection=[('export', 'Export'), ('import', 'Import'),
                   ('update', 'Update'), ('delete', 'Cancel / Delete')],
        string="Process Type"
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.user.company_id
    )
    instance_id = fields.Many2one(
        comodel_name='procountor.instance',
        string='Instance',
        help='Instance')
    process_request_message = fields.Char(
        string="Request Message"
    )
    process_response_message = fields.Text(
        string="Response Message"
    )
    fault_operation = fields.Boolean(
        string="Fault Process",
        default=False
    )
    procountor_operation_message = fields.Char(
        string="Message"
    )
    create_date = fields.Datetime(
        string='Created on'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if type(vals) == dict:
                procountor_operation_id = vals.get('procountor_operation_id')
                operation = procountor_operation_id and self.env['procountor.log'].browse(procountor_operation_id) or False
                company_id = operation and operation.company_id.id or self.env.user.company_id.id
                vals.update({'company_id': company_id})
        return super(ProcountorLogLine, self).create(vals_list)

    def generate_procountor_process_line(self, procountor_operation_name, procountor_operation_type, instance,
                                      procountor_operation_message, process_request_message, process_response_message,
                                      log_id, fault_operation=False):
        """
        From this method procountor log line's record will create.
        """
        vals = {
            'procountor_operation_name': procountor_operation_name,
            'procountor_operation_type': procountor_operation_type,
            'instance_id': instance.id,
            'procountor_operation_message': procountor_operation_message,
            'process_request_message': pprint.pformat(process_request_message) if process_request_message else False,
            'process_response_message': pprint.pformat(process_response_message) if process_response_message else False,
            'procountor_operation_id': log_id and log_id.id,
            'fault_operation': fault_operation
        }
        log_line_id = self.create(vals)
        return log_line_id
