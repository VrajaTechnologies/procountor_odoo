import logging
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger("Procountor")


class ProcountorVatStatus(models.Model):
    _name = 'procountor.vat.status'
    _description = 'Procountor Vat Status'
    _rec_name = "procountor_vat_description"

    procountor_vat_status = fields.Integer(string="Procountor Vat Status", copy=False,
                                           help="Procountor Vat Status")
    procountor_vat_description = fields.Char(string="Procountor Vat Description", copy=False,
                                             help="Procountor Vat Description")

    def import_vat_settings_procountor_to_odoo(self, instance):
        """This method is used for import vat status and vat percent in odoo
            Note : We only import those record which is mark as true in sales
            author : Mithilesh Lathiya"""
        vat_api_url = "{0}/vats/default/".format(instance.procountor_api_url)
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {0}'.format(instance.procountor_api_access_token)
        }
        log_id = self.env['procountor.log'].generate_procountor_logs('vat', 'import', instance, 'Process Started')
        is_error = False
        try:
            response_status, response_data = instance.procountor_api_calling("GET", vat_api_url, {}, headers)
            if response_status and response_data.get('vatInformation'):
                for vat_info in response_data.get('vatInformation')[0].get('percentages', []):
                    if vat_info.get('sales'):
                        existing_vat = self.env['procountor.vat.percent'].search(
                            [('procountor_vat_percent', '=', vat_info.get('vatPercent'))])
                        if existing_vat:
                            message = 'Vat Percent {0} Already Exist In Odoo.'.format(vat_info.get('vatPercent'))
                            self.env['procountor.log.line'].generate_procountor_process_line('vat', 'import',
                                                                                             instance, message, False,
                                                                                             response_data, log_id,
                                                                                             False)
                            continue
                        else:
                            vat_percent_id = self.env['procountor.vat.percent'].create(
                                {'procountor_vat_percent': vat_info.get('vatPercent')})
                            message = 'Vat Percent {0} Created Successfully In Odoo.'.format(vat_info.get('vatPercent'))
                            self.env['procountor.log.line'].generate_procountor_process_line('vat', 'import',
                                                                                             instance, message, False,
                                                                                             response_data, log_id,
                                                                                             False)
                # Start code for create vat status in odoo
                for vat_status in response_data.get('vatStatuses'):
                    if vat_status.get('sales'):
                        existing_vat = self.search(
                            [('procountor_vat_status', '=', vat_status.get('vatStatus'))])
                        if existing_vat:
                            message = 'Vat Status {0} Already Exist In Odoo.'.format(vat_status.get('vatStatus'))
                            self.env['procountor.log.line'].generate_procountor_process_line('vat', 'import',
                                                                                             instance, message, False,
                                                                                             response_data, log_id,
                                                                                             False)
                            continue
                        else:
                            vat_status_id = self.create(
                                {'procountor_vat_status': vat_status.get('vatStatus'),
                                 'procountor_vat_description': vat_status.get('description')})
                            message = 'Vat Status {0} -{1} Created Successfully In Odoo.'.format(
                                vat_status.get('vatStatus'), vat_status.get('description'))
                            self.env['procountor.log.line'].generate_procountor_process_line('vat', 'import',
                                                                                             instance, message, False,
                                                                                             response_data, log_id,
                                                                                             False)

            else:
                is_error = True
                error_msg = 'Getting some error when try to import vat from procountor to odoo.'
                self.env['procountor.log.line'].generate_procountor_process_line('vat', 'import', instance, error_msg,
                                                                                 vat_api_url, response_data, log_id,
                                                                                 True)
        except Exception as e:
            is_error = True
            error_msg = 'Getting some error when try to import vat from procountor to odoo.'
            self.env['procountor.log.line'].generate_procountor_process_line('vat', 'import', instance, error_msg,
                                                                             vat_api_url, e, log_id, True)

        log_id.procountor_operation_message = 'Process Has Been Finished'
        if not log_id.procountor_operation_line_ids:
            log_id.unlink()
        if is_error:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Getting some issue while import Vat Settings!',
                    'message': 'Please Check Following Log : {0}'.format(log_id.name),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
