from odoo import models, fields, api

class EventEvent(models.Model):
    _inherit = 'event.event'
    
    facilitator_id = fields.Many2one(
        'res.partner', 
        string='Facilitator',
        domain="[('is_facilitator', '=', True)]",
        help="Main facilitator for this event"
    )
    facilitator_type = fields.Selection([
        ('internal', 'Internal'), 
        ('external', 'External')
    ], string='Facilitator Type', compute='_compute_facilitator_type', store=True)
    
    @api.depends('facilitator_id', 'facilitator_id.category_id')
    def _compute_facilitator_type(self):
        for event in self:
            if not event.facilitator_id:
                event.facilitator_type = False
                continue
                
            # Check categories to determine if internal or external
            categories = event.facilitator_id.category_id.mapped('name')
            if 'Internal Facilitator' in categories:
                event.facilitator_type = 'internal'
            elif 'External Facilitator' in categories:
                event.facilitator_type = 'external'
            else:
                event.facilitator_type = False