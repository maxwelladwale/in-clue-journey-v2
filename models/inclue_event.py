from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class EventEvent(models.Model):
    _inherit = 'event.event'

    survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string='Survey',
        help="Survey to be sent to attendees after the event."
    )
    survey_sent = fields.Boolean(
        string='Survey Sent',
        default=False,
        help="Indicates if the survey has been sent to attendees."
    )

    # In the EventEvent class, add this method:
    def get_next_session_type(self, partner):
        participation_model = self.env['inclue.participation']
        participations = participation_model.search([
            # ('event_id', '=', event.id),
            ('partner_id', '=', partner.id),
            ('survey_sent', '=', True)
        ])

        completed_sessions = {p.session_type for p in participations if p.session_type}

        # Define session types in order
        session_types = ['kickoff', 'followup1', 'followup2', 'followup3', 'followup4', 'followup5', 'followup6']
        
        for session_type in session_types:
            if session_type not in completed_sessions:
                return session_type  # First uncompleted session

        return None  # All sessions done
    def action_send_inclue_survey(self):
        _logger.info("action_send_inclue_survey() called for event IDs: %s", self.ids)
        participation_model = self.env['inclue.participation']

        for event in self:
            _logger.info("Processing Event ID: %s", event.id)

            # Skip if survey already sent
            if event.survey_sent:
                _logger.info("Survey already sent for event ID %s. Skipping.", event.id)
                event.message_post(body="ℹ️ Surveys have already been sent for this event. Skipping.")
                continue

            if not event.survey_id:
                _logger.warning("No survey linked to event ID: %s. Skipping survey sending.", event.id)
                event.message_post(body="⚠️ No survey linked to event. Skipping survey sending.")
                continue

            emails_sent = 0
            emails_failed = 0

            for registration in event.registration_ids.filtered(lambda r: r.state != 'cancel'):
                partner = registration.partner_id
                if not partner or not partner.email:
                    _logger.warning("Skipping registration ID %s: Missing partner or email.", registration.id)
                    continue

                _logger.info("Processing registration ID: %s for partner: %s", registration.id, partner.name)

                participation = participation_model.search([
                    ('event_id', '=', event.id),
                    ('partner_id', '=', partner.id),
                    ('survey_id', '=', event.survey_id.id),
                ], limit=1)

                if participation:
                    if participation.survey_sent:
                        _logger.info("Survey already sent to partner: %s. Skipping.", partner.name)
                        continue
                    _logger.info("Existing participation record found with ID: %s for partner: %s", participation.id, partner.name)
                else:
                    _logger.info("No participation record found. Creating one for partner: %s", partner.name)
                    session_type = self.get_next_session_type(partner)
                    if not session_type:
                        _logger.info("All sessions completed for partner %s. No new participation needed.", partner.name)
                        continue
                    participation = participation_model.create({
                        'event_id': event.id,
                        'partner_id': partner.id,
                        'survey_id': event.survey_id.id,
                        'session_type': session_type,  # ✅ Use the calculated one
                        'survey_sent': False,
                    })
                    _logger.info("Assigning session_type '%s' to participation for partner %s", session_type, partner.name)
                    _logger.info("Created new participation record with ID: %s", participation.id)

                if participation.send_survey_email():
                    participation.survey_sent = True
                    emails_sent += 1
                else:
                    emails_failed += 1

            _logger.info("For event ID %s, emails sent: %s, emails failed: %s", event.id, emails_sent, emails_failed)

            if emails_sent:
                event.survey_sent = True
                event.message_post(body=f"✅ Survey sent to {emails_sent} attendee(s).")
            if emails_failed:
                event.message_post(body=f"⚠️ Failed to send survey to {emails_failed} attendee(s).")