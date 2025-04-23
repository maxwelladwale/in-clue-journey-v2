from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    def _mark_done(self):
        """Override to hook into survey completion"""
        res = super(SurveyUserInput, self)._mark_done()

        for record in self:
            _logger.info("🎯 Survey submitted by partner ID: %s for survey ID: %s", record.partner_id.id, record.survey_id.id)

            # Look for related inclue.participation record
            participation = self.env['inclue.participation'].search([
                ('survey_id', '=', record.survey_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('user_input_id', '=', record.id),
                ('completed', '=', False)
            ], limit=1)

            if participation:
                _logger.info("✅ Marking participation ID %s as completed", participation.id)
                participation.write({
                    'completed': True,
                    'date_completed': fields.Datetime.now(),
                })
            else:
                _logger.warning("⚠️ No matching participation found for survey ID: %s, partner ID: %s", record.survey_id.id, record.partner_id.id)

        return res
