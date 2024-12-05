import logging
import json
from datetime import datetime
from odoo import models, fields, _

_logger = logging.getLogger("Procountor")


class ExportInvoiceToProcountor(models.TransientModel):
    """
    Model for adding customer into procountor.
    """
    _name = "export.invoice.to.procountor"
    _description = "Export Invoice To Procountor"

    procountor_instance_id = fields.Many2one("procountor.instance", string="Procountor Instance")

    def export_invoice_to_procountor(self):
        """This method use for export invoice from odoo to procountor
            author - mithilesh lathiya
            """
        procountor_instance = self.procountor_instance_id
        active_invoice_ids = self.env["account.move"].browse(self._context.get("active_ids", [])).filtered(
            lambda x: x.state == 'posted' and not x.export_invoice_to_procountor == True)

        log_id = self.env['procountor.log'].generate_procountor_logs('invoice', 'export', procountor_instance,
                                                                     'Process Started')
        is_error = False
        if active_invoice_ids:
            error = self.env['account.move'].export_invoice_data_odoo_to_procountor(procountor_instance, active_invoice_ids,
                                                                            log_id)
            if error:
                is_error = True

        else:
            is_error = True
            message = "We did not find any invoice for export in procountor."
            self.env['procountor.log.line'].generate_procountor_process_line('invoice', 'export',
                                                                             procountor_instance,
                                                                             message, False, message, log_id, True)
        if is_error:
            log_id.procountor_operation_message = 'Process Has Been Finished'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Getting some issue while export invoice!',
                    'message': 'Please Check Following Log : {0}'.format(log_id.name),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        log_id.procountor_operation_message = 'Process Has Been Finished'
        if not log_id.procountor_operation_line_ids:
            log_id.unlink()
