from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class InclueParticipation(models.Model):
    _name = 'inclue.participation'
    _description = 'Tracks user participation in the iN-Clue journey'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Participant',
        required=True,
        ondelete='cascade',
        help="The partner associated with this participation."
    )
    event_id = fields.Many2one(
        comodel_name='event.event',
        string='Event',
        required=True,
        ondelete='cascade',
        help="The event associated with this participation."
    )
    survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string='Linked Survey',
        ondelete='cascade',
        help="The survey associated with this participation."
    )
    user_input_id = fields.Many2one(
        comodel_name='survey.user_input',
        string='Survey Response',
        ondelete='cascade',
        help="The user's response to the survey."
    )
    survey_sent = fields.Boolean(
        string='Survey Sent',
        default=False,
        help="Indicates if the survey has been sent to the participant."
    )
    session_type = fields.Selection([
        ('kickoff', 'KickOff Session'),
        ('followup1', 'FollowUp Session 1'),
        ('followup2', 'FollowUp Session 2'),
        ('followup3', 'FollowUp Session 3'),
        ('followup4', 'FollowUp Session 4'),
        ('followup5', 'FollowUp Session 5'),
        ('followup6', 'FollowUp Session 6'),
    ], string='Session Type', default='kickoff')
    completed = fields.Boolean(
        string='Completed',
        default=False,
        help="Indicates if the participation has been completed."
    )
    date_completed = fields.Datetime(
        string='Completion Date',
        help="The date when the participation was completed."
    )
    @api.model
    def create(self, vals):
        _logger.info("Creating a new inclue.participation record with vals: %s", vals)
        participation = super(InclueParticipation, self).create(vals)
        _logger.info("Created inclue.participation record with ID: %s", participation.id)
        if participation.survey_id and not participation.survey_sent:
            _logger.info("Survey is linked and not sent yet. Attempting to send email for participation ID: %s", participation.id)
            participation.send_survey_email()
        return participation

    def send_survey_email(self):
        _logger.info("send_survey_email() called for participation ID: %s", self.id)

        template = self.env.ref('in_clue_event_surveys.mail_template_inclue_survey', raise_if_not_found=False)
        if not template:
            _logger.error("❌ Survey email template not found for participation ID: %s. Skipping survey sending.", self.id)
            return False

        try:
            if not self.user_input_id:
                user_input = self.env['survey.user_input'].create({
                    'survey_id': self.survey_id.id,
                    'partner_id': self.partner_id.id,
                })
                self.user_input_id = user_input.id
                _logger.info("Survey user_input created with ID %s", user_input.id)
            else:
                user_input = self.user_input_id

            if not user_input.access_token:
                _logger.error("❌ No access_token found for user_input ID: %s. Skipping survey email sending.", user_input.id)
                return False

            mail_id = template.send_mail(self.id, force_send=False)
            mail = self.env['mail.mail'].browse(mail_id)

            _logger.info(
                "📨 Mail %s created from template ID %s for %s. State=%s, From=%s, To=%s",
                mail_id, template.id, self.partner_id.email, mail.state, mail.email_from, mail.email_to
            )

            mail.send(raise_exception=True)

            self.survey_sent = True
            _logger.info("✅ Survey email successfully sent to %s (Mail ID: %s)", self.partner_id.email, mail_id)
            return True

        except Exception as e:
            _logger.exception("❌ Failed to send survey email to %s for participation ID: %s. Exception: %s", self.partner_id.email, self.id, e)
            return False

    def unlink(self):
        events = self.mapped('event_id')
        _logger.info("Unlinking participations %s", self.ids)

        for p in self:
            regs = self.env['event.registration'].search([
                ('event_id', '=', p.event_id.id),
                ('partner_id', '=', p.partner_id.id),
            ])
            if regs:
                _logger.info("Deleting %s registrations for event %s / partner %s", regs, p.event_id.id, p.partner_id.id)
                regs.unlink()

            uis = self.env['survey.user_input'].search([
                ('survey_id', '=', p.survey_id.id),
                ('partner_id', '=', p.partner_id.id),
            ])
            if uis:
                _logger.info("Deleting %s survey.user_input for survey %s / partner %s", uis, p.survey_id.id, p.partner_id.id)
                uis.unlink()

        res = super(InclueParticipation, self).unlink()

        for ev in events:
            count = self.env['inclue.participation'].search_count([('event_id', '=', ev.id)])
            if count == 0 and ev.survey_sent:
                _logger.info("Resetting survey_sent on event %s (no participations left)", ev.id)
                ev.survey_sent = False

        return res

    def cron_update_completed_status(self):
        _logger.info("Inclue Cron: Running update for completed status")
        try:
            records = self.search([
                ('completed', '=', False),
                ('user_input_id.state', '=', 'done')
            ])

            _logger.info(f"Inclue Cron: Found {len(records)} records to update.")

            for record in records:
                record.write({
                    'completed': True,
                    'date_completed': fields.Datetime.now()
                })
                _logger.info(f"Inclue Cron: Updated record ID {record.id}")

        except Exception as e:
            _logger.exception("Inclue Cron: Failed to update completed statuses.")

    @api.depends('user_input_id.state')
    def _compute_completion_status(self):
        for rec in self:
            _logger.info("Checking completion status for participation ID: %s", rec.id)
            if rec.user_input_id and rec.user_input_id.state == 'done':
                rec.completed = True
                _logger.info("Participation ID %s marked as completed", rec.id)
                if not rec.date_completed:
                    rec.date_completed = fields.Datetime.now()
                    _logger.info("Completion date set for participation ID %s", rec.id)
            else:
                rec.completed = False
                _logger.info("Participation ID %s not completed", rec.id)
