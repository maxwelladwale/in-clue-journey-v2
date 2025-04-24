from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_facilitator = fields.Boolean('Is Facilitator', default=False)
    facilitator_languages = fields.Many2many('res.lang', string='Facilitation Languages')
    facilitator_regions = fields.Many2many('res.country.state', string='Facilitation Regions')
    facilitator_rate = fields.Float('Facilitation Rate', help="Rate for external facilitators per session")
    
    # Add this line to create a reverse relationship from events
    event_ids = fields.One2many('event.event', 'facilitator_id', string='Facilitated Events')
    
    # Statistics fields
    facilitation_count = fields.Integer('Sessions Facilitated', compute='_compute_facilitation_stats')
    participant_count = fields.Integer('Total Participants', compute='_compute_facilitation_stats')
    
    @api.depends('event_ids')  # Now this field exists
    def _compute_facilitation_stats(self):
        for partner in self:
            partner.facilitation_count = len(partner.event_ids)
            
            # Count participants across all events
            registrations = self.env['event.registration'].search([
                ('event_id', 'in', partner.event_ids.ids),
                ('state', '!=', 'cancel')
            ])
            partner.participant_count = len(registrations)