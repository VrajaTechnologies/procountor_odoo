import requests
import logging
from odoo import models, fields, _, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger("Procountor")


class ProcountorInstance(models.Model):
    _name = 'procountor.instance'
    _description = 'Procountor Instance'

    name = fields.Char(
        string='Name',
        help='Enter Instance Name',
        copy=False,
        tracking=True
    )
    active = fields.Boolean(
        string='Active',
        copy=False,
        tracking=True,
        default=True
    )
    image = fields.Binary(
        string="Image",
        help="Select Image."
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company'
    )
    procountor_api_url = fields.Char(
        string="API URL",
        default="https://pts-procountor.pubdev.azure.procountor.com/api",
        help="Please enter API URL of your procountor account",
        copy=False,
        tracking=True,
    )
    procountor_client_id = fields.Char(
        string="Client ID",
        help='Please enter Client ID of your procountor account',
        copy=False,
        tracking=True
    )
    procountor_client_secret = fields.Char(
        string="Client Secret",
        help='Please enter Client Secret of your procountor account',
        copy=False,
        tracking=True
    )
    procountor_redirect_url = fields.Char(
        string="Redirect URL",
        help='Please enter Redirect URL which is enter by you while register account',
        copy=False,
        tracking=True
    )
    procountor_api_key = fields.Char(
        string="API Key",
        help="Please enter API Key of your procountor account",
        copy=False,
        tracking=True
    )
    procountor_api_access_token = fields.Char(
        string="Access Token",
        help="This field shows api access token, Access tokens are used to authorize calls to API endpoints.",
        copy=False
    )

    @api.model_create_multi
    def create(self, vals):
        """
        In this method auto generated cron added at the time of instance creation.
        """
        instance = super(ProcountorInstance, self).create(vals)
        instance.generate_procountor_access_token()
        instance.generate_procountor_access_token_using_cron()
        return instance

    def procountor_api_calling(self, request_type, api_url, request_data, header):
        """
        This method is used to call API.
        """
        _logger.info("Request API Header:::: %s" % header)
        _logger.info("Request API URL:::: %s" % api_url)
        _logger.info("Request API Data:::: %s" % request_data)
        response_data = requests.request(method=request_type, url=api_url, headers=header, data=request_data)
        if response_data.status_code in [200, 201]:
            response_data = response_data.json()
            _logger.info(">>> Response Data {}".format(response_data))
            return True, response_data
        else:
            return False, response_data.text

    def setup_procountor_automation_cron(self, cron_name, model_name, code_method, interval_number=10,
                                         interval_type='minutes', numbercall=1, nextcall_timegap_minutes=10):
        """
        This method is used to create cron record.
        """
        self.env['ir.cron'].create({
            'name': cron_name,
            'model_id': self.env['ir.model'].search([('model', '=', model_name)]).id,
            'state': 'code',
            'code': code_method,
            'interval_number': interval_number,
            'interval_type': interval_type,
            'numbercall': numbercall,
            'nextcall': datetime.now() + timedelta(minutes=nextcall_timegap_minutes),
            'procountor_instance': self.id
        })
        return True

    def procountor_generate_access_token_cron(self, instance):
        try:
            instance_record = self.env['procountor.instance'].browse(instance)
            instance_record.generate_procountor_access_token()
        except Exception as e:
            _logger.info("Getting an error in Generate Access Token: {0}".format(e))

    def generate_procountor_access_token_using_cron(self):
        code_method = 'model.procountor_generate_access_token_cron({0})'.format(self.id)
        existing_cron = self.env['ir.cron'].search([('code', '=', code_method), ('active', 'in', [True, False])])
        if existing_cron:
            return True
        cron_name = "Procountor: [{0}] generate access token automatically".format(self.name)
        model_name = 'procountor.instance'
        self.setup_procountor_automation_cron(cron_name, model_name, code_method,
                                              interval_type='minutes', interval_number=55,
                                              numbercall=-1, nextcall_timegap_minutes=20)
        return True

    def generate_procountor_access_token(self, instance=False):
        try:
            instance = instance if instance else self
            api_url = "{0}/oauth/token".format(instance.procountor_api_url)
            payload = 'grant_type=client_credentials&client_id={0}&client_secret={1}&redirect_uri={2}&api_key={3}'.format(
                instance.procountor_client_id, instance.procountor_client_secret, instance.procountor_redirect_url,
                instance.procountor_api_key)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            response_status, response_data = instance.procountor_api_calling("POST", api_url, payload, headers)

            if response_status and response_data and response_data.get('access_token'):
                instance.procountor_api_access_token = response_data.get('access_token')
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e)

    def unlink(self):
        """
        This method is used to delete related scheduled actions to particular instance.
        """
        cron_records = self.env['ir.cron'].search([('procountor_instance', 'in', self.ids)])
        if cron_records:
            cron_records.unlink()
        return super(ProcountorInstance, self).unlink()

    def action_procountor_open_instance_view_form(self):
        form_id = self.sudo().env.ref('procountor_odoo_connector.procountor_instance_form')
        action = {
            'name': _('Procountor Instance'),
            'view_id': False,
            'res_model': 'procountor.instance',
            'context': self._context,
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(form_id.id, 'form')],
            'type': 'ir.actions.act_window',
        }
        return action

    def import_customer_procountor_to_odoo(self):
        pass

